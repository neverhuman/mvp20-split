"""Installed failed/repaired trace continuity, using only Planning credentials."""

import json
import os
import sys
from pathlib import Path

from amphora_agent_planning.access import Principal
from amphora_agent_planning.budget import BudgetPolicy
from amphora_agent_planning.context import AttemptBinding, RequestSnapshot
from amphora_agent_planning.extraction import ExtractionSnapshot
from amphora_agent_planning.orchestration import PlanningRunner
from amphora_agent_planning.persistence.extraction import ExtractionJournal
from amphora_agent_planning.providers.capture import unknown_usage
from amphora_agent_planning.providers.port import ProviderReply
from amphora_contracts_core import Scope
from sqlalchemy import create_engine


def main():
    stage, project, *profile = sys.argv[1:]
    assert profile in ([], ["edits"])
    fixture = "extraction-edits.json" if profile else "extraction.json"
    raw = json.loads((Path(__file__).parents[1] / "extraction/fixtures" / fixture).read_bytes())
    scope = Scope(tenant_id="planning-extraction-edits" if profile else "planning-extraction-traces", project_id=project)
    def rescope(value):
        if isinstance(value, dict):
            if set(value) == {"tenant_id", "project_id"}:
                value.update(scope.model_dump())
            for child in value.values():
                rescope(child)
        elif isinstance(value, list):
            for child in value:
                rescope(child)
    rescope(raw)
    snapshot = RequestSnapshot.from_bytes(json.dumps(raw["request"]).encode(), actor_id="fixture", scope=scope)
    raw["task"]["request_sha256"] = snapshot.sha256
    task = ExtractionSnapshot.from_bytes(json.dumps(raw["task"]).encode(), snapshot)
    context = snapshot.document().context.model_dump(mode="json")
    policy = {key: context[key] for key in ("model", "prompt", "policy", "output_schema", "allowed_actions", "limits")}
    policy.update(format="planning-budget-policy.v1", per_attempt_accounting_units=40)
    policy = BudgetPolicy.from_bytes(json.dumps(policy).encode())
    calls = []
    class Provider:
        def supports(self, model):
            return True
        def reply(self, binding):
            calls.append(binding.ordinal)
            content = b"{" if binding.ordinal == 1 else json.dumps(raw["draft"]).encode()
            return ProviderReply((content,), unknown_usage())
    principal = Principal("fixture", scope, frozenset({"record_requests", "record_attempts", "read_attempts"}))
    engine = create_engine(os.environ["AMPHORA_TEST_PLANNING_SERVICE_URL"],
                           connect_args={"options": "-c statement_timeout=5000"})
    try:
        runner = PlanningRunner(engine, Provider(), timeout_seconds=30)
        journal = ExtractionJournal(engine)
        runner.journal.register(principal, snapshot)
        registered = journal.register(principal, task)
        first = AttemptBinding(snapshot, 1)
        runner.execute(principal, first, policy)
        failed = journal.record(principal, task.document().task_id, first.reference(), "failed")
        records = [failed]
        if stage != "failed":
            result = runner.run(principal, snapshot, policy)
            assert result.stop_reason == "proposed"
            repaired = journal.record(principal, task.document().task_id, result.latest.binding.reference(),
                                       "repaired", failed.projection.reference())
            assert repaired.projection.document().prior == failed.projection.reference()
            assert repaired.projection.document().repair_depth == 1
            records.append(repaired)
        assert calls == {"failed": [1], "repair": [2], "replay": []}[stage]
        assert all(journal.read_trace(principal, row.projection.reference()) == row for row in records)
        charges = [runner.settlements.read(principal, row.projection.document().attempt).charge.accounting_units
                   for row in records]
        assert charges == [40] * len(records)
        print(json.dumps({"pid": os.getpid(), "calls": calls, "task_sha256": task.sha256,
            "task_version": task.document().schema_version,
            "output_profile": snapshot.document().context.output_schema.model_dump(mode="json"),
            "registered_at": registered.registered_at.isoformat(), "charges": charges,
            "traces": [{"sha256": row.projection.sha256, "recorded_at": row.recorded_at.isoformat(),
                        "status": row.projection.document().outcome.status} for row in records]}))
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
