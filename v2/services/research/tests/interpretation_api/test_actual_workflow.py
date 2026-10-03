"""Independent HTTP owners preserve useful weak evidence, original pins and later corrections."""
import json
import os
import sys
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pytest
from amphora_contracts_research import (
    AssessObservationUseRequest,
    NormalizationTargetRecord,
    NormalizeObservationRequest,
    ObservationRevision,
)
from amphora_research.scientific_api.operations import ACTIONS

from ..assessment.live_peers import Owner
from ..scientific_api.test_actual_workflow import denied
from .actual_fixtures import InterpretationPeers

pytestmark = pytest.mark.postgres


def wire(record):
    return record.model_dump(mode="json")


def selection(request):
    return {"scope":wire(request.profile.scope),"kind":request.kind,"interpretation_id":request.interpretation_id}


def test_actual_interpretation_correction_and_offline_replacement(ledger,tmp_path):
    data_python = os.environ.get("AMPHORA_TEST_DATA_PYTHON")
    research_python = os.environ.get("AMPHORA_TEST_RESEARCH_INTERPRETATION_PYTHON")
    replacement_python = os.environ.get("AMPHORA_TEST_RESEARCH_INTERPRETATION_REPLACEMENT_PYTHON")
    if not all((data_python,research_python,replacement_python)):
        pytest.skip("Independent Data/Research and fresh interpretation replacement interpreters required")
    peers = InterpretationPeers(ledger,tmp_path,data_python)
    research = None
    try:
        identity_proof = peers.bind_real_sample_evidence()
        lab_profile,lab_request = peers.lab()
        normalization,exploratory,strict = peers.interpretation_profiles()
        scope = wire(peers.scope)
        config = {"database_url_env":"RESEARCH_DB","principals":[
            {"token_env":"RESEARCH_TOKEN","actor_id":"fixture","scope":scope,"actions":sorted(ACTIONS)},
            {"token_env":"RESEARCH_READ_TOKEN","actor_id":"fixture","scope":scope,"actions":sorted(action for action in ACTIONS if action.startswith("read_"))},
            {"token_env":"OTHER_TOKEN","actor_id":"other","scope":scope,"actions":sorted(ACTIONS)}],
            "science":{"lab_profiles":[wire(lab_profile.document)],"eligibility_profiles":[],"synthesis_profiles":[],
                "normalization_profiles":[wire(normalization.to_wire())],"observation_use_profiles":[wire(exploratory.to_wire()),wire(strict.to_wire())],
                "data":{"endpoint":peers.data.endpoint,"token_env":"READ_TOKEN"},
                "publication":{"actor_id":"publisher","token_env":"PUBLISH_TOKEN"},"consumer_publishers":[]}}
        path = tmp_path/"research.json"
        path.write_text(json.dumps(config))
        research = Owner("amphora_research",path,peers.environment,"s"*32,research_python)
        lab = research.request("/v1/lab-intakes",wire(lab_request))
        original = ObservationRevision.model_validate_json(json.dumps(lab["outcome"]["resolution"]["observations"][0]))
        normalize = NormalizeObservationRequest(wire_version="1",kind="normalization",interpretation_id="normalize-original",
            profile=normalization.reference,observation=original.reference,targets=NormalizationTargetRecord(value_unit="g/L",coordinate_unit=None))
        explore = AssessObservationUseRequest(wire_version="1",kind="observation-use",interpretation_id="explore-original",
            profile=exploratory.reference,experiment=peers.plan.reference,observations=(original.reference,))
        strict_request = explore.model_copy(update={"interpretation_id":"strict-original","profile":strict.reference})
        denied(research,"/v1/observation-normalizations",wire(normalize),403,"h"*32)
        denied(research,"/v1/observation-uses",wire(explore),401,"z"*32)
        foreign = wire(explore)
        foreign["profile"]["scope"]["project_id"] = "foreign"
        denied(research,"/v1/observation-uses",foreign,403)
        normalized = research.request("/v1/observation-normalizations",wire(normalize))
        normalization_result = normalized["outcome"]["projection"]["result"]
        assert normalization_result["original"] == wire(original.value)
        assert Decimal(normalization_result["normalized"]["quantity"]["value"]) == Decimal("0.00125")
        assert normalization_result["normalized"]["quantity"]["unit"] == "g/L"
        initial = research.request("/v1/observation-uses",wire(explore))
        strict_result = research.request("/v1/observation-uses",wire(strict_request))
        point = initial["outcome"]["projection"]["reviews"][0]
        assert point["disposition"] == "usable" and "controls_failed" in point["focus"]
        assert point["observation"]["quality"]["flags"] == ["questionable","low_accuracy"]
        assert initial["outcome"]["projection"]["missing_expectations"] == ["second"]
        assert wire(identity_proof) in initial["outcome"]["projection"]["sources"]
        assert strict_result["outcome"]["projection"]["reviews"][0]["disposition"] == "excluded"
        denied(research,"/v1/observation-interpretations/read",selection(explore),403,"o"*32)

        # Accept the original pin while its source is unavailable, then append a
        # correction before that interpretation has committed a result.
        peers.data.stop()
        pinned = explore.model_copy(update={"interpretation_id":"pinned-before-correction"})
        denied(research,"/v1/observation-uses",wire(pinned),503)
        assert research.request("/v1/observation-interpretations/read",selection(pinned))["outcome"] == {"status":"pending"}
        peers.restart_data()
        correction_request = peers.corrected_lab(lab_profile,original)
        corrected_lab = research.request("/v1/lab-intakes",wire(correction_request))
        corrected = ObservationRevision.model_validate_json(json.dumps(corrected_lab["outcome"]["resolution"]["observations"][0]))
        correction = research.request("/v1/observation-corrections/read",wire(corrected.reference))
        assert correction["before"] == wire(original) and correction["after"] == wire(corrected)
        assert correction["changed_fields"] == ["source","value","quality"] and correction["policy"] == "future_campaigns_only"
        resumed_original = research.request("/v1/observation-uses",wire(pinned))
        assert resumed_original["outcome"]["projection"]["reviews"][0]["observation"] == wire(original)
        later_request = explore.model_copy(update={"interpretation_id":"later-iteration","observations":(corrected.reference,)})
        later = research.request("/v1/observation-uses",wire(later_request))
        later_point = later["outcome"]["projection"]["reviews"][0]
        assert later_point["observation"] == wire(corrected) and later_point["disposition"] == "usable"
        assert "reported_quality_flags" in later_point["focus"]
        assert research.request("/v1/observation-uses",wire(explore)) == initial
        impact_query = {"wire_version":"1","source":wire(original.reference),"after":None,"limit":128}
        impact = research.request("/v1/interpretation-impact",impact_query)
        assert impact["policy"] == "future_campaigns_only"
        assert {ref["interpretation_id"] for ref in impact["interpretations"]} == {
            normalize.interpretation_id,explore.interpretation_id,strict_request.interpretation_id,pinned.interpretation_id}
        corrected_impact = research.request("/v1/interpretation-impact",impact_query|{"source":wire(corrected.reference)})
        assert [ref["interpretation_id"] for ref in corrected_impact["interpretations"]] == [later_request.interpretation_id]

        # Deny new Data reads without altering historical Research records. This
        # proves current access checks, not a per-source rights-revision scenario.
        peers.restart_data(allow_reads=False)
        denied_request = later_request.model_copy(update={"interpretation_id":"access-denied-pending"})
        assert denied(research,"/v1/observation-uses",wire(denied_request),403)["code"] == "peer_access_denied"
        assert research.request("/v1/observation-interpretations/read",selection(denied_request))["outcome"] == {"status":"pending"}
        assert research.request("/v1/observation-uses",wire(explore)) == initial
        peers.data.stop()
        research.stop()
        for name in ("lab_profiles","normalization_profiles","observation_use_profiles"):
            config["science"][name] = []
        path.write_text(json.dumps(config))
        research = Owner("amphora_research",path,peers.environment,"s"*32,replacement_python)
        history = [("/v1/observation-normalizations",normalize,normalized),
            ("/v1/observation-uses",explore,initial),("/v1/observation-uses",strict_request,strict_result),
            ("/v1/observation-uses",pinned,resumed_original),("/v1/observation-uses",later_request,later)]
        for route,request,result in history:
            assert research.request(route,wire(request)) == result
            assert research.request("/v1/observation-interpretations/read",selection(request)) == result
        assert research.request("/v1/observation-corrections/read",wire(corrected.reference)) == correction
        assert research.request("/v1/interpretation-impact",impact_query) == impact
        denied(research,"/v1/observation-uses",wire(denied_request),503)
        denied(research,"/v1/observation-uses",wire(explore.model_copy(update={"interpretation_id":"unaccepted"})),404)
        peers.restart_data()
        resumed = research.request("/v1/observation-uses",wire(denied_request))
        assert resumed["outcome"]["status"] == "interpreted" and resumed["request"] == wire(denied_request)
        assert resumed["outcome"]["projection"]["reviews"][0]["observation"] == wire(corrected)
        target = os.environ.get("AMPHORA_INTERPRETATION_HTTP_EVIDENCE")
        if target:
            Path(target).write_text(json.dumps({"timestamp_local":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "scope":scope,"test_python":sys.executable,"research_python":research_python,"replacement_python":replacement_python,
                "data_python":data_python,"identity_proof":wire(identity_proof),"original":wire(original),"corrected":wire(corrected),
                "normalization":normalized,"exploratory":initial,"strict_action":strict_result,"correction":correction,
                "pinned_after_correction":resumed_original,"later":later,"impact":impact,"resumed":resumed,
                "cases":["actual_Artifact_dependencies","authenticated_intake_and_correction","exact_normalization",
                    "weak_usable_and_focus","strict_action_only_exclusion","pending_pin_survives_correction",
                    "explicit_later_revision_selection","exact_future_only_impacts","current_Data_access_denial",
                    "independent_installed_replacement","zero_profile_offline_history","stored_profile_retry_after_access_restored"],
                "limits":["Synthetic science; no physical validity or quality UI","Interpretation input transitions, not new Runtime authority",
                    "Idle process replacement, not crash-at-barrier proof","Access-grant denial, not per-source rights revocation"]},indent=2)+"\n")
    finally:
        if research is not None:
            research.stop()
        peers.data.stop()
