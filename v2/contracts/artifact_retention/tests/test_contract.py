import json
from pathlib import Path

import pytest
from pydantic import ValidationError
from amphora_contracts_artifacts import parse_command
from amphora_contracts_artifact_retention import DerivedClosureReservationReceipt, parse_derived_closure_command
from amphora_contracts_commands import CommandEncodingError


def document():
    scope = {"tenant_id": "tenant", "project_id": "project"}
    return {"identity": {"scope": scope, "actor_id": "runtime", "command_id": "reserve-closure",
                         "command_family": "artifacts.reserve_derived_closure"},
        "payload": {"profile": "derived-closure-retention-v1", "artifact": {
            "artifact_id": "root", "scope": scope, "sha256": "a" * 64, "size_bytes": 20,
            "media_type": "application/json", "schema_ref": {"schema_id": "test", "version": "1", "sha256": "b" * 64}},
            "intent": {"runtime_owner": "runtime", "intent_id": "intent",
                       "semantic_completion_sha256": "c" * 64, "output_binding": "output"}}}


def test_new_command_roundtrip_and_legacy_separation():
    raw = document()
    command = parse_derived_closure_command(json.dumps(raw))
    assert parse_derived_closure_command(command.canonical_bytes).canonical_bytes == command.canonical_bytes
    with pytest.raises(CommandEncodingError):
        parse_command("artifacts.reserve", command.canonical_bytes)
    raw["identity"]["command_family"] = "artifacts.reserve"
    del raw["payload"]["profile"]
    legacy = parse_command("artifacts.reserve", json.dumps(raw))
    with pytest.raises(CommandEncodingError):
        parse_derived_closure_command(legacy.canonical_bytes)


@pytest.mark.parametrize("mutation", ["missing_profile", "unknown_profile", "extra", "foreign_scope", "fractional_size"])
def test_invalid_reservation_rejects(mutation):
    raw = document()
    if mutation == "missing_profile":
        del raw["payload"]["profile"]
    elif mutation == "unknown_profile":
        raw["payload"]["profile"] = "future"
    elif mutation == "extra":
        raw["payload"]["members"] = []
    elif mutation == "foreign_scope":
        raw["payload"]["artifact"]["scope"] = {"tenant_id": "foreign", "project_id": "project"}
    else:
        raw["payload"]["artifact"]["size_bytes"] = .5
    with pytest.raises(CommandEncodingError):
        parse_derived_closure_command(json.dumps(raw))


def receipt(count=1, status="reserved"):
    raw = document()["payload"]
    outcome = {"status": status, "binding": {"reservation_id": "reservation", "artifact": raw["artifact"], "intent": raw["intent"]}}
    if status == "confirmed":
        outcome["proof"] = {"status": "committed", "runtime_receipt_id": "receipt"}
    if status == "released":
        outcome["proof"] = {"status": "aborted", "runtime_receipt_id": "receipt", "reason_code": "cancelled"}
    return {"profile": raw["profile"], "reservation": {"outcome": outcome}, "artifact_count": count, "members_sha256": "d" * 64}


@pytest.mark.parametrize("count", [0, 4097, -1, True, 1.0, "1"])
def test_receipt_count_is_strict_and_bounded(count):
    with pytest.raises(ValidationError):
        DerivedClosureReservationReceipt.model_validate(receipt(count))


@pytest.mark.parametrize("count,status", [(1, "reserved"), (4096, "confirmed"), (32, "released")])
def test_current_status_wraps_unchanged_root_proof(count, status):
    result = DerivedClosureReservationReceipt.model_validate(receipt(count, status))
    assert DerivedClosureReservationReceipt.model_validate_json(result.model_dump_json()) == result
    assert result.reservation.outcome.status == status


def test_command_goldens_pin_additive_and_legacy_bytes():
    fixtures = Path(__file__).parent / "fixtures"
    raw = document()
    assert parse_derived_closure_command(json.dumps(raw)).canonical_bytes == (fixtures / "closure.json").read_bytes()
    raw["identity"]["command_family"] = "artifacts.reserve"
    del raw["payload"]["profile"]
    assert parse_command("artifacts.reserve", json.dumps(raw)).canonical_bytes == (fixtures / "legacy.json").read_bytes()
