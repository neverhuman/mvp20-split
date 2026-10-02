import hashlib
from dataclasses import replace
from datetime import UTC, datetime

import pytest
from amphora_contracts_knowledge import (
    CompleteReasoning,
    DomainRevisionRef,
    EvaluatedReasoning,
    GroundLiteral,
    ReasoningFinding,
    ReasoningPublicationRequest,
    ReasoningRequest,
    ReasoningResult,
    ReasoningStatus,
    ReferenceValidation,
    RuleSetRef,
)
from amphora_knowledge.access import Principal
from amphora_knowledge.authoring.canonical import KnowledgeError, canonical
from amphora_knowledge.publication.payload import PublicationRequestDocument, ReasoningArtifact
from pydantic import ValidationError


@pytest.fixture
def case(graph_fixture):
    graph = graph_fixture.proposal.graph
    claim = graph_fixture.proposal.operations[2].assertion
    target = GroundLiteral(subject=claim.subject, predicate=claim.predicate, object=claim.object, polarity=claim.polarity)
    request = ReasoningRequest(wire_version="1", request_id="reason", snapshot=DomainRevisionRef(graph=graph, revision=1, sha256="a" * 64),
        rule_set=RuleSetRef(graph=graph, rule_set_id="rules", version="1", sha256="b" * 64), context=claim.applicability,
        subject=claim.applicability, purpose="arbitrary_caller_purpose", targets=(target,))
    result = ReasoningResult(wire_version="1", authority="synthetic_logical_entailment", request=request,
        outcome=CompleteReasoning(status="complete"), work=1, findings=(ReasoningFinding(target=target, status="supported",
        positive=True, negative=False, conflict=False, supporting_assertions=(claim.reference,), opposing_assertions=()),),
        steps=(), excluded_context=())
    observed = ReferenceValidation(checked_at=datetime.now(UTC), artifacts=(claim.applicability,), sources=(),
        conversion_traces=(), questions=(), evidence_needs=())
    status = ReasoningStatus(wire_version="1", request=request, actor_id="author",
                             decision=EvaluatedReasoning(outcome="evaluated", result=result, validation=observed))
    publication = ReasoningPublicationRequest(wire_version="1", graph=graph, publication_id="publish", reasoning_request_id="reason")
    principal = Principal("author", graph.scope, frozenset({"publish_reasoning"}))
    return principal, publication, status, observed


def test_exact_result_bytes_and_complete_review_are_bound_to_payload(case):
    principal, request, status, observed = case
    document = PublicationRequestDocument.authorized(principal, request)
    extra = observed.artifacts[0].model_copy(update={"artifact_id": "expanded-trace-output"})
    fresh = observed.model_copy(update={"artifacts": (*observed.artifacts, extra)})
    artifact = ReasoningArtifact.reviewed(document, status, fresh)
    assert artifact.body == canonical(status.decision.result)
    assert artifact.content.sha256 == hashlib.sha256(artifact.body).hexdigest()
    assert artifact.content.size_bytes == len(artifact.body)
    assert artifact.content.schema_ref.schema_id == "knowledge.reasoning-result.payload"
    assert set(artifact.declaration.inputs) == set(fresh.artifacts)
    assert artifact.declaration.transformation.transformation_id == "knowledge.synthetic_logical_entailment"
    assert artifact.declaration.transformation.transformation_id != status.request.purpose
    assert artifact == ReasoningArtifact.reviewed(document, status, fresh)


@pytest.mark.parametrize("kind", ["actor", "graph", "request"])
def test_cannot_publish_another_actor_or_result(case, kind):
    principal, request, status, observed = case
    if kind == "actor":
        status = status.model_copy(update={"actor_id": "other"})
    elif kind == "graph":
        request = request.model_copy(update={"graph": request.graph.model_copy(update={"graph_id": "other"})})
    else:
        request = request.model_copy(update={"reasoning_request_id": "other"})
    with pytest.raises(KnowledgeError, match="publication_reasoning_mismatch"):
        ReasoningArtifact.reviewed(PublicationRequestDocument.authorized(principal, request), status, observed)


def test_publication_requires_its_own_scoped_grant(case):
    principal, request, _, _ = case
    with pytest.raises(KnowledgeError, match="access_denied"):
        PublicationRequestDocument.authorized(replace(principal, actions=frozenset({"reason_graph"})), request)


@pytest.mark.parametrize("kind,code", [("empty", "publication_input_scope_mismatch"),
    ("missing", "publication_required_input_missing"), ("duplicate", "publication_duplicate_input"),
    ("foreign", "publication_input_scope_mismatch")])
def test_no_silent_input_omission_or_substitution(case, kind, code):
    principal, request, status, observed = case
    ref = observed.artifacts[0]
    inputs = {"empty": (), "missing": (ref.model_copy(update={"artifact_id": "wrong"}),),
              "duplicate": (ref, ref), "foreign": (ref.model_copy(update={"scope": ref.scope.model_copy(update={"project_id": "foreign"})}),)}[kind]
    with pytest.raises(KnowledgeError, match=code):
        ReasoningArtifact.reviewed(PublicationRequestDocument.authorized(principal, request), status,
                                   observed.model_copy(update={"artifacts": inputs}))


def test_pending_reasoning_cannot_be_published(case):
    principal, request, status, observed = case
    with pytest.raises(KnowledgeError, match="publication_reasoning_pending"):
        ReasoningArtifact.reviewed(PublicationRequestDocument.authorized(principal, request), status.model_copy(update={"decision": None}), observed)


def test_constructed_boolean_work_is_not_normalized_into_a_valid_result(case):
    principal, request, status, observed = case
    bad_result = status.decision.result.model_copy(update={"work": True})
    status = status.model_copy(update={"decision": status.decision.model_copy(update={"result": bad_result})})
    with pytest.raises(ValidationError):
        ReasoningArtifact.reviewed(PublicationRequestDocument.authorized(principal, request), status, observed)
