"""Initial structured control language. No expression strings or executable code."""

from __future__ import annotations

from typing import Annotated, Literal

from amphora_contracts_core import Identifier, SafePositiveInt, Scope, WireModel
from amphora_contracts_tools import ToolBinding
from pydantic import Field


class Invoke(WireModel):
    kind: Literal["invoke"]
    node_id: Identifier
    tool: ToolBinding


class Predicate(WireModel):
    source_node: Identifier
    source_port: Identifier
    operator: Literal["equals", "not_equals"]
    value: str | bool


class Branch(WireModel):
    kind: Literal["branch"]
    node_id: Identifier
    predicate: Predicate


class Join(WireModel):
    kind: Literal["join"]
    node_id: Identifier
    policy: Literal["all_succeeded", "all_terminal"]


class Finish(WireModel):
    kind: Literal["finish"]
    node_id: Identifier


class Iterate(WireModel):
    kind: Literal["iterate"]
    node_id: Identifier
    max_iterations: Annotated[int, Field(ge=1, le=10000)]
    body: GraphBody


Node = Annotated[Invoke | Branch | Join | Finish | Iterate, Field(discriminator="kind")]


class Edge(WireModel):
    source: Identifier
    target: Identifier
    route: Literal["next", "true", "false"] = "next"


class GraphBody(WireModel):
    nodes: Annotated[tuple[Node, ...], Field(min_length=1, max_length=256)]
    edges: Annotated[tuple[Edge, ...], Field(max_length=1024)]


class CampaignDefinition(WireModel):
    schema_version: Literal["1"]
    campaign_id: Identifier
    revision: SafePositiveInt
    scope: Scope
    body: GraphBody


Iterate.model_rebuild()
