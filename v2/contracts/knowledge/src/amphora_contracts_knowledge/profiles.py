"""Discover the graph's pinned authoring universe without implicit migration."""

from typing import Literal

from amphora_contracts_core import WireModel

from .records import DomainVocabulary
from .references import DomainGraphRef, StructuralPolicyRef, VocabularyRef


class GraphAuthoringProfile(WireModel):
    wire_version: Literal["1"]
    graph: DomainGraphRef
    vocabulary: DomainVocabulary
    vocabulary_reference: VocabularyRef
    policy: StructuralPolicyRef
    origin: Literal["configured_default", "stored"]
