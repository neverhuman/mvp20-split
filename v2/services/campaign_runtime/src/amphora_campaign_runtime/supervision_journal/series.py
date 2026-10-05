"""Bounded original lineage and narrowing ceilings, not provider accounting."""

from dataclasses import dataclass

from ..supervision_scope.observations import require
from .frames import RequestFrame


def successor(previous, current):
    old, new = previous.request, current.request
    require(old.reference == new.reference and old.checkpoint_id == new.checkpoint_id,
            'decision_mismatch')
    require(previous.document().prepared_by == current.document().prepared_by, 'preparer_mismatch')
    require(old.planning_request.actor_id == new.planning_request.actor_id, 'planning_actor_mismatch')
    require(old.snapshot.footprint_sha256 == new.snapshot.footprint_sha256, 'footprint_mismatch')
    previous.footprint().compare(new.snapshot.cut, current.footprint().observations)
    require(new.deadline_unix_ms <= old.deadline_unix_ms, 'deadline_widened')
    left, right = old.planning_request.context, new.planning_request.context
    for name in ('objective', 'prompt', 'policy', 'model', 'output_schema'):
        require(getattr(left, name) == getattr(right, name), 'context_binding_changed')
    require(set(right.allowed_actions) <= set(left.allowed_actions), 'actions_widened')
    require(left.limits.accounting_unit == right.limits.accounting_unit, 'accounting_unit_changed')
    for name in ('max_input_tokens', 'max_output_tokens', 'max_attempts', 'total_tokens', 'total_accounting_units'):
        require(getattr(right.limits, name) <= getattr(left.limits, name), 'limits_widened')
    for item in left.entries:
        declaration = item.role == 'constraint' and item.artifact.sha256 == old.planning_request.decision_scope
        if item.required and not declaration:
            require(item in right.entries, 'required_context_lost')


@dataclass(frozen=True)
class RequestSeries:
    frames: tuple[RequestFrame, ...]

    def __post_init__(self):
        require(type(self.frames) is tuple and 1 <= len(self.frames) <= 16, 'series_size')
        frames = tuple(RequestFrame.from_bytes(item.canonical) for item in self.frames)
        engagements = set()
        for index, frame in enumerate(frames):
            request = frame.request
            lineage = request.lineage
            require(lineage.ordinal == index + 1, 'lineage_ordinal')
            engagement = request.planning_request.reference.engagement_id
            require(engagement not in engagements, 'reused_engagement')
            engagements.add(engagement)
            if index:
                require(lineage.root_request_sha256 == frames[0].request_sha256 and
                        lineage.parent_request_sha256 == frames[index - 1].request_sha256, 'lineage_hash')
                successor(frames[index - 1], frame)
        object.__setattr__(self, 'frames', frames)

    def append(self, frame):
        return type(self)((*self.frames, frame))
