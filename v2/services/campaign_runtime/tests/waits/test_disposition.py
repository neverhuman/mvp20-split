"""Scientific receipt disposition, timeout clock and graph-state projection."""

from dataclasses import replace
from datetime import timedelta

import pytest
from amphora_campaign_runtime.lifecycle.model import TransitionError
from amphora_campaign_runtime.waits import ReceiptEvidence
from amphora_campaign_runtime.waits.disposition import WaitDisposition
from amphora_contracts_graph_runtime import DomainReceipt


@pytest.mark.parametrize("status,expected,node", [("accepted", "accepted", "succeeded"),
    ("rejected", "blocked", "blocked"), ("abstained", "abstained", "failed")])
def test_receipt_meaning_is_not_command_or_worker_success(wait_env, status, expected, node):
    f = wait_env
    raw = f.evidence.receipt.model_dump(mode="json")
    if status != "accepted":
        raw["outcome"] = {"status": status, "reason_code": "domain_reason"}
    evidence = ReceiptEvidence(DomainReceipt.model_validate(raw))
    disposition = WaitDisposition.received(f.record, evidence)
    assert disposition.status == expected and disposition.node_status == node
    assert (disposition.output is not None) == (status == "accepted")
    closure = disposition.closure(7)
    assert closure.closure_revision == 7 and closure.expectation_sha256 == f.record.sha256
    assert closure.outcome.receipt.model_dump(mode="json") == evidence.receipt.model_dump(mode="json")


def test_timeout_is_explicit_and_cannot_invent_artifact(wait_env):
    f = wait_env
    with pytest.raises(TransitionError, match="wait_timeout_not_due"):
        WaitDisposition.timeout(f.record, f.record.deadline - timedelta(microseconds=1))
    disposition = WaitDisposition.timeout(f.record, f.record.deadline)
    assert disposition.status == f.record.expectation.on_timeout and disposition.output is None
    assert disposition.closure(2).outcome.reason_code == "wait_deadline_expired"


def test_cancel_is_distinct_from_scientific_abstention(wait_env):
    disposition = WaitDisposition(wait_env.record, "cancelled", "campaign_cancelled")
    assert disposition.node_status == "skipped" and disposition.closure(2).outcome.receipt is None


def test_invalid_disposition_cannot_relabel_receipt(wait_env):
    f = wait_env
    with pytest.raises(TransitionError, match="wait_acceptance_evidence_required"):
        WaitDisposition(f.record, "accepted")
    with pytest.raises(TransitionError, match="wait_disposition_mismatch"):
        WaitDisposition(f.record, "abstained", "invented", f.evidence)
    with pytest.raises(TransitionError, match="wait_timeout_reason_required"):
        WaitDisposition(f.record, "blocked", "invented")
    with pytest.raises(TransitionError, match="wait_terminal_reason_required"):
        WaitDisposition(f.record, "unknown", "invented")
    invalid = replace(f.evidence, receipt=f.evidence.receipt.model_copy(update={"purpose": "wrong"}))
    with pytest.raises(TransitionError, match="wait_receipt_purpose_mismatch"):
        WaitDisposition.received(f.record, invalid)
