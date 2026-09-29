"""Wire-v4 typed Artifact/graph conversions; no implicit I/O or scientific computation."""

from __future__ import annotations

from typing import Annotated, Literal

from amphora_contracts_core import Identifier, WireModel
from pydantic import Field, TypeAdapter

from .awaitable import AwaitV3, ExecutableCampaignV3, ExecutionPlanV3
from .nodes import BranchV2, ControlEdge, FinishV2, InvokeV2, IterateV2, JoinV2, ScatterV2
from .plans import ExecutableCampaign, ExecutionPlan, PlanDocument, PlanLock
from .values import ValuePort, ValueSource


class BindingLimits(WireModel):
    max_items: Annotated[int, Field(ge=0, le=10000)] = 256
    max_artifacts: Annotated[int, Field(ge=1, le=1024)] = 256
    max_bytes: Annotated[int, Field(ge=1, le=262144)] = 262144
    timeout_seconds: Annotated[int, Field(ge=1, le=300)] = 30


class ArtifactProjectV4(WireModel):
    kind: Literal["artifact_project"]
    node_id: Identifier
    source: ValueSource
    path: Annotated[tuple[Annotated[str, Field(max_length=128)] | Annotated[int, Field(ge=0, le=10000)], ...], Field(max_length=16)] = ()
    mode: Literal["values", "references", "items"]
    output: ValuePort
    limits: BindingLimits = Field(default_factory=BindingLimits)


class MaterializeField(WireModel):
    name: Identifier
    source: ValueSource
    mode: Literal["inline", "references"]


class ArtifactMaterializeV4(WireModel):
    kind: Literal["artifact_materialize"]
    node_id: Identifier
    fields: Annotated[tuple[MaterializeField, ...], Field(max_length=64)]
    output: ValuePort
    limits: BindingLimits = Field(default_factory=BindingLimits)


class ScatterV4(ScatterV2):
    body: ExecutableScopeV4


class IterateV4(IterateV2):
    body: ExecutableScopeV4


ExecutableNodeV4 = Annotated[InvokeV2 | BranchV2 | JoinV2 | ScatterV4 | IterateV4 | FinishV2
    | AwaitV3 | ArtifactProjectV4 | ArtifactMaterializeV4, Field(discriminator="kind")]


class ExecutableScopeV4(WireModel):
    inputs: Annotated[tuple[ValuePort, ...], Field(max_length=64)] = ()
    outputs: Annotated[tuple[ValuePort, ...], Field(max_length=64)] = ()
    nodes: Annotated[tuple[ExecutableNodeV4, ...], Field(min_length=1, max_length=256)]
    edges: Annotated[tuple[ControlEdge, ...], Field(max_length=1024)] = ()


ScatterV4.model_rebuild()
IterateV4.model_rebuild()


class ExecutableCampaignV4(ExecutableCampaign):
    schema_version: Literal["4"]
    profile: Literal["deterministic-v3"]
    body: ExecutableScopeV4


class PlanLockV4(PlanLock):
    schema_version: Literal["4"]
    compiler_profile: Literal["amphora-deterministic-compiler-v3"]


class PlanDocumentV4(PlanDocument):
    profile: Literal["amphora-execution-plan-v3"]
    definition: ExecutableCampaignV4
    lock: PlanLockV4


class ExecutionPlanV4(ExecutionPlan):
    schema_version: Literal["4"]
    document: PlanDocumentV4


class BindingPrimitiveDescriptor(WireModel):
    schema_version: Literal["1"] = "1"
    kind: Literal["artifact_project", "artifact_materialize"]
    owner: Literal["campaign_runtime"] = "campaign_runtime"
    executable_profile: Literal["deterministic-v3"] = "deterministic-v3"
    modes: Annotated[tuple[Identifier, ...], Field(min_length=1, max_length=3)]
    authority: Literal["typed_data_conversion"] = "typed_data_conversion"
    scientific_authority: Literal["none"] = "none"


_DEFINITIONS = TypeAdapter(Annotated[ExecutableCampaign | ExecutableCampaignV3 | ExecutableCampaignV4, Field(discriminator="schema_version")])
_PLANS = TypeAdapter(Annotated[ExecutionPlan | ExecutionPlanV3 | ExecutionPlanV4, Field(discriminator="schema_version")])


def parse_executable_campaign(raw):
    return _DEFINITIONS.validate_json(raw)


def parse_execution_plan(raw):
    return _PLANS.validate_json(raw)
