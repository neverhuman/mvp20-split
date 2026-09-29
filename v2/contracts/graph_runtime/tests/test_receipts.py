"""External evidence has a distinct issuer/scope/command boundary from worker reports."""

import copy
import json

import pytest
from amphora_contracts_commands import CommandEncodingError
from amphora_contracts_graph_runtime import (
    DomainReceipt,
    SubmitDomainReceipt,
    WaitClosure,
    WaitObservation,
    parse_graph_command,
)
from amphora_contracts_runtime import parse_command
from jsonschema import Draft202012Validator
from pydantic import ValidationError


def receipt_command(status="accepted"):
    scope = {"tenant_id": "test", "project_id": "wait"}
    artifact = {"artifact_id": "subject", "scope": scope, "sha256": "a" * 64,
                "media_type": "application/json", "size_bytes": 2,
                "schema_ref": {"schema_id": "synthetic", "version": "1", "sha256": "b" * 64}}
    outcome = {"status": status, "reason_code": "fixture_disposition"}
    if status == "accepted":
        outcome = {"status": status, "output": {"kind": "artifact", "artifact": dict(artifact, artifact_id="output"),
                                               "representation": "synthetic", "unit": "1"}}
    elif status == "superseded":
        outcome["replacement_revision"] = "revision-2"
    return {"identity": {"scope": scope, "actor_id": "issuer", "command_family": "graph.submit_receipt", "command_id": "delivery-1"},
            "payload": {"run_id": "run-1", "activation_id": "c" * 64, "wait_revision": 1,
                        "expectation_sha256": "d" * 64, "receipt": {"issuer_id": "issuer", "receipt_id": "receipt-1",
                            "scope": scope, "purpose": "fixture-evaluation", "revision": "revision-1",
                            "subject": artifact, "outcome": outcome}}}


@pytest.mark.parametrize("status", ["accepted", "rejected", "abstained", "superseded"])
def test_distinct_receipt_outcomes_roundtrip_with_exact_command_identity(status):
    raw = receipt_command(status)
    payload = SubmitDomainReceipt.model_validate_json(json.dumps(raw["payload"]))
    Draft202012Validator(SubmitDomainReceipt.model_json_schema()).validate(raw["payload"])
    Draft202012Validator(DomainReceipt.model_json_schema(mode="serialization")).validate(
        json.loads(payload.receipt.model_dump_json()))
    parsed = parse_graph_command("graph.submit_receipt", json.dumps(raw))
    assert parse_graph_command("graph.submit_receipt", parsed.canonical_bytes).canonical_bytes == parsed.canonical_bytes
    with pytest.raises(CommandEncodingError, match="unknown_family"):
        parse_command("graph.submit_receipt", json.dumps(raw))


@pytest.mark.parametrize("location", ["receipt", "subject", "output"])
def test_foreign_scope_rejected_before_command_registration(location):
    raw = copy.deepcopy(receipt_command())
    receipt = raw["payload"]["receipt"]
    scope = {"tenant_id": "foreign", "project_id": "wait"}
    if location == "receipt":
        receipt["scope"] = scope
    elif location == "subject":
        receipt["subject"]["scope"] = scope
    else:
        receipt["outcome"]["output"]["artifact"]["scope"] = scope
    with pytest.raises(CommandEncodingError, match="scope_mismatch"):
        parse_graph_command("graph.submit_receipt", json.dumps(raw))


def test_identity_actor_must_be_the_declared_issuer():
    raw = receipt_command()
    raw["identity"]["actor_id"] = "worker"
    with pytest.raises(CommandEncodingError, match="issuer_mismatch"):
        parse_graph_command("graph.submit_receipt", json.dumps(raw))


@pytest.mark.parametrize("outcome", [{"status": "accepted"}, {"status": "succeeded", "outputs": []},
    {"status": "rejected", "reason_code": "failed", "output": {}},
    {"status": "superseded", "reason_code": "outdated"},
    {"status": "accepted", "output": {"kind": "number", "value": "1", "unit": "1"}}])
def test_receipts_cannot_erase_missingness_or_smuggle_worker_reports(outcome):
    raw = receipt_command()["payload"]["receipt"]
    raw["outcome"] = outcome
    with pytest.raises(ValidationError):
        DomainReceipt.model_validate_json(json.dumps(raw))


@pytest.mark.parametrize("status", ["accepted", "blocked", "abstained", "cancelled"])
def test_versioned_wait_observation_and_closure_examples(status):
    request = receipt_command()["payload"]
    receipt = request["receipt"]
    expectation = {"scope": receipt["scope"], "run_id": request["run_id"], "activation_id": request["activation_id"],
        "plan_sha256": "e" * 64, "wait_revision": 1, "issuer_id": receipt["issuer_id"], "purpose": receipt["purpose"],
        "expected_revision": receipt["revision"], "subject": receipt["subject"], "deadline_us": 1790625660123456,
        "on_timeout": "blocked", "output_type": {"kind": "artifact", "schema_ref": receipt["subject"]["schema_ref"],
            "representation": "synthetic", "unit": "1", "media_type": "application/json"}}
    closure = {"scope": receipt["scope"], "run_id": request["run_id"], "activation_id": request["activation_id"],
        "wait_revision": 1, "expectation_sha256": request["expectation_sha256"], "closure_revision": 2,
        "outcome": {"status": status, "receipt": receipt} if status == "accepted" else
                   {"status": status, "reason_code": "fixture_terminal"}}
    for closed in (None, closure):
        raw = {"expectation": expectation, "expectation_sha256": request["expectation_sha256"], "closure": closed}
        parsed = WaitObservation.model_validate_json(json.dumps(raw))
        Draft202012Validator(WaitObservation.model_json_schema()).validate(raw)
        assert WaitObservation.model_validate_json(parsed.model_dump_json()) == parsed
    if status == "accepted":
        closure["outcome"]["receipt"]["outcome"] = {"status": "rejected", "reason_code": "unavailable"}
        with pytest.raises(ValidationError):
            WaitClosure.model_validate_json(json.dumps(closure))
