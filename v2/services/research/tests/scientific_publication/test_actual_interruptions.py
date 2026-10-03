"""Nine real process-death boundaries for Artifact-only scientific publication."""
import http.client
import json
import os
import sys
import time
import urllib.error
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

import pytest
from amphora_research.observations.intake_store import LabIntakeStore
from amphora_research.scientific_api.operations import ACTIONS
from amphora_research.scientific_publication.artifact import ScientificArtifact
from amphora_research.scientific_publication.store import ScientificPublicationStore

from ..assessment.live_peers import Owner
from ..scientific_api.peer_fixtures import ScientificPeers

pytestmark = pytest.mark.postgres
STAGES = {"prepared":"prepared","begin_returned":"prepared","stream_started":"streaming",
    "stream_returned":"streaming","stream_verified":"streamed","finalizing":"finalizing",
    "data_finalized":"finalizing","terminal_before_commit":"finalizing","terminal_committed":"published"}


def publication_command(peers, family, identity):
    original = peers.data.token
    peers.data.token = peers.environment["PUBLISH_TOKEN"]
    try:
        return peers.data.request("/v1/commands/"+family+"/"+identity)
    finally:
        peers.data.token = original


def test_actual_scientific_publication_death_and_replacement(ledger,tmp_path):
    data_python = os.environ.get("AMPHORA_TEST_DATA_PYTHON")
    research_python = os.environ.get("AMPHORA_TEST_RESEARCH_SCIENCE_PYTHON")
    replacement_python = os.environ.get("AMPHORA_TEST_RESEARCH_SCIENCE_REPLACEMENT_PYTHON")
    if not all((data_python,research_python,replacement_python)):
        pytest.skip("Independent Data/Research and fresh replacement interpreters required")
    peers = ScientificPeers(ledger,tmp_path,data_python)
    research = dying = replacement = None
    cases = []
    try:
        profile,template = peers.lab()
        scope = peers.scope.model_dump(mode="json")
        config = {"database_url_env":"RESEARCH_DB","principals":[
            {"token_env":"RESEARCH_TOKEN","actor_id":"fixture","scope":scope,"actions":sorted(ACTIONS)}],
            "science":{"lab_profiles":[profile.document.model_dump(mode="json")],"eligibility_profiles":[],"synthesis_profiles":[],
                "data":{"endpoint":peers.data.endpoint,"token_env":"READ_TOKEN"},
                "publication":{"actor_id":"publisher","token_env":"PUBLISH_TOKEN"},"consumer_publishers":[]}}
        path = tmp_path/"research.json"
        path.write_text(json.dumps(config))
        research = Owner("amphora_research",path,peers.environment,"s"*32,research_python)
        config["science"]["lab_profiles"] = []
        config["science"]["publication"]["actor_id"] = "new-publisher"
        replacement_path = tmp_path/"replacement.json"
        replacement_path.write_text(json.dumps(config))
        store = ScientificPublicationStore(peers.identities.engine)
        for stage,expected in STAGES.items():
            intake = template.model_copy(update={"intake_id":"kill-"+stage})
            accepted = research.request("/v1/lab-intakes",intake.model_dump(mode="json"))
            assert accepted["outcome"]["status"] == "resolved"
            artifact = ScientificArtifact.from_intake(LabIntakeStore(peers.identities.engine).read(peers.scope,"fixture",intake.intake_id))
            query = {"wire_version":"1","target":{"kind":"lab-intake","scope":scope,"intake_id":intake.intake_id}}
            dying = Owner("amphora_research",path,peers.environment,"s"*32,research_python,
                barrier=stage,fault_host=Path(__file__).with_name("fault_host.py"))
            try:
                with ThreadPoolExecutor(max_workers=1) as pool:
                    call = pool.submit(dying.request,"/v1/scientific-publications",query)
                    try:
                        assert dying.events.get(timeout=30) == {"barrier":stage}
                    finally:
                        dying.stop()
                    assert isinstance(call.exception(timeout=15),(urllib.error.URLError,http.client.RemoteDisconnected,ConnectionError))
                before = store.lookup(artifact)
                assert before.stage == expected and before.publisher == "publisher"
                finalized = None
                if stage in {"data_finalized","terminal_before_commit","terminal_committed"}:
                    observed = publication_command(peers,"artifacts.finalize",before.command_id("artifacts.finalize"))
                    assert observed["outcome"]["status"] == "finalized"
                    finalized = observed["outcome"]["receipt"]["artifact"]
                replacement = Owner("amphora_research",replacement_path,peers.environment,"s"*32,replacement_python)
                initial = replacement.request("/v1/scientific-publications/read",query)
                assert initial["outcome"]["status"] == ("published" if stage == "terminal_committed" else "pending")
                if stage == "terminal_committed":
                    peers.data.stop()
                deadline = time.monotonic()+30
                while True:
                    recovered = replacement.request("/v1/scientific-publications",query)
                    if recovered["outcome"]["status"] != "pending":
                        break
                    assert time.monotonic() < deadline,"Scientific publication lease failed to expire"
                    time.sleep(0.1)
                assert recovered["outcome"]["status"] == "published"
                assert set(recovered["outcome"]) == {"status","derivation"}
                assert replacement.request("/v1/scientific-publications",query) == recovered
                after = store.lookup(artifact)
                uncertain = stage in {"stream_started","stream_returned"}
                assert after.ordinal == (2 if uncertain else 1)
                for family in ("artifacts.begin_derived_upload","artifacts.finalize"):
                    assert (before.command_id(family) != after.command_id(family)) is uncertain
                if uncertain:
                    begun = publication_command(peers,"artifacts.begin_derived_upload",before.command_id("artifacts.begin_derived_upload"))
                    assert begun["identity"]["actor_id"] == "publisher"
                    with pytest.raises(urllib.error.HTTPError) as missing:
                        publication_command(peers,"artifacts.finalize",before.command_id("artifacts.finalize"))
                    assert missing.value.code == 404
                if finalized is not None:
                    assert recovered["outcome"]["derivation"]["artifact"] == finalized
                cases.append({"timestamp_local":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),"barrier":stage,"query":query,
                    "stage_after_kill":before.stage,"status_after_kill":initial["outcome"]["status"],
                    "begin_id_before":before.command_id("artifacts.begin_derived_upload"),"finalize_id_before":before.command_id("artifacts.finalize"),
                    "begin_id_after":after.command_id("artifacts.begin_derived_upload"),"finalize_id_after":after.command_id("artifacts.finalize"),
                    "recovered_ordinal":after.ordinal,"abandoned_upload_not_finalized":uncertain,"result":recovered})
                if stage == "terminal_committed":
                    for case in cases:
                        assert replacement.request("/v1/scientific-publications",case["query"]) == case["result"]
            finally:
                dying.stop()
                if replacement is not None:
                    replacement.stop()
        target = os.environ.get("AMPHORA_SCIENTIFIC_PUBLICATION_RECOVERY_EVIDENCE")
        if target:
            Path(target).write_text(json.dumps({"timestamp_local":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),"scope":scope,
                "test_python":sys.executable,"research_python":research_python,"replacement_python":replacement_python,"data_python":data_python,
                "lease_profile":"Test-only five-second DB-clock lease; production replacement sixty seconds",
                "cases":cases,"limits":["Synthetic science; no Runtime receipt authority","Process death, not host power loss",
                    "Lab-intake payload here; all three publication kinds have separate shape/workflow tests"]},indent=2)+"\n")
    finally:
        for owner in (research,dying,replacement,peers.data):
            if owner is not None:
                owner.stop()
