"""Separate installed workers preserve owner intents; peer outcomes are scripted."""

import importlib.util
import json
import os
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

from amphora_agent_planning.access import Principal
from amphora_agent_planning.owner_handoff.journal import HandoffJournal
from amphora_agent_planning.owner_handoff.selection import HandoffSelection
from amphora_agent_planning.owner_handoff.store import HandoffStore
from amphora_agent_planning.persistence.journal import PlanningJournal
from amphora_contracts_core import Scope
from sqlalchemy import create_engine

from ..owner_handoff.test_journal import acknowledge, setup_handoff


def test_handoff_process_stage():
    assert all(importlib.util.find_spec(name) is None for name in (
        "amphora_data_artifacts", "amphora_knowledge", "amphora_research", "amphora_campaign_runtime"))
    stage = os.environ["AMPHORA_HANDOFF_STAGE"]
    principal = Principal("fixture", Scope(tenant_id="handoff-storage-probe", project_id=os.environ["AMPHORA_HANDOFF_PROJECT"]),
        frozenset({"record_requests", "record_attempts", "read_attempts"}))
    engine = create_engine(os.environ["AMPHORA_TEST_PLANNING_SERVICE_URL"])
    try:
        if stage == "prepare":
            fixture = SimpleNamespace(principal=principal, engine=engine, journal=PlanningJournal(engine))
            store, journal, selection, review, questions = setup_handoff(fixture)
            lease = store.acquire(principal, selection.effect_id)
            state = journal.prepare(principal, lease, review, questions=questions)
            store.release(principal, lease)
        else:
            origin = json.loads(Path(os.environ["AMPHORA_HANDOFF_ORIGIN"]).read_bytes())
            selection = HandoffSelection.restore(bytes.fromhex(origin["selection"]), principal)
            store = HandoffStore(engine, "research", trace_publisher_id="data-owner")
            journal = HandoffJournal(store)
            state = journal.read(principal, selection.effect_id)
            if stage == "dispatch":
                lease = store.acquire(principal, selection.effect_id, seconds=2)
                state = journal.advance(principal, lease, state.position, "dispatch")
                # Leave committed intent and an unreleased lease. No actual POST.
            elif stage == "recover":
                assert state.progress.state == "dispatching"
                lease = store.acquire(principal, selection.effect_id)
                state = acknowledge(journal, principal, lease, state)
                store.release(principal, lease)
            else:
                assert stage == "replay"
                state = journal.read(replace(principal, actions=frozenset({"read_attempts"})), selection.effect_id)
                assert state.terminal
        result = {"pid": os.getpid(), "stage": stage, "selection": selection.canonical.hex(),
            "effect_id": selection.effect_id, "request": state.payload.request.sha256, "payload": state.payload.sha256,
            "prepared_at": state.prepared_at.isoformat(), "position": state.position,
            "dispatches": state.progress.dispatches, "outcome": state.progress.state,
            "events": [event.canonical.hex() for event, _ in state.events]}
        Path(os.environ["AMPHORA_HANDOFF_OUTPUT"]).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    finally:
        engine.dispose()
