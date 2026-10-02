"""Bounded, exact ordered-history verification and semantic reconstruction."""

from dataclasses import dataclass

from amphora_contracts_knowledge import DomainHead

from ..authoring.canonical import KnowledgeError, digest
from ..authoring.state import GraphState
from .accepted import AcceptedEdit


@dataclass(frozen=True)
class ReplayedGraph:
    state: GraphState
    head: DomainHead | None


class GraphReplay:
    def __init__(self, graph, vocabulary, policy, max_changes=10000):
        if type(max_changes) is not int or not 1 <= max_changes <= 10000:
            raise KnowledgeError("invalid_replay_limit")
        self.graph, self.vocabulary, self.policy = graph, vocabulary, policy
        self.max_changes = max_changes

    def rebuild(self, records):
        state = GraphState(self.graph, self.vocabulary, self.policy)
        head = None
        seen = set()
        for index, record in enumerate(records, start=1):
            if index > self.max_changes:
                raise KnowledgeError("replay_limit")
            content = record.content
            if record.reference.graph != self.graph or content.proposal.graph != self.graph:
                raise KnowledgeError("replay_graph_mismatch")
            if record.reference.change_id in seen:
                raise KnowledgeError("duplicate_accepted_change")
            if record.reference.position != index or content.position != index:
                raise KnowledgeError("replay_position_gap")
            if record.reference.sha256 != digest(content):
                raise KnowledgeError("accepted_change_digest_mismatch")
            if content.policy != self.policy.reference or content.authority != "structural_only":
                raise KnowledgeError("replay_policy_mismatch")
            rebuilt = AcceptedEdit.review(state, head, content.proposal, actor_id=content.actor_id,
                observation=content.validation, accepted_at=content.accepted_at)
            if rebuilt.record != record:
                raise KnowledgeError("replayed_change_mismatch")
            seen.add(record.reference.change_id)
            state, head = rebuilt.state, rebuilt.head
        return ReplayedGraph(state, head)
