"""Executable wire-v3 adds authored external waits; frozen v2 roots remain intact."""

from __future__ import annotations

from typing import Annotated, Literal

from amphora_contracts_core import Identifier, WireModel
from pydantic import Field, TypeAdapter

from .nodes import BranchV2, ControlEdge, FinishV2, InvokeV2, IterateV2, JoinV2, ScatterV2
from .plans import ExecutableCampaign, ExecutionPlan, PlanDocument, PlanLock
from .values import ValuePort, ValueSource


class AwaitV3(WireModel):
    kind: Literal["await"]
    node_id: Identifier
    issuer_id: Identifier
    purpose: Identifier
    expected_revision: Identifier
    subject: ValueSource
    output: ValuePort
    timeout_seconds: Annotated[int, Field(ge=1, le=86400)]
    on_timeout: Literal["blocked", "abstained"]


class ScatterV3(ScatterV2):
    body: ExecutableScopeV3


class IterateV3(IterateV2):
    body: ExecutableScopeV3


ExecutableNodeV3 = Annotated[
    InvokeV2 | BranchV2 | JoinV2 | ScatterV3 | IterateV3 | FinishV2 | AwaitV3,
    Field(discriminator="kind"),
]


class ExecutableScopeV3(WireModel):
    inputs: Annotated[tuple[ValuePort, ...], Field(max_length=64)] = ()
    outputs: Annotated[tuple[ValuePort, ...], Field(max_length=64)] = ()
    nodes: Annotated[tuple[ExecutableNodeV3, ...], Field(min_length=1, max_length=256)]
    edges: Annotated[tuple[ControlEdge, ...], Field(max_length=1024)] = ()


ScatterV3.model_rebuild()
IterateV3.model_rebuild()


class ExecutableCampaignV3(ExecutableCampaign):
    schema_version: Literal["3"]
    profile: Literal["deterministic-v2"]
    body: ExecutableScopeV3


class PlanLockV3(PlanLock):
    schema_version: Literal["3"]
    compiler_profile: Literal["amphora-deterministic-compiler-v2"]


class PlanDocumentV3(PlanDocument):
    profile: Literal["amphora-execution-plan-v2"]
    definition: ExecutableCampaignV3
    lock: PlanLockV3


class ExecutionPlanV3(ExecutionPlan):
    schema_version: Literal["3"]
    document: PlanDocumentV3


_DEFINITIONS = TypeAdapter(Annotated[ExecutableCampaign | ExecutableCampaignV3, Field(discriminator="schema_version")])
_PLANS = TypeAdapter(Annotated[ExecutionPlan | ExecutionPlanV3, Field(discriminator="schema_version")])


def parse_executable_campaign(raw):
    return _DEFINITIONS.validate_json(raw)


def parse_execution_plan(raw):
    return _PLANS.validate_json(raw)
