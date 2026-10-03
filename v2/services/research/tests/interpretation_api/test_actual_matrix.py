"""Actual HTTP context matrix: weak results coexist with exact quarantines and future corrections."""
import json
import os
import sys
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pytest
from amphora_contracts_research import AssessObservationUseRequest, ReportedObservation
from amphora_research.scientific_api.operations import ACTIONS

from ..assessment.live_peers import Owner
from .matrix_fixtures import MatrixPeers, numeric, wire

pytestmark = pytest.mark.postgres


def test_actual_context_return_and_consumer_matrix(ledger,tmp_path):
    data_python = os.environ.get("AMPHORA_TEST_DATA_PYTHON")
    research_python = os.environ.get("AMPHORA_TEST_RESEARCH_INTERPRETATION_PYTHON")
    if not all((data_python,research_python)):
        pytest.skip("Independent Data/Research interpreters required")
    peers = MatrixPeers(ledger,tmp_path,data_python)
    research = None
    try:
        lab_profile,lab_request,explore,strict = peers.matrix()
        eligibility_profile,eligibility_request = peers.eligibility(lab_request)
        config = {"database_url_env":"RESEARCH_DB","principals":[
            {"token_env":"RESEARCH_TOKEN","actor_id":"fixture","scope":wire(peers.scope),"actions":sorted(ACTIONS)}],
            "science":{"lab_profiles":[wire(lab_profile.document)],"eligibility_profiles":[wire(eligibility_profile.document)],
                "synthesis_profiles":[],"normalization_profiles":[],"observation_use_profiles":[wire(explore.to_wire()),wire(strict.to_wire())],
                "data":{"endpoint":peers.data.endpoint,"token_env":"READ_TOKEN"},
                "publication":{"actor_id":"publisher","token_env":"PUBLISH_TOKEN"},"consumer_publishers":["fixture"]}}
        path = tmp_path/"research.json"
        path.write_text(json.dumps(config))
        research = Owner("amphora_research",path,peers.environment,"s"*32,research_python)
        lab = research.request("/v1/lab-intakes",wire(lab_request))
        resolution = lab["outcome"]["resolution"]
        assert resolution["disposition"] == "partial"
        assert resolution["missing_expectations"] == ["wrong-state","wrong-sample","convertible","inverse-unconfigured","not-returned"]
        assert len(resolution["observations"]) == 10
        specimens = peers.plan.samples
        assert specimens[0].state.candidate == specimens[1].state.candidate
        assert specimens[0].state.reference != specimens[1].state.reference
        for specimen,basis in zip(specimens,("observed","proposed"),strict=True):
            state = research.request("/v1/material-states/read",wire(specimen.state.reference))
            assert state == wire(specimen.state)
            assert [event["event_id"] for event in state["preparation"]] == ["heat","quench"]
            assert [event["context"]["duration"] for event in state["preparation"]] == [
                {"value":"2.00","unit":"min"},{"value":"30.0","unit":"s"}]
            assert {event["attribution"]["basis"] for event in state["preparation"]} == {basis}
            assert state["features"][0]["evidence"]["basis"] == ("measured" if basis == "observed" else "unknown")
        request = AssessObservationUseRequest(wire_version="1",kind="observation-use",interpretation_id="matrix-explore",
            profile=explore.reference,experiment=peers.plan.reference,observations=tuple(row.reference for row in peers.rows))
        initial = research.request("/v1/observation-uses",wire(request))
        projection = initial["outcome"]["projection"]
        points = {row["observation"]["reference"]["observation_id"]:row for row in projection["reviews"]}
        assert [row["observation"]["reference"]["observation_id"] for row in projection["reviews"]] == [row.reference.observation_id for row in peers.rows]
        expected = {"matched-observed":"usable","matched-proposed":"usable","wrong-state":"quarantined","wrong-sample":"quarantined",
            "convertible":"usable","inverse-unconfigured":"quarantined","replicate-high":"usable","replicate-low":"usable",
            "below-detection":"usable","missing-value":"usable"}
        assert {name:point["disposition"] for name,point in points.items()} == expected
        assert "disposition" not in projection  # No invented campaign-wide verdict.
        assert projection["missing_expectations"] == ["wrong-state","wrong-sample","inverse-unconfigured","not-returned"]
        for row in peers.rows:
            point = points[row.reference.observation_id]
            assert point["observation"]["value"] == wire(row.value)
            assert point["observation"]["binding"] == wire(row.binding)
            assert point["observation"]["quality"] == wire(row.quality)
        assert "controls_failed" in points["matched-observed"]["focus"]
        assert "reported_quality_flags" in points["matched-observed"]["focus"]
        assert "material_feature_unknown" in points["matched-proposed"]["focus"]
        assert "material_state_revision_mismatch" in points["wrong-state"]["focus"]
        assert "sample_revision_mismatch" in points["wrong-sample"]["focus"]
        converted = points["convertible"]["normalization"]
        assert Decimal(converted["normalized"]["quantity"]["value"]) == Decimal("1.25")
        assert converted["normalized"]["quantity"]["unit"] == "g/L"
        assert points["inverse-unconfigured"]["normalization"]["normalized"] is None
        assert points["inverse-unconfigured"]["normalization"]["reason"] == "normalization_direction_unconfigured"
        assert points["replicate-high"]["observation"]["value"] == numeric("9.0")
        assert points["replicate-low"]["observation"]["value"] == numeric("1.0")
        assert points["below-detection"]["observation"]["value"] == {
            "kind":"censored","lower":None,"upper":{"quantity":{"value":"0.01","unit":"mg/L"},"inclusive":False}}
        assert "measurement_unavailable" in points["missing-value"]["focus"]
        for specimen in specimens:
            assert wire(specimen.sample.identity_evidence) in projection["sources"]
            for event in specimen.state.preparation:
                assert wire(event.attribution.source) in projection["sources"]
        strict_result = research.request("/v1/observation-uses",wire(request.model_copy(update={"interpretation_id":"matrix-strict","profile":strict.reference})))
        strict_points = {row["observation"]["reference"]["observation_id"]:row for row in strict_result["outcome"]["projection"]["reviews"]}
        assert strict_points["matched-observed"]["disposition"] == "excluded"
        assert strict_points["matched-proposed"]["disposition"] == "unresolved"
        assert strict_points["missing-value"]["disposition"] == "unresolved"
        assert strict_points["replicate-high"]["disposition"] == "usable"

        assessment = research.request("/v1/scientific-assessments",wire(eligibility_request))
        decision = assessment["outcome"]["decision"]
        assert decision["assessment"]["disposition"] == "eligible"
        assert decision["assessment"]["focus"] == ["accuracy"]
        publication = research.request("/v1/scientific-publications",{"wire_version":"1","target":{"kind":"decision","reference":decision["reference"]}})
        artifact = publication["outcome"]["derivation"]["artifact"]
        consumer = peers.consumer([artifact])
        assert research.request("/v1/scientific-consumers",{"wire_version":"1","decision":decision["reference"],"consumer":consumer}) == consumer
        original = peers.rows[0]
        corrected = ReportedObservation.model_validate_json(json.dumps(wire(original)|{"reference":wire(original.reference.model_copy(update={"revision":2})),
            "supersedes":wire(original.reference),"value":numeric("1.30"),"quality":{"controls":"passed","flags":["questionable"]}}))
        correction_request = peers.return_report(lab_profile,(corrected,),"matrix-correction")
        research.request("/v1/lab-intakes",wire(correction_request))
        correction = research.request("/v1/observation-corrections/read",wire(corrected.reference))
        assert correction["before"] == points["matched-observed"]["observation"]
        assert correction["after"]["value"] == numeric("1.30")
        assert correction["policy"] == "future_campaigns_only"
        query = {"wire_version":"1","source":wire(original.reference),"after":None,"limit":128}
        impact = research.request("/v1/scientific-impact",query)
        assert impact["decisions"] == [decision["reference"]] and impact["policy"] == "future_campaigns_only"
        interpretations = research.request("/v1/interpretation-impact",query)
        assert {item["interpretation_id"] for item in interpretations["interpretations"]} == {"matrix-explore","matrix-strict"}
        consumers = research.request("/v1/scientific-consumers/read",{"wire_version":"1","decision":decision["reference"],"after":None,"limit":128})
        assert consumers["consumers"] == [consumer]
        assert research.request("/v1/scientific-decisions/read",decision["reference"]) == decision
        assert research.request("/v1/observation-uses",wire(request)) == initial
        target = os.environ.get("AMPHORA_CONTEXT_MATRIX_EVIDENCE")
        if target:
            Path(target).write_text(json.dumps({"timestamp_local":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "scope":wire(peers.scope),"test_python":sys.executable,"research_python":research_python,"data_python":data_python,
                "lab":lab,"exploratory":initial,"strict":strict_result,"decision":decision,"correction":correction,
                "impact":impact,"interpretations":interpretations,"consumers":consumers,
                "limits":["Synthetic evidence, no scientific validity","Explicit fixture consumer, no deployed fitness engine",
                    "No campaign-quality verdict, UI, or new Runtime authority"]},indent=2)+"\n")
    finally:
        if research is not None:
            research.stop()
        peers.data.stop()
