"""Pure result preparation from exact interpreted history and reviewed sources."""

import hashlib
from dataclasses import dataclass, replace
from importlib.resources import files
from typing import Literal

from amphora_contracts_artifacts import (
    ContentDescriptor,
    DerivationDeclaration,
    FinalizedReceipt,
    TransformationDescriptor,
)
from amphora_contracts_core import ArtifactRef, Digest, SchemaRef, WireModel
from amphora_contracts_planning import AnswerProposal

from ..context.policy import require
from ..extraction import TraceProjection
from ..publication.candidate import PublishedCandidate
from ..publication.payload import TraceArtifact
from ..publication.records import encode
from ..repair.feedback import RepairFeedback
from ..research_proposals import ResearchProposalValidator


class AnswerRecord(WireModel):
    profile: Literal["planning-candidate-answer.v1"]
    authority: Literal["proposal_only"]
    validation: Literal["quotation_and_structure_only"]
    task_sha256: Digest
    candidate_sha256: Digest
    interpretation: ArtifactRef
    answer: AnswerProposal


def answer_schema():
    raw = files("amphora_agent_planning.result_publication").joinpath("candidate-answer-v1.schema.json").read_bytes()
    return SchemaRef(schema_id="planning.candidate-answer-content", version="1", sha256=hashlib.sha256(raw).hexdigest())


def interpretation(task, observation, review, publication, prior=None):
    require(publication.payload is not None and publication.attempt is not None and
            publication.attempt.stage == "finalized", "interpretation_not_published")
    attempt = publication.attempt
    require(attempt.result is not None, "interpretation_receipt_missing")
    result = attempt.result
    require(replace(attempt, stage="finalizing", result=None).finalized(publication.identity,
        publication.payload.artifact, FinalizedReceipt(upload_id=result.upload_id, artifact=result.artifact), result) == attempt,
        "interpretation_receipt_binding")
    projection = TraceProjection(publication.payload.artifact.body)
    require(TraceProjection.derive(projection.document().trace_id, task, observation, prior).canonical ==
            projection.canonical, "result_observation_binding")
    require(review.task.canonical == task.canonical, "result_review_binding")
    expected = TraceArtifact.reviewed(publication.identity, projection, review)
    require(expected == publication.payload.artifact, "interpretation_payload_binding")
    return projection, result.artifact, expected.declaration.inputs


@dataclass(frozen=True)
class ResultArtifact:
    body: bytes
    content: ContentDescriptor
    declaration: DerivationDeclaration

    @classmethod
    def feedback(cls, task, observation, review, publication, feedback, prior=None):
        projection, reference, inputs = interpretation(task, observation, review, publication, prior)
        feedback = RepairFeedback.from_bytes(feedback.canonical).verify_history(task, projection, observation, prior)
        return cls._build(feedback.canonical, feedback.publication_descriptor(), "diagnostic_feedback",
                          task.sha256, projection.sha256, reference, inputs)

    @classmethod
    def answer(cls, task, observation, review, publication, questions, local_id, prior=None):
        projection, reference, inputs = interpretation(task, observation, review, publication, prior)
        candidate = PublishedCandidate.from_publication(task, observation, review, publication)
        proposals = ResearchProposalValidator().validate(candidate, questions).document()
        matches = [answer for answer in proposals.answers if answer.local_id == local_id]
        require(len(matches) == 1, "result_answer_unavailable")
        record = AnswerRecord(profile="planning-candidate-answer.v1", authority="proposal_only",
            validation="quotation_and_structure_only", task_sha256=task.sha256,
            candidate_sha256=proposals.candidate_sha256, interpretation=reference, answer=matches[0])
        body = encode(record.model_dump(mode="json"))
        require(len(body) <= 262144, "result_payload_limit")
        descriptor = ContentDescriptor(sha256=hashlib.sha256(body).hexdigest(), size_bytes=len(body),
            media_type="application/json", schema_ref=answer_schema())
        return cls._build(body, descriptor, "candidate_answer", task.sha256, projection.sha256, reference, inputs)

    @classmethod
    def _build(cls, body, content, kind, task_sha256, trace_sha256, reference, inputs):
        # Direct inputs are complete even though the interpretation itself also
        # has transitive ancestry. No silent truncation at Data's128-input bound.
        indexed = {}
        for item in (*inputs, reference):
            require(item.scope == reference.scope, "result_input_scope")
            require(item.artifact_id not in indexed or indexed[item.artifact_id] == item, "result_input_collision")
            indexed[item.artifact_id] = item
        require(0 < len(indexed) <= 128, "result_input_limit")
        method = {"profile": "planning-result-publication.v1", "kind": kind,
            "task_sha256": task_sha256, "trace_sha256": trace_sha256, "payload_sha256": content.sha256}
        declaration = DerivationDeclaration(transformation=TransformationDescriptor(
            transformation_id="planning." + kind, version="1", sha256=hashlib.sha256(encode(method)).hexdigest()),
            inputs=tuple(indexed[key] for key in sorted(indexed)))
        return cls(body, content, declaration)

    def bind_slot(self, trace, kind, local_id):
        require(type(self.body) is bytes and 0 < len(self.body) <= 262144, "result_payload_limit")
        require(self.content.sha256 == hashlib.sha256(self.body).hexdigest() and
                self.content.size_bytes == len(self.body) and self.content.media_type == "application/json",
                "result_content_binding")
        if kind == "feedback":
            feedback = RepairFeedback.from_bytes(self.body)
            require(feedback.canonical == self.body and feedback.document().parent == trace and
                    self.content == feedback.publication_descriptor() and local_id == "diagnostics",
                    "result_feedback_binding")
        else:
            record = AnswerRecord.model_validate_json(self.body)
            require(encode(record.model_dump(mode="json")) == self.body and self.content.schema_ref == answer_schema() and
                    record.answer.local_id == local_id and record.interpretation.scope == trace.scope and
                    record.interpretation.sha256 == trace.sha256, "result_answer_binding")
        return self

    @property
    def fingerprint(self):
        return hashlib.sha256(encode({"content": self.content.model_dump(mode="json"),
            "declaration": self.declaration.model_dump(mode="json")})).hexdigest()
