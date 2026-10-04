"""Installed result SDK recovery with scripted remote receipts across processes."""

import importlib.util
import json
import os
from pathlib import Path
from types import SimpleNamespace

from amphora_agent_planning.access import Principal
from amphora_agent_planning.persistence.journal import PlanningJournal
from amphora_agent_planning.result_publication.journal import ResultJournal
from amphora_agent_planning.result_publication.selection import ResultSelection
from amphora_agent_planning.result_publication.store import ResultStore
from amphora_agent_planning.result_publication.workflow import ResultPublisher
from amphora_contracts_core import Scope
from amphora_tool_protocol import ArtifactClient, TransportLost, WorkerIdentity
from sqlalchemy import create_engine

from ..publication.test_workflow import DataPeer
from ..result_publication.test_workflow import workflow


class NoPreparation:
    def prepare(self, *_):
        raise AssertionError("Historical recovery attempted new source preparation")


def test_result_workflow_stage():
    assert all(importlib.util.find_spec(name) is None for name in (
        "amphora_data_artifacts", "amphora_knowledge", "amphora_research", "amphora_campaign_runtime"))
    stage = os.environ["AMPHORA_RESULT_WORKFLOW_STAGE"]
    principal = Principal("fixture", Scope(tenant_id="result-workflow-probe", project_id=os.environ["AMPHORA_RESULT_PROJECT"]),
        frozenset({"record_requests", "record_attempts", "read_attempts"}))
    peer_path = Path(os.environ["AMPHORA_RESULT_PEER_STATE"])
    engine = create_engine(os.environ["AMPHORA_TEST_PLANNING_SERVICE_URL"])
    try:
        if stage == "uncertain":
            fixture = SimpleNamespace(principal=principal, engine=engine, journal=PlanningJournal(engine))
            publisher, peer, preparer, selection = workflow(fixture)
            peer.lost_put = True
            try:
                publisher.publish(principal, selection)
            except TransportLost:
                pass
            else:
                raise AssertionError("Expected uncertain PUT")
            state = publisher.journal.read(principal, selection.publication_id)
            assert state.attempt.stage == "streaming" and preparer.calls == 1
        else:
            prior = json.loads(Path(os.environ["AMPHORA_RESULT_WORKFLOW_ORIGIN"]).read_bytes())
            selection = ResultSelection.restore(bytes.fromhex(prior["selection"]), principal)
            journal = ResultJournal(ResultStore(engine, "data-owner", trace_publisher_id="data-owner"))
            state = journal.read(principal, selection.publication_id)
            peer = DataPeer(state.identity, state.payload.artifact)
            remote = json.loads(peer_path.read_bytes())
            peer.commands = {key: value.encode() for key, value in remote["commands"].items()}
            peer.uploads = remote["uploads"]
            publisher = ResultPublisher(journal, NoPreparation(), ArtifactClient(peer, WorkerIdentity(principal.actor_id, principal.scope)))
            state = publisher.publish(principal, selection)
            assert state.attempt.stage == "finalized" and state.attempt.identity.ordinal == 2
            if stage == "replay":
                assert not peer.calls
            else:
                assert stage == "recover"
                assert [path for method, path, _ in peer.calls if method == "PUT"] == ["/v1/uploads/upload-2/content"]
        peer_path.write_text(json.dumps({"commands": {key: value.decode() for key, value in peer.commands.items()},
            "uploads": peer.uploads}), encoding="utf-8")
        result = {"pid": os.getpid(), "stage": stage, "selection": selection.canonical.hex(),
            "identity": state.identity.sha256, "payload": state.payload.sha256,
            "prepared_at": state.prepared_at.isoformat(), "position": state.position,
            "upload_ordinal": state.attempt.identity.ordinal, "outcome": state.attempt.stage,
            "events": [event.canonical.hex() for event, _ in state.events], "peer_calls": len(peer.calls)}
        Path(os.environ["AMPHORA_RESULT_WORKFLOW_OUTPUT"]).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    finally:
        engine.dispose()
