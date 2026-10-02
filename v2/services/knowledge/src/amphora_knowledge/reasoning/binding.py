"""Bind private symbols to exact owner-reconstructed graph state and context."""

from dataclasses import dataclass

from amphora_contracts_core import ArtifactRef
from amphora_contracts_knowledge import AssertionRevisionRef, DomainRevisionRef

from ..authoring.canonical import KnowledgeError, digest
from ..authoring.state import GraphState
from .model import Atom, Fact, Seed


@dataclass(frozen=True)
class BoundAssertion:
    reference: AssertionRevisionRef
    seed: Seed


@dataclass(frozen=True)
class GraphInputs:
    snapshot: DomainRevisionRef
    context: ArtifactRef
    assertions: tuple[BoundAssertion, ...]
    excluded_context: tuple[AssertionRevisionRef, ...]

    @classmethod
    def from_state(cls, state, context):
        # GraphState is an owner composition point, not an untrusted snapshot DTO.
        if type(state) is not GraphState or type(context) is not ArtifactRef:
            raise KnowledgeError("invalid_reasoning_binding")
        if context.scope != state.graph.scope:
            raise KnowledgeError("reasoning_context_scope_mismatch")
        reference = state.reference
        included, excluded = [], []
        for assertion in state.assertions.active():
            if assertion.applicability != context:
                excluded.append(assertion.reference)
                continue
            atom = Atom(digest(assertion.subject), assertion.predicate, digest(assertion.object))
            included.append(BoundAssertion(assertion.reference,
                Seed(Fact(atom, assertion.polarity), digest(assertion.reference))))
        return cls(reference, context, tuple(included), tuple(excluded))

    @property
    def seeds(self):
        return tuple(assertion.seed for assertion in self.assertions)

    def fact(self, reference):
        for assertion in self.assertions:
            if assertion.reference == reference:
                return assertion.seed.fact
        raise KnowledgeError("reasoning_assertion_not_applicable")

    def references(self, origins):
        indexed = {assertion.seed.origin: assertion.reference for assertion in self.assertions}
        if any(origin not in indexed for origin in origins):
            raise KnowledgeError("reasoning_origin_not_bound")
        return tuple(indexed[origin] for origin in sorted(set(origins)))
