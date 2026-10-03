"""Correction DTO schemas retain ordinary DomainReceipt boundaries."""
import json
from pathlib import Path

import pytest
from amphora_contracts_graph_runtime import ReceiptCorrection, ReceiptCorrectionView
from jsonschema import Draft202012Validator
from pydantic import ValidationError

EXAMPLES = Path(__file__).parents[1] / "examples"


@pytest.mark.parametrize("name", ["receipt-correction-root", "receipt-correction-successor"])
def test_examples_roundtrip_and_match_both_schema_directions(name):
    body = (EXAMPLES / (name + ".json")).read_text(encoding="utf-8")
    record = ReceiptCorrection.model_validate_json(body)
    for mode in ("validation", "serialization"):
        Draft202012Validator(ReceiptCorrection.model_json_schema(mode=mode)).validate(json.loads(body))
    assert ReceiptCorrection.model_validate_json(record.model_dump_json()) == record


@pytest.mark.parametrize("change", [{"ordinal":0}, {"ordinal":True}, {"ordinal":9007199254740992},
    {"schema_version":"2"}, {"unexpected":True}])
def test_invalid_wire_identity_is_rejected(change):
    body = json.loads((EXAMPLES / "receipt-correction-root.json").read_text(encoding="utf-8"))
    body.update(change)
    with pytest.raises(ValidationError):
        ReceiptCorrection.model_validate_json(json.dumps(body))
    assert list(Draft202012Validator(ReceiptCorrection.model_json_schema()).iter_errors(body))


def test_selection_view_exposes_a_reusable_public_revision_reference():
    body = (EXAMPLES / "receipt-correction-view.json").read_text(encoding="utf-8")
    view = ReceiptCorrectionView.model_validate_json(body)
    assert view.reference.chain == view.record.chain
    assert view.reference.ordinal == view.record.ordinal
    for mode in ("validation", "serialization"):
        Draft202012Validator(ReceiptCorrectionView.model_json_schema(mode=mode)).validate(json.loads(body))
