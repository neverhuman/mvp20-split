"""Synthetic producer records and return coverage cannot claim scientific or Runtime acceptance."""
import hashlib
import json
from pathlib import Path

import pytest
from amphora_contracts_research import (
    LabReportResolution,
    LabReturnProfile,
    SyntheticLabReport,
    synthetic_lab_report_schema,
    synthetic_lab_report_schema_document,
)
from jsonschema import Draft202012Validator
from pydantic import ValidationError

EXAMPLES = Path(__file__).absolute().parents[1] / "examples"
CASES = (("synthetic-lab-report",SyntheticLabReport),("lab-return-profile",LabReturnProfile),("lab-report-resolution",LabReportResolution))


@pytest.mark.parametrize("name,model",CASES)
def test_report_examples_keep_exact_json_and_schema_parity(name,model):
    payload = json.loads((EXAMPLES / (name+".json")).read_text(encoding="utf-8"))
    parsed = model.model_validate_json(json.dumps(payload))
    assert json.loads(parsed.model_dump_json()) == payload
    for mode in ("validation","serialization"):
        schema = model.model_json_schema(mode=mode)
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(payload)


@pytest.mark.parametrize("name,model",CASES)
@pytest.mark.parametrize("mutation",[lambda p:p.update(authority="scientific"),lambda p:p.update(runtime_accepted=True)])
def test_report_documents_cannot_promote_themselves(name,model,mutation):
    payload = json.loads((EXAMPLES / (name+".json")).read_text(encoding="utf-8"))
    mutation(payload)
    with pytest.raises(ValidationError):
        model.model_validate_json(json.dumps(payload))
    assert list(Draft202012Validator(model.model_json_schema()).iter_errors(payload))


def test_payload_schema_digest_is_self_contained_and_repeatable():
    body = synthetic_lab_report_schema_document()
    assert body == synthetic_lab_report_schema_document()
    assert hashlib.sha256(body).hexdigest() == synthetic_lab_report_schema().sha256
    schema = json.loads(body)
    assert "$id" not in schema
    Draft202012Validator(schema).validate(json.loads((EXAMPLES / "synthetic-lab-report.json").read_text(encoding="utf-8")))


def test_producer_payload_cannot_supply_its_own_hash_reference_or_verdict():
    payload = json.loads((EXAMPLES / "synthetic-lab-report.json").read_text(encoding="utf-8"))
    for key in ("source","accepted"):
        row = dict(payload["observations"][0])
        row[key] = payload["raw_report"] if key == "source" else True
        invalid = payload|{"observations":[row]}
        with pytest.raises(ValidationError):
            SyntheticLabReport.model_validate_json(json.dumps(invalid))
        assert list(Draft202012Validator(SyntheticLabReport.model_json_schema()).iter_errors(invalid))


def test_empty_return_is_explicit_and_report_resource_bound_is_strict():
    payload = json.loads((EXAMPLES / "synthetic-lab-report.json").read_text(encoding="utf-8"))
    assert SyntheticLabReport.model_validate_json(json.dumps(payload|{"observations":[]})).observations == ()
    invalid = payload|{"observations":payload["observations"]*65}
    with pytest.raises(ValidationError):
        SyntheticLabReport.model_validate_json(json.dumps(invalid))
    assert list(Draft202012Validator(SyntheticLabReport.model_json_schema()).iter_errors(invalid))
