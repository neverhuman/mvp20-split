import json
from pathlib import Path

import pytest
from amphora_contracts_research import (
    EvidenceAssessment,
    EvidenceAssessmentProfile,
    EvidenceAssessmentRequest,
    EvidenceAssessmentStatus,
)
from jsonschema import Draft202012Validator
from pydantic import ValidationError

EXAMPLES = Path(__file__).absolute().parents[1] / "examples"
MODELS = {"assessment-profile": EvidenceAssessmentProfile, "assessment-request": EvidenceAssessmentRequest,
          "assessment": EvidenceAssessment, "assessment-status": EvidenceAssessmentStatus}


@pytest.mark.parametrize("name", MODELS)
def test_published_examples_round_trip_in_both_schema_modes(name):
    value = json.loads((EXAMPLES / (name + ".json")).read_text())
    model = MODELS[name]
    record = model.model_validate_json(json.dumps(value))
    assert json.loads(record.model_dump_json()) == value
    for mode in ("validation", "serialization"):
        schema = model.model_json_schema(mode=mode)
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(value)


@pytest.mark.parametrize(("name", "mutation"), [
    ("assessment-profile", lambda x: x.update(authority="scientific")),
    ("assessment-profile", lambda x: x.update(targets=[])),
    ("assessment-profile", lambda x: x.update(answer_publishers=[])),
    ("assessment-profile", lambda x: x.update(requirements=[])),
    ("assessment-profile", lambda x: x["requirements"][0].update(categories=["best"])),
    ("assessment-profile", lambda x: x["targets"][0].update(target_sha256="wrong")),
    ("assessment-request", lambda x: x.update(authority="synthetic")),
    ("assessment-request", lambda x: x.update(accepted=True)),
    ("assessment-request", lambda x: x.update(issuer="trusted")),
    ("assessment-request", lambda x: x.update(disposition="supported")),
    ("assessment-request", lambda x: x.update(answers=[{"criterion_id": "c", "artifact": {},
                                                     "disposition": "supported"}])),
    ("assessment-request", lambda x: x["question"].update(revision=True)),
    ("assessment-request", lambda x: x.update(assessment_id="")),
    ("assessment", lambda x: x.update(scientifically_established=True)),
    ("assessment", lambda x: x.update(scientifically_established=0)),
    ("assessment", lambda x: x.update(sufficient="true")),
    ("assessment", lambda x: x.update(disposition="certain")),
    ("assessment", lambda x: x["needs"][0]["gap"].update(reason="none")),
    ("assessment-status", lambda x: x.update(outcome={"status": "accepted"})),
])
def test_untrusted_claims_and_invalid_shapes_rejected_by_python_and_schema(name, mutation):
    value = json.loads((EXAMPLES / (name + ".json")).read_text())
    mutation(value)
    with pytest.raises(ValidationError):
        MODELS[name].model_validate_json(json.dumps(value))
    assert list(Draft202012Validator(MODELS[name].model_json_schema()).iter_errors(value))


@pytest.mark.parametrize("status", ["pending", "failed"])
def test_pending_or_failed_status_cannot_include_a_result(status):
    value = json.loads((EXAMPLES / "assessment-status.json").read_text())
    assessment = value["outcome"]["assessment"]
    value["outcome"] = {"status": status} if status == "pending" else {"status": status, "code": "denied"}
    EvidenceAssessmentStatus.model_validate_json(json.dumps(value))
    value["outcome"]["assessment"] = assessment
    with pytest.raises(ValidationError):
        EvidenceAssessmentStatus.model_validate_json(json.dumps(value))


@pytest.mark.parametrize(("name", "field", "count"), [
    ("assessment-profile", "targets", 33),
    ("assessment-profile", "requirements", 129),
    ("assessment-profile", "answer_publishers", 33),
    ("assessment", "needs", 4097),
])
def test_bounded_collections_have_matching_schema_limits(name, field, count):
    value = json.loads((EXAMPLES / (name + ".json")).read_text())
    value[field] = [value[field][0]] * count
    with pytest.raises(ValidationError):
        MODELS[name].model_validate_json(json.dumps(value))
    assert list(Draft202012Validator(MODELS[name].model_json_schema()).iter_errors(value))
