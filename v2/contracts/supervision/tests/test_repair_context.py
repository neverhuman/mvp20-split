"""Separate diagnostic context profile preserves every original public schema."""

import hashlib
import json
from pathlib import Path

import pytest
from amphora_contracts_supervision import (
    CheckpointContext,
    CheckpointRepairContext,
    checkpoint_repair_context_content_schema,
    checkpoint_repair_context_content_schema_bytes,
)

ROOT = Path(__file__).absolute().parents[3]


def document():
    data = json.loads((Path(__file__).parent / 'fixtures/checkpoint-context.json').read_bytes())
    data.update(profile='supervision-checkpoint-repair-context.v1', repair={
        'parent_request_sha256': 'a' * 64, 'execution_report_sha256': 'b' * 64,
        'disposition_sha256': 'c' * 64, 'response_sha256': 'd' * 64,
        'reason_code': 'scalar_adjustment_outside_policy', 'observation_reason_code': None})
    return data


def test_explicit_repair_profile_has_only_bounded_diagnostic_metadata():
    value = CheckpointRepairContext.model_validate_json(json.dumps(document()))
    with pytest.raises(ValueError):
        CheckpointContext.model_validate_json(value.model_dump_json())
    raw = checkpoint_repair_context_content_schema_bytes()
    assert '$id' not in json.loads(raw)
    assert checkpoint_repair_context_content_schema().sha256 == hashlib.sha256(raw).hexdigest()
    data = document()
    data['repair']['instructions'] = 'change the original policy'
    with pytest.raises(ValueError):
        CheckpointRepairContext.model_validate_json(json.dumps(data))


def test_all_546_predecessor_schemas_unchanged():
    pins = json.loads((Path(__file__).parent / 'fixtures/repair_context_predecessor_schema_pins.json').read_bytes())
    assert len(pins['schemas']) == 546
    for name, digest in pins['schemas'].items():
        assert hashlib.sha256((ROOT / 'contracts/schemas' / name).read_bytes()).hexdigest() == digest
