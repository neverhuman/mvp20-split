"""Focused acceptance factory; authentication and actual peer reads remain adapter duties."""

from dataclasses import dataclass

from amphora_contracts_knowledge import (
    AcceptedChangeContent,
    AcceptedChangeRef,
    AcceptedGraphChange,
    DomainHead,
)

from ..authoring.canonical import KnowledgeError, digest
from ..authoring.references import ReferencedInputs
from ..authoring.state import GraphState


def require_observation(proposal, observation, accepted_at):
    inputs = ReferencedInputs.collect(proposal)
    expected = (inputs.artifacts, inputs.sources, inputs.traces, inputs.questions, inputs.needs)
    actual = (observation.artifacts, observation.sources, observation.conversion_traces,
              observation.questions, observation.evidence_needs)
    if actual != expected:
        raise KnowledgeError("reference_validation_mismatch")
    if accepted_at.tzinfo is None or observation.checked_at.tzinfo is None or observation.checked_at > accepted_at:
        raise KnowledgeError("invalid_review_time")


@dataclass(frozen=True)
class AcceptedEdit:
    state: GraphState
    record: AcceptedGraphChange

    @property
    def head(self):
        return DomainHead(snapshot=self.record.content.resulting_snapshot, change=self.record.reference)

    @classmethod
    def review(cls, state, head, proposal, *, actor_id, observation, accepted_at):
        require_observation(proposal, observation, accepted_at)
        resulting = state.apply(proposal, head)
        content = AcceptedChangeContent(proposal=proposal, actor_id=actor_id, policy=state.policy.reference,
            validation=observation, accepted_at=accepted_at, position=resulting.revision,
            resulting_snapshot=resulting.reference, authority="structural_only")
        reference = AcceptedChangeRef(graph=state.graph, change_id=proposal.change_id,
                                      position=resulting.revision, sha256=digest(content))
        return cls(resulting, AcceptedGraphChange(wire_version="1", reference=reference, content=content))
