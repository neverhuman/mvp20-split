"""Exact graph material selection, independent of an extraction or campaign task."""

from dataclasses import dataclass

from amphora_contracts_knowledge import (
    DomainGraphRef,
    DomainHead,
    StructuralPolicyRef,
    VocabularyRef,
)

from ..context.policy import require


@dataclass(frozen=True)
class GraphPins:
    graph: DomainGraphRef
    base: DomainHead | None
    vocabulary: VocabularyRef
    policy: StructuralPolicyRef

    def validated(self):
        graph = DomainGraphRef.model_validate(self.graph.model_dump(mode="python", warnings=False))
        head = None if self.base is None else DomainHead.model_validate(self.base.model_dump(mode="python", warnings=False))
        vocabulary = VocabularyRef.model_validate(self.vocabulary.model_dump(mode="python", warnings=False))
        policy = StructuralPolicyRef.model_validate(self.policy.model_dump(mode="python", warnings=False))
        require(head is None or (head.snapshot.graph == graph == head.change.graph and
                head.snapshot.revision == head.change.position), "graph_pin_head")
        return GraphPins(graph, head, vocabulary, policy)
