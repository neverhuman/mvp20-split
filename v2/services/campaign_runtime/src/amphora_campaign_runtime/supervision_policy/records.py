"""Private admitted policy DTOs; domain objects own eligibility and value rules."""

from typing import Annotated, Literal

from amphora_contracts_campaigns import ScalarType
from amphora_contracts_core import Digest, Identifier, Scope, WireModel
from amphora_contracts_graph_runtime import NumberValue, ScalarValue
from amphora_contracts_planning import CampaignNodeAddress
from pydantic import Field


class NumericBounds(WireModel):
    kind: Literal['range']
    minimum: NumberValue
    maximum: NumberValue


class AllowedValues(WireModel):
    kind: Literal['choices']
    values: Annotated[tuple[ScalarValue, ...], Field(min_length=1, max_length=64)]


class FieldPolicyRecord(WireModel):
    name: Identifier
    value_type: ScalarType
    constraint: Annotated[NumericBounds | AllowedValues, Field(discriminator='kind')]


class CheckpointRuleRecord(WireModel):
    checkpoint_id: Identifier
    target: CampaignNodeAddress
    kind: Literal['invoke', 'artifact_materialize']
    fields: Annotated[tuple[FieldPolicyRecord, ...], Field(max_length=64)] = ()
    reads: Annotated[tuple[CampaignNodeAddress, ...], Field(max_length=255)] = ()
    timeout_seconds: Annotated[int, Field(ge=1, le=300)]
    max_requests: Annotated[int, Field(ge=1, le=16)]
    max_model_calls: Annotated[int, Field(ge=1, le=256)]
    fallback: Literal['continue_unchanged', 'block_target']


class SupervisionCeilings(WireModel):
    max_checkpoints: Annotated[int, Field(ge=1, le=10000)]
    max_requests: Annotated[int, Field(ge=1, le=160000)]
    max_model_calls: Annotated[int, Field(ge=1, le=2560000)]


class PolicyRecord(WireModel):
    profile: Literal['runtime-supervision-policy.v1'] = 'runtime-supervision-policy.v1'
    scope: Scope
    plan_sha256: Digest
    checkpoints: Annotated[tuple[CheckpointRuleRecord, ...], Field(min_length=1, max_length=64)]
    ceilings: SupervisionCeilings
