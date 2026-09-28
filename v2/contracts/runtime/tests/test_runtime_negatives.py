import copy
import json
from pathlib import Path

import pytest
from amphora_contracts_commands import CommandEncodingError
from amphora_contracts_runtime import CommandReceipt, parse_command
from pydantic import ValidationError

CASES = json.loads((Path(__file__).parent / "fixtures/commands.json").read_text())


def command(family):
    return copy.deepcopy(next(c["command"] for c in CASES if c["family"] == family))


@pytest.mark.parametrize("family,change", [
    ("runtime.claim", lambda p: p.update(lease_seconds=0)),
    ("runtime.renew", lambda p: p["attempt"].update(fence=0)),
    ("runtime.admit_fixture", lambda p: p["budget"].update(limit=0)),
    ("runtime.admit_fixture", lambda p: p["invocations"][0].update(side_effects="external")),
    ("runtime.complete", lambda p: p.update(expected_checkpoint_revision=-1)),
    ("runtime.cancel", lambda p: p.update(expected_run_revision="1")),
])
def test_invalid_transition_inputs(family, change):
    value = command(family)
    change(value["payload"])
    with pytest.raises(CommandEncodingError, match="schema_invalid"):
        parse_command(family, json.dumps(value))


def test_input_scope_is_bound_to_command_scope():
    family = "runtime.admit_fixture"
    value = command(family)
    value["payload"]["invocations"][0]["inputs"][0]["artifact"]["scope"]["project_id"] = "other"
    with pytest.raises(CommandEncodingError, match="scope_mismatch"):
        parse_command(family, json.dumps(value))


@pytest.mark.parametrize("status", ["pending", "accepted", "rejected"])
def test_receipt_dispositions_do_not_conflate_pending_and_committed(status):
    identity = command("runtime.cancel")["identity"]
    outcome = {"status": status, "binding": {
        "identity": identity, "request_sha256": "a" * 64, "operation_id": "op-1"}}
    if status == "accepted":
        outcome["committed"] = {"kind": "run", "object_id": "run-1", "revision": 1}
    if status == "rejected":
        outcome["reason_code"] = "stale_attempt"
    assert CommandReceipt.model_validate_json(json.dumps({"outcome": outcome}))
    outcome["unverified_success"] = True
    with pytest.raises(ValidationError):
        CommandReceipt.model_validate_json(json.dumps({"outcome": outcome}))
