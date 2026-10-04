"""Immutable preparation witness; history replay is not fresh source processing."""

import hashlib
import json
from dataclasses import dataclass

from amphora_contracts_artifacts import ContentDescriptor, DerivationDeclaration
from amphora_contracts_research import ResearchQuestion, ResearchQuestionRef

from ..context.policy import require
from ..context.snapshot import _constant, _object
from ..publication.payload import TraceArtifact
from ..publication.records import encode
from ..publication.review_record import ReviewRecord
from ..repair.feedback import RepairFeedback
from ..research_proposals import QuestionContext
from .identity import ResultIdentity
from .payload import AnswerRecord, ResultArtifact


def question_bytes(task, questions):
    if questions is None:
        return b"null"
    require(questions.task_sha256 == task.sha256, "result_question_task_binding")
    questions = QuestionContext.bind(task, questions.documents(), questions.unavailable())
    return encode({"records": [record.model_dump(mode="json") for record in questions.documents()],
        "gaps": [{"reference": reference.model_dump(mode="json"), "reason": reason}
                 for reference, reason in questions.unavailable()]})


def restore_questions(raw, task):
    require(type(raw) is bytes and 0 < len(raw) <= 8388608, "result_question_witness_limit")
    value = json.loads(raw.decode("utf-8"), object_pairs_hook=_object, parse_constant=_constant)
    if value is None:
        require(raw == b"null", "result_question_witness_canonical")
        return None
    require(type(value) is dict and set(value) == {"records", "gaps"} and
            type(value["records"]) is list and type(value["gaps"]) is list and
            len(value["records"]) <= 64 and len(value["gaps"]) <= 64, "result_question_witness_shape")
    require(all(type(gap) is dict and set(gap) == {"reference", "reason"} for gap in value["gaps"]),
            "result_question_witness_shape")
    result = QuestionContext.bind(task,
        tuple(ResearchQuestion.model_validate_json(json.dumps(record)) for record in value["records"]),
        tuple((ResearchQuestionRef.model_validate_json(json.dumps(gap["reference"])), gap["reason"]) for gap in value["gaps"]))
    require(question_bytes(task, result) == raw, "result_question_witness_canonical")
    return result


@dataclass(frozen=True)
class PreparedResult:
    identity: ResultIdentity
    artifact: ResultArtifact
    review: ReviewRecord
    questions: bytes
    manifest: bytes

    @classmethod
    def create(cls, principal, selection, history, review, *, questions=None, feedback=None):
        selected = selection.document()
        if selected["kind"] == "feedback":
            require(feedback is not None, "result_diagnostics_missing")
            artifact = ResultArtifact.feedback(*history.arguments(review), feedback, history.prior)
        else:
            require(questions is not None and feedback is None, "result_answer_context")
            artifact = ResultArtifact.answer(*history.arguments(review), questions, selected["local_id"], history.prior)
        identity = ResultIdentity.bind(principal, selection.trace(), selected["kind"], selected["local_id"],
                                       selected["publisher_id"], artifact)
        require(identity.publication_id == selection.publication_id, "result_slot_binding")
        witness = question_bytes(history.task, questions)
        require(len(witness) <= 8388608, "result_question_witness_limit")
        manifest = cls._manifest(selection, history, identity, artifact)
        return cls(identity, artifact, ReviewRecord.from_review(review), witness, manifest)

    @staticmethod
    def _manifest(selection, history, identity, artifact):
        raw = encode({"format": "planning-result-preparation.v1", "selection_sha256": selection.sha256,
            "identity": identity.document(), "task_sha256": history.task.sha256,
            "observation_sha256": history.projection.document().outcome.observation_sha256,
            "interpretation": history.interpretation.attempt.result.artifact.model_dump(mode="json"),
            "content": artifact.content.model_dump(mode="json"),
            "declaration": artifact.declaration.model_dump(mode="json")})
        require(len(raw) <= 262144, "result_manifest_limit")
        return raw

    @property
    def sha256(self):
        digest = hashlib.sha256(b"planning-result-preparation.v1")
        for raw in (self.artifact.body, self.review.canonical, self.questions, self.manifest):
            digest.update(len(raw).to_bytes(8, "big"))
            digest.update(raw)
        return digest.hexdigest()

    @classmethod
    def restore(cls, row, principal, selection, history):
        manifest = bytes(row["manifest_bytes"])
        require(0 < len(manifest) <= 262144, "result_manifest_limit")
        value = json.loads(manifest.decode("utf-8"), object_pairs_hook=_object, parse_constant=_constant)
        require(type(value) is dict and set(value) == {"format", "selection_sha256", "identity", "task_sha256",
            "observation_sha256", "interpretation", "content", "declaration"} and
            value["format"] == "planning-result-preparation.v1", "result_manifest_shape")
        artifact = ResultArtifact(bytes(row["body_bytes"]), ContentDescriptor.model_validate_json(json.dumps(value["content"])),
            DerivationDeclaration.model_validate_json(json.dumps(value["declaration"])))
        identity = ResultIdentity.restore(encode(value["identity"]), principal, artifact)
        selected = selection.document()
        expected_identity = ResultIdentity._encode(principal.actor_id, selection.trace(), selected["kind"],
            selected["local_id"], selected["publisher_id"], artifact)
        require(identity == expected_identity and identity.publication_id == selection.publication_id, "result_slot_binding")
        review = ReviewRecord.from_bytes(bytes(row["review_bytes"]))
        # Reconstruct historical provenance only: no source body, peer read, or
        # attempt to rerun quotation/scientific validation on revoked inputs.
        interpreted = TraceArtifact.restore(history.interpretation.identity, history.projection, history.task, review)
        require(interpreted == history.interpretation.payload.artifact, "result_review_binding")
        reference = history.interpretation.attempt.result.artifact
        kind = "diagnostic_feedback" if selected["kind"] == "feedback" else "candidate_answer"
        rebuilt = ResultArtifact._build(artifact.body, artifact.content, kind, history.task.sha256,
            history.projection.sha256, reference, interpreted.declaration.inputs)
        require(rebuilt == artifact, "result_ancestry_binding")
        if selected["kind"] == "feedback":
            RepairFeedback.from_bytes(artifact.body).verify_history(history.task, history.projection,
                                                                  history.observation, history.prior)
        else:
            answer = AnswerRecord.model_validate_json(artifact.body)
            require(answer.task_sha256 == history.task.sha256 and answer.interpretation == reference and
                    answer.candidate_sha256 == history.projection.document().outcome.candidate_sha256,
                    "result_answer_history")
        questions = bytes(row["question_bytes"])
        context = restore_questions(questions, history.task)
        require(selected["kind"] != "answer" or context is not None, "result_answer_context")
        require(cls._manifest(selection, history, identity, artifact) == manifest, "result_manifest_binding")
        prepared = cls(identity, artifact, review, questions, manifest)
        require(prepared.sha256 == row["payload_sha256"], "stored_result_payload")
        return prepared
