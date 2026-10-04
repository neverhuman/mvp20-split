"""Bounded identities/digests of actual input; no duplicate raw-source repository."""

import hashlib
import json
from dataclasses import dataclass
from typing import Annotated, Literal

from amphora_contracts_core import ArtifactRef, Digest, Identifier, WireModel
from amphora_contracts_planning import EngagementRef, ExtractionTraceRef
from amphora_contracts_research import ResearchQuestionRef
from pydantic import Field, ValidationError

from ..context.policy import require
from ..context.snapshot import _constant, _object
from ..research_proposals.context import GAP_CODES
from .binding import encoded
from .prompt import RepairPrompt
from .request import RepairRequestPlan


class PacketIdentity(WireModel):
    sha256: Digest
    size_bytes: Annotated[int, Field(ge=1, le=8388608)]


class QuestionRead(WireModel):
    reference: ResearchQuestionRef
    sha256: Digest


class QuestionGap(WireModel):
    reference: ResearchQuestionRef
    reason: Identifier


class InputReads(WireModel):
    artifacts: Annotated[tuple[ArtifactRef, ...], Field(min_length=1, max_length=128)]
    knowledge_sha256: Digest
    questions: Annotated[tuple[QuestionRead, ...], Field(max_length=64)]
    unavailable: Annotated[tuple[QuestionGap, ...], Field(max_length=64)]


class PreparationRecord(WireModel):
    profile: Literal["planning-repair-preparation.v1"]
    authority: Literal["input_observation_only"]
    root: EngagementRef
    engagement: EngagementRef
    task_id: Identifier
    task_sha256: Digest
    request_sha256: Digest
    parent: ExtractionTraceRef
    packet: PacketIdentity
    inputs: InputReads


@dataclass(frozen=True)
class PreparationManifest:
    canonical: bytes

    @classmethod
    def from_bytes(cls, raw):
        require(type(raw) is bytes and 0 < len(raw) <= 262144, "repair_preparation_size")
        try:
            value = json.loads(raw.decode("utf-8"), object_pairs_hook=_object, parse_constant=_constant)
            record = PreparationRecord.model_validate_json(json.dumps(value, allow_nan=False))
        except (UnicodeDecodeError, ValueError, ValidationError, RecursionError) as exc:
            raise ValueError("invalid_repair_preparation") from exc
        scope = record.engagement.scope
        require(record.root.scope == record.parent.scope == scope, "repair_preparation_scope")
        refs = record.inputs.artifacts
        require(all(ref.scope == scope for ref in refs) and len({ref.artifact_id for ref in refs}) == len(refs),
                "repair_preparation_artifacts")
        questions = [item.reference for item in (*record.inputs.questions, *record.inputs.unavailable)]
        require(len(set(questions)) == len(questions) and all(ref.scope == scope for ref in questions), "repair_preparation_questions")
        require(all(item.reason in GAP_CODES for item in record.inputs.unavailable), "repair_preparation_gap")
        canonical = encoded(record.model_dump(mode="json"))
        require(len(canonical) <= 262144, "repair_preparation_size")
        return cls(canonical)

    @classmethod
    def bind(cls, prepared):
        history, plan = prepared.history, prepared.plan
        plan.feedback.verify_history(history.task, history.projection, history.observation, history.prior)
        require(RepairRequestPlan.build(history.root, history.task, plan.feedback, plan.feedback_reference(),
                plan.interpretation_reference()) == plan, "repair_preparation_plan")
        require(RepairPrompt.render(plan, prepared.sources, prepared.knowledge, prepared.questions) == prepared.packet,
                "repair_preparation_packet")
        task = prepared.plan.task
        document = task.document()
        require(prepared.sources.task.canonical == task.canonical and prepared.knowledge.task_sha256 == task.sha256 and
                prepared.questions.task_sha256 == task.sha256, "repair_preparation_task")
        knowledge = prepared.knowledge
        # Same definition as the graph packet; snapshot/profile are immutable pins.
        knowledge_sha = hashlib.sha256(knowledge.profile_bytes + b"\n" + (knowledge.snapshot_bytes or b"")).hexdigest()
        questions = [{"reference": record.reference.model_dump(mode="json"), "sha256": hashlib.sha256(raw).hexdigest()}
                     for raw, record in zip(prepared.questions.records, prepared.questions.documents(), strict=True)]
        return cls.from_bytes(encoded({"profile": "planning-repair-preparation.v1", "authority": "input_observation_only",
            "root": prepared.history.root.task.document().engagement.model_dump(mode="json"),
            "engagement": document.engagement.model_dump(mode="json"), "task_id": document.task_id,
            "task_sha256": task.sha256, "request_sha256": task.request.sha256,
            "parent": prepared.history.projection.reference().model_dump(mode="json"),
            "packet": {"sha256": hashlib.sha256(prepared.packet).hexdigest(), "size_bytes": len(prepared.packet)},
            "inputs": {"artifacts": [ref.model_dump(mode="json") for ref in prepared.sources.inputs()],
                "knowledge_sha256": knowledge_sha, "questions": questions,
                "unavailable": [{"reference": ref.model_dump(mode="json"), "reason": reason}
                                for ref, reason in prepared.questions.unavailable()]}}))

    def document(self):
        return PreparationRecord.model_validate_json(self.canonical)

    @property
    def sha256(self):
        return hashlib.sha256(self.canonical).hexdigest()
