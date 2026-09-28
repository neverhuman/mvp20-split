import json

import pytest
from amphora_contracts_artifacts import UploadContentReceipt
from jsonschema import Draft202012Validator
from pydantic import ValidationError


def test_provisional_receipt_has_no_usable_artifact_reference():
    raw = {"upload_id": "upload-1", "attempt_id": "attempt-2", "generation": 2}
    receipt = UploadContentReceipt.model_validate_json(json.dumps(raw))
    Draft202012Validator(UploadContentReceipt.model_json_schema()).validate(receipt.model_dump())
    assert receipt.status == "streamed"
    assert "artifact" not in receipt.model_dump()
    for change in [{"generation": 0}, {"status": "finalized"}, {"artifact": {}}]:
        with pytest.raises(ValidationError):
            UploadContentReceipt.model_validate_json(json.dumps({**raw, **change}))
