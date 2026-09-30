"""Runtime-owned named read capabilities; no scientific-view authority."""

from typing import Annotated, Literal

from amphora_contracts_core import WireModel
from pydantic import Field

from .observations import GraphReadCut


class DigestViewFilter(WireModel):
    kind: Literal["digest"] = "digest"
    name: Literal["scope_key", "focus_activation_id"]
    required: bool


class RadiusViewFilter(WireModel):
    kind: Literal["integer"] = "integer"
    name: Literal["radius"] = "radius"
    required: Literal[False] = False
    minimum: Literal[0] = 0
    maximum: Literal[2] = 2
    default: Literal[1] = 1


ViewFilter = Annotated[DigestViewFilter | RadiusViewFilter, Field(discriminator="kind")]


class GraphViewDefinition(WireModel):
    view_id: Literal["execution_topology", "successor_lineage"]
    view_version: Literal["1"] = "1"
    owner: Literal["campaign-runtime"] = "campaign-runtime"
    result_schema: Literal["graph-runtime.topology-page", "graph-runtime.successor-lineage"]
    result_schema_version: Literal["1"] = "1"
    required_capability: Literal["runtime.authored-topology.v1", "runtime.successor-lineage.v1"]
    result_bound: Annotated[int, Field(ge=1, le=256)]
    filters: Annotated[tuple[ViewFilter, ...], Field(max_length=3)]


class GraphViewCatalog(WireModel):
    schema_version: Literal["1"] = "1"
    cut: GraphReadCut
    views: Annotated[tuple[GraphViewDefinition, ...], Field(max_length=2)]
