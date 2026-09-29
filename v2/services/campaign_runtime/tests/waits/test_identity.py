"""Pinned wait scope/type/revision and exact clock identity, without transition claims."""

import copy
import hashlib
import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest
from amphora_campaign_runtime.lifecycle.model import TransitionError
from amphora_campaign_runtime.waits import ReceiptEvidence, WaitAddress, WaitRecord, WaitRetentionIntent
from amphora_campaign_runtime.waits.model import microseconds
from amphora_contracts_campaigns import parse_executable_campaign
from amphora_contracts_core import ArtifactRef
from amphora_contracts_graph_runtime import DomainReceipt, WaitExpectation
from export_schemas import ROOT
from pydantic import ValidationError


def fixture():
    raw = json.loads((ROOT / "contracts/fixtures/v3/await_cases.json").read_bytes())[0]["payload"]
    definition = parse_executable_campaign(json.dumps(raw))
    subject = ArtifactRef.model_validate_json(json.dumps({"artifact_id": "subject", "scope": raw["scope"],
        "schema_ref": raw["body"]["inputs"][0]["value_type"]["schema_ref"], "sha256": "a" * 64,
        "media_type": "application/json", "size_bytes": 2}))
    address = WaitAddress(definition.scope, "run-1", "b" * 64, "c" * 64)
    node = definition.body.nodes[0]
    now = datetime(2026, 9, 28, 20, 0, 0, 123456, tzinfo=UTC)
    record = WaitRecord.pin(address, node, subject, opened_at=now, run_deadline=now + timedelta(seconds=120))
    output = {**subject.model_dump(mode="json"), "artifact_id": "output",
              "schema_ref": node.output.value_type.schema_ref.model_dump(mode="json")}
    receipt = {"issuer_id": node.issuer_id, "receipt_id": "evidence-1", "scope": raw["scope"], "purpose": node.purpose,
               "revision": node.expected_revision, "subject": subject.model_dump(mode="json"),
               "outcome": {"status": "accepted", "output": {"kind": "artifact", "artifact": output,
                   "representation": node.output.value_type.representation, "unit": node.output.value_type.unit}}}
    return record, receipt, (address, node, subject, now)


def evidence(raw):
    return ReceiptEvidence(DomainReceipt.model_validate_json(json.dumps(raw)))


def test_wait_pin_deadline_hash_and_revalidation():
    record, raw, (_, _, _, now) = fixture()
    assert record.deadline == now + timedelta(seconds=60)
    assert microseconds(record.deadline) == 1790625660123456
    document = {"profile": "amphora-wait-expectation-v1", "expectation": record.expectation.model_dump(mode="json")}
    assert record.sha256 == hashlib.sha256(json.dumps(document, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    record.validate_receipt(evidence(raw))
    assert WaitRecord(WaitExpectation.model_validate_json(record.expectation.model_dump_json())) == record
    encoded = {"profile": "amphora-domain-receipt-v1", "receipt": evidence(raw).receipt.model_dump(mode="json")}
    assert evidence(raw).sha256 == hashlib.sha256(json.dumps(encoded, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def test_run_deadline_caps_wait_and_naive_or_expired_clock_is_rejected():
    _, _, (address, node, subject, now) = fixture()
    value = WaitRecord.pin(address, node, subject, opened_at=now, run_deadline=now + timedelta(seconds=1))
    assert value.deadline == now + timedelta(seconds=1)
    with pytest.raises(TransitionError, match="wait_run_expired"):
        WaitRecord.pin(address, node, subject, opened_at=now, run_deadline=now)
    with pytest.raises(TransitionError, match="wait_naive_deadline"):
        microseconds(now.replace(tzinfo=None))


@pytest.mark.parametrize("field,value,reason", [("issuer_id", "other", "issuer"), ("purpose", "other", "purpose"),
                                              ("revision", "revision-2", "revision"), ("revision", "revision-0", "revision")])
def test_foreign_receipt_binding_rejected(field, value, reason):
    record, raw, _ = fixture()
    raw[field] = value
    with pytest.raises(TransitionError, match="wait_receipt_" + reason + "_mismatch"):
        record.validate_receipt(evidence(raw))


def test_same_scope_wrong_subject_and_superseded_receipt_cannot_satisfy_wait():
    record, raw, _ = fixture()
    raw["subject"]["artifact_id"] = "another-candidate"
    with pytest.raises(TransitionError, match="wait_receipt_subject_mismatch"):
        record.validate_receipt(evidence(raw))
    raw = fixture()[1]
    raw["outcome"] = {"status": "superseded", "replacement_revision": "revision-2", "reason_code": "corrected"}
    with pytest.raises(TransitionError, match="wait_receipt_superseded"):
        record.validate_receipt(evidence(raw))


@pytest.mark.parametrize("field,value", [("representation", "other"), ("unit", "g/mol"),
                                       ("media_type", "application/octet-stream"), ("schema", "d" * 64)])
def test_accepted_output_must_match_exact_declared_type(field, value):
    record, raw, _ = fixture()
    output = raw["outcome"]["output"]
    if field == "schema":
        output["artifact"]["schema_ref"]["sha256"] = value
    elif field == "media_type":
        output["artifact"][field] = value
    else:
        output[field] = value
    with pytest.raises(TransitionError, match="wait_output_type_mismatch"):
        record.validate_receipt(evidence(raw))


@pytest.mark.parametrize("status", ["rejected", "abstained"])
def test_nonaccepted_scientific_outcomes_are_preserved_without_fabricated_output(status):
    record, raw, _ = fixture()
    raw["outcome"] = {"status": status, "reason_code": "unavailable"}
    record.validate_receipt(evidence(raw))
    assert evidence(raw).receipt.outcome.status == status


def test_foreign_scope_is_rejected_even_if_model_was_constructed_without_validation():
    record, raw, _ = fixture()
    raw["subject"]["scope"] = {"tenant_id": "foreign", "project_id": "foreign"}
    with pytest.raises(TransitionError, match="wait_foreign_subject"):
        evidence(raw)
    raw = fixture()[1]
    raw["outcome"]["output"]["artifact"]["scope"] = {"tenant_id": "foreign", "project_id": "foreign"}
    with pytest.raises(TransitionError, match="wait_foreign_output"):
        evidence(raw)
    with pytest.raises(ValidationError):
        WaitRecord(record.expectation.model_copy(update={"wait_revision": True}))
    raw = copy.deepcopy(record.expectation.model_dump(mode="json"))
    raw["subject"]["scope"] = {"tenant_id": "foreign", "project_id": "foreign"}
    with pytest.raises(TransitionError, match="wait_foreign_subject"):
        replace(record, expectation=WaitExpectation.model_validate_json(json.dumps(raw)))


def test_nonaccepted_receipt_cannot_prepare_artifact_retention():
    record, raw, _ = fixture()
    raw["outcome"] = {"status": "abstained", "reason_code": "no_evidence"}
    with pytest.raises(TransitionError, match="wait_retention_output_required"):
        WaitRetentionIntent(record, evidence(raw), "operation-1", "runtime-owner")
