import hashlib
from dataclasses import replace
from importlib.resources import files

import jsonschema
import pytest
from amphora_agent_planning.access import Principal
from amphora_agent_planning.extraction import TraceProjection
from amphora_agent_planning.publication import AttemptIdentity, PublicationAttempt
from amphora_agent_planning.publication.records import encode
from amphora_agent_planning.repair.feedback import RepairFeedback
from amphora_agent_planning.research_proposals import QuestionContext
from amphora_agent_planning.result_publication.identity import ResultIdentity
from amphora_agent_planning.result_publication.payload import (
    AnswerRecord,
    ResultArtifact,
    answer_schema,
)
from amphora_contracts_core import Finding

from ..publication.test_values import receipts
from ..research_proposals.support import ResearchCase


def prepared():
    case = ResearchCase()
    bound = case.bind()
    arguments = (bound.task, bound.observation, bound.review, bound.publication)
    projection = TraceProjection(bound.publication.payload.artifact.body)
    feedback = RepairFeedback.create(bound.task, projection, bound.observation,
        (Finding(code="needs_exploration", location="/answers/0", message="Synthetic unresolved context"),))
    artifact = ResultArtifact.feedback(*arguments, feedback)
    questions = QuestionContext.bind(bound.task, ())
    principal = Principal("fixture", bound.task.document().scope, frozenset({"read_attempts", "record_attempts"}))
    return arguments, projection, feedback, artifact, questions, principal


def test_feedback_preserves_exact_bytes_complete_ancestry_and_diagnostic_authority():
    arguments, projection, feedback, artifact, _, principal = prepared()
    assert artifact.body == feedback.canonical
    assert artifact.content == feedback.publication_descriptor()
    expected = (*arguments[3].payload.artifact.declaration.inputs, arguments[3].attempt.result.artifact)
    assert set(artifact.declaration.inputs) == set(expected)
    assert tuple(ref.artifact_id for ref in artifact.declaration.inputs) == tuple(sorted(ref.artifact_id for ref in expected))
    identity = ResultIdentity.bind(principal, projection.reference(), "feedback", "diagnostics", "data-owner", artifact)
    assert ResultIdentity.restore(identity.canonical, replace(principal, actions=frozenset({"read_attempts"})), artifact) == identity
    assert artifact.bind_slot(projection.reference(), "feedback", "diagnostics") == artifact


def test_answer_revalidates_selected_proposal_without_promoting_scientific_authority():
    arguments, projection, _, feedback, questions, principal = prepared()
    artifact = ResultArtifact.answer(*arguments, questions, "a")
    record = AnswerRecord.model_validate_json(artifact.body)
    assert record.authority == "proposal_only" and record.validation == "quotation_and_structure_only"
    assert record.answer.answer == "A does not cause B." and record.answer.question.revision == 1
    assert artifact.declaration.inputs == feedback.declaration.inputs
    assert record.interpretation == arguments[3].attempt.result.artifact
    assert artifact.content.schema_ref == answer_schema()
    schema = AnswerRecord.model_json_schema(mode="validation")
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    assert files("amphora_agent_planning.result_publication").joinpath("candidate-answer-v1.schema.json").read_bytes() == encode(schema) + b"\n"
    jsonschema.Draft202012Validator(schema).validate(record.model_dump(mode="json"))
    identity = ResultIdentity.bind(principal, projection.reference(), "answer", "a", "data-owner", artifact)
    assert ResultIdentity.restore(identity.canonical, principal, artifact) == identity
    assert identity.publication_id != ResultIdentity.bind(principal, projection.reference(), "feedback", "diagnostics", "data-owner", feedback).publication_id


@pytest.mark.parametrize("kind", ["feedback", "answer"])
def test_existing_upload_oracles_accept_result_identity_without_reusing_trace_identity(kind):
    arguments, projection, _, feedback, questions, principal = prepared()
    artifact = feedback if kind == "feedback" else ResultArtifact.answer(*arguments, questions, "a")
    identity = ResultIdentity.bind(principal, projection.reference(), kind,
        "diagnostics" if kind == "feedback" else "a", "data-owner", artifact)
    attempt = PublicationAttempt.first(identity)
    upload, stream, final, derivation = receipts(identity, artifact, attempt)
    final_attempt = attempt.begun(identity, artifact, upload).start_stream().streamed(stream).start_finalize().finalized(
        identity, artifact, final, derivation)
    assert final_attempt.result.artifact.sha256 == hashlib.sha256(artifact.body).hexdigest()
    assert AttemptIdentity.for_publication(identity, 1) != AttemptIdentity.for_publication(arguments[3].identity, 1)


def test_changed_content_or_publisher_stays_same_effect_slot_but_conflicts_in_identity():
    arguments, projection, feedback, artifact, _, principal = prepared()
    identity = ResultIdentity.bind(principal, projection.reference(), "feedback", "diagnostics", "data-owner", artifact)
    changed = ResultIdentity.bind(principal, projection.reference(), "feedback", "diagnostics", "replacement-config", artifact)
    record = feedback.document().model_dump(mode="json")
    record["findings"][0]["message"] = "Different diagnostic"
    second = ResultArtifact.feedback(*arguments, RepairFeedback.from_bytes(encode(record)))
    changed_body = ResultIdentity.bind(principal, projection.reference(), "feedback", "diagnostics", "data-owner", second)
    assert identity.publication_id == changed.publication_id == changed_body.publication_id
    assert len({identity.sha256, changed.sha256, changed_body.sha256}) == 3
    with pytest.raises(ValueError, match="result_identity_binding"):
        ResultIdentity.restore(identity.canonical, principal, second)


@pytest.mark.parametrize("fault", ["unpublished", "body", "observation", "receipt"])
def test_unverified_interpretation_cannot_prepare_result(fault):
    arguments, _projection, feedback, _, _, _ = prepared()
    task, observation, review, publication = arguments
    if fault == "unpublished":
        publication = replace(publication, attempt=replace(publication.attempt, stage="finalizing"))
    elif fault == "body":
        publication = replace(publication, payload=replace(publication.payload,
            artifact=replace(publication.payload.artifact, body=b"{}")))
    elif fault == "observation":
        changed = observation.document().model_dump(mode="json")
        changed["output_sha256"] = "0" * 64
        observation = replace(observation, canonical=encode(changed))
    else:
        publication = replace(publication, attempt=replace(publication.attempt,
            result=publication.attempt.result.model_copy(update={"request_sha256": "0" * 64})))
    with pytest.raises(ValueError):
        ResultArtifact.feedback(task, observation, review, publication, feedback)


def test_unavailable_answer_is_not_invented():
    arguments, _, _, _, questions, _ = prepared()
    with pytest.raises(ValueError, match="result_answer_unavailable"):
        ResultArtifact.answer(*arguments, questions, "absent")


@pytest.mark.parametrize("fault", ["kind", "slot", "actor", "scope", "content", "schema", "answer_key"])
def test_result_identity_cannot_relabel_payload_or_authority(fault):
    arguments, projection, _, artifact, questions, principal = prepared()
    kind, local_id = "feedback", "diagnostics"
    if fault == "kind": kind = "accepted"
    if fault == "slot": local_id = "another"
    if fault == "actor": principal = replace(principal, actions=frozenset({"read_attempts"}))
    if fault == "scope": principal = replace(principal, scope=principal.scope.model_copy(update={"project_id": "foreign"}))
    if fault == "content": artifact = replace(artifact, body=artifact.body + b" ")
    if fault == "schema": artifact = replace(artifact, content=artifact.content.model_copy(update={"schema_ref": answer_schema()}))
    if fault == "answer_key":
        artifact = ResultArtifact.answer(*arguments, questions, "a")
        kind, local_id = "answer", "other"
    with pytest.raises(PermissionError if fault in {"actor", "scope"} else ValueError):
        ResultIdentity.bind(principal, projection.reference(), kind, local_id, "data-owner", artifact)


@pytest.mark.parametrize("fault", ["collision", "scope", "count"])
def test_derived_ancestry_never_silently_drops_inputs(fault):
    arguments, projection, _, artifact, _, _ = prepared()
    reference = arguments[3].attempt.result.artifact
    inputs = tuple(item for item in artifact.declaration.inputs if item != reference)
    if fault == "collision":
        inputs += (reference.model_copy(update={"sha256": "0" * 64}),)
    elif fault == "scope":
        inputs += (reference.model_copy(update={"scope": reference.scope.model_copy(update={"project_id": "foreign"})}),)
    else:
        inputs = tuple(reference.model_copy(update={"artifact_id": "input-" + str(i)}) for i in range(128))
    with pytest.raises(ValueError, match="result_input_"):
        ResultArtifact._build(artifact.body, artifact.content, "diagnostic_feedback", arguments[0].sha256,
                              projection.sha256, reference, inputs)


@pytest.mark.parametrize("fault", ["noncanonical", "format", "actor", "size"])
def test_stored_identity_is_strictly_reconstructed(fault):
    _, projection, _, artifact, _, principal = prepared()
    identity = ResultIdentity.bind(principal, projection.reference(), "feedback", "diagnostics", "data-owner", artifact)
    raw = identity.canonical
    if fault == "noncanonical": raw += b" "
    if fault == "format": raw = encode(identity.document() | {"format": "another"})
    if fault == "actor": raw = encode(identity.document() | {"actor_id": "other"})
    if fault == "size": raw = b"x" * 16385
    with pytest.raises(ValueError):
        ResultIdentity.restore(raw, principal, artifact)
