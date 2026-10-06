"""Bounded public metadata shapes preserve all predecessor public bytes."""

import hashlib
import json
from pathlib import Path

import pytest
from amphora_contracts_supervision import (
    CheckpointContextPage,
    CheckpointInspectionPage,
    CheckpointRequestPage,
    CheckpointResponsePage,
)

FIXTURES = Path(__file__).parent / 'fixtures'
ROOT = Path(__file__).absolute().parents[3]
PROFILES = [(CheckpointInspectionPage, 'inspection-checkpoints'), (CheckpointRequestPage, 'inspection-requests'),
            (CheckpointContextPage, 'inspection-context'), (CheckpointResponsePage, 'inspection-responses')]


@pytest.mark.parametrize('model,name', PROFILES)
def test_literal_metadata_pages_round_trip_without_private_payload(model, name):
    raw = (FIXTURES / (name + '.json')).read_bytes()
    value = model.model_validate_json(raw)
    assert model.model_validate_json(value.model_dump_json()) == value
    assert 'payload_json' not in value.model_dump_json() and 'canonical_command' not in value.model_dump_json()
    assert value.total >= len(value.items)


@pytest.mark.parametrize('model,name', PROFILES)
@pytest.mark.parametrize('fault', ['oversize', 'cursor', 'count', 'extra', 'version'])
def test_page_boundaries_reject_unbounded_or_injected_state(model, name, fault):
    raw = json.loads((FIXTURES / (name + '.json')).read_bytes())
    if fault == 'oversize':
        raw['items'] = raw['items'][:1] * 11
    elif fault == 'cursor':
        raw['next_cursor'] = 'x' * 4097
    elif fault == 'count':
        raw['total'] = -1
    elif fault == 'extra':
        raw['items'][0]['raw_prompt'] = 'private'
    else:
        raw['schema_version'] = '2'
    with pytest.raises(ValueError):
        model.model_validate_json(json.dumps(raw))


def test_omission_and_retention_remain_explicit_not_success():
    context = CheckpointContextPage.model_validate_json((FIXTURES / 'inspection-context.json').read_bytes())
    assert context.items[0].kind == 'included'
    assert context.items[1].kind == 'omitted' and context.items[1].omission.reason == 'budget'
    response = CheckpointResponsePage.model_validate_json((FIXTURES / 'inspection-responses.json').read_bytes())
    assert response.items[0].status == 'proposed' and not response.items[0].selected_by_winner
    requests = CheckpointRequestPage.model_validate_json((FIXTURES / 'inspection-requests.json').read_bytes())
    assert requests.items[0].report_stop_reason == 'provider_unconfigured' and requests.items[0].attempts == ()


def test_all_548_predecessor_schema_files_remain_byte_identical():
    pins = json.loads((FIXTURES / 'inspection_predecessor_schema_pins.json').read_bytes())['schemas']
    assert len(pins) == 548
    for name, digest in pins.items():
        assert hashlib.sha256((ROOT / 'contracts/schemas' / name).read_bytes()).hexdigest() == digest
