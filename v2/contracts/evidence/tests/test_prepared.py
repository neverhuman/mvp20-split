import json

import pytest
from amphora_contracts_evidence import PreparedDocument, PreparedLabRecord, prepared_schema
from jsonschema import Draft202012Validator
from pydantic import ValidationError


def test_document_and_lab_outputs_preserve_data_not_acceptance():
    document = PreparedDocument(wire_version="1", text="Raw instructions are data")
    Draft202012Validator(PreparedDocument.model_json_schema()).validate(json.loads(document.model_dump_json()))
    fields = {key: None for key in PreparedLabRecord.model_fields if key != "wire_version"}
    fields.update(wire_version="1", value="<0.1")
    record = PreparedLabRecord.model_validate_json(json.dumps(fields))
    Draft202012Validator(PreparedLabRecord.model_json_schema()).validate(fields)
    assert record.unit is None and record.value == "<0.1"
    fields["accepted"] = True
    with pytest.raises(ValidationError):
        PreparedLabRecord.model_validate_json(json.dumps(fields))


def test_preparation_schema_profiles_are_distinct_and_stable():
    assert prepared_schema("document") == prepared_schema("document")
    assert prepared_schema("document") != prepared_schema("lab")
