"""Explicit pytest process stages using scripted peers and the real owned journal."""

import importlib.util
import json
import os
from pathlib import Path
from types import SimpleNamespace

from amphora_agent_planning.access import Principal
from amphora_agent_planning.context import AttemptBinding
from amphora_agent_planning.persistence.budget import BudgetLedger
from amphora_agent_planning.persistence.journal import PlanningJournal
from amphora_agent_planning.persistence.preparation import PreparationJournal
from amphora_agent_planning.persistence.settlement import SettlementJournal
from amphora_contracts_core import Scope
from sqlalchemy import create_engine

from ..persistence.test_preparation import enrolled
from ..persistence.test_repair_runner import Inputs, Provider, execute


def test_process_stage():
    for name in ("amphora_knowledge", "amphora_research", "amphora_data_artifacts", "amphora_campaign_runtime"):
        assert importlib.util.find_spec(name) is None
    stage = os.environ["AMPHORA_REPAIR_STAGE"]
    scope = Scope(tenant_id="planning-repair-workflow", project_id=os.environ["AMPHORA_REPAIR_PROJECT"])
    principal = Principal("fixture", scope, frozenset({"record_requests", "record_attempts", "read_attempts"}))
    engine = create_engine(os.environ["AMPHORA_TEST_PLANNING_SERVICE_URL"])
    try:
        s = SimpleNamespace(principal=principal, engine=engine, journal=PlanningJournal(engine))
        prepared = enrolled(s)
        binding = AttemptBinding(prepared.plan.task.request, 1)
        preparations, ledger = PreparationJournal(engine), BudgetLedger(engine)
        stored = preparations.register(principal, prepared)
        reservation = ledger.reserve(principal, binding, prepared.history.root.policy)
        inputs, provider = Inputs(prepared), Provider()
        if stage == "prepare":
            outcome = None
            assert not preparations.issued(principal, binding)
        else:
            assert stage in {"run", "replay"}
            inputs.denied = stage == "replay"
            outcome = execute(s, inputs, provider)
            assert outcome.trace is not None
            assert len(provider.packets) == inputs.calls == (1 if stage == "run" else 0)
        settlement = SettlementJournal(engine).read(principal, binding.reference())
        result = {"pid": os.getpid(), "stage": stage, "manifest": stored.manifest.sha256,
            "registered_at": stored.registered_at.isoformat(), "request": prepared.plan.task.request.sha256,
            "packet": stored.manifest.document().packet.sha256, "reservation": str(reservation),
            "calls": len(provider.packets), "input_reads": inputs.calls,
            "trace": None if outcome is None else outcome.trace.sha256,
            "settlement": None if settlement is None else str(settlement)}
        Path(os.environ["AMPHORA_REPAIR_RESULT"]).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    finally:
        engine.dispose()
