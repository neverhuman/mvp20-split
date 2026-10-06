"""Attributable bounded diagnostic metadata within a separate context profile."""

import hashlib
import json
from typing import Literal

from amphora_contracts_core import Digest, Identifier, SchemaRef, WireModel

from .context import CheckpointContext


class CheckpointRepairFeedback(WireModel):
    parent_request_sha256: Digest
    execution_report_sha256: Digest
    disposition_sha256: Digest
    response_sha256: Digest | None
    reason_code: Identifier
    observation_reason_code: Identifier | None


class CheckpointRepairContext(CheckpointContext):
    profile: Literal['supervision-checkpoint-repair-context.v1'] = 'supervision-checkpoint-repair-context.v1'
    repair: CheckpointRepairFeedback


def checkpoint_repair_context_content_schema_bytes() -> bytes:
    schema = CheckpointRepairContext.model_json_schema(mode='validation')
    return (json.dumps(schema, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False) + '\n').encode('utf-8')


def checkpoint_repair_context_content_schema() -> SchemaRef:
    return SchemaRef(schema_id='supervision.checkpoint-repair-context-content', version='1',
        sha256=hashlib.sha256(checkpoint_repair_context_content_schema_bytes()).hexdigest())
