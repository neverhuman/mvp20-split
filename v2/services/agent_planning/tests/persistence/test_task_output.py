import json
import time
from pathlib import Path

import pytest
from amphora_agent_planning.budget import BudgetPolicy
from amphora_agent_planning.context import AttemptBinding, RequestSnapshot
from amphora_agent_planning.orchestration import PlanningRunner
from amphora_agent_planning.providers import observe
from amphora_agent_planning.providers.port import ProviderReply
from amphora_contracts_planning import ProviderUsage
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

pytestmark = pytest.mark.postgres


def fixture(s):
    raw = json.loads((Path(__file__).parents[1] / "extraction/fixtures/extraction.json").read_bytes())
    def rescope(value):
        if isinstance(value, dict):
            if set(value) == {"tenant_id", "project_id"}:
                value.update(s.principal.scope.model_dump())
            for child in value.values():
                rescope(child)
        elif isinstance(value, list):
            for child in value:
                rescope(child)
    rescope(raw)
    snapshot = RequestSnapshot.from_bytes(json.dumps(raw["request"]).encode(), actor_id=s.principal.actor_id,
                                         scope=s.principal.scope)
    context = snapshot.document().context.model_dump(mode="json")
    policy = {key: context[key] for key in ("model", "prompt", "policy", "output_schema", "allowed_actions", "limits")}
    policy.update(format="planning-budget-policy.v1", per_attempt_accounting_units=40)
    raw["draft"]["diagnostics"] = [{"code": "fixture", "target_path": "/entities/0", "kind": "unsupported",
                                     "description": '"' * 4000} for _ in range(7)]
    return snapshot, BudgetPolicy.from_bytes(json.dumps(policy).encode()), json.dumps(raw["draft"]).encode()


class Response:
    def __init__(self, raw):
        self.raw = raw
        self.calls = 0

    def supports(self, model):
        return True

    def reply(self, binding):
        self.calls += 1
        return ProviderReply([self.raw], ProviderUsage(input_tokens=None, output_tokens=None,
                                                      accounting_units=None, certainty="unknown"))


def test_large_encoded_task_output_is_immutable_and_charged_conservatively(stored):
    s = stored
    snapshot, policy, raw = fixture(s)
    provider = Response(raw)
    runner = PlanningRunner(s.engine, provider, timeout_seconds=30)
    result = runner.run(s.principal, snapshot, policy)
    observed = result.latest.observation
    assert result.stop_reason == "proposed" and observed.document().schema_version == "2"
    assert len(raw) <= 65536 < len(observed.canonical) <= 262144
    assert runner.run(s.principal, snapshot, policy) == result and provider.calls == 1
    charge = runner.settlements.read(s.principal, result.latest.binding.reference()).charge
    assert charge.tokens == 2048 and charge.accounting_units == 40
    assert runner.journal.read_attempt(s.principal, result.latest.binding.reference()).observation == observed


def test_late_task_output_preserves_original_unknown_version_and_charge(stored):
    s = stored
    snapshot, policy, raw = fixture(s)
    binding = AttemptBinding(snapshot, 1)
    runner = PlanningRunner(s.engine, Response(raw), timeout_seconds=1)
    runner.journal.register(s.principal, snapshot)
    runner.ledger.reserve(s.principal, binding, policy)
    ticket = runner.dispatch.issue(s.principal, binding, 1)
    time.sleep(1.05)
    recovered = runner.dispatch.recover(s.principal, binding)
    assert recovered.observation.document().schema_version == "2"
    original = runner.settlements.settle(s.principal, binding)
    late = observe(binding, Response(raw))
    assert runner.dispatch.complete(s.principal, binding, ticket, late) == recovered
    assert runner.dispatch.read_late(s.principal, binding) == late
    assert len(late.canonical) > 65536
    assert runner.settlements.read(s.principal, binding.reference()) == original


@pytest.mark.parametrize("version", [None, "1", 2])
def test_database_does_not_extend_legacy_or_missing_version_storage_allowance(stored, version):
    s = stored
    s.journal.register(s.principal, s.snapshot)
    s.journal.begin_attempt(s.principal, s.first)
    value = {} if version is None else {"schema_version": version}
    raw = json.dumps(value).encode() + b" " * 65536
    with pytest.raises(DBAPIError) as caught, s.engine.begin() as connection:
        connection.execute(text("INSERT INTO planning.observations "
            "(tenant_id,project_id,engagement_id,ordinal,canonical_bytes,capture_bytes) "
            "VALUES (:tenant,:project,:engagement,1,:raw,:capture)"),
            {"tenant": s.principal.scope.tenant_id, "project": s.principal.scope.project_id,
             "engagement": s.first.reference().engagement.engagement_id, "raw": raw, "capture": b""})
    assert caught.value.orig.sqlstate == "23514"
