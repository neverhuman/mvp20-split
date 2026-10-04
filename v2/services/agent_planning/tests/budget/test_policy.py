import copy
import hashlib
import json
from pathlib import Path

import pytest
from amphora_agent_planning.budget import BudgetPolicy
from amphora_agent_planning.context import AttemptBinding, RequestSnapshot
from amphora_contracts_core import Scope
from amphora_contracts_planning import reference_proposal_schema


def documents():
    request = json.loads((Path(__file__).parents[1] / "context/fixtures/request.json").read_bytes())
    context = request["context"]
    context["output_schema"] = reference_proposal_schema().model_dump(mode="json")
    policy = {key: copy.deepcopy(context[key]) for key in
              ("model", "prompt", "policy", "output_schema", "allowed_actions", "limits")}
    policy.update(format="planning-budget-policy.v1", per_attempt_accounting_units=60)
    return request, policy


def bind(request):
    return AttemptBinding(RequestSnapshot.from_bytes(json.dumps(request).encode(), actor_id="fixture",
        scope=Scope.model_validate(request["reference"]["scope"])), 1)


def reviewed(policy):
    return BudgetPolicy.from_bytes(json.dumps(policy).encode())


def test_exact_demand_and_narrower_request_do_not_change_owner_policy():
    request, raw_policy = documents()
    policy = reviewed(raw_policy)
    expected = hashlib.sha256(policy.canonical).hexdigest()
    raw_policy["limits"]["total_accounting_units"] = 99999
    assert policy.sha256 == expected
    original = bind(request)
    demand = policy.demand(original)
    assert (demand.tokens, demand.accounting_units) == (2048, 60)
    assert demand.policy_sha256 == expected and demand.attempt == original.reference()
    request["context"]["limits"].update(max_input_tokens=512, max_output_tokens=512, max_attempts=1,
                                        total_tokens=1024, total_accounting_units=60)
    request["context"]["allowed_actions"] = ["abstain"]
    narrowed = policy.demand(bind(request))
    assert (narrowed.tokens, narrowed.accounting_units) == (1024, 60)
    assert narrowed.attempt.request_sha256 != demand.attempt.request_sha256
    assert policy.sha256 == expected


@pytest.mark.parametrize("name,value", [("max_input_tokens", 1025), ("max_output_tokens", 1025),
    ("max_attempts", 3), ("total_tokens", 4097), ("total_accounting_units", 101)])
def test_request_cannot_raise_reviewed_ceilings(name, value):
    request, policy = documents()
    request["context"]["limits"][name] = value
    with pytest.raises(ValueError, match="budget_ceiling_exceeded"):
        reviewed(policy).demand(bind(request))


@pytest.mark.parametrize("target", ["model", "prompt", "policy", "output_schema"])
def test_request_cannot_swap_reviewed_binding(target):
    request, policy = documents()
    if target == "model":
        request["context"][target]["model_revision"] = "2"
    else:
        request["context"][target]["sha256"] = "f" * 64
    with pytest.raises(ValueError, match="budget_policy_binding"):
        reviewed(policy).demand(bind(request))


def test_action_units_and_minimum_attempt_cost_remain_authoritative():
    request, policy = documents()
    request["context"]["allowed_actions"].append("propose_campaign")
    with pytest.raises(ValueError, match="budget_actions_exceeded"):
        reviewed(policy).demand(bind(request))
    request, policy = documents()
    request["context"]["limits"]["accounting_unit"] = "other-unit"
    with pytest.raises(ValueError, match="budget_unit_mismatch"):
        reviewed(policy).demand(bind(request))
    request["context"]["limits"].update(accounting_unit="fixture-unit", total_accounting_units=59)
    with pytest.raises(ValueError, match="attempt_accounting_exceeded"):
        reviewed(policy).demand(bind(request))


@pytest.mark.parametrize("variant,code", [("scope", "budget_policy_scope"), ("actions", "budget_policy_actions"),
    ("tokens", "budget_policy_tokens"), ("units", "budget_policy_accounting"), ("float", "invalid_budget_policy")])
def test_invalid_reviewed_configuration_is_not_activated(variant, code):
    _, policy = documents()
    if variant == "scope":
        policy["prompt"]["scope"]["project_id"] = "foreign"
    elif variant == "actions":
        policy["allowed_actions"] = ["abstain", "abstain"]
    elif variant == "tokens":
        policy["limits"]["total_tokens"] = 100
    elif variant == "units":
        policy["per_attempt_accounting_units"] = 101
    else:
        policy["per_attempt_accounting_units"] = 1.5
    with pytest.raises(ValueError, match=code):
        reviewed(policy)


@pytest.mark.parametrize("raw,code", [(b"", "budget_policy_size"), (b"x" * 16385, "budget_policy_size"),
    (b"\xff", "invalid_budget_policy"), (b"{}", "invalid_budget_policy"),
    (b'{"x":1,"x":2}', "duplicate_json_key"), (b'{"x":NaN}', "nonfinite_json")],
    ids=["empty", "oversized", "utf8", "shape", "duplicate", "nonfinite"])
def test_strict_bounded_policy_input(raw, code):
    with pytest.raises(ValueError, match=code):
        BudgetPolicy.from_bytes(raw)
