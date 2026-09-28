"""Authored definitions and immutable compiler products, not execution authority."""

from typing import Annotated, Literal

from amphora_contracts_core import Digest, Identifier, SafePositiveInt, SchemaRef, Scope, WireModel
from amphora_contracts_tools import LockEntry
from pydantic import Field

from .nodes import ExecutableScope
from .values import ValuePort


class ContextPin(WireModel):
    kind: Literal["policy", "evaluator", "model", "source", "knowledge"]
    identity: Identifier
    revision: Identifier
    sha256: Digest


class ExecutableCampaign(WireModel):
    schema_version: Literal["2"]
    profile: Literal["deterministic-v1"]
    campaign_id: Identifier
    revision: SafePositiveInt
    scope: Scope
    context: Annotated[tuple[ContextPin, ...], Field(max_length=256)] = ()
    body: ExecutableScope


class PlanLock(WireModel):
    schema_version: Literal["2"]
    compiler_profile: Literal["amphora-deterministic-compiler-v1"]
    definition_sha256: Digest
    tools: Annotated[tuple[LockEntry, ...], Field(max_length=256)]
    schemas: Annotated[tuple[SchemaRef, ...], Field(max_length=512)]
    context: Annotated[tuple[ContextPin, ...], Field(max_length=256)]


class NodeBinding(WireModel):
    node_id: Identifier
    inputs: Annotated[tuple[ValuePort, ...], Field(max_length=64)]
    outputs: Annotated[tuple[ValuePort, ...], Field(max_length=64)]


class ScopePlan(WireModel):
    path: Annotated[tuple[Identifier, ...], Field(max_length=16)]
    order: Annotated[tuple[Identifier, ...], Field(min_length=1, max_length=256)]
    nodes: Annotated[tuple[NodeBinding, ...], Field(min_length=1, max_length=256)]


class PlanDocument(WireModel):
    profile: Literal["amphora-execution-plan-v1"]
    definition: ExecutableCampaign
    lock: PlanLock
    scopes: Annotated[tuple[ScopePlan, ...], Field(min_length=1, max_length=1024)]


class ExecutionPlan(WireModel):
    schema_version: Literal["2"]
    sha256: Digest
    document: PlanDocument


class LoopOccurrence(WireModel):
    kind: Literal["loop"]
    node_id: Identifier
    index: Annotated[int, Field(ge=0, le=9999)]


class ScatterOccurrence(WireModel):
    kind: Literal["scatter"]
    node_id: Identifier
    index: Annotated[int, Field(ge=0, le=9999)]
    membership_sha256: Digest


Occurrence = Annotated[LoopOccurrence | ScatterOccurrence, Field(discriminator="kind")]


class ActivationPath(WireModel):
    schema_version: Literal["2"]
    node_id: Identifier
    occurrences: Annotated[tuple[Occurrence, ...], Field(max_length=16)] = ()
