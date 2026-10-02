"""Actual Data/Research/Knowledge processes; all cross-owner consumption is HTTP."""

import copy
import hashlib
import json
import os
import sys
import urllib.error
import uuid
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
from postgres_fixture import owned_state, research_owner
from sqlalchemy import URL

from ..validation.conftest import records
from .processes import Owner, owned_script

pytestmark = pytest.mark.postgres

RESEARCH_SEED = '''
import json,os
from amphora_contracts_research import ResearchQuestion,EvidenceNeed
from amphora_research.persistence.migrate import upgrade
from amphora_research.persistence.ledger import IdentityLedger
from sqlalchemy import create_engine
upgrade(os.environ['PEER_MIGRATION'])
engine=create_engine(os.environ['PEER_DATABASE'])
try:
 ledger=IdentityLedger(engine)
 for name,model in [('PEER_QUESTION',ResearchQuestion),('PEER_NEED',EvidenceNeed)]:
  record=model.model_validate_json(os.environ[name])
  ledger.publish(record.reference.scope,record)
finally:
 engine.dispose()
'''


def publish(data, scope, content, schema):
    descriptor = {"sha256": hashlib.sha256(content).hexdigest(), "size_bytes": len(content),
        "media_type": "application/octet-stream" if schema["schema_id"] == "fixture.bytes" else "application/json",
        "schema_ref": schema}

    def command(family, payload):
        return {"identity": {"command_family": family, "command_id": uuid.uuid4().hex,
            "actor_id": "fixture", "scope": scope}, "payload": payload}

    started = data.request("/v1/uploads", command("artifacts.begin_upload", {"content": descriptor}))
    data.request(f"/v1/uploads/{started['upload_id']}/content", content=content, method="PUT")
    final = data.request("/v1/artifacts/finalize", command("artifacts.finalize",
        {"upload_id": started["upload_id"], "content": descriptor}))
    return final["artifact"]


def test_actual_peer_validation_and_owner_restart(stored_graph, tmp_path):
    case = stored_graph
    peer = records(case.proposal)
    state = owned_state()
    research_owner(state)
    host, port = state["endpoint"].split(":")
    url = URL.create("postgresql+psycopg", username="artifact_service", password=state["password"],
        host=host, port=int(port), database=state["database"])
    data_python = os.environ.get("AMPHORA_TEST_DATA_PYTHON", sys.executable)
    research_python = os.environ.get("AMPHORA_TEST_RESEARCH_PYTHON", sys.executable)
    knowledge_python = os.environ.get("AMPHORA_TEST_KNOWLEDGE_PYTHON", sys.executable)
    environment = dict(os.environ, DATA_DATABASE=url.render_as_string(hide_password=False), DATA_TOKEN="d"*32, DATA_READ_TOKEN="b"*32,
        PEER_MIGRATION=url.set(username="artifact_migrator").render_as_string(hide_password=False),
        RESEARCH_TOKEN="r"*32, KNOWLEDGE_TOKEN="k"*32,
        KNOWLEDGE_DATABASE=case.engine.url.render_as_string(hide_password=False))
    owned_script(data_python, "import os; from amphora_data_artifacts.persistence.migrate import upgrade; upgrade(os.environ['PEER_MIGRATION'])", environment)
    scope = case.proposal.graph.scope.model_dump(mode="json")
    schema = {"schema_id": "fixture.bytes", "version": "1",
              "sha256": hashlib.sha256(b'{"type":"string","contentEncoding":"base64"}').hexdigest()}
    data_config = tmp_path / "data.json"
    (tmp_path / "bytes").mkdir()
    data_config.write_text(json.dumps({"database_url_env": "DATA_DATABASE", "storage_root": str(tmp_path / "bytes"),
        "acquisition": True, "principals": [{"token_env": "DATA_TOKEN", "actor_id": "fixture", "scope": scope,
            "actions": ["read", "source_history", "upload", "finalize", "acquire", "manage_source_rights"]},
            {"token_env": "DATA_READ_TOKEN", "actor_id": "knowledge-reader", "scope": scope,
             "actions": ["read", "source_history"]}],
        "profiles": [{"media_type": "application/octet-stream", **schema}]}), encoding="utf-8")
    owners = []
    try:
        data = Owner("amphora_data_artifacts", data_config, environment, "d"*32, python=data_python)
        owners.append(data)
        artifact = publish(data, scope, peer.raw, schema)
        rights = {"wire_version": "1", "reference": {"scope": scope, "rights_id": "fixture", "revision": 1},
            "supersedes": None, "status": "granted", "allowed_uses": ["read", "process"],
            "expires_at": None, "retention": "retain_audit_payload"}
        data.request("/v1/acquisition/rights", rights)
        source = peer.source_record.model_dump(mode="json")
        source["reference"]["raw"] = artifact
        prepared = data.request("/v1/acquisition/prepare", source)
        output = publish(data, scope, prepared["content_json_utf8"].encode(), prepared["schema_ref"])
        trace = data.request("/v1/acquisition/retain", {"wire_version": "1", "source": source,
            "trace_id": "actual-conversion", "output": output})
        proposal = peer.proposal.model_dump(mode="json")

        def substitute(value):
            if isinstance(value, dict):
                if "artifact_id" in value:
                    value.clear()
                    value.update(copy.deepcopy(artifact))
                elif "trace_id" in value:
                    value.clear()
                    value.update(copy.deepcopy(trace))
                for child in value.values():
                    substitute(child)
            elif isinstance(value, list):
                for child in value:
                    substitute(child)

        substitute(proposal)
        question = peer.question_record.model_dump(mode="json")
        need = peer.need_record.model_dump(mode="json")
        question["applicability"], need["required_context"] = artifact, artifact
        environment.update(PEER_MIGRATION=url.set(username="research_migrator").render_as_string(hide_password=False),
            PEER_DATABASE=url.set(username="research_service").render_as_string(hide_password=False),
            PEER_QUESTION=json.dumps(question), PEER_NEED=json.dumps(need))
        owned_script(research_python, RESEARCH_SEED, environment)
        research_config = tmp_path / "research.json"
        research_config.write_text(json.dumps({"database_url_env": "PEER_DATABASE", "principals": [
            {"token_env": "RESEARCH_TOKEN", "actor_id": "reader", "scope": scope, "actions": ["read_declarations"]}]}))
        research = Owner("amphora_research", research_config, environment, "r"*32, python=research_python)
        owners.append(research)
        config = tmp_path / "knowledge.json"
        config.write_text(json.dumps({"database_url_env": "KNOWLEDGE_DATABASE", "principals": [
            {"token_env": "KNOWLEDGE_TOKEN", "actor_id": "author", "scope": scope, "actions": ["read_graph", "propose_graph", "rebuild_graph"]}],
            "vocabulary": case.vocabulary.record.model_dump(mode="json"), "policy": case.policy.definition(),
            "data": {"endpoint": data.endpoint, "token_env": "DATA_READ_TOKEN"},
            "research": {"endpoint": research.endpoint, "token_env": "RESEARCH_TOKEN"}}))
        knowledge = Owner("amphora_knowledge", config, environment, "k"*32, python=knowledge_python)
        owners.append(knowledge)
        accepted = knowledge.request("/v1/graph-proposals", proposal)
        assert accepted["decision"]["outcome"] == "accepted"
        head = accepted["decision"]["head"]
        original_snapshot = knowledge.request("/v1/graph-snapshots/read", head["snapshot"])
        assert original_snapshot["content"]["assertions"][0]["posture"] == "hypothesis"
        assert original_snapshot["content"]["assertions"][0]["research_links"][0]["need"] == need["reference"]
        rebuild_query = {"wire_version": "1", "graph": proposal["graph"], "rebuild_id": "before-restart"}
        rebuilt = knowledge.request("/v1/graph-rebuilds", rebuild_query)
        assert rebuilt["result"]["outcome"] == "published" and rebuilt["result"]["head"] == head
        knowledge.stop()
        knowledge = Owner("amphora_knowledge", config, environment, "k"*32,
            python=os.environ.get("AMPHORA_TEST_KNOWLEDGE_REPLACEMENT_PYTHON", knowledge_python))
        owners.append(knowledge)
        assert knowledge.request("/v1/graph-proposals", proposal) == accepted
        assert knowledge.request("/v1/graph-snapshots/read", head["snapshot"]) == original_snapshot
        assert knowledge.request("/v1/graph-rebuilds/read", rebuild_query) == rebuilt
        assert knowledge.request("/v1/graph-rebuilds", rebuild_query) == rebuilt
        change = knowledge.request("/v1/graph-changes/read", head["change"])
        assert change["content"]["actor_id"] == "author"
        assert change["content"]["validation"]["conversion_traces"] == [trace]
        # An unavailable Research owner remains pending, never an invented unknown.
        pending = copy.deepcopy(proposal)
        pending["change_id"], pending["graph"]["graph_id"] = "pending", "pending-graph"
        def regraph(value):
            if isinstance(value, dict):
                if "graph_id" in value:
                    value["graph_id"] = "pending-graph"
                for child in value.values():
                    regraph(child)
            elif isinstance(value, list):
                for child in value:
                    regraph(child)
        regraph(pending)
        research.stop()
        with pytest.raises(urllib.error.HTTPError) as error:
            knowledge.request("/v1/graph-proposals", pending)
        assert error.value.code == 503
        assert knowledge.request("/v1/graphs/pending-graph/proposals/pending")["decision"] is None
        research = Owner("amphora_research", research_config, environment, "r"*32,
            port=research.port, python=research_python)
        owners.append(research)
        assert knowledge.request("/v1/graph-proposals", pending)["decision"]["outcome"] == "accepted"
        # Current source rights gate new observations; old accepted receipt is historical.
        revoked = copy.deepcopy(rights)
        revoked.update(supersedes=rights["reference"], status="revoked", allowed_uses=[])
        revoked["reference"]["revision"] = 2
        data.request("/v1/acquisition/rights", revoked)
        denied = copy.deepcopy(proposal)
        denied["change_id"] = "revoked-new"
        result = knowledge.request("/v1/graph-proposals", denied)
        assert result["decision"]["outcome"] == "rejected"
        assert result["decision"]["findings"][0]["code"] == "peer_access_denied"
        assert knowledge.request("/v1/graph-heads/read", proposal["graph"]) == head
        assert knowledge.request("/v1/graph-proposals", proposal) == accepted
        rebuilt_after_revocation = knowledge.request("/v1/graph-rebuilds", dict(rebuild_query, rebuild_id="after-revocation"))
        assert rebuilt_after_revocation["result"]["head"] == head
        evidence = {"timestamp": datetime.now(ZoneInfo("America/Chicago")).strftime("%Y-%m-%d %H:%M:%S"),
            "tier": "actual PostgreSQL and three owner HTTP processes", "graph": proposal["graph"],
            "source": source["reference"], "trace": trace, "head": head,
            "question": question["reference"], "need": need["reference"],
            "cases": ["accepted_exact_provenance", "hypothesis_not_promoted", "knowledge_restart_exact_receipt_and_snapshot",
                "research_outage_pending", "research_recovery_exact_retry", "revoked_rights_new_proposal_rejected",
                "historical_receipt_stable_after_revocation", "published_rebuild_survives_restart",
                "historical_rebuild_never_consumes_revoked_source_payloads"],
            "limits": ["Synthetic software proof only", "Independent wheel replacement belongs to V1", "No mid-build kill proof yet"]}
        destination = Path(os.environ.get("AMPHORA_KNOWLEDGE_ACCEPTANCE_EVIDENCE", str(tmp_path / "evidence.json")))
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    finally:
        for owner in reversed(owners):
            owner.stop()
