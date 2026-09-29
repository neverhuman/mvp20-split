"""Versioned observation of typed conversion nodes; legacy page schemas remain intact."""

from typing import Annotated, Literal

from pydantic import Field

from .models import GraphNodeView, GraphRunPage


class GraphNodeViewV3(GraphNodeView):
    kind: Literal["invoke", "branch", "join", "scatter", "iterate", "finish", "await",
                  "artifact_project", "artifact_materialize"]


class GraphRunPageV3(GraphRunPage):
    schema_version: Literal["3"] = "3"
    nodes: Annotated[tuple[GraphNodeViewV3, ...], Field(max_length=100)]
