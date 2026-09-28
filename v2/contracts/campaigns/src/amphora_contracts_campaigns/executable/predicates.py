"""Finite predicate syntax with explicitly typed immutable JSON projections."""

from __future__ import annotations

from typing import Annotated, Literal

from amphora_contracts_core import WireModel
from pydantic import Field

from .values import ScalarConstant, ScalarType, ValueSource


class ScalarProjection(WireModel):
    source: ValueSource
    # Empty path uses a scalar directly. Artifact paths require pinned-schema verification.
    path: Annotated[tuple[Annotated[str, Field(max_length=128)] | Annotated[int, Field(ge=0, le=10000)], ...], Field(max_length=16)] = ()
    value_type: ScalarType


class ComparePredicate(WireModel):
    kind: Literal["compare"]
    left: ScalarProjection
    operator: Literal["eq", "ne", "lt", "le", "gt", "ge"]
    right: ScalarConstant


class ConstantPredicate(WireModel):
    kind: Literal["constant"]
    value: bool


class AllPredicate(WireModel):
    kind: Literal["all"]
    predicates: Annotated[tuple[PredicateV2, ...], Field(min_length=1, max_length=16)]


class AnyPredicate(WireModel):
    kind: Literal["any"]
    predicates: Annotated[tuple[PredicateV2, ...], Field(min_length=1, max_length=16)]


class NotPredicate(WireModel):
    kind: Literal["not"]
    predicate: PredicateV2


PredicateV2 = Annotated[ComparePredicate | ConstantPredicate | AllPredicate | AnyPredicate | NotPredicate, Field(discriminator="kind")]
AllPredicate.model_rebuild()
AnyPredicate.model_rebuild()
NotPredicate.model_rebuild()
