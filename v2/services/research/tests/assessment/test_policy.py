from dataclasses import FrozenInstanceError, replace

import pytest
from amphora_contracts_core import ArtifactRef, SchemaRef, Scope
from amphora_contracts_research import (
    AnswerCriterion,
    EvidenceNeed,
    EvidenceNeedRef,
    ResearchQuestion,
    ResearchQuestionRef,
)
from amphora_research.assessment.policy import (
    AssessmentError,
    AssessmentPolicy,
    CandidateAnswer,
    EvidenceObservation,
    NeedRequirement,
)
from amphora_research.identity.questions import QuestionDefinition, ResearchIdentityError

SCOPE = Scope(tenant_id="fixture", project_id="assessment")
OTHER = Scope(tenant_id="fixture", project_id="other")
METHOD = SchemaRef(schema_id="measurement", version="1", sha256="a" * 64)


def artifact(name, **changes):
    return ArtifactRef(artifact_id=name, scope=SCOPE, sha256="b" * 64, media_type="application/json",
                       schema_ref=METHOD, size_bytes=2).model_copy(update=changes)


def fixture():
    question = QuestionDefinition(ResearchQuestion(
        wire_version="1", reference=ResearchQuestionRef(scope=SCOPE, question_id="q", revision=1),
        objective="Synthetic measurement criterion", applicability=artifact("context"),
        criteria=(AnswerCriterion(criterion_id="c", description="Configured criterion"),), supersedes=None))
    need = EvidenceNeed(wire_version="1", reference=EvidenceNeedRef(scope=SCOPE, need_id="n", revision=1),
                        question=question.record.reference, criterion_ids=("c",), method=METHOD,
                        required_context=artifact("context"), supersedes=None)
    requirement = NeedRequirement(need, frozenset({"observation"}), frozenset({"fixture-observer"}))
    policy = AssessmentPolicy(question, "fixture-policy", "1", "fixture.measurement", (requirement,))
    answer = CandidateAnswer("c", artifact("answer"), "supported")
    evidence = EvidenceObservation(artifact("receipt"), need.reference, "c", answer.artifact, METHOD,
                                   artifact("context"), "observation", "fixture-observer", policy.purpose,
                                   "synthetic", "supported")
    return policy, answer, evidence


def test_matching_synthetic_evidence_is_only_sufficient_for_pinned_policy():
    policy, answer, evidence = fixture()
    result = policy.assess((answer,), (evidence,))
    assert result.answered and result.sufficient
    assert result.disposition == "supported"
    assert result.needs[0].supporting == (evidence.receipt,)
    assert result.needs[0].contradicting == ()
    assert result.needs[0].gap is None
    assert result.policy_sha256 == policy.sha256
    assert result.scientifically_established is False
    with pytest.raises(FrozenInstanceError):
        result.answered = False


@pytest.mark.parametrize(("change", "reason"), [
    ({"category": "opinion"}, "category_mismatch"),
    ({"category": "simulation"}, "category_mismatch"),
    ({"category": "independent_replication"}, "category_mismatch"),
    ({"issuer": "someone-else"}, "untrusted_issuer"),
    ({"purpose": "different.decision"}, "purpose_mismatch"),
    ({"authority": "scientific"}, "authority_mismatch"),
    ({"disposition": "unknown"}, "unknown"),
    ({"criterion_id": "other"}, "criterion_mismatch"),
    ({"subject": artifact("another-answer")}, "answer_revision_mismatch"),
    ({"subject": artifact("answer", sha256="c" * 64)}, "answer_revision_mismatch"),
    ({"context": artifact("different-context")}, "context_mismatch"),
    ({"context": artifact("context", sha256="c" * 64)}, "context_mismatch"),
    ({"method": METHOD.model_copy(update={"sha256": "c" * 64})}, "method_mismatch"),
    ({"need": EvidenceNeedRef(scope=SCOPE, need_id="n", revision=2)}, "need_revision_mismatch"),
    ({"need": EvidenceNeedRef(scope=SCOPE, need_id="other", revision=1)}, "need_revision_mismatch"),
    ({"need": EvidenceNeedRef(scope=OTHER, need_id="n", revision=1)}, "scope_mismatch"),
    ({"receipt": artifact("receipt", scope=OTHER)}, "scope_mismatch"),
    ({"subject": artifact("answer", scope=OTHER)}, "scope_mismatch"),
    ({"context": artifact("context", scope=OTHER)}, "scope_mismatch"),
])
def test_mismatched_receipt_never_satisfies_declared_measurement_need(change, reason):
    policy, answer, evidence = fixture()
    result = policy.assess((answer,), (replace(evidence, **change),))
    assert result.answered and not result.sufficient
    assert result.disposition == "unknown"
    assert result.reviews[0].reason == reason
    assert result.needs[0].gap == "no_matching_evidence"
    assert result.needs[0].supporting == ()


@pytest.mark.parametrize(("status", "gap", "disposition"), [
    ("unknown", "answer_unknown", "unknown"),
    ("contradicted", "answer_contradicted", "contradicted"),
])
def test_observation_does_not_override_knowledge_disposition(status, gap, disposition):
    policy, answer, evidence = fixture()
    result = policy.assess((replace(answer, disposition=status),), (evidence,))
    assert result.answered and not result.sufficient
    assert result.disposition == disposition
    assert result.needs[0].gap == gap


def test_absence_is_explicit_unknown_not_false_and_missing_answer_remains_visible():
    policy, answer, evidence = fixture()
    missing = policy.assess((), (evidence,))
    assert not missing.answered and not missing.sufficient
    assert missing.disposition == "unknown"
    assert missing.reviews[0].reason == "missing_answer"
    assert missing.needs[0].gap == "missing_answer"
    answered = policy.assess((answer,), ())
    assert answered.answered and answered.disposition == "unknown"
    assert answered.needs[0].gap == "no_matching_evidence"


def test_contradiction_is_preserved_and_conflict_never_uses_a_majority_vote():
    policy, answer, evidence = fixture()
    negative = replace(evidence, receipt=artifact("negative"), disposition="contradicted")
    result = policy.assess((answer,), (negative,))
    assert result.disposition == "contradicted"
    assert result.needs[0].gap == "evidence_contradicted"
    assert result.needs[0].contradicting == (negative.receipt,)
    observations = (evidence, replace(evidence, receipt=artifact("second-positive")), negative)
    conflict = policy.assess((answer,), observations)
    assert conflict.disposition == "unknown" and not conflict.sufficient
    assert conflict.needs[0].gap == "evidence_conflict"
    assert len(conflict.needs[0].supporting) == 2
    assert conflict == policy.assess((answer,), tuple(reversed(observations)))


def test_exact_remaining_need_and_criterion_not_just_overall_boolean():
    policy, answer, evidence = fixture()
    second_need = policy.requirements[0].need.model_copy(update={
        "reference": EvidenceNeedRef(scope=SCOPE, need_id="replication", revision=1)})
    second = NeedRequirement(second_need, frozenset({"independent_replication"}), frozenset({"replicator"}))
    policy = replace(policy, requirements=(*policy.requirements, second))
    result = policy.assess((answer,), (evidence,))
    assert [(item.criterion_id, item.need.need_id, item.gap) for item in result.needs] == [
        ("c", "n", None), ("c", "replication", "no_matching_evidence")]
    replica = replace(evidence, receipt=artifact("replicated"), need=second_need.reference,
                      category="independent_replication", issuer="replicator")
    assert policy.assess((answer,), (replica, evidence)).sufficient


def test_multi_criterion_need_cannot_reuse_receipt_for_another_answer():
    policy, answer, evidence = fixture()
    question = QuestionDefinition(policy.question.record.model_copy(update={
        "criteria": (*policy.question.record.criteria, AnswerCriterion(criterion_id="d", description="Other"))}))
    need = policy.requirements[0].need.model_copy(update={"criterion_ids": ("c", "d")})
    policy = replace(policy, question=question, requirements=(replace(policy.requirements[0], need=need),))
    other_answer = CandidateAnswer("d", artifact("different-answer"), "supported")
    result = policy.assess((answer, other_answer), (evidence,))
    assert result.answered and not result.sufficient
    assert [item.gap for item in result.needs] == [None, "no_matching_evidence"]
    assert not policy.assess((answer,), (evidence,)).answered


@pytest.mark.parametrize("changed", [False, True])
def test_receipt_repetition_and_same_identity_different_bytes_are_errors(changed):
    policy, answer, evidence = fixture()
    duplicate = replace(evidence, receipt=artifact("receipt", sha256="c" * 64)) if changed else evidence
    with pytest.raises(AssessmentError, match="duplicate_receipt"):
        policy.assess((answer,), (evidence, duplicate))


@pytest.mark.parametrize(("mutation", "code"), [
    (lambda p, a, e: p.assess((a, a), ()), "duplicate_answer"),
    (lambda p, a, e: p.assess((replace(a, criterion_id="unknown"),), ()), "unknown_criterion"),
    (lambda p, a, e: p.assess((replace(a, artifact=artifact("a", scope=OTHER)),), ()), "answer_scope_mismatch"),
    (lambda p, a, e: p.assess((a,) * 33, ()), "invalid_answer_count"),
    (lambda p, a, e: p.assess([], ()), "invalid_answer_count"),
    (lambda p, a, e: p.assess((), (e,) * 257), "invalid_observation_count"),
    (lambda p, a, e: p.assess((), []), "invalid_observation_count"),
    (lambda p, a, e: replace(p, requirements=()), "invalid_requirement_count"),
    (lambda p, a, e: replace(p, requirements=[]), "invalid_requirement_count"),
    (lambda p, a, e: replace(p, requirements=p.requirements * 129), "invalid_requirement_count"),
    (lambda p, a, e: replace(p, requirements=p.requirements * 2), "duplicate_need"),
    (lambda p, a, e: replace(p, purpose="invalid purpose"), "invalid_identifier"),
    (lambda p, a, e: replace(a, disposition="certain"), "invalid_disposition"),
    (lambda p, a, e: replace(e, disposition="certain"), "invalid_disposition"),
    (lambda p, a, e: replace(e, category="best"), "invalid_category"),
    (lambda p, a, e: replace(e, authority="established"), "invalid_authority"),
    (lambda p, a, e: replace(p.requirements[0], categories=frozenset()), "invalid_categories"),
    (lambda p, a, e: replace(p.requirements[0], categories={"observation"}), "invalid_categories"),
    (lambda p, a, e: replace(p.requirements[0], categories=frozenset({"best"})), "invalid_categories"),
    (lambda p, a, e: replace(p.requirements[0], issuers=frozenset()), "invalid_issuers"),
    (lambda p, a, e: replace(p.requirements[0], issuers={"observer"}), "invalid_issuers"),
    (lambda p, a, e: replace(p.requirements[0], issuers=frozenset(str(x) for x in range(33))), "invalid_issuers"),
])
def test_invalid_inputs_fail_closed(mutation, code):
    with pytest.raises(AssessmentError, match=code):
        mutation(*fixture())


def test_every_criterion_requires_predeclared_evidence_and_exact_question_revision():
    policy, _, _ = fixture()
    question = QuestionDefinition(policy.question.record.model_copy(update={
        "criteria": (*policy.question.record.criteria, AnswerCriterion(criterion_id="d", description="Other"))}))
    with pytest.raises(AssessmentError, match="uncovered_criterion"):
        replace(policy, question=question)
    wrong_question = policy.question.record.reference.model_copy(update={"revision": 2})
    wrong_need = replace(policy.requirements[0], need=policy.requirements[0].need.model_copy(
        update={"question": wrong_question}))
    with pytest.raises(ResearchIdentityError, match="question_revision_mismatch"):
        replace(policy, requirements=(wrong_need,))


def test_policy_digest_binds_exact_declarations_and_configuration():
    policy, _, _ = fixture()
    variants = [replace(policy, version="2"), replace(policy, purpose="other"),
                replace(policy, policy_id="other"),
                replace(policy, requirements=(replace(policy.requirements[0], issuers=frozenset({"other"})),)),
                replace(policy, requirements=(replace(policy.requirements[0], categories=frozenset({"opinion"})),))]
    assert len({policy.sha256, *(item.sha256 for item in variants)}) == 6
    assert fixture()[0].sha256 == policy.sha256
