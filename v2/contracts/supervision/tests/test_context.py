"""Public untrusted checkpoint context preserves exact scalars and old schemas."""

import hashlib
import json
from pathlib import Path

import pytest
from amphora_contracts_supervision import CheckpointContext, checkpoint_context_schema

ROOT = Path(__file__).absolute().parents[3]


def document():
    return json.loads((Path(__file__).parent / 'fixtures/checkpoint-context.json').read_bytes())


def test_context_exact_decimal_and_profile_roundtrip():
    record = CheckpointContext.model_validate_json(json.dumps(document()))
    assert record.fields[0].original_value.value == '0.1234567890123456789'
    assert CheckpointContext.model_validate_json(record.model_dump_json()) == record
    assert record.future_proposals == 'retained_only'
    assert checkpoint_context_schema().sha256 == hashlib.sha256(
        (ROOT / 'contracts/schemas/v1/supervision.checkpoint-context.validation.json').read_bytes()).hexdigest()


@pytest.mark.parametrize('change', ['extra', 'float', 'negative', 'future', 'profile', 'fields'])
def test_context_closed_portable_bounds(change):
    data = document()
    if change == 'extra':
        data['accepted'] = True
    elif change == 'float':
        data['fields'][0]['original_value']['value'] = 0.1
    elif change == 'negative':
        data['remaining']['slot_model_calls'] = -1
    elif change == 'future':
        data['future_proposals'] = 'activate_now'
    elif change == 'profile':
        data['profile'] = 'supervision-checkpoint-context.v2'
    else:
        data['fields'] *= 65
    with pytest.raises(ValueError):
        CheckpointContext.model_validate_json(json.dumps(data))


def test_all_542_predecessor_schemas_unchanged():
    pins = json.loads((Path(__file__).parent / 'fixtures/context_predecessor_schema_pins.json').read_bytes())
    assert len(pins['schemas']) == 542
    for name, digest in pins['schemas'].items():
        assert hashlib.sha256((ROOT / 'contracts/schemas' / name).read_bytes()).hexdigest() == digest
