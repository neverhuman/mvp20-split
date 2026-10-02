"""Immutable semantic graph state; edits neither commit nor grant scientific authority."""

from dataclasses import dataclass

from amphora_contracts_knowledge import (
    AddAssertion,
    AddEntity,
    CorrectAssertion,
    DomainGraphContent,
    DomainGraphRef,
    DomainGraphSnapshot,
    DomainRevisionRef,
    MergeEntities,
    RetractAssertion,
    ReviseEntityContext,
)

from .assertions import AssertionHistory
from .canonical import KnowledgeError, digest
from .entities import EntityHistory
from .policy import StructuralPolicy
from .references import ReferencedInputs
from .vocabulary import Vocabulary


@dataclass(frozen=True)
class GraphState:
    graph: DomainGraphRef
    vocabulary: Vocabulary
    policy: StructuralPolicy
    revision: int = 0
    entities: EntityHistory = EntityHistory()
    assertions: AssertionHistory = AssertionHistory()

    def to_content(self):
        if self.revision == 0:
            raise KnowledgeError("unpublished_graph")
        self.policy.check_size(self.entities, self.assertions)
        return DomainGraphContent(graph=self.graph, revision=self.revision,
            vocabulary=self.vocabulary.reference, policy=self.policy.reference,
            entities=tuple(sorted(self.entities.records, key=lambda r: (r.reference.entity_id, r.reference.revision))),
            assertions=tuple(sorted(self.assertions.records, key=lambda r: (r.reference.assertion_id, r.reference.revision))),
            aliases=tuple(sorted(self.entities.aliases, key=lambda r: (r.source.entity_id, r.source.revision))),
            retractions=tuple(sorted(self.assertions.retractions, key=lambda r: (r.assertion.assertion_id, r.assertion.revision))))

    @property
    def reference(self):
        return DomainRevisionRef(graph=self.graph, revision=self.revision, sha256=digest(self.to_content()))

    def to_snapshot(self):
        content = self.to_content()
        reference = DomainRevisionRef(graph=self.graph, revision=self.revision, sha256=digest(content))
        return DomainGraphSnapshot(wire_version="1", reference=reference, content=content)

    def apply(self, proposal, head):
        if proposal.graph != self.graph:
            raise KnowledgeError("proposal_graph_mismatch")
        if proposal.vocabulary != self.vocabulary.reference or proposal.policy != self.policy.reference:
            raise KnowledgeError("graph_configuration_mismatch")
        if self.revision == 0:
            if head is not None or self.entities.records or self.assertions.records or self.entities.aliases or self.assertions.retractions:
                raise KnowledgeError("invalid_genesis_state")
        elif (head is None or head.snapshot != self.reference or head.change.graph != self.graph
              or head.change.position != self.revision):
            raise KnowledgeError("invalid_current_head")
        if proposal.base != head:
            raise KnowledgeError("stale_head")
        if not 1 <= len(proposal.operations) <= 128:
            raise KnowledgeError("operation_limit")
        if self.revision >= 9007199254740991:
            raise KnowledgeError("graph_revision_limit")
        ReferencedInputs.collect(proposal)
        entities, assertions = self.entities, self.assertions
        for operation in proposal.operations:
            if isinstance(operation, AddEntity):
                self.vocabulary.require_type(operation.entity.entity_type)
                entities = entities.add(operation.entity)
            elif isinstance(operation, ReviseEntityContext):
                self.vocabulary.require_type(operation.replacement.entity_type)
                entities = entities.revise_context(operation.prior, operation.replacement)
            elif isinstance(operation, MergeEntities):
                entities = entities.merge(operation.source, operation.target, proposal.change_id)
            elif isinstance(operation, (AddAssertion, CorrectAssertion)):
                record = operation.assertion if isinstance(operation, AddAssertion) else operation.replacement
                left, right = entities.find(record.subject), entities.find(record.object)
                self.vocabulary.require_relation(record.predicate, left.entity_type, right.entity_type)
                assertions = (assertions.add(record) if isinstance(operation, AddAssertion)
                              else assertions.correct(operation.prior, record))
            elif isinstance(operation, RetractAssertion):
                assertions = assertions.retract(operation.assertion, proposal.change_id)
            else:
                raise KnowledgeError("unknown_operation")
            self.policy.check_size(entities, assertions)
        return GraphState(self.graph, self.vocabulary, self.policy, self.revision + 1, entities, assertions)
