"""Published checkpoint context data; no dispatch or execution authority."""

import hashlib
import json
from typing import Annotated, Literal

from amphora_contracts_campaigns import ActivationPath, ScalarType
from amphora_contracts_core import ArtifactRef, Digest, Identifier, SchemaRef, WireModel
from amphora_contracts_graph_runtime import NumberValue, ScalarValue
from amphora_contracts_planning import EngagementRef, ProposalAction
from pydantic import Field

from .checkpoints import CheckpointSnapshot
from .requests import SupervisionLineage, SupervisionRef


class CheckpointRange(WireModel):
    kind: Literal['range']
    minimum: NumberValue
    maximum: NumberValue


class CheckpointChoices(WireModel):
    kind: Literal['choices']
    values: Annotated[tuple[ScalarValue, ...], Field(min_length=1, max_length=64)]


class CheckpointFieldContext(WireModel):
    name: Identifier
    value_type: ScalarType
    original_value: ScalarValue
    original_value_sha256: Digest
    constraint: Annotated[CheckpointRange | CheckpointChoices, Field(discriminator='kind')]


class CheckpointAllowance(WireModel):
    slot_requests: Annotated[int, Field(ge=0, le=16)]
    slot_model_calls: Annotated[int, Field(ge=0, le=256)]
    campaign_requests: Annotated[int, Field(ge=0, le=160000)]
    campaign_model_calls: Annotated[int, Field(ge=0, le=2560000)]


class CheckpointContext(WireModel):
    schema_version: Literal['1'] = '1'
    profile: Literal['supervision-checkpoint-context.v1'] = 'supervision-checkpoint-context.v1'
    reference: SupervisionRef
    engagement: EngagementRef
    lineage: SupervisionLineage
    checkpoint_id: Identifier
    checkpoint_seed_sha256: Digest
    recipe_sha256: Digest
    objective: ArtifactRef
    policy: ArtifactRef
    budget_policy: ArtifactRef
    snapshot: CheckpointSnapshot
    target: ActivationPath
    fields: Annotated[tuple[CheckpointFieldContext, ...], Field(max_length=64)]
    remaining: CheckpointAllowance
    deadline_unix_ms: Annotated[int, Field(ge=1, le=9007199254740991)]
    allowed_actions: Annotated[tuple[ProposalAction, ...], Field(min_length=1, max_length=4)]
    future_proposals: Literal['retained_only'] = 'retained_only'


def checkpoint_context_schema() -> SchemaRef:
    schema = CheckpointContext.model_json_schema(mode='validation')
    schema['$schema'] = 'https://json-schema.org/draft/2020-12/schema'
    schema['$id'] = 'urn:amphora:supervision.checkpoint-context:1:validation'
    raw = (json.dumps(schema, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False) + '\n').encode('utf-8')
    return SchemaRef(schema_id='supervision.checkpoint-context', version='1', sha256=hashlib.sha256(raw).hexdigest())


def checkpoint_context_content_schema_bytes() -> bytes:
    """Local-pointer-only Data validator profile, distinct from schema publication metadata."""
    schema = CheckpointContext.model_json_schema(mode='validation')
    return (json.dumps(schema, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False) + '\n').encode('utf-8')


def checkpoint_context_content_schema() -> SchemaRef:
    return SchemaRef(schema_id='supervision.checkpoint-context-content', version='1',
                     sha256=hashlib.sha256(checkpoint_context_content_schema_bytes()).hexdigest())
