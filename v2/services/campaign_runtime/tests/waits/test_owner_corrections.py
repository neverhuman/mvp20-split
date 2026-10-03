"""Actual owner receipt wires through pure Runtime pin policy; no live commit claim."""
import json
from pathlib import Path

import pytest
from amphora_campaign_runtime.lifecycle.model import TransitionError
from amphora_campaign_runtime.waits import ReceiptEvidence, WaitRecord
from amphora_campaign_runtime.waits.disposition import WaitDisposition
from amphora_contracts_graph_runtime import DomainReceipt, WaitExpectation


@pytest.mark.parametrize("owner,future_status", [("research","abstained"),("knowledge","blocked")])
def test_actual_correction_keeps_original_pin_usable_and_new_revision_truthful(owner,future_status):
    fixture = json.loads((Path(__file__).parent/"fixtures/owner_corrections.json").read_text(encoding="utf-8"))["owners"][owner]
    root, corrected, notice = [DomainReceipt.model_validate_json(json.dumps(fixture[name])) for name in ("root","corrected","notice")]
    output = root.outcome.output
    expectation = WaitExpectation.model_validate_json(json.dumps({"scope":root.scope.model_dump(mode="json"),
        "run_id":"pre-correction-campaign", "activation_id":"a"*64, "plan_sha256":"b"*64,
        "wait_revision":1,"issuer_id":root.issuer_id,"purpose":root.purpose,"expected_revision":root.revision,
        "subject":root.subject.model_dump(mode="json"),"output_type":{"kind":"artifact",
            "schema_ref":output.artifact.schema_ref.model_dump(mode="json"),"representation":output.representation,"unit":output.unit},
        "deadline_us":9007199254740991,"on_timeout":"abstained"}))
    wait = WaitRecord(expectation)
    original_hash = wait.sha256
    assert WaitDisposition.received(wait,ReceiptEvidence(root)).status == "accepted"
    with pytest.raises(TransitionError,match="wait_receipt_superseded"):
        WaitDisposition.received(wait,ReceiptEvidence(notice))
    with pytest.raises(TransitionError,match="wait_receipt_revision_mismatch"):
        WaitDisposition.received(wait,ReceiptEvidence(corrected))
    assert wait.sha256 == original_hash
    assert WaitDisposition.received(wait,ReceiptEvidence(root)).status == "accepted"
    future = WaitRecord(expectation.model_copy(update={"run_id":"next-campaign","expected_revision":corrected.revision}))
    assert WaitDisposition.received(future,ReceiptEvidence(corrected)).status == future_status
