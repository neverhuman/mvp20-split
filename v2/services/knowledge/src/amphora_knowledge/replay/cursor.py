"""Immutable verified replay prefix; catch-up consumes only the exact next tail."""

from dataclasses import dataclass

from amphora_contracts_knowledge import DomainHead

from ..authoring.canonical import KnowledgeError, digest
from ..authoring.state import GraphState
from .accepted import AcceptedEdit


@dataclass(frozen=True)
class ReplayedGraph:
    state: GraphState
    head: DomainHead | None


@dataclass(frozen=True)
class ReplayCursor:
    """Owner-private domain state, never reconstructed from caller snapshot DTOs."""

    state: GraphState
    head: DomainHead | None
    seen: frozenset[str]
    max_changes: int

    @property
    def result(self):
        return ReplayedGraph(self.state, self.head)

    def append(self, record):
        position = self.state.revision + 1
        if position > self.max_changes:
            raise KnowledgeError("replay_limit")
        content = record.content
        if record.reference.graph != self.state.graph or content.proposal.graph != self.state.graph:
            raise KnowledgeError("replay_graph_mismatch")
        if record.reference.change_id in self.seen:
            raise KnowledgeError("duplicate_accepted_change")
        if record.reference.position != position or content.position != position:
            raise KnowledgeError("replay_position_gap")
        if record.reference.sha256 != digest(content):
            raise KnowledgeError("accepted_change_digest_mismatch")
        if content.policy != self.state.policy.reference or content.authority != "structural_only":
            raise KnowledgeError("replay_policy_mismatch")
        rebuilt = AcceptedEdit.review(self.state, self.head, content.proposal, actor_id=content.actor_id,
            observation=content.validation, accepted_at=content.accepted_at)
        if rebuilt.record != record:
            raise KnowledgeError("replayed_change_mismatch")
        return ReplayCursor(rebuilt.state, rebuilt.head, self.seen | {record.reference.change_id}, self.max_changes)

    def through(self, records, watermark):
        """Bound the tail and prove the complete expected head, not only its number."""
        target = 0 if watermark is None else watermark.change.position
        if target < self.state.revision:
            raise KnowledgeError("replay_watermark_regression")
        if watermark is not None and (watermark.change.graph != self.state.graph
                or watermark.snapshot.graph != self.state.graph):
            raise KnowledgeError("replay_graph_mismatch")
        cursor = self
        for record in records:
            if cursor.state.revision >= target:
                raise KnowledgeError("replay_watermark_exceeded")
            cursor = cursor.append(record)
        if cursor.head != watermark:
            raise KnowledgeError("replay_watermark_mismatch")
        return cursor
