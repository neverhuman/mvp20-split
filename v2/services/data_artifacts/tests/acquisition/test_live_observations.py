"""Actual Research HTTP peer; setup writes run in a Research-owned process."""

import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request

import pytest
from amphora_contracts_evidence import ObserveSourceIdentity
from amphora_data_artifacts.acquisition.research import ResearchClient, ResearchLookupError
from postgres_fixture import owned_state, research_owner
from sqlalchemy import URL

pytestmark = pytest.mark.postgres
OWNER_SETUP = '''
import json,os
from amphora_contracts_core import Scope
from amphora_contracts_research import CandidateRevision, SampleIdentity
from amphora_research.persistence.migrate import upgrade
from amphora_research.persistence.ledger import IdentityLedger
from sqlalchemy import create_engine
upgrade(os.environ["OBS_MIGRATION"])
if os.environ["OBS_SEED"] == "1":
 scope=Scope.model_validate_json(os.environ["OBS_SCOPE"])
 raw=json.loads(os.environ["OBS_ARTIFACT"])
 candidate={"scope":scope.model_dump(),"candidate_id":"c1","revision":1}
 engine=create_engine(os.environ["OBS_DATABASE"])
 try:
  ledger=IdentityLedger(engine)
  ledger.publish(scope,CandidateRevision.model_validate_json(json.dumps({"wire_version":"1",
   "reference":candidate,"representation":raw,"supersedes":None})))
  ledger.publish(scope,SampleIdentity.model_validate_json(json.dumps({"wire_version":"1",
   "reference":{"scope":scope.model_dump(),"sample_id":"s1","revision":1},"candidate":candidate,
   "material_state":None,"identity_evidence":raw,"supersedes":None})))
 finally:
  engine.dispose()
'''


def test_actual_peer_unknown_then_known_preserves_original_observation(ingestion, tmp_path):
    e = ingestion
    research_python = os.environ.get("AMPHORA_TEST_RESEARCH_PYTHON", sys.executable)
    source = e.source(b'{"candidate_id":"c1","candidate_revision":"1","sample_id":"s1","sample_revision":"1"}',
                      "synthetic_lab_json")
    prepared = e.workflow.prepare(e.principal, source)
    output = e.publish(prepared.content, prepared.output_schema)
    trace = e.workflow.retain(e.principal, source, "trace", output)
    command = ObserveSourceIdentity(wire_version="1", observation_id="before", trace=trace)
    state = owned_state()
    research_owner(state)
    host, port = state["endpoint"].split(":")
    database = URL.create("postgresql+psycopg", username="research_service", password=state["password"],
                          host=host, port=int(port), database=state["database"])
    environment = dict(os.environ, OBS_DATABASE=database.render_as_string(hide_password=False),
        OBS_MIGRATION=database.set(username="research_migrator").render_as_string(hide_password=False),
        OBS_SCOPE=e.principal.scope.model_dump_json(), OBS_ARTIFACT=source.reference.raw.model_dump_json(),
        OBS_TOKEN="t" * 32, OBS_SEED="0")
    setup = subprocess.run([research_python, "-I", "-c", OWNER_SETUP], env=environment,
                           capture_output=True, timeout=30)
    assert setup.returncode == 0, "Research fixture setup failed"
    config = {"database_url_env": "OBS_DATABASE", "principals": [{"token_env": "OBS_TOKEN",
        "actor_id": "acquisition", "scope": e.principal.scope.model_dump(), "actions": ["resolve_identity"]}]}
    config_path = tmp_path / "research.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        server_port = listener.getsockname()[1]
    endpoint = f"http://127.0.0.1:{server_port}"
    process = subprocess.Popen([research_python, "-I", "-m", "amphora_research", "serve", "--config", str(config_path),
                                "--port", str(server_port)], env=environment, stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    try:
        deadline = time.monotonic() + 15
        while True:
            assert process.poll() is None, "Research host exited before ready"
            try:
                with urllib.request.urlopen(endpoint + "/health", timeout=3) as response:
                    assert response.status == 200
                break
            except urllib.error.URLError:
                assert time.monotonic() < deadline, "Research readiness timeout"
                time.sleep(0.05)
        e.workflow.research = ResearchClient(endpoint, "t" * 32)
        original = e.workflow.observe(e.principal, command)
        assert original.resolution.reason == "unknown_candidate"
        seeded = subprocess.run([research_python, "-I", "-c", OWNER_SETUP], env=environment | {"OBS_SEED": "1"},
                                capture_output=True, timeout=30)
        assert seeded.returncode == 0, "Research fixture seed failed"
        assert e.workflow.observe(e.principal, command) == original
        later = e.workflow.observe(e.principal, command.model_copy(update={"observation_id": "after"}))
        assert later.resolution.reason == "exact_identity_only" and later.scientific_authority == "none"
        assert e.ledger.trace_history(e.principal, "trace").disposition == "quarantined"
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=10)
    pending = command.model_copy(update={"observation_id": "unavailable"})
    with pytest.raises(ResearchLookupError, match="research_unavailable"):
        e.workflow.observe(e.principal, pending)
    assert e.workflow.observations.history(e.principal, "unavailable").result is None
    assert e.workflow.observe(e.principal, command) == original
