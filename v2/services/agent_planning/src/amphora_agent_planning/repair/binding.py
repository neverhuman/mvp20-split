"""Immutable family identities and narrowing rules derived from owned facts."""

import json
from dataclasses import dataclass

from ..budget import BudgetPolicy
from ..context import AttemptBinding
from ..context.policy import require
from ..extraction.snapshot import ExtractionSnapshot


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


@dataclass(frozen=True)
class RepairRoot:
    task: ExtractionSnapshot
    policy: BudgetPolicy

    @classmethod
    def bind(cls, task, policy):
        task = ExtractionSnapshot.from_bytes(task.canonical, task.request)
        policy = BudgetPolicy.from_bytes(policy.canonical)
        policy.demand(AttemptBinding(task.request, 1))
        return cls(task, policy)

    @property
    def engagement_id(self):
        return self.task.document().engagement.engagement_id

    @property
    def canonical(self):
        return encoded({"format": "planning-repair-root.v1", "root": self.engagement_id,
            "task_sha256": self.task.sha256, "request_sha256": self.task.request.sha256,
            "policy_sha256": self.policy.sha256})

    def validate_child(self, child):
        child = ExtractionSnapshot.from_bytes(child.canonical, child.request)
        root_request, request = self.task.request.document(), child.request.document()
        root, task = self.task.document(), child.document()
        require(task.engagement != root.engagement, "repair_child_identity")
        for field in ("actor_id", "purpose", "decision_scope", "runtime_cut"):
            require(getattr(request, field) == getattr(root_request, field), "repair_request_authority")
        for field in ("scope", "objective", "prompt", "policy", "model", "output_schema"):
            require(getattr(request.context, field) == getattr(root_request.context, field), "repair_context_authority")
        require(set(request.context.allowed_actions) <= set(root_request.context.allowed_actions),
                "repair_actions_exceeded")
        for field, ceiling in root_request.context.limits.model_dump().items():
            actual = getattr(request.context.limits, field)
            require(actual == ceiling if isinstance(ceiling, str) else actual <= ceiling, "repair_limits_exceeded")
        for field in ("schema_version", "scope", "sources", "target", "existing_entities", "known_questions", "known_needs"):
            require(getattr(task, field) == getattr(root, field), "repair_task_pins")
        require(getattr(task, "existing_assertions", ()) == getattr(root, "existing_assertions", ()), "repair_task_pins")
        # Additional context may describe diagnostics, never replace the original facts or capabilities.
        for entry in root_request.context.entries:
            require(entry in request.context.entries, "repair_context_removed")
        for entry in request.context.entries:
            require(entry in root_request.context.entries or entry.role == "result", "repair_context_added")
        require(request.context.omissions == root_request.context.omissions, "repair_omissions_changed")
        self.policy.demand(AttemptBinding(child.request, 1))
        return child

    def member_bytes(self, task, parent=None):
        return encoded({"format": "planning-repair-member.v1", "root": self.engagement_id,
            "task_sha256": task.sha256, "request_sha256": task.request.sha256,
            "parent": None if parent is None else parent.model_dump(mode="json")})
