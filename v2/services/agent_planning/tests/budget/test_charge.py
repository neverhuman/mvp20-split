import hashlib
import json
from pathlib import Path

import pytest
from amphora_agent_planning.budget import BudgetPolicy
from amphora_agent_planning.budget.charge import BudgetCharge
from amphora_agent_planning.context import AttemptBinding, RequestSnapshot
from amphora_agent_planning.providers import FixtureProvider, observe
from amphora_contracts_core import Scope


@pytest.fixture
def charge_input():
    raw = json.loads((Path(__file__).parents[1] / "context/fixtures/request.json").read_bytes())
    binding = AttemptBinding(RequestSnapshot.from_bytes(json.dumps(raw).encode(), actor_id="fixture",
        scope=Scope.model_validate(raw["reference"]["scope"])), 1)
    context = raw["context"]
    policy = {key: context[key] for key in
              ("model", "prompt", "policy", "output_schema", "allowed_actions", "limits")}
    policy.update(format="planning-budget-policy.v1", per_attempt_accounting_units=60)
    demand = BudgetPolicy.from_bytes(json.dumps(policy).encode()).demand(binding)
    wire = observe(binding, FixtureProvider("interrupted")).document().model_dump(mode="json")
    return demand, wire


@pytest.mark.parametrize("status", ["proposed", "abstained", "invalid", "unavailable", "policy_rejected", "unknown"])
def test_status_never_grants_a_refund(charge_input, status):
    demand, wire = charge_input
    wire.update(status=status)
    wire["usage"] = dict(input_tokens=10, output_tokens=10, accounting_units=1, certainty="reported")
    raw = json.dumps(wire).encode()
    charge = BudgetCharge.reconcile(demand, raw)
    assert (charge.tokens, charge.accounting_units, charge.overage) == (2048, 60, False)
    assert charge.observation_sha256 == hashlib.sha256(raw).hexdigest()


@pytest.mark.parametrize("counts,expected", [
    ((None, None, None), (1024, 1024, 60, False)),
    ((2000, None, 80), (2000, 1024, 80, True)),
    ((None, 3000, None), (1024, 3000, 60, True)),
    ((0, 0, 0), (1024, 1024, 60, False)),
    ((16777216, 16777216, 9007199254740991), (16777216, 16777216, 9007199254740991, True)),
], ids=["unknown", "partial-overage", "output-overage", "zero", "maximum-exact"])
def test_uncertain_counts_are_lower_bounds_never_clipped(charge_input, counts, expected):
    demand, wire = charge_input
    wire["usage"] = dict(zip(("input_tokens", "output_tokens", "accounting_units"), counts, strict=True),
                         certainty="unknown")
    charge = BudgetCharge.reconcile(demand, json.dumps(wire).encode())
    assert (charge.input_tokens, charge.output_tokens, charge.accounting_units, charge.overage) == expected


def test_charge_rejects_another_attempt(charge_input):
    demand, wire = charge_input
    wire["attempt"]["ordinal"] = 2
    with pytest.raises(ValueError, match="charge_attempt_mismatch"):
        BudgetCharge.reconcile(demand, json.dumps(wire).encode())
