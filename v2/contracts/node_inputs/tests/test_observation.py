import copy
import json
from pathlib import Path

import pytest
from amphora_contracts_node_inputs import NodeInputObservation, ScopeInputSummary
from pydantic import ValidationError


def example():
    invocation = json.loads((Path(__file__).parent / "prepared.json").read_bytes())
    invocation["activation_id"] = "a" * 64
    return dict(schema_version="1", profile="runtime-node-inputs-v1", scope=copy.deepcopy(invocation["inputs"][0]["artifact"]["scope"]),
        run_id="run", activation_id="a" * 64, scope_key="b" * 64, observed_run_revision=4,
        scope_inputs=[dict(port="context", kind="artifact", item_count=1, missing_count=0,
            artifact=invocation["inputs"][0]["artifact"])], invocation=invocation)


def test_closed_roundtrip_and_no_execution_credentials():
    record = NodeInputObservation.model_validate_json(json.dumps(example()))
    assert NodeInputObservation.model_validate_json(record.model_dump_json()) == record
    assert not {"fence", "lease_expires_at", "grant_id", "worker_id", "attempt_id"} & set(type(record.invocation).model_fields)
    raw = example(); raw["invocation"] = None
    assert NodeInputObservation.model_validate_json(json.dumps(raw)).invocation is None


@pytest.mark.parametrize("change", ["scope", "activation", "duplicate", "extra", "counts", "kind", "limit"])
def test_inconsistent_observations_reject(change):
    raw = example()
    if change == "scope": raw["scope"]["project_id"] = "other"
    if change == "activation": raw["invocation"]["activation_id"] = "c" * 64
    if change == "duplicate": raw["scope_inputs"] *= 2
    if change == "extra": raw["lease"] = "secret"
    if change == "counts": raw["scope_inputs"][0]["missing_count"] = 1
    if change == "kind": raw["scope_inputs"][0]["kind"] = "string"
    if change == "limit": raw["scope_inputs"] *= 65
    with pytest.raises(ValidationError): NodeInputObservation.model_validate_json(json.dumps(raw))


def test_collection_summaries_bound_counts_without_expanding_values():
    ScopeInputSummary(port="members", kind="collection", item_count=10000, missing_count=7)
    with pytest.raises(ValidationError):
        ScopeInputSummary(port="members", kind="collection", item_count=1, missing_count=2)
