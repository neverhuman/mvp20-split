"""Canonical semantic content is separate from incidental build metadata."""

from typing import Annotated, Literal

from amphora_contracts_core import SafePositiveInt, WireModel
from pydantic import Field

from .records import AssertionRetraction, DomainAssertion, DomainEntity, EntityAlias
from .references import DomainGraphRef, DomainRevisionRef, StructuralPolicyRef, VocabularyRef


class DomainGraphContent(WireModel):
    graph: DomainGraphRef
    revision: SafePositiveInt
    vocabulary: VocabularyRef
    policy: StructuralPolicyRef
    entities: Annotated[tuple[DomainEntity, ...], Field(max_length=4096)]
    assertions: Annotated[tuple[DomainAssertion, ...], Field(max_length=8192)]
    aliases: Annotated[tuple[EntityAlias, ...], Field(max_length=4096)]
    retractions: Annotated[tuple[AssertionRetraction, ...], Field(max_length=8192)]


class DomainGraphSnapshot(WireModel):
    wire_version: Literal["1"]
    reference: DomainRevisionRef
    content: DomainGraphContent
