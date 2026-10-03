"""Independently installed HTTP owners and Research replacement; no scripted peer results."""
import json
import os
import sys
import urllib.error
from datetime import datetime
from pathlib import Path

import pytest
from amphora_research.scientific_api.operations import ACTIONS

from ..assessment.live_peers import Owner
from .peer_fixtures import ScientificPeers

pytestmark = pytest.mark.postgres


def denied(owner, route, query, status, token=None):
    original = owner.token
    if token is not None:
        owner.token = token
    try:
        with pytest.raises(urllib.error.HTTPError) as failed:
            owner.request(route,query)
        assert failed.value.code == status
        assert failed.value.headers["Cache-Control"] == "no-store"
        return json.load(failed.value)
    finally:
        owner.token = original


def test_actual_scientific_http_and_offline_replacement(ledger,tmp_path):
    data_python = os.environ.get("AMPHORA_TEST_DATA_PYTHON")
    research_python = os.environ.get("AMPHORA_TEST_RESEARCH_SCIENCE_PYTHON")
    replacement_python = os.environ.get("AMPHORA_TEST_RESEARCH_SCIENCE_REPLACEMENT_PYTHON")
    if not all((data_python,research_python,replacement_python)):
        pytest.skip("Independent Data/Research and fresh replacement interpreters required")
    peers = ScientificPeers(ledger,tmp_path,data_python)
    research = None
    try:
        scope = peers.scope.model_dump(mode="json")
        lab_profile,lab_request = peers.lab()
        eligibility_profile,eligibility_request = peers.decision("eligibility")
        synthesis_profile,synthesis_request = peers.decision("synthesis")
        readonly = [action for action in ACTIONS if action.startswith("read_")]
        config = {"database_url_env":"RESEARCH_DB","principals":[
            {"token_env":"RESEARCH_TOKEN","actor_id":"fixture","scope":scope,"actions":sorted(ACTIONS)},
            {"token_env":"RESEARCH_READ_TOKEN","actor_id":"fixture","scope":scope,"actions":readonly},
            {"token_env":"OTHER_TOKEN","actor_id":"other","scope":scope,"actions":sorted(ACTIONS)}],
            "science":{"lab_profiles":[lab_profile.document.model_dump(mode="json")],
                "eligibility_profiles":[eligibility_profile.document.model_dump(mode="json")],
                "synthesis_profiles":[synthesis_profile.document.model_dump(mode="json")],
                "data":{"endpoint":peers.data.endpoint,"token_env":"READ_TOKEN"},
                "publication":{"actor_id":"publisher","token_env":"PUBLISH_TOKEN"},"consumer_publishers":["fixture"]}}
        path = tmp_path/"research.json"
        path.write_text(json.dumps(config),encoding="utf-8")
        research = Owner("amphora_research",path,peers.environment,"s"*32,research_python)
        assert research.request("/health")["authority"] == "synthetic_science"
        def wire(record):
            return record.model_dump(mode="json")
        denied(research,"/v1/lab-intakes",wire(lab_request),403,"h"*32)
        denied(research,"/v1/lab-intakes",wire(lab_request),401,"z"*32)
        lab = research.request("/v1/lab-intakes",wire(lab_request))
        resolution = lab["outcome"]["resolution"]
        assert resolution["disposition"] == "partial" and resolution["missing_expectations"] == ["second"]
        assert resolution["observations"][0]["quality"] == {"controls":"failed","flags":["questionable","low_accuracy"]}
        lab_selection = {"kind":"lab-intake","scope":scope,"intake_id":lab_request.intake_id}
        assert research.request("/v1/lab-intakes/read",lab_selection) == lab
        assert research.request("/v1/material-states/read",wire(peers.state.reference)) == wire(peers.state)
        assert research.request("/v1/experiments/read",wire(peers.plan.reference)) == wire(peers.plan)
        observation = resolution["observations"][0]
        assert research.request("/v1/observations/read",observation["reference"]) == observation
        outcomes = []
        for request in (eligibility_request,synthesis_request):
            query = wire(request)
            denied(research,"/v1/scientific-assessments",query,403,"h"*32)
            result = research.request("/v1/scientific-assessments",query)
            assert result["outcome"]["status"] == "assessed"
            assert research.request("/v1/scientific-assessments",query) == result
            decision = result["outcome"]["decision"]
            assert research.request("/v1/scientific-decisions/read",decision["reference"]) == decision
            denied(research,"/v1/scientific-assessments/read",query,403,"o"*32)
            outcomes.append((query,result))
        assert outcomes[0][1]["outcome"]["decision"]["assessment"]["focus"] == ["accuracy"]
        assert outcomes[0][1]["outcome"]["decision"]["assessment"]["disposition"] == "eligible"
        assert outcomes[1][1]["outcome"]["decision"]["assessment"]["alternatives"][0]["disposition"] == "eligible"
        publications = []
        for target in (lab_selection,*[{"kind":"decision","reference":result["outcome"]["decision"]["reference"]} for _,result in outcomes]):
            query = {"wire_version":"1","target":target}
            denied(research,"/v1/scientific-publications",query,403,"h"*32)
            result = research.request("/v1/scientific-publications",query)
            assert result["outcome"]["status"] == "published"
            assert set(result["outcome"]) == {"status","derivation"}
            assert research.request("/v1/scientific-publications/read",query) == result
            publications.append((query,result))
        decision = outcomes[0][1]["outcome"]["decision"]["reference"]
        published = publications[1][1]["outcome"]["derivation"]["artifact"]
        wrong_consumer = peers.consumer([wire(eligibility_request.reports[0])])
        registration = {"wire_version":"1","decision":decision,"consumer":wrong_consumer}
        denied(research,"/v1/scientific-consumers",registration,422)
        consumer = peers.consumer([published])
        registration["consumer"] = consumer
        denied(research,"/v1/scientific-consumers",registration,403,"h"*32)
        assert research.request("/v1/scientific-consumers",registration) == consumer
        assert research.request("/v1/scientific-consumers",registration) == consumer
        consumer_query = {"wire_version":"1","decision":decision,"after":None,"limit":128}
        consumers = research.request("/v1/scientific-consumers/read",consumer_query)
        assert consumers["consumers"] == [consumer]
        impact_query = {"wire_version":"1","source":wire(eligibility_request.reports[0]),"after":None,"limit":128}
        impact = research.request("/v1/scientific-impact",impact_query)
        assert impact["policy"] == "future_campaigns_only" and impact["decisions"] == [decision]
        peers.data.stop()
        pending = wire(eligibility_request.model_copy(update={"decision_id":"accepted-before-replacement"}))
        denied(research,"/v1/scientific-assessments",pending,503)
        assert research.request("/v1/scientific-assessments/read",pending)["outcome"] == {"status":"pending"}
        research.stop()
        for key in ("lab_profiles","eligibility_profiles","synthesis_profiles"):
            config["science"][key] = []
        config["science"]["publication"]["actor_id"] = "new-publisher"
        path.write_text(json.dumps(config),encoding="utf-8")
        research = Owner("amphora_research",path,peers.environment,"s"*32,replacement_python)
        assert research.request("/v1/lab-intakes",wire(lab_request)) == lab
        for query,result in outcomes:
            assert research.request("/v1/scientific-assessments",query) == result
            assert research.request("/v1/scientific-assessments/read",query) == result
        for query,result in publications:
            assert research.request("/v1/scientific-publications",query) == result
            assert research.request("/v1/scientific-publications/read",query) == result
        assert research.request("/v1/scientific-consumers/read",consumer_query) == consumers
        assert research.request("/v1/scientific-impact",impact_query) == impact
        denied(research,"/v1/scientific-assessments",pending,503)
        denied(research,"/v1/scientific-assessments",wire(eligibility_request.model_copy(update={"decision_id":"not-accepted"})),404)
        denied(research,"/v1/scientific-assessments/read",wire(eligibility_request.model_copy(update={"decision_id":"not-accepted"})),404)
        data_port = int(peers.data.endpoint.rsplit(":",1)[1])
        peers.data = Owner("amphora_data_artifacts",peers.data_config,peers.environment,"d"*32,data_python,port=data_port)
        resumed = research.request("/v1/scientific-assessments",pending)
        assert resumed["outcome"]["status"] == "assessed" and resumed["request"] == pending
        target = os.environ.get("AMPHORA_SCIENTIFIC_HTTP_EVIDENCE")
        if target:
            Path(target).write_text(json.dumps({"timestamp_local":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "scope":scope,"test_python":sys.executable,"research_python":research_python,"replacement_python":replacement_python,
                "data_python":data_python,"lab":lab,"decisions":[result for _,result in outcomes],
                "publications":[result for _,result in publications],"consumers":consumers,"impact":impact,"resumed":resumed,
                "cases":["actual_lab_and_both_decision_HTTP","partial_failed_controls_preserved","optional_accuracy_focus",
                    "typed_Artifact_only_publication","consumer_exact_lineage","separate_grants_and_original_actor",
                    "all_scientific_record_reads","isolated_Research_replacement","offline_history_and_publication_replay",
                    "pending_profile_survives_removal","fresh_rights_after_Data_restart"],
                "limits":["Synthetic evidence, no scientific validity","Idle process replacement, not crash-barrier durability",
                    "No physical laboratory or quality UI"]},indent=2)+"\n",encoding="utf-8")
    finally:
        if research is not None:
            research.stop()
        peers.data.stop()
