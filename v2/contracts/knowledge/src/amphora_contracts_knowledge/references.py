"""Scoped graph, stable object and exact immutable revision addresses."""

from amphora_contracts_core import Digest, Identifier, SafePositiveInt, Scope, WireModel


class VocabularyRef(WireModel):
    vocabulary_id: Identifier
    version: Identifier
    sha256: Digest


class StructuralPolicyRef(WireModel):
    policy_id: Identifier
    version: Identifier
    sha256: Digest


class DomainGraphRef(WireModel):
    scope: Scope
    graph_id: Identifier


class DomainRevisionRef(WireModel):
    graph: DomainGraphRef
    revision: SafePositiveInt
    sha256: Digest


class EntityRevisionRef(WireModel):
    graph: DomainGraphRef
    entity_id: Identifier
    revision: SafePositiveInt


class AssertionRevisionRef(WireModel):
    graph: DomainGraphRef
    assertion_id: Identifier
    revision: SafePositiveInt


class AcceptedChangeRef(WireModel):
    graph: DomainGraphRef
    change_id: Identifier
    position: SafePositiveInt
    sha256: Digest


class DomainHead(WireModel):
    snapshot: DomainRevisionRef
    change: AcceptedChangeRef
