"""Synthetic process lineage; no reaction, safety, conservation or lab authority."""

from typing import Annotated, Literal

from amphora_contracts_core import ArtifactRef, Digest, Identifier, SchemaRef, WireModel
from amphora_contracts_tools import ToolBinding
from pydantic import Field, FiniteFloat

from .evaluations import ExecutionPointer
from .membership import GenerationIdentity, MembershipPageReference


class ProcessContext(WireModel):
    generation: GenerationIdentity
    candidate_id: Digest
    process_batch_id: Identifier


class MaterialAmount(WireModel):
    value: Annotated[FiniteFloat, Field(ge=0)]
    unit: Annotated[str, Field(min_length=1, max_length=64)]


class MaterialState(WireModel):
    schema_version: Literal["1"]
    profile: Literal["synthetic-process-material-v1"]
    context: ProcessContext
    state_id: Identifier
    revision: Annotated[int, Field(ge=1, le=9007199254740991)]
    kind: Literal["molecule", "formulation", "mixture", "intermediate", "product", "sample"]
    representation: ArtifactRef
    composition: ArtifactRef | None
    material_batch_id: Identifier | None
    amount: MaterialAmount | None
    phase: Annotated[str, Field(min_length=1, max_length=64)] | None
    conditions: ArtifactRef
    unknowns: Annotated[tuple[Identifier, ...], Field(max_length=32)]


class ProcessPort(WireModel):
    port: Identifier
    required: bool
    representation: SchemaRef
    maximum: Annotated[int, Field(ge=1, le=32)]


class ProcessBinding(WireModel):
    tool: ToolBinding
    inputs: Annotated[tuple[ProcessPort, ...], Field(min_length=1, max_length=32)]
    outputs: Annotated[tuple[ProcessPort, ...], Field(min_length=1, max_length=32)]


class MaterialUse(WireModel):
    port: Identifier
    ordinal: Annotated[int, Field(ge=0, le=31)]
    material: ArtifactRef


class AbsentProcessInput(WireModel):
    port: Identifier
    reason_code: Identifier


class ProcessDerivation(WireModel):
    schema_version: Literal["1"]
    profile: Literal["synthetic-process-derivation-v1"]
    context: ProcessContext
    occurrence_id: Identifier
    tool: ToolBinding
    inputs: Annotated[tuple[MaterialUse, ...], Field(min_length=1, max_length=32)]
    absent: Annotated[tuple[AbsentProcessInput, ...], Field(max_length=32)]
    outputs: Annotated[tuple[MaterialUse, ...], Field(min_length=1, max_length=32)]
    conditions: ArtifactRef
    producer: ExecutionPointer
    unknowns: Annotated[tuple[Identifier, ...], Field(max_length=32)]


class MaterialMappingPolicy(WireModel):
    mode: Literal["pairwise", "keyed", "cartesian"]
    unmatched: Literal["reject", "retain_excluded"]
    cartesian_opt_in: bool
    maximum_outputs: Annotated[int, Field(ge=1, le=10000)]


class MaterialMappingItem(WireModel):
    key: Identifier
    state: ArtifactRef


class MaterialMappingPair(WireModel):
    left_key: Identifier
    right_key: Identifier
    left: ArtifactRef
    right: ArtifactRef


class MaterialMappingExclusion(WireModel):
    side: Literal["left", "right"]
    key: Identifier
    state: ArtifactRef
    reason_code: Literal["unmatched_key"]


class MaterialMappingPage(WireModel):
    schema_version: Literal["1"]
    profile: Literal["synthetic-process-mapping-page-v1"]
    context: ProcessContext
    ordinal: Annotated[int, Field(ge=0, le=511)]
    pairs: Annotated[tuple[MaterialMappingPair, ...], Field(max_length=64)]
    excluded: Annotated[tuple[MaterialMappingExclusion, ...], Field(max_length=64)]


class MaterialMappingManifest(WireModel):
    schema_version: Literal["1"]
    profile: Literal["synthetic-process-mapping-manifest-v1"]
    context: ProcessContext
    policy: MaterialMappingPolicy
    left: ArtifactRef
    right: ArtifactRef
    pair_count: Annotated[int, Field(ge=0, le=10000)]
    excluded_count: Annotated[int, Field(ge=0, le=20000)]
    pages: Annotated[tuple[MembershipPageReference, ...], Field(max_length=512)]
