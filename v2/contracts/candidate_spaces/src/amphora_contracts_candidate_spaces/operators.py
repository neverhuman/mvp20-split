"""One proposed move with retained source identity; no trusted completion."""

from typing import Annotated, Literal

from amphora_contracts_core import Digest, Identifier, SchemaRef, WireModel
from pydantic import Field

from .designs import (
    CandidateDesign,
    FiniteCoordinate,
    NumericDesign,
    PolymerDesign,
    SequenceDesign,
)


class SetCoordinate(WireModel):
    kind: Literal["set_coordinate"]
    coordinate_id: Identifier
    value: FiniteCoordinate


class ReplaceUnit(WireModel):
    kind: Literal["replace_unit"]
    site_id: Identifier
    unit_id: Identifier


class SubstituteBase(WireModel):
    kind: Literal["substitute_base"]
    position: Annotated[int, Field(ge=0, le=4095)]
    base: Literal["A", "C", "G", "T"]


class NumericMoveRequest(WireModel):
    wire_version: Literal["1"]
    source: NumericDesign
    operator: SchemaRef
    move: SetCoordinate


class PolymerMoveRequest(WireModel):
    wire_version: Literal["1"]
    source: PolymerDesign
    operator: SchemaRef
    move: ReplaceUnit


class SequenceMoveRequest(WireModel):
    wire_version: Literal["1"]
    source: SequenceDesign
    operator: SchemaRef
    move: SubstituteBase


class ProposedDesignChange(WireModel):
    wire_version: Literal["1"]
    source_sha256: Digest
    operator: SchemaRef
    move: Annotated[SetCoordinate | ReplaceUnit | SubstituteBase, Field(discriminator="kind")]
    result: CandidateDesign
