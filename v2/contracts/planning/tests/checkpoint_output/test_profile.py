"""Explicit scalar checkpoint proposals preserve legacy campaign interpretation."""

import json
from pathlib import Path

import pytest
from amphora_contracts_planning import (
    CampaignDraft,
    CheckpointDraft,
    checkpoint_draft_schema,
)

FIXTURES = Path(__file__).absolute().parents[4] / 'contracts/supervision/tests/fixtures'


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


def test_exact_decimal_occurrence_and_profile_are_explicit():
    data = draft()
    parsed = CheckpointDraft.model_validate_json(json.dumps(data))
    assert parsed.candidate.changes[0].proposed.value == '0.123456789012345678901'
    assert parsed.candidate.changes[0].target.occurrences[0].index == 3
    assert checkpoint_draft_schema().schema_id == 'planning.checkpoint-draft'
    with pytest.raises(ValueError):
        CampaignDraft.model_validate_json(json.dumps(data))
    old = json.loads((FIXTURES / 'capture-adjustment.json').read_bytes())
    with pytest.raises(ValueError):
        CheckpointDraft.model_validate_json(json.dumps(old))
    old['schema_version'] = '2'
    with pytest.raises(ValueError):
        CheckpointDraft.model_validate_json(json.dumps(old))


@pytest.mark.parametrize('alteration', ['float', 'authority', 'extra', 'static_target', 'empty'])
def test_unversioned_or_broad_adjustment_shapes_reject(alteration):
    data = draft()
    change = data['candidate']['changes'][0]
    if alteration == 'float':
        change['proposed']['value'] = 0.5
    elif alteration == 'authority':
        data['authority'] = 'accepted'
    elif alteration == 'extra':
        change['schema_ref'] = {'version': '1'}
    elif alteration == 'static_target':
        change['target'] = {'scope_path': ['search'], 'node_id': 'pack'}
    else:
        data['candidate']['changes'] = []
    with pytest.raises(ValueError):
        CheckpointDraft.model_validate_json(json.dumps(data))


