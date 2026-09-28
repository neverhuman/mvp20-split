"""Independent frontier/address and value oracles, before durable advancement exists."""

import json

import pytest
from amphora_campaign_runtime.compiler import compile_campaign
from amphora_campaign_runtime.coordinator import FrontierPlanner, ScopeAddress
from amphora_campaign_runtime.coordinator.bindings import ValueEnvironment
from amphora_campaign_runtime.coordinator.values import BoundValues
from amphora_campaign_runtime.lifecycle.model import TransitionError
from amphora_contracts_campaigns import ActivationPath, ValueBinding, ValuePort
from amphora_contracts_core import Scope
from amphora_contracts_graph_runtime import GraphBinding

from ..compiler.conftest import definition


@pytest.mark.parametrize("index,ready,waiting", [
    (0, {"affine"}, {"finish"}), (1, {"choose"}, {"left", "right", "collect", "finish"}),
    (2, {"batch"}, {"finish"}), (3, {"loop"}, {"finish"}),
])
def test_manual_initial_frontier_sets(compiler_env, index, ready, waiting):
    env = compiler_env
    plan = compile_campaign(definition(env.raw[index]), env.tools, env.schemas)
    address = ScopeAddress(plan.sha256)
    before = FrontierPlanner().scope(plan, address)
    assert {item.address.path.node_id for item in before if item.status == "ready"} == ready
    assert {item.address.path.node_id for item in before if item.status == "waiting"} == waiting
    assert FrontierPlanner().scope(plan, address) == before
    assert len({item.address.key for item in before}) == len(before)
    assert [item.priority for item in before] == sorted(item.priority for item in before)
    with pytest.raises(TransitionError, match="graph_scope_plan_mismatch"):
        FrontierPlanner().scope(plan, ScopeAddress("0" * 64))


def test_loop_occurrences_have_distinct_scopes_and_deterministic_priorities(compiler_env):
    env = compiler_env
    plan = compile_campaign(definition(env.raw[3]), env.tools, env.schemas)
    addresses = []
    for index in (0, 1):
        path = ActivationPath.model_validate_json(json.dumps({"schema_version": "2", "node_id": "finish",
             "occurrences": [{"kind": "loop", "node_id": "loop", "index": index}]}))
        address = ScopeAddress(plan.sha256, path.occurrences)
        node, = FrontierPlanner().scope(plan, address)
        assert node.priority == (0, index, 0) and node.status == "ready"
        addresses.append((address.key, node.address.key))
    assert addresses[0][0] != addresses[1][0] and addresses[0][1] != addresses[1][1]


def test_numeric_literal_bridge_preserves_finite_magnitude_without_command_floats():
    environment = ValueEnvironment(BoundValues(()), {})
    for literal, expected in [(0.25, "0.25"), (1e100, "1" + "0" * 100), (5e-324, "0." + "0" * 323 + "5")]:
        binding = ValueBinding.model_validate_json(json.dumps({"port": "value", "source": {"kind": "number", "value": literal, "unit": "1"}}))
        result = environment.bind((binding,))
        assert result.values["value"].value == expected
        assert BoundValues.from_records(result.record()) == result


def test_typed_collection_missingness_and_units_are_not_coerced():
    scope = Scope(tenant_id="test", project_id="graph")
    port = {"name": "values", "value_type": {"kind": "collection", "max_items": 2, "missing_slots": True,
             "item": {"kind": "scalar", "scalar": "number", "unit": "g/mol"}}}
    binding = {"port": "values", "value": {"kind": "collection", "items": [
        {"kind": "number", "value": "0.25", "unit": "g/mol"}, {"kind": "missing", "member_id": "m2", "reason_code": "failed"}]}}
    values = BoundValues((GraphBinding.model_validate_json(json.dumps(binding)),))
    values.validate((ValuePort.model_validate_json(json.dumps(port)),), scope)
    for change in ("missing_slots", "unit"):
        if change == "missing_slots":
            port["value_type"]["missing_slots"] = False
        else:
            port["value_type"]["missing_slots"] = True
            port["value_type"]["item"]["unit"] = "1"
        with pytest.raises(TransitionError, match="graph_input_type_mismatch"):
            values.validate((ValuePort.model_validate_json(json.dumps(port)),), scope)
