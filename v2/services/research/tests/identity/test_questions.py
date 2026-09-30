import json

import pytest
from amphora_contracts_research import EvidenceNeed, ResearchQuestion
from amphora_research.identity.questions import QuestionDefinition, ResearchIdentityError


def records():
    scope = {"tenant_id": "test", "project_id": "research"}
    schema = {"schema_id": "fixture", "version": "1", "sha256": "a" * 64}
    artifact = {"artifact_id": "context", "scope": scope, "sha256": "b" * 64,
                "media_type": "application/json", "schema_ref": schema, "size_bytes": 2}
    qref = {"scope": scope, "question_id": "q", "revision": 1}
    question = {"wire_version": "1", "reference": qref, "objective": "Synthetic comparison",
                "applicability": artifact, "criteria": [{"criterion_id": "c", "description": "Method context"}],
                "supersedes": None}
    need = {"wire_version": "1", "reference": {"scope": scope, "need_id": "n", "revision": 1},
            "question": qref, "criterion_ids": ["c"], "method": schema,
            "required_context": artifact, "supersedes": None}
    return json.loads(json.dumps([question, need]))


def question(value):
    return QuestionDefinition(ResearchQuestion.model_validate_json(json.dumps(value)))


def need(value):
    return EvidenceNeed.model_validate_json(json.dumps(value))


def test_exact_question_need_binding_is_only_a_declaration():
    q, n = records()
    bound = question(q).bind_need(need(n))
    assert bound.record.question.question_id == "q"
    assert not hasattr(bound, "accepted")


@pytest.mark.parametrize(("mutation", "code"), [
    (lambda x: x["applicability"]["scope"].update(project_id="other"), "applicability_scope_mismatch"),
    (lambda x: x["criteria"].append(x["criteria"][0]), "duplicate_criterion"),
    (lambda x: x["reference"].update(revision=2), "missing_predecessor"),
    (lambda x: x.update(supersedes=x["reference"]), "invalid_predecessor"),
])
def test_invalid_question_rejected(mutation, code):
    q, _ = records()
    mutation(q)
    with pytest.raises(ResearchIdentityError, match=code):
        question(q)


@pytest.mark.parametrize(("mutation", "code"), [
    (lambda x: x["question"].update(revision=2), "question_revision_mismatch"),
    (lambda x: x["reference"]["scope"].update(project_id="other"), "need_scope_mismatch"),
    (lambda x: x["required_context"]["scope"].update(project_id="other"), "need_scope_mismatch"),
    (lambda x: x.update(criterion_ids=["c", "c"]), "duplicate_criterion"),
    (lambda x: x.update(criterion_ids=["unknown"]), "unknown_criterion"),
    (lambda x: x["reference"].update(revision=2), "missing_predecessor"),
    (lambda x: x.update(supersedes=x["reference"]), "invalid_predecessor"),
])
def test_invalid_need_cannot_bind(mutation, code):
    q, n = records()
    mutation(n)
    with pytest.raises(ResearchIdentityError, match=code):
        question(q).bind_need(need(n))


def test_question_and_need_corrections_pin_new_revisions():
    q, n = records()
    q["supersedes"] = dict(q["reference"])
    q["reference"]["revision"] = 2
    n["question"] = q["reference"]
    n["supersedes"] = dict(n["reference"])
    n["reference"]["revision"] = 2
    bound = question(q).bind_need(need(n))
    assert bound.record.question.revision == 2
    assert bound.record.supersedes.revision == 1
