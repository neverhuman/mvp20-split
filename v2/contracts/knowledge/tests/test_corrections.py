import json
from pathlib import Path

import pytest
from amphora_contracts_knowledge import CorrectReasoningReceipt, SelectReasoningReceipt
from jsonschema import Draft202012Validator
from pydantic import ValidationError


@pytest.mark.parametrize("model,name", [(CorrectReasoningReceipt,"correct-reasoning-receipt"),
                                        (SelectReasoningReceipt,"select-reasoning-receipt")])
def test_correction_requests_are_reference_only_and_match_schema(model,name):
    raw = (Path(__file__).parents[1]/"examples"/(name+".json")).read_text(encoding="utf-8")
    record = model.model_validate_json(raw)
    for mode in ("validation", "serialization"):
        Draft202012Validator(model.model_json_schema(mode=mode)).validate(json.loads(raw))
    assert model.model_validate_json(record.model_dump_json()) == record
    with pytest.raises(ValidationError):
        model.model_validate_json(json.dumps(json.loads(raw) | {"source_receipt":{}}))
