"""Deterministic tentative child requests; no publication or dispatch authority."""

import hashlib
from dataclasses import dataclass

from amphora_contracts_core import ArtifactRef

from ..context import RequestSnapshot
from ..context.policy import require
from ..extraction import ExtractionSnapshot
from ..publication.payload import content_schema
from .binding import RepairRoot, encoded
from .feedback import RepairFeedback


def artifact(reference):
    return ArtifactRef.model_validate_json(reference.model_dump_json(warnings=False))


@dataclass(frozen=True)
class RepairRequestPlan:
    task: ExtractionSnapshot
    feedback: RepairFeedback
    feedback_reference_bytes: bytes
    interpretation_reference_bytes: bytes

    @classmethod
    def build(cls, root, parent_task, feedback, feedback_reference, interpretation_reference):
        root = RepairRoot.bind(root.task, root.policy)
        parent_task = ExtractionSnapshot.from_bytes(parent_task.canonical, parent_task.request)
        if parent_task.document().engagement == root.task.document().engagement:
            require(parent_task.canonical == root.task.canonical, "repair_parent_task")
        else:
            root.validate_child(parent_task)
        feedback = RepairFeedback.from_bytes(feedback.canonical)
        record = feedback.document()
        require(record.task_sha256 == parent_task.sha256 and record.request_sha256 == parent_task.request.sha256,
                "repair_feedback_task")
        require(record.outcome.status not in {"abstained", "policy_rejected"}, "repair_terminal_parent")
        feedback_ref, interpretation = artifact(feedback_reference), artifact(interpretation_reference)
        scope = parent_task.document().scope
        require(record.parent.scope == feedback_ref.scope == interpretation.scope == scope, "repair_input_scope")
        feedback.bind_reference(feedback_ref)
        require(interpretation.sha256 == record.parent.sha256 and interpretation.media_type == "application/json" and
                interpretation.schema_ref == content_schema() and 0 < interpretation.size_bytes <= 1048576,
                "repair_interpretation_artifact")
        require(feedback_ref.artifact_id != interpretation.artifact_id, "repair_input_identity")
        identity = hashlib.sha256(encoded({"profile": "planning-repair-request.v1", "parent": record.parent.model_dump(mode="json"),
            "feedback": feedback_ref.model_dump(mode="json"), "interpretation": interpretation.model_dump(mode="json")})).hexdigest()
        request = parent_task.request.document().model_dump(mode="json")
        request["reference"]["engagement_id"] = "repair-" + identity
        entries = request["context"]["entries"]
        for reference in (interpretation, feedback_ref):
            entry = {"artifact": reference.model_dump(mode="json"), "role": "result", "required": True}
            previous = [item for item in entries if item["artifact"]["artifact_id"] == reference.artifact_id]
            require(not previous, "repair_context_identity")
            entries.append(entry)
        require(len(entries) <= 128, "repair_context_capacity")
        snapshot = RequestSnapshot.from_bytes(encoded(request), actor_id=request["actor_id"], scope=scope)
        task = parent_task.document().model_dump(mode="json")
        task.update(task_id="repair-task-" + identity, engagement=request["reference"], request_sha256=snapshot.sha256)
        task = ExtractionSnapshot.from_bytes(encoded(task), snapshot)
        root.validate_child(task)
        return cls(task, feedback, encoded(feedback_ref.model_dump(mode="json")), encoded(interpretation.model_dump(mode="json")))

    def feedback_reference(self):
        return ArtifactRef.model_validate_json(self.feedback_reference_bytes)

    def interpretation_reference(self):
        return ArtifactRef.model_validate_json(self.interpretation_reference_bytes)
