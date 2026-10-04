"""Abrupt process exit at committed boundaries; synthetic provider markers only."""

import hashlib
import json
import os
import sys
from pathlib import Path

import amphora_agent_planning
from amphora_agent_planning.access import Principal
from amphora_agent_planning.budget import BudgetPolicy
from amphora_agent_planning.context import AttemptBinding, RequestSnapshot
from amphora_agent_planning.orchestration import PlanningRunner
from amphora_agent_planning.providers import FixtureProvider
from amphora_contracts_core import Scope
from amphora_contracts_planning import reference_proposal_schema
from sqlalchemy import create_engine


def main():
    phase, scenario, project = sys.argv[1:]
    assert Path(amphora_agent_planning.__file__).absolute().is_relative_to(Path(sys.prefix).absolute())
    raw = json.loads((Path(__file__).parents[1] / "context/fixtures/request.json").read_bytes())
    scope = Scope(tenant_id="planning-crash", project_id=project)
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
    raw["context"]["output_schema"] = reference_proposal_schema().model_dump(mode="json")
    snapshot = RequestSnapshot.from_bytes(json.dumps(raw).encode(), actor_id="fixture", scope=scope)
    first = AttemptBinding(snapshot, 1)
    principal = Principal("fixture", scope, frozenset({"record_requests", "record_attempts", "read_attempts"}))
    context = snapshot.document().context.model_dump(mode="json")
    policy_data = {key: context[key] for key in
                   ("model", "prompt", "policy", "output_schema", "allowed_actions", "limits")}
    policy_data.update(format="planning-budget-policy.v1", per_attempt_accounting_units=40)
    policy = BudgetPolicy.from_bytes(json.dumps(policy_data).encode())
    markers = Path(os.environ["AMPHORA_PLANNING_PROBE_MARKERS"])
    calls = []

    class MarkedProvider:
        def supports(self, model):
            return True

        def reply(self, binding):
            calls.append(binding.ordinal)
            marker = markers / f"attempt-{binding.ordinal}.json"
            try:
                with marker.open("x", encoding="utf-8") as stream:
                    json.dump({"pid": os.getpid(), "ordinal": binding.ordinal,
                               "request_sha256": snapshot.sha256}, stream)
            except FileExistsError:
                (markers / "duplicate.flag").write_text("repeated physical attempt", encoding="utf-8")
                raise
            reply = FixtureProvider("abstain").reply(binding)
            if phase == "crash" and scenario == "provider_return":
                os._exit(73)
            return reply

    engine = create_engine(os.environ["AMPHORA_TEST_PLANNING_SERVICE_URL"],
                           connect_args={"options": "-c statement_timeout=5000"})
    runner = PlanningRunner(engine, MarkedProvider(), timeout_seconds=1)
    try:
        if phase == "crash":
            print(json.dumps({"pid": os.getpid(), "request_sha256": snapshot.sha256}), flush=True)
            runner.journal.register(principal, snapshot)
            runner.ledger.reserve(principal, first, policy)
            if scenario == "reservation":
                os._exit(71)
            if scenario == "issuance":
                assert runner.dispatch.issue(principal, first, 1) is not None
                os._exit(72)
            if scenario == "observation":
                runner.settlements.settle = lambda *_: os._exit(74)
            runner.execute(principal, first, policy)
            if scenario == "settlement":
                os._exit(75)
            raise AssertionError("Crash boundary not reached")
        outcome = runner.run(principal, snapshot, policy)
        assert outcome.stop_reason == "abstained"
        charges = [runner.settlements.read(principal, a.binding.reference()).charge.accounting_units
                   for a in outcome.attempts]
        print(json.dumps({"pid": os.getpid(), "request_sha256": snapshot.sha256,
            "statuses": [a.observation.document().status for a in outcome.attempts],
            "records": [hashlib.sha256(a.observation.canonical).hexdigest() for a in outcome.attempts],
            "charges": charges, "calls": calls, "stop": outcome.stop_reason}))
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
