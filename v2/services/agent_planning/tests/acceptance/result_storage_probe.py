"""Independent owned result journal stages; remote receipts are scripted."""

import importlib.util
import json
import os
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

from amphora_agent_planning.access import Principal
from amphora_agent_planning.persistence.journal import PlanningJournal
from amphora_agent_planning.result_publication.journal import ResultJournal
from amphora_agent_planning.result_publication.selection import ResultSelection
from amphora_agent_planning.result_publication.store import ResultStore
from amphora_contracts_core import Scope
from sqlalchemy import create_engine

from ..publication.test_values import receipts
from ..result_publication.test_journal import setup_result


def test_result_process_stage():
    assert all(importlib.util.find_spec(name) is None for name in (
        "amphora_data_artifacts", "amphora_knowledge", "amphora_research", "amphora_campaign_runtime"))
    stage = os.environ["AMPHORA_RESULT_STAGE"]
    principal = Principal("fixture", Scope(tenant_id="result-storage-probe", project_id=os.environ["AMPHORA_RESULT_PROJECT"]),
        frozenset({"record_requests", "record_attempts", "read_attempts"}))
    engine = create_engine(os.environ["AMPHORA_TEST_PLANNING_SERVICE_URL"])
    try:
        if stage == "prepare":
            fixture = SimpleNamespace(principal=principal, engine=engine, journal=PlanningJournal(engine))
            store, journal, selection, review, feedback = setup_result(fixture)
            lease = store.acquire(principal, selection.publication_id)
            state = journal.prepare(principal, lease, review, feedback=feedback)
            store.release(principal, lease)
        else:
            origin = json.loads(Path(os.environ["AMPHORA_RESULT_ORIGIN"]).read_bytes())
            selection = ResultSelection.restore(bytes.fromhex(origin["selection"]), principal)
            store = ResultStore(engine, "data-owner", trace_publisher_id="data-owner")
            journal = ResultJournal(store)
            state = journal.read(principal, selection.publication_id)
            if stage == "stream":
                lease = store.acquire(principal, selection.publication_id, seconds=1)
                upload, _, _, _ = receipts(state.identity, state.payload.artifact, state.attempt)
                state = journal.advance(principal, lease, state.position, "begun", upload.model_dump(mode="json"))
                state = journal.advance(principal, lease, state.position, "streaming")
                # Exit with durable intent and unreleased lease, before any PUT.
            elif stage == "recover":
                lease = store.acquire(principal, selection.publication_id)
                assert state.attempt.stage == "streaming"
                state = journal.advance(principal, lease, state.position, "abandoned")
                state = journal.advance(principal, lease, state.position, "replacement")
                upload, stream, receipt, derivation = receipts(state.identity, state.payload.artifact, state.attempt)
                for action, value in [("begun", upload.model_dump(mode="json")), ("streaming", None),
                    ("streamed", stream.model_dump(mode="json")), ("finalizing", None),
                    ("finalized", {"receipt": receipt.model_dump(mode="json"), "derivation": derivation.model_dump(mode="json")})]:
                    state = journal.advance(principal, lease, state.position, action, value)
                store.release(principal, lease)
            else:
                assert stage == "replay"
                state = journal.read(replace(principal, actions=frozenset({"read_attempts"})), selection.publication_id)
                assert state.attempt.stage == "finalized"
        result = {"pid": os.getpid(), "stage": stage, "selection": selection.canonical.hex(),
            "identity": state.identity.sha256, "payload": state.payload.sha256,
            "prepared_at": state.prepared_at.isoformat(), "position": state.position,
            "upload_ordinal": state.attempt.identity.ordinal, "outcome": state.attempt.stage,
            "events": [event.canonical.hex() for event, _ in state.events]}
        Path(os.environ["AMPHORA_RESULT_OUTPUT"]).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    finally:
        engine.dispose()
