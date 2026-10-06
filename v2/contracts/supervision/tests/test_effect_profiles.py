"""Additive profiles cannot turn old proposals into materialization authority."""

import hashlib
import json
from pathlib import Path

import pytest
from amphora_contracts_supervision import CheckpointDecision, SupervisionDecision

FIXTURES = Path(__file__).absolute().parent / 'fixtures'


def draft():
    data = json.loads((FIXTURES / 'capture-adjustment.json').read_bytes())
    data['schema_version'] = '2'
    candidate = data['candidate']
    candidate['kind'] = 'materialization_adjustment'
    candidate['checkpoint_seed_sha256'] = 'b' * 64
    candidate['changes'] = [{'target': {'schema_version': '2', 'node_id': 'pack',
        'occurrences': [{'kind': 'loop', 'node_id': 'search', 'index': 3}]}, 'field_name': 'temperature',
        'previous_value_sha256': 'c' * 64, 'proposed': {'kind': 'number', 'value': '0.123456789012345678901', 'unit': 'K'}}]
    return data


def decision(outcome):
    request = json.loads((FIXTURES / 'checkpoint-request.json').read_bytes())
    return {'reference': request['reference'], 'revision': 1, 'checkpoint_seed_sha256': 'b' * 64,
            'outcome': outcome}


@pytest.mark.parametrize('outcome', [
    {'kind': 'pending', 'stage': 'checkpoint', 'request_sha256': None},
    {'kind': 'fallback', 'action': 'continue_unchanged', 'reason_code': 'deadline_exhausted'},
    {'kind': 'fallback', 'action': 'block_target', 'reason_code': 'checkpoint_limit_exhausted'},
    {'kind': 'cancelled', 'reason_code': 'run_cancelled'},
])
def test_checkpoint_outcomes_need_no_fabricated_planning_request(outcome):
    data = decision(outcome)
    assert CheckpointDecision.model_validate_json(json.dumps(data)).outcome.kind == outcome['kind']
    with pytest.raises(ValueError):
        SupervisionDecision.model_validate_json(json.dumps(data))


def test_model_effect_requires_bound_request_response_and_exact_scalar():
    field = draft()['candidate']['changes'][0]
    effect = {'kind': 'adjusted_materialization_fields', 'target': field['target'],
              'selection_sha256': 'd' * 64, 'changes': [{'field_name': field['field_name'],
              'previous_value_sha256': field['previous_value_sha256'], 'value': field['proposed']}]}
    data = decision({'kind': 'model_accepted', 'request_sha256': 'e' * 64,
                     'response_sha256': 'f' * 64, 'effect': effect})
    record = CheckpointDecision.model_validate_json(json.dumps(data))
    assert record.outcome.effect.changes[0].value.value == field['proposed']['value']
    del data['outcome']['request_sha256']
    with pytest.raises(ValueError):
        CheckpointDecision.model_validate_json(json.dumps(data))


def test_all_predecessor_schema_bytes_unchanged():
    root = FIXTURES.parents[3]
    pins = json.loads((FIXTURES / 'effects_predecessor_schema_pins.json').read_bytes())
    assert len(pins['schemas']) == 538
    for name, digest in pins['schemas'].items():
        assert hashlib.sha256((root / 'contracts/schemas' / name).read_bytes()).hexdigest() == digest
