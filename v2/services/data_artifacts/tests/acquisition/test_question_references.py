"""QEV-01: real owner HTTP reads exchange immutable public declarations/artifacts."""

import hashlib
import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

import pytest
from amphora_contracts_research import EvidenceNeed, ResearchQuestion
from postgres_fixture import owned_state, research_owner
from sqlalchemy import URL

from .process_support import OwnerProcess, configuration

pytestmark = pytest.mark.postgres
SEED = '''
import os
from amphora_contracts_research import ResearchQuestion,EvidenceNeed
from amphora_research.persistence.migrate import upgrade
from amphora_research.persistence.ledger import IdentityLedger
from sqlalchemy import create_engine
upgrade(os.environ["QEV_MIGRATION"])
engine=create_engine(os.environ["QEV_DATABASE"])
try:
 ledger=IdentityLedger(engine)
 for key,model in [("QEV_QUESTION",ResearchQuestion),("QEV_NEED",EvidenceNeed)]:
  record=model.model_validate_json(os.environ[key])
  ledger.publish(record.reference.scope,record)
finally:
 engine.dispose()
'''


def start_peer(python, config, environment, port):
    process = subprocess.Popen([python, "-I", "-m", "amphora_research", "serve", "--config", str(config),
        "--port", str(port)], env=environment, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    try:
        deadline = time.monotonic() + 15
        while True:
            assert process.poll() is None, "Research host exited"
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=3) as response:
                    assert response.status == 200
                return process
            except urllib.error.URLError:
                assert time.monotonic() < deadline, "Research readiness timeout"
                time.sleep(0.05)
    except BaseException:
        process.kill()
        process.wait(timeout=10)
        raise


def test_qev01_declarations_cross_owner_http_without_acceptance(ingestion, tmp_path):
    e = ingestion
    research_python = os.environ.get("AMPHORA_TEST_RESEARCH_PYTHON", sys.executable)
    content = b"Synthetic applicability and declared method context; no accepted result."
    artifact = e.publish(content)
    scope = e.principal.scope.model_dump()
    question = ResearchQuestion.model_validate_json(json.dumps({"wire_version": "1",
        "reference": {"scope": scope, "question_id": "qev-question", "revision": 1},
        "objective": "Synthetic comparison", "applicability": artifact.model_dump(mode="json"),
        "criteria": [{"criterion_id": "criterion", "description": "Declared context required"}], "supersedes": None}))
    need = EvidenceNeed.model_validate_json(json.dumps({"wire_version": "1",
        "reference": {"scope": scope, "need_id": "qev-need", "revision": 1},
        "question": question.reference.model_dump(mode="json"), "criterion_ids": ["criterion"],
        "method": artifact.schema_ref.model_dump(mode="json"),
        "required_context": artifact.model_dump(mode="json"), "supersedes": None}))
    state = owned_state()
    research_owner(state)
    host, port = state["endpoint"].split(":")
    database = URL.create("postgresql+psycopg", username="research_service", password=state["password"],
                         host=host, port=int(port), database=state["database"])
    environment = dict(os.environ, QEV_DATABASE=database.render_as_string(hide_password=False),
        QEV_MIGRATION=database.set(username="research_migrator").render_as_string(hide_password=False),
        QEV_QUESTION=question.model_dump_json(), QEV_NEED=need.model_dump_json(), QEV_TOKEN="q"*32)
    seeded = subprocess.run([research_python, "-I", "-c", SEED], env=environment, capture_output=True, timeout=30)
    assert seeded.returncode == 0, "Research-owned fixture seeding failed"
    config = tmp_path / "research.json"
    config.write_text(json.dumps({"database_url_env": "QEV_DATABASE", "principals": [
        {"token_env": "QEV_TOKEN", "actor_id": "declaration-reader", "scope": scope,
         "actions": ["read_declarations"]}]}), encoding="utf-8")
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    endpoint = f"http://127.0.0.1:{port}"
    process = start_peer(research_python, config, environment, port)
    data = None
    try:
        data_config, data_env = configuration(e, tmp_path)
        data = OwnerProcess(data_config, data_env)
        for kind, record in [("questions", question), ("evidence-needs", need)]:
            request = urllib.request.Request(endpoint + f"/v1/{kind}/read", data=record.reference.model_dump_json().encode(),
                headers={"Authorization": "Bearer " + "q"*32, "Content-Type": "application/json"})
            with urllib.request.urlopen(request, timeout=5) as response:
                received = type(record).model_validate_json(response.read())
            assert received == record
            linked = received.applicability if kind == "questions" else received.required_context
            assert data.request(f"/v1/artifacts/{linked.artifact_id}") == linked.model_dump(mode="json")
            raw_request = urllib.request.Request(f"http://127.0.0.1:{data.port}/v1/artifacts/{linked.artifact_id}/content",
                headers={"Authorization": "Bearer " + "k"*32})
            with urllib.request.urlopen(raw_request, timeout=5) as response:
                raw = response.read()
            assert raw == content and hashlib.sha256(raw).hexdigest() == linked.sha256
            assert "accepted" not in received.model_dump() and "scientific_authority" not in received.model_dump()
        assert need.question == question.reference
        # A Research token conveys no Data authority, even for a returned public reference.
        denied = urllib.request.Request(f"http://127.0.0.1:{data.port}/v1/artifacts/{artifact.artifact_id}/content",
            headers={"Authorization": "Bearer " + "q"*32})
        with pytest.raises(urllib.error.HTTPError) as error:
            urllib.request.urlopen(denied, timeout=5)
        assert error.value.code == 401
        process.kill()
        process.wait(timeout=10)
        replacement_python = os.environ.get("AMPHORA_TEST_RESEARCH_REPLACEMENT_PYTHON", research_python)
        process = start_peer(replacement_python, config, environment, port)
        for kind, record in [("questions", question), ("evidence-needs", need)]:
            request = urllib.request.Request(endpoint + f"/v1/{kind}/read", data=record.reference.model_dump_json().encode(),
                headers={"Authorization": "Bearer " + "q"*32, "Content-Type": "application/json"})
            with urllib.request.urlopen(request, timeout=5) as response:
                assert type(record).model_validate_json(response.read()) == record
    finally:
        if data is not None:
            data.stop()
        process.kill()
        process.wait(timeout=10)
    evidence = {"timestamp_local": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "case": "QEV-01",
        "question": question.model_dump(mode="json"), "need": need.model_dump(mode="json"),
        "artifact_sha256_verified": artifact.sha256, "cross_owner_token_status": 401,
        "authority": "declarations_only", "research_replacement": "exact question/need history preserved",
        "owners": "actual Data and Research HTTP processes",
        "independent_peer_requested": "AMPHORA_TEST_RESEARCH_PYTHON" in os.environ}
    path = Path(__file__).absolute().parents[4] / ".test-results/bp0601-qev.json"
    path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
