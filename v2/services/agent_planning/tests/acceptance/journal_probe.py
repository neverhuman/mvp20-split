"""Installed owner process probe; URL secrets arrive only through environment."""

import hashlib
import json
import os
import sys
from pathlib import Path

from amphora_agent_planning.access import Principal
from amphora_agent_planning.budget import BudgetPolicy
from amphora_agent_planning.context import AttemptBinding, RequestSnapshot
from amphora_agent_planning.orchestration import PlanningRunner
from amphora_agent_planning.persistence.budget import BudgetLedger
from amphora_agent_planning.persistence.journal import PlanningJournal
from amphora_agent_planning.persistence.settlement import SettlementJournal
from amphora_agent_planning.providers import FixtureProvider, observe
from amphora_contracts_core import Scope
from amphora_contracts_planning import reference_proposal_schema
from sqlalchemy import create_engine


def main():
    stage, project = sys.argv[1:]
    raw = json.loads((Path(__file__).parents[1] / "context/fixtures/request.json").read_bytes())
    scope = Scope(tenant_id="planning-installed", project_id=project)
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
    if stage.startswith("budget_"):
        raw["reference"]["engagement_id"] = "budget-decision"
    if stage.startswith("dispatch_"):
        raw["reference"]["engagement_id"] = "dispatch-decision"
    raw["context"]["output_schema"] = reference_proposal_schema().model_dump(mode="json")
    request = RequestSnapshot.from_bytes(json.dumps(raw).encode(), actor_id="fixture", scope=scope)
    principal = Principal("fixture", scope, frozenset({"record_requests", "record_attempts", "read_attempts"}))
    first, second = AttemptBinding(request, 1), AttemptBinding(request, 2)
    engine = create_engine(os.environ["AMPHORA_TEST_PLANNING_SERVICE_URL"],
                           connect_args={"options": "-c statement_timeout=5000"})
    journal = PlanningJournal(engine)
    try:
        if stage.startswith("dispatch_"):
            context = request.document().context.model_dump(mode="json")
            fixture_policy = {key: context[key] for key in
                ("model", "prompt", "policy", "output_schema", "allowed_actions", "limits")}
            fixture_policy.update(format="planning-budget-policy.v1", per_attempt_accounting_units=40)
            policy = BudgetPolicy.from_bytes(json.dumps(fixture_policy).encode())
            calls = []
            class Counted:
                def supports(self, model):
                    return True
                def reply(self, binding):
                    calls.append(binding.ordinal)
                    return FixtureProvider("abstain").reply(binding)
            runner = PlanningRunner(engine, Counted(), timeout_seconds=30)
            if stage == "dispatch_prepare":
                journal.register(principal, request)
                runner.ledger.reserve(principal, first, policy)
                ticket = runner.dispatch.issue(principal, first, 1)
                assert ticket is not None
                print(json.dumps({"pid": os.getpid(), "request_sha256": request.sha256,
                    "deadline": ticket.deadline.isoformat(), "status": "pending"}))
                return
            outcome = runner.run(principal, request, policy)
            assert outcome.stop_reason == "abstained"
            assert [a.observation.document().status for a in outcome.attempts] == ["unknown", "abstained"]
            assert calls == ([2] if stage == "dispatch_run" else [])
            settlements = [runner.settlements.read(principal, b.reference()) for b in (first, second)]
            assert sum(r.charge.accounting_units for r in settlements) == 80
            print(json.dumps({"pid": os.getpid(), "request_sha256": request.sha256,
                "calls": calls, "records": [hashlib.sha256(a.observation.canonical).hexdigest()
                                           for a in outcome.attempts],
                "charges": [r.charge.accounting_units for r in settlements], "stop": outcome.stop_reason}))
            return
        if stage.startswith("budget_"):
            context = request.document().context.model_dump(mode="json")
            fixture_policy = {key: context[key] for key in
                ("model", "prompt", "policy", "output_schema", "allowed_actions", "limits")}
            fixture_policy.update(format="planning-budget-policy.v1", per_attempt_accounting_units=60)
            policy = BudgetPolicy.from_bytes(json.dumps(fixture_policy).encode())
            ledger = BudgetLedger(engine)
            if stage == "budget_prepare":
                journal.register(principal, request)
                reserved = ledger.reserve(principal, first, policy)
            else:
                reserved = ledger.read(principal, first.reference())
                assert reserved is not None and ledger.reserve(principal, first, policy) == reserved
            if stage in {"budget_settle", "budget_settle_replay"}:
                settlements = SettlementJournal(engine)
                if stage == "budget_settle":
                    journal.record(principal, first, observe(first, FixtureProvider("interrupted")))
                    settled = settlements.settle(principal, first)
                else:
                    settled = settlements.read(principal, first.reference())
                    assert settled is not None and settlements.settle(principal, first) == settled
                try:
                    ledger.reserve(principal, second, policy)
                except ValueError as exc:
                    assert str(exc) == "accounting_budget_exhausted"
                else:
                    raise AssertionError("Unknown usage incorrectly refunded")
                assert journal.read_attempt(principal, second.reference()) is None
                print(json.dumps({"pid": os.getpid(), "request_sha256": request.sha256,
                    "observation_sha256": settled.charge.observation_sha256,
                    "tokens": settled.charge.tokens, "units": settled.charge.accounting_units,
                    "overage": settled.charge.overage, "registered_at": settled.registered_at.isoformat()}))
                return
            assert journal.read_attempt(principal, first.reference()).observation is None
            print(json.dumps({"pid": os.getpid(), "request_sha256": request.sha256,
                "policy_sha256": reserved.demand.policy_sha256, "tokens": reserved.demand.tokens,
                "units": reserved.demand.accounting_units, "registered_at": reserved.registered_at.isoformat()}))
            return
        if stage == "prepare":
            journal.register(principal, request)
            assert journal.begin_attempt(principal, first).observation is None
        else:
            assert journal.read_request(principal, request.document().reference) == request
            if stage == "interrupted":
                assert journal.read_attempt(principal, first.reference()).observation is None
                journal.record(principal, first, observe(first, FixtureProvider("interrupted")))
                journal.begin_attempt(principal, second)
            elif stage == "finish":
                assert journal.read_attempt(principal, second.reference()).observation is None
                result = observe(second, FixtureProvider("proposal"))
                assert journal.record(principal, second, result) == journal.record(principal, second, result)
            elif stage != "replay":
                raise ValueError("unknown_probe_stage")
        attempts = []
        for binding in (first, second):
            stored = journal.read_attempt(principal, binding.reference())
            if stored is None:
                attempts.append(None)
            elif stored.observation is None:
                attempts.append({"ordinal": binding.ordinal, "status": "pending"})
            else:
                wire = stored.observation.document()
                attempts.append({"ordinal": binding.ordinal, "status": wire.status,
                    "record_sha256": hashlib.sha256(stored.observation.canonical).hexdigest(),
                    "capture_sha256": stored.observation.capture.sha256, "usage": wire.usage.model_dump(mode="json")})
        print(json.dumps({"pid": os.getpid(), "request_sha256": request.sha256, "attempts": attempts}))
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
