"""Public materialization proposals bind exact checkpoint identity before pure selection."""

import json

import pytest
from amphora_campaign_runtime.supervision_effects import scalar_digest
from amphora_campaign_runtime.supervision_effects.proposal import select_fields
from amphora_contracts_planning import CheckpointDraft

from ..supervision_checkpoints.test_values import binding
from .test_selection import original, path


def proposal(seed):
    return {'schema_version': '2', 'authority': 'proposal_only', 'scientific_authority': 'not_established',
        'action': 'propose_campaign', 'rationale': 'Synthetic scalar selection', 'decision_scope': 'd' * 64,
        'candidate': {'kind': 'materialization_adjustment', 'cut': seed.footprint().cut.model_dump(mode='json'),
            'checkpoint_seed_sha256': seed.sha256, 'changes': [{'target': path(seed).model_dump(mode='json'),
                'field_name': 'a', 'previous_value_sha256': scalar_digest(binding().value),
                'proposed': {'kind': 'integer', 'value': 2}}], 'expected_evidence': []},
        'evidence_requests': [], 'alternatives': [], 'unresolved': []}


def test_public_profile_selects_only_original_concrete_occurrence():
    seed = original(nested=True)
    selected = select_fields(seed, CheckpointDraft.model_validate_json(json.dumps(proposal(seed))))
    assert selected.resolve((binding(),)) == (binding(2),)


@pytest.mark.parametrize('case,reason', [('seed', 'selection_proposal_seed'), ('cut', 'selection_proposal_seed'),
    ('multiple', 'selection_multiple_occurrences'), ('abstain', 'selection_materialization_proposal_required')])
def test_no_cross_seed_cut_or_occurrence_acceptance(case, reason):
    seed = original(nested=True)
    data = proposal(seed)
    if case == 'seed':
        data['candidate']['checkpoint_seed_sha256'] = 'e' * 64
    elif case == 'cut':
        data['candidate']['cut']['revision'] += 1
    elif case == 'multiple':
        other = json.loads(json.dumps(data['candidate']['changes'][0]))
        other['target']['occurrences'][0]['index'] = 1
        data['candidate']['changes'].append(other)
    else:
        data.update(action='abstain', candidate=None)
    with pytest.raises(ValueError, match=reason):
        select_fields(seed, CheckpointDraft.model_validate_json(json.dumps(data)))
