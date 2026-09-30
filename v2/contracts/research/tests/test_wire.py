import json

import pytest
from amphora_contracts_research import CandidateRevisionRef, EvidenceNeed, ResearchQuestion, SampleIdentity
from jsonschema import Draft202012Validator
from pydantic import ValidationError

SCOPE = {"tenant_id": "test", "project_id": "research"}
SCHEMA = {"schema_id": "fixture", "version": "1", "sha256": "a" * 64}
ARTIFACT = {"artifact_id": "context", "scope": SCOPE, "sha256": "b" * 64,
            "media_type": "application/json", "schema_ref": SCHEMA, "size_bytes": 2}
QUESTION = {"scope": SCOPE, "question_id": "q1", "revision": 1}


def question():
    return {"wire_version": "1", "reference": QUESTION, "objective": "Compare synthetic observations",
            "applicability": ARTIFACT, "criteria": [{"criterion_id": "c1", "description": "Required context"}],
            "supersedes": None}


def need():
    return {"wire_version": "1", "reference": {"scope": SCOPE, "need_id": "n1", "revision": 1},
            "question": QUESTION, "criterion_ids": ["c1"], "method": SCHEMA,
            "required_context": ARTIFACT, "supersedes": None}


@pytest.mark.parametrize(("model", "value"), [(ResearchQuestion, question()), (EvidenceNeed, need())])
def test_question_and_need_schema_roundtrip(model, value):
    parsed = model.model_validate_json(json.dumps(value))
    assert json.loads(parsed.model_dump_json()) == value
    for mode in ("validation", "serialization"):
        schema = model.model_json_schema(mode=mode)
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(value)


@pytest.mark.parametrize("mutation", [
    lambda x: x.update(criteria=[]),
    lambda x: x.update(objective=""),
    lambda x: x.update(objective="x" * 2049),
    lambda x: x.update(scientifically_answered=True),
    lambda x: x["reference"].update(revision=True),
    lambda x: x["reference"].update(revision="1"),
])
def test_strict_question_shape_has_no_acceptance_flag(mutation):
    value = json.loads(json.dumps(question()))
    mutation(value)
    with pytest.raises(ValidationError):
        ResearchQuestion.model_validate_json(json.dumps(value))
    assert list(Draft202012Validator(ResearchQuestion.model_json_schema()).iter_errors(value))


def test_candidate_identity_does_not_substitute_for_sample_identity():
    candidate = {"scope": SCOPE, "candidate_id": "c1", "revision": 1}
    with pytest.raises(ValidationError):
        SampleIdentity.model_validate_json(json.dumps(candidate))
    sample = {"wire_version": "1", "reference": {"scope": SCOPE, "sample_id": "s1", "revision": 1},
              "candidate": candidate, "material_state": None, "identity_evidence": ARTIFACT, "supersedes": None}
    parsed = SampleIdentity.model_validate_json(json.dumps(sample))
    Draft202012Validator(SampleIdentity.model_json_schema()).validate(sample)
    assert parsed.material_state is None
    assert parsed.candidate == CandidateRevisionRef.model_validate_json(json.dumps(candidate))
