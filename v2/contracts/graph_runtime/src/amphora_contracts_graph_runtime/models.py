"""Admission and bounded graph observations, separate from unchanged worker contracts."""

from typing import Annotated, Literal

from amphora_contracts_campaigns import ActivationPath
from amphora_contracts_core import Digest, Identifier, SafePositiveInt, Scope, WireModel
from amphora_contracts_runtime import AttemptBudget
from pydantic import Field

from .values import GraphBinding


class GraphLimits(WireModel):
    max_activations: Annotated[int, Field(ge=1, le=100000)] = 10000
    deadline_seconds: Annotated[int, Field(ge=1, le=86400)] = 3600


class AdmitGraphRun(WireModel):
    schema_version: Literal["1"] = "1"
    plan_sha256: Digest
    inputs: Annotated[tuple[GraphBinding, ...], Field(max_length=64)]
    budget: AttemptBudget
    limits: GraphLimits = GraphLimits()


class AdvanceGraph(WireModel):
    schema_version: Literal["1"] = "1"
    run_id: Identifier
    max_transitions: Annotated[int, Field(ge=1, le=256)] = 64


class GraphNodeView(WireModel):
    activation_id: Digest
    path: ActivationPath
    kind: Literal["invoke", "branch", "join", "scatter", "iterate", "finish"]
    status: Literal["waiting", "ready", "issued", "succeeded", "skipped", "failed", "blocked"]
    reason_code: Identifier | None


class GraphRunPage(WireModel):
    schema_version: Literal["1"] = "1"
    scope: Scope
    run_id: Identifier
    plan_sha256: Digest
    status: Literal["running", "completed", "cancelled", "failed", "blocked"]
    revision: Annotated[int, Field(ge=0, le=9007199254740991)]
    node_count: Annotated[int, Field(ge=0, le=100000)]
    budget_limit: SafePositiveInt
    reserved: Annotated[int, Field(ge=0, le=9007199254740991)]
    spent: Annotated[int, Field(ge=0, le=9007199254740991)]
    stop_reason: Identifier | None
    nodes: Annotated[tuple[GraphNodeView, ...], Field(max_length=100)]
    next_after: Digest | None
