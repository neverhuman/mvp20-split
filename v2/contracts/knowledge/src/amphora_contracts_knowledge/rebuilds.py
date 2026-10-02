"""Reconstruction has its own identity; it never creates an accepted graph edit."""

from typing import Annotated, Literal

from amphora_contracts_core import Identifier, WireModel
from pydantic import Field

from .references import DomainGraphRef, DomainHead


class GraphRebuildRequest(WireModel):
    wire_version: Literal["1"]
    graph: DomainGraphRef
    rebuild_id: Identifier


class PublishedRebuild(WireModel):
    outcome: Literal["published"]
    head: DomainHead
    attempts: Annotated[int, Field(ge=1, le=3)]


class UnpublishedRebuild(WireModel):
    outcome: Literal["deferred", "failed"]
    code: Identifier
    attempts: Annotated[int, Field(ge=1, le=3)]


class GraphRebuildStatus(WireModel):
    wire_version: Literal["1"]
    request: GraphRebuildRequest
    actor_id: Identifier
    initial_head: DomainHead
    result: Annotated[PublishedRebuild | UnpublishedRebuild, Field(discriminator="outcome")] | None
