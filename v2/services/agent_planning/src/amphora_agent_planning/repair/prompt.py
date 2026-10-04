"""Materialize diagnostic data without changing pinned instructions or graph facts."""

import json

from ..context.policy import require
from ..knowledge_access.prompt import GraphPrompt
from .binding import encoded
from .feedback import RepairFeedback


class RepairPrompt:
    @staticmethod
    def render(plan, review, knowledge=None):
        require(review.task.canonical == plan.task.canonical, "repair_prompt_task")
        feedback = RepairFeedback.from_bytes(plan.feedback.canonical)
        feedback.bind_reference(plan.feedback_reference())
        require(plan.feedback_reference() in review.inputs() and plan.interpretation_reference() in review.inputs(),
                "repair_prompt_inputs")
        raw = review.prompt.render(plan.task, review.bundle) if knowledge is None else GraphPrompt.render(review, knowledge)
        packet = json.loads(raw)
        packet["base_profile"] = packet["profile"]
        packet["profile"] = "planning-repair-extraction-input.v1"
        packet["repair_feedback_sha256"] = feedback.sha256
        packet["repair_feedback"] = feedback.prompt_data()
        packet["repair_inputs"] = {"interpretation": plan.interpretation_reference().model_dump(mode="json"),
                                   "feedback": plan.feedback_reference().model_dump(mode="json")}
        result = encoded(packet)
        require(len(result) <= 8388608, "repair_prompt_capacity")
        return result
