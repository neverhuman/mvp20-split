"""Synthetic candidate encodings; transport validity is not domain legality."""

import re
from typing import Annotated, Literal

from amphora_contracts_core import Identifier, SchemaRef, Scope, WireModel
from pydantic import Field

FiniteCoordinate = Annotated[float, Field(ge=-1e6, le=1e6)]
PositiveDescriptor = Annotated[float, Field(gt=0, le=1e9)]


class DesignHeader(WireModel):
    wire_version: Literal["1"]
    scope: Scope
    authority: Literal["synthetic"]
    profile: SchemaRef


class NumericCoordinate(WireModel):
    coordinate_id: Identifier
    unit: Annotated[str, Field(min_length=1, max_length=64)]
    lower: FiniteCoordinate
    upper: FiniteCoordinate
    value: FiniteCoordinate


class NumericDesign(DesignHeader):
    kind: Literal["numeric"]
    coordinates: Annotated[tuple[NumericCoordinate, ...], Field(min_length=1, max_length=32)]


class RepeatUnit(WireModel):
    unit_id: Identifier
    label: Annotated[str, Field(min_length=1, max_length=128)]


class CompositionFraction(WireModel):
    unit_id: Identifier
    fraction: Annotated[float, Field(ge=0, le=1)]


class PolymerSite(WireModel):
    site_id: Identifier
    unit_id: Identifier


class PolymerBond(WireModel):
    left: Identifier
    right: Identifier


class PolymerDistribution(WireModel):
    number_average_dp: PositiveDescriptor | None
    weight_average_dp: PositiveDescriptor | None
    dispersity: Annotated[float, Field(ge=1, le=1e6)] | None


class PolymerEndGroup(WireModel):
    site_id: Identifier
    label: Annotated[str, Field(min_length=1, max_length=128)]


class PolymerMetadata(WireModel):
    sequence_arrangement: Literal["random", "alternating", "block", "defined"] | None
    tacticity: Literal["atactic", "isotactic", "syndiotactic"] | None
    degree_of_polymerization: Annotated[int, Field(ge=1, le=1000000)] | None
    distribution: PolymerDistribution | None
    branching: Literal["linear", "branched"] | None
    end_groups: Annotated[tuple[PolymerEndGroup, ...], Field(max_length=128)] | None
    bigsmiles: Annotated[str, Field(min_length=1, max_length=4096)] | None


class PolymerDesign(DesignHeader):
    kind: Literal["polymer"]
    repeat_units: Annotated[tuple[RepeatUnit, ...], Field(min_length=1, max_length=32)]
    composition: Annotated[tuple[CompositionFraction, ...], Field(min_length=1, max_length=32)] | None
    sites: Annotated[tuple[PolymerSite, ...], Field(min_length=1, max_length=128)]
    bonds: Annotated[tuple[PolymerBond, ...], Field(max_length=127)]
    metadata: PolymerMetadata


class SequenceDesign(DesignHeader):
    kind: Literal["sequence"]
    alphabet: Literal["DNA-ACGT-v1"]
    sequence: Annotated[str, Field(min_length=1, max_length=4096, pattern=re.compile(r"^[ACGT]+$(?![\s\S])"))]


CandidateDesign = Annotated[NumericDesign | PolymerDesign | SequenceDesign, Field(discriminator="kind")]
