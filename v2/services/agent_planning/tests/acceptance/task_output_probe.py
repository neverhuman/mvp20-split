"""Installed typed-output replay; no private peer modules or live provider calls."""

import hashlib
import json
import os
import sys
from pathlib import Path

from amphora_agent_planning.access import Principal
from amphora_agent_planning.budget import BudgetPolicy
from amphora_agent_planning.context import RequestSnapshot
from amphora_agent_planning.orchestration import PlanningRunner
from amphora_agent_planning.providers.port import ProviderReply
from amphora_contracts_core import Scope
from amphora_contracts_planning import ProviderUsage
from sqlalchemy import create_engine


def main():
    stage, project = sys.argv[1:]
    raw = json.loads((Path(__file__).parents[1] / "extraction/fixtures/extraction.json").read_bytes())
    scope = Scope(tenant_id="planning-task-format", project_id=project)
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
    context = snapshot.document().context.model_dump(mode="json")
    policy = {key: context[key] for key in ("model", "prompt", "policy", "output_schema", "allowed_actions", "limits")}
    policy.update(format="planning-budget-policy.v1", per_attempt_accounting_units=40)
    policy = BudgetPolicy.from_bytes(json.dumps(policy).encode())
    raw["draft"]["diagnostics"] = [{"code": "fixture", "target_path": "/entities/0", "kind": "unsupported",
                                     "description": '"' * 4000} for _ in range(7)]
    body = json.dumps(raw["draft"]).encode()
    calls = []
    class Provider:
        def supports(self, model):
            return True
        def reply(self, binding):
            calls.append(binding.ordinal)
            return ProviderReply([body], ProviderUsage(input_tokens=None, output_tokens=None,
                                                       accounting_units=None, certainty="unknown"))
    principal = Principal("fixture", scope, frozenset({"record_requests", "record_attempts", "read_attempts"}))
    engine = create_engine(os.environ["AMPHORA_TEST_PLANNING_SERVICE_URL"],
                           connect_args={"options": "-c statement_timeout=5000"})
    try:
        runner = PlanningRunner(engine, Provider(), timeout_seconds=30)
        result = runner.run(principal, snapshot, policy)
        assert calls == ([1] if stage == "write" else [])
        observed = result.latest.observation
        assert result.stop_reason == "proposed" and observed.document().schema_version == "2"
        assert len(body) <= 65536 < len(observed.canonical) <= 262144
        settlement = runner.settlements.read(principal, result.latest.binding.reference())
        assert settlement.charge.accounting_units == 40
        print(json.dumps({"pid": os.getpid(), "request_sha256": snapshot.sha256,
            "output_sha256": observed.document().output_sha256,
            "observation_sha256": hashlib.sha256(observed.canonical).hexdigest(),
            "payload_sha256": observed.document().proposal.payload_sha256,
            "captured_bytes": len(body), "encoded_bytes": len(observed.canonical),
            "units": settlement.charge.accounting_units, "calls": calls}))
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
