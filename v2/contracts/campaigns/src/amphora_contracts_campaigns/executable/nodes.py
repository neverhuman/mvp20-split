"""Explicit bounded executable scopes; semantic validation belongs to the compiler."""

from __future__ import annotations

from typing import Annotated, Literal

from amphora_contracts_core import Identifier, WireModel
from amphora_contracts_tools import ToolBinding
from pydantic import Field

from .predicates import PredicateV2
from .values import ValueBinding, ValuePort, ValueSource, ValueType


class AllCollectionPolicy(WireModel):
    kind: Literal["all"]
    skipped: Literal["exclude", "fail"] = "exclude"


class PartialCollectionPolicy(WireModel):
    kind: Literal["partial"]
    minimum: Annotated[int, Field(ge=0, le=10000)]
    close: Literal["all_terminal", "deadline"]
    deadline_seconds: Annotated[int, Field(ge=1, le=86400)] | None = None


CollectionPolicy = Annotated[AllCollectionPolicy | PartialCollectionPolicy, Field(discriminator="kind")]


class InvokeV2(WireModel):
    kind: Literal["invoke"]
    node_id: Identifier
    tool: ToolBinding
    inputs: Annotated[tuple[ValueBinding, ...], Field(max_length=64)]
    checkpoint: ValueSource | None = None
    timeout_seconds: Annotated[int, Field(ge=1, le=86400)]


class BranchV2(WireModel):
    kind: Literal["branch"]
    node_id: Identifier
    predicate: PredicateV2


class JoinMember(WireModel):
    member_id: Identifier
    source: ValueSource
    required: bool = True


class JoinV2(WireModel):
    kind: Literal["join"]
    node_id: Identifier
    members: Annotated[tuple[JoinMember, ...], Field(max_length=10000)]
    policy: CollectionPolicy
    output: ValuePort


class ScatterV2(WireModel):
    kind: Literal["scatter"]
    node_id: Identifier
    collection: ValueSource
    item_input: Identifier
    captures: Annotated[tuple[ValueBinding, ...], Field(max_length=64)] = ()
    max_members: Annotated[int, Field(ge=0, le=10000)]
    max_parallel: Annotated[int, Field(ge=1, le=1024)]
    body: ExecutableScope
    result_port: Identifier
    output: ValuePort
    policy: CollectionPolicy


class LoopStateSlot(WireModel):
    name: Identifier
    value_type: ValueType
    initial: ValueSource
    feedback_port: Identifier


class IterateV2(WireModel):
    kind: Literal["iterate"]
    node_id: Identifier
    state: Annotated[tuple[LoopStateSlot, ...], Field(min_length=1, max_length=64)]
    captures: Annotated[tuple[ValueBinding, ...], Field(max_length=64)] = ()
    body: ExecutableScope
    until: PredicateV2
    max_iterations: Annotated[int, Field(ge=1, le=10000)]
    on_limit: Literal["finish", "blocked"]


class FinishV2(WireModel):
    kind: Literal["finish"]
    node_id: Identifier
    outputs: Annotated[tuple[ValueBinding, ...], Field(max_length=64)]


ExecutableNode = Annotated[InvokeV2 | BranchV2 | JoinV2 | ScatterV2 | IterateV2 | FinishV2, Field(discriminator="kind")]


class ControlEdge(WireModel):
    source: Identifier
    target: Identifier
    route: Literal["next", "true", "false"] = "next"


class ExecutableScope(WireModel):
    inputs: Annotated[tuple[ValuePort, ...], Field(max_length=64)] = ()
    outputs: Annotated[tuple[ValuePort, ...], Field(max_length=64)] = ()
    nodes: Annotated[tuple[ExecutableNode, ...], Field(min_length=1, max_length=256)]
    edges: Annotated[tuple[ControlEdge, ...], Field(max_length=1024)] = ()


ScatterV2.model_rebuild()
IterateV2.model_rebuild()
