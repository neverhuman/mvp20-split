import copy
import json
from pathlib import Path

import pytest
from amphora_contracts_artifacts import ReservationReceipt, parse_command
from amphora_contracts_commands import CommandEncodingError
from jsonschema import Draft202012Validator
from pydantic import ValidationError

CASES = json.loads((Path(__file__).parent / "fixtures/commands.json").read_text())
RESERVE = next(c["command"] for c in CASES if c["family"] == "artifacts.reserve")


@pytest.mark.parametrize("status,proof", [
    ("reserved", None),
    ("confirmed", {"status": "committed", "runtime_receipt_id": "receipt-1"}),
    ("released", {"status": "aborted", "runtime_receipt_id": "receipt-2", "reason_code": "cancelled"}),
])
def test_receipt_proof_shape(status, proof):
    outcome = {"status": status, "binding": {"reservation_id": "reserve-1", **RESERVE["payload"]}}
    if proof is not None:
        outcome["proof"] = proof
    record = {"schema_version": "1", "outcome": outcome}
    schema = ReservationReceipt.model_json_schema()
    Draft202012Validator(schema).validate(record)
    assert ReservationReceipt.model_validate_json(json.dumps(record))
    outcome["expires_at"] = "2026-01-01T00:00:00Z"
    assert list(Draft202012Validator(schema).iter_errors(record))
    with pytest.raises(ValidationError):
        ReservationReceipt.model_validate_json(json.dumps(record))


def test_released_requires_aborted_proof_and_scope_mismatch_rejects():
    record = {"schema_version": "1", "outcome": {
        "status": "released", "binding": {"reservation_id": "reserve-1", **RESERVE["payload"]},
        "proof": {"status": "committed", "runtime_receipt_id": "receipt-1"}}}
    with pytest.raises(ValidationError):
        ReservationReceipt.model_validate_json(json.dumps(record))
    wrong_scope = copy.deepcopy(RESERVE)
    wrong_scope["payload"]["artifact"]["scope"]["project_id"] = "other"
    with pytest.raises(CommandEncodingError, match="scope_mismatch"):
        parse_command("artifacts.reserve", json.dumps(wrong_scope))
