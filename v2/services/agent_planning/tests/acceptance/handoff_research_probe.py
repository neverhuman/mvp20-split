"""Installed Planning workflow against actual Research; Data inputs are synthetic."""

import hashlib
import importlib.util
import json
import os
from pathlib import Path
from types import SimpleNamespace

from amphora_agent_planning.access import Principal
from amphora_agent_planning.owner_handoff.history import HandoffHistory
from amphora_agent_planning.owner_handoff.journal import HandoffJournal
from amphora_agent_planning.owner_handoff.preparation import HandoffPreparer
from amphora_agent_planning.owner_handoff.selection import HandoffSelection
from amphora_agent_planning.owner_handoff.store import HandoffStore
from amphora_agent_planning.owner_handoff.transport import (
    OwnerTransport,
    OwnerUnavailable,
)
from amphora_agent_planning.owner_handoff.workflow import OwnerHandoff
from amphora_agent_planning.persistence.journal import PlanningJournal
from amphora_contracts_core import Scope
from sqlalchemy import create_engine

from ..owner_handoff.test_journal import setup_handoff
from ..owner_handoff.test_workflow import Preparer
from ..research_proposals.support import ResearchCase


class Transport(OwnerTransport):
    def __init__(self, endpoint, token, lose=False):
        super().__init__("research", "research", endpoint, token)
        self.reads = self.writes = 0
        self.lose = lose

    def read(self, *args, **kwargs):
        self.reads += 1
        return super().read(*args, **kwargs)

    def submit(self, *args, **kwargs):
        self.writes += 1
        record = super().submit(*args, **kwargs)
        if self.lose:
            self.lose = False
            raise OwnerUnavailable("synthetic_lost_reply_after_actual_commit")
        return record


class ForbiddenInputs:
    def prepare(self, *args, **kwargs):
        raise AssertionError("Historical recovery attempted new preparation")

    def authorize(self, *args, **kwargs):
        raise AssertionError("Historical recovery attempted new source processing")


def test_actual_research_handoff_stage():
    assert all(importlib.util.find_spec(name) is None for name in (
        "amphora_research", "amphora_knowledge", "amphora_data_artifacts", "amphora_campaign_runtime"))
    stage = os.environ["AMPHORA_HANDOFF_STAGE"]
    principal = Principal("fixture", Scope(tenant_id="planning-owner-handoff", project_id=os.environ["AMPHORA_HANDOFF_PROJECT"]),
        frozenset({"record_requests", "record_attempts", "read_attempts"}))
    engine = create_engine(os.environ["AMPHORA_TEST_PLANNING_SERVICE_URL"])
    try:
        if stage == "uncertain":
            fixture = SimpleNamespace(engine=engine, principal=principal, journal=PlanningJournal(engine))
            store, journal, selection, review, questions = setup_handoff(fixture)
            preparer = Preparer(engine, review, questions)
        else:
            origin = json.loads(Path(os.environ["AMPHORA_HANDOFF_ORIGIN"]).read_bytes())
            selection = HandoffSelection.restore(bytes.fromhex(origin["selection"]), principal)
            store = HandoffStore(engine, "research", trace_publisher_id="data-owner")
            journal = HandoffJournal(store)
            preparer = ForbiddenInputs()
            if stage.startswith("need"):
                if stage == "need":
                    with engine.begin() as connection:
                        history = HandoffHistory.load(connection, principal, selection, store.traces)
                    case = ResearchCase(scope=principal.scope)
                    bound = case.bind()
                    assert bound.task.canonical == history.task.canonical
                    reference = history.interpretation.attempt.result.artifact
                    case.data.artifacts[reference.artifact_id] = reference
                    case.data.payloads[reference.artifact_id] = history.projection.canonical
                    preparer = HandoffPreparer(case.data)
                selection = HandoffSelection.bind(principal, selection.trace(), "publication", "need", "n", "research")
        transport = Transport(os.environ["AMPHORA_HANDOFF_ENDPOINT"], os.environ["AMPHORA_HANDOFF_TOKEN"], stage == "uncertain")
        result = OwnerHandoff(journal, preparer, transport).submit(principal, selection)
        state = result.state
        if stage == "uncertain":
            assert state.progress.state == "uncertain" and transport.writes == 1
        elif stage == "denied":
            assert result.reason == "owner_access_denied" and transport.writes == 0
        else:
            assert state.terminal and state.progress.state == "acknowledged"
            assert transport.writes == (1 if stage == "need" else 0)
            if stage.endswith("replay"):
                assert transport.reads == 0
        value = {"stage": stage, "pid": os.getpid(), "selection": selection.canonical.hex(),
            "request": state.payload.request.sha256, "payload": state.payload.sha256,
            "prepared_at": state.prepared_at.isoformat(), "position": state.position,
            "outcome": state.progress.state, "reason": result.reason,
            "reads": transport.reads, "writes": transport.writes,
            "events": [hashlib.sha256(event.canonical).hexdigest() for event, _ in state.events]}
        Path(os.environ["AMPHORA_HANDOFF_OUTPUT"]).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    finally:
        engine.dispose()
