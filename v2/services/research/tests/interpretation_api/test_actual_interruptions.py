"""Kill real Research processes at durable boundaries; recover through independent HTTP peers."""
import hashlib
import http.client
import json
import os
import sys
import urllib.error
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

import pytest
from amphora_contracts_research import AssessObservationUseRequest
from amphora_research.scientific_api.operations import ACTIONS
from sqlalchemy import text

from ..assessment.live_peers import Owner
from ..scientific_api.test_actual_workflow import denied
from .actual_fixtures import InterpretationPeers
from .matrix_fixtures import wire

pytestmark = pytest.mark.postgres
TABLES = {
    "lab":("lab_intents","lab_terminals","observation_revisions","lab_observations"),
    "interpretation":("interpretation_intents","interpretation_results","interpretation_sources",
        "interpretation_observations","interpretation_material_states","interpretation_experiments"),
}


def snapshot(peers, family):
    key = {"tenant":peers.scope.tenant_id,"project":peers.scope.project_id}
    tables = TABLES[family]
    with peers.identities.engine.connect() as connection:
        counts = {table:connection.execute(text(f"SELECT count(*) FROM research.{table} WHERE tenant_id=:tenant AND project_id=:project"),key).scalar_one()
            for table in tables}
        intent = connection.execute(text(f"SELECT canonical_bytes FROM research.{tables[0]} WHERE tenant_id=:tenant AND project_id=:project"),key).scalar_one()
    return counts,hashlib.sha256(bytes(intent)).hexdigest()


@pytest.mark.parametrize("family",["lab","interpretation"])
@pytest.mark.parametrize("stage",["intent_committed","result_before_commit","result_committed"])
def test_actual_intake_and_interpretation_process_death(ledger,tmp_path,family,stage):
    data_python = os.environ.get("AMPHORA_TEST_DATA_PYTHON")
    research_python = os.environ.get("AMPHORA_TEST_RESEARCH_INTERPRETATION_PYTHON")
    replacement_python = os.environ.get("AMPHORA_TEST_RESEARCH_INTERPRETATION_REPLACEMENT_PYTHON")
    if not all((data_python,research_python,replacement_python)):
        pytest.skip("Independent Data/Research and replacement interpreters required")
    peers = InterpretationPeers(ledger,tmp_path,data_python)
    research = replacement = None
    try:
        peers.bind_real_sample_evidence()
        lab_profile,lab_request = peers.lab()
        _,explore,_ = peers.interpretation_profiles()
        config = {"database_url_env":"RESEARCH_DB","principals":[
            {"token_env":"RESEARCH_TOKEN","actor_id":"fixture","scope":wire(peers.scope),"actions":sorted(ACTIONS)},
            {"token_env":"OTHER_TOKEN","actor_id":"other","scope":wire(peers.scope),"actions":sorted(ACTIONS)}],
            "science":{"lab_profiles":[wire(lab_profile.document)],"eligibility_profiles":[],"synthesis_profiles":[],
                "normalization_profiles":[],"observation_use_profiles":[wire(explore.to_wire())],
                "data":{"endpoint":peers.data.endpoint,"token_env":"READ_TOKEN"},
                "publication":{"actor_id":"publisher","token_env":"PUBLISH_TOKEN"},"consumer_publishers":[]}}
        path = tmp_path/"research.json"
        path.write_text(json.dumps(config))
        if family == "interpretation":
            research = Owner("amphora_research",path,peers.environment,"s"*32,research_python)
            research.request("/v1/lab-intakes",wire(lab_request))
            research.stop()
            request = AssessObservationUseRequest(wire_version="1",kind="observation-use",interpretation_id="interrupted",
                profile=explore.reference,experiment=peers.plan.reference,observations=(peers.observation.reference,))
            route = "/v1/observation-uses"
            read_route = "/v1/observation-interpretations/read"
            selection = {"scope":wire(peers.scope),"kind":"observation-use","interpretation_id":"interrupted"}
            terminal_status = "interpreted"
        else:
            request = lab_request
            route = "/v1/lab-intakes"
            read_route = "/v1/lab-intakes/read"
            selection = {"kind":"lab-intake","scope":wire(peers.scope),"intake_id":request.intake_id}
            terminal_status = "resolved"
        barrier = family+":"+stage
        research = Owner("amphora_research",path,peers.environment,"s"*32,research_python,
            barrier=barrier,fault_host=Path(__file__).with_name("fault_host.py"))
        committed = stage == "result_committed"
        with ThreadPoolExecutor(max_workers=1) as pool:
            call = pool.submit(research.request,route,wire(request))
            try:
                assert research.events.get(timeout=30) == {"barrier":barrier}
                before = research.request(read_route,selection)
                assert before["outcome"]["status"] == (terminal_status if committed else "pending")
                counts_before,intent_hash = snapshot(peers,family)
                assert counts_before[TABLES[family][0]] == 1
                if not committed:
                    assert all(counts_before[table] == 0 for table in TABLES[family][1:])
            finally:
                research.stop()
            assert isinstance(call.exception(timeout=15),(urllib.error.URLError,http.client.RemoteDisconnected,ConnectionError))
        counts_killed,hash_killed = snapshot(peers,family)
        assert counts_killed == counts_before and hash_killed == intent_hash
        peers.data.stop()
        config["science"]["lab_profiles"] = []
        config["science"]["observation_use_profiles"] = []
        path.write_text(json.dumps(config))
        replacement = Owner("amphora_research",path,peers.environment,"s"*32,replacement_python)
        assert replacement.request(read_route,selection) == before
        denied(replacement,read_route,selection,403,"o"*32)
        if committed:
            recovered = replacement.request(route,wire(request))
            assert recovered == before
        else:
            denied(replacement,route,wire(request),503)
            assert replacement.request(read_route,selection) == before
            peers.restart_data()
            recovered = replacement.request(route,wire(request))
            assert recovered["outcome"]["status"] == terminal_status
        assert replacement.request(route,wire(request)) == recovered
        counts_after,hash_after = snapshot(peers,family)
        assert hash_after == intent_hash
        expected_counts = {table:1 for table in TABLES[family]}
        if family == "interpretation":
            projection = recovered["outcome"]["projection"]
            expected_counts["interpretation_sources"] = len(projection["sources"])
            assert projection["profile"] == wire(explore.to_wire())
            assert projection["reviews"][0]["observation"]["reference"] == wire(peers.observation.reference)
            assert projection["reviews"][0]["disposition"] == "usable"
        else:
            assert recovered["outcome"]["resolution"]["observations"][0]["reference"] == wire(peers.observation.reference)
            assert recovered["outcome"]["resolution"]["observations"][0]["quality"]["controls"] == "failed"
        assert counts_after == expected_counts
        target = os.environ.get("AMPHORA_SCIENTIFIC_INTERRUPTION_EVIDENCE")
        if target:
            directory = Path(target)
            directory.mkdir(parents=True,exist_ok=True)
            (directory/(family+"-"+stage+".json")).write_text(json.dumps({
                "timestamp_local":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),"barrier":barrier,"scope":wire(peers.scope),
                "test_python":sys.executable,"research_python":research_python,"replacement_python":replacement_python,"data_python":data_python,
                "intent_sha256":intent_hash,"counts_before_kill":counts_before,"counts_after_kill":counts_killed,"counts_after_recovery":counts_after,
                "before":before,"recovered":recovered,"replay_offline":committed,"retired_profile_resumed":not committed,
                "limits":["Actual process death, not host power loss","Synthetic evidence, no scientific validity or UI"]},indent=2)+"\n")
    finally:
        if research is not None:
            research.stop()
        if replacement is not None:
            replacement.stop()
        peers.data.stop()
