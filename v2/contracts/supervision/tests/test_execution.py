"""Execution reports add no usage, fake attempt or graph-decision authority."""

import hashlib
import json
from pathlib import Path

import pytest
from amphora_contracts_supervision import CheckpointExecutionReport

ROOT = Path(__file__).absolute().parents[3]


def report():
    original = json.loads((Path(__file__).parent / 'fixtures/checkpoint-request.json').read_bytes())
    return {'reference': original['reference'], 'request_sha256': 'a' * 64,
        'engagement': original['planning_request']['reference'],
        'planning_request_sha256': original['planning_request_sha256'],
        'stop_reason': 'provider_unconfigured', 'attempts': []}


def test_zero_attempt_report_is_distinct_from_usage_or_a_decision():
    wire = CheckpointExecutionReport.model_validate_json(json.dumps(report()))
    assert wire.attempts == () and wire.schema_version == '1'
    assert CheckpointExecutionReport.model_validate_json(wire.model_dump_json()) == wire


@pytest.mark.parametrize('change', ['pending', 'extra', 'version', 'digest', 'unbounded'])
def test_closed_profile(change):
    data = report()
    if change == 'pending':
        data['stop_reason'] = 'attempt_pending'
    elif change == 'extra':
        data['accepted'] = True
    elif change == 'version':
        data['schema_version'] = '2'
    elif change == 'digest':
        data['request_sha256'] = 'no'
    else:
        data['attempts'] = [{'attempt': {'engagement': data['engagement'], 'ordinal': 1,
            'request_sha256': data['planning_request_sha256']}, 'observation_sha256': 'b' * 64,
            'status': 'unknown'}] * 17
    with pytest.raises(ValueError):
        CheckpointExecutionReport.model_validate_json(json.dumps(data))


def test_all_544_predecessor_schemas_unchanged():
    pins = json.loads((Path(__file__).parent / 'fixtures/execution_predecessor_schema_pins.json').read_bytes())
    assert len(pins['schemas']) == 544
    for name, digest in pins['schemas'].items():
        assert hashlib.sha256((ROOT / 'contracts/schemas' / name).read_bytes()).hexdigest() == digest
