"""New profile traverses the production capture parser without widening old output."""

import json

import pytest
from amphora_agent_planning.campaign_output import CampaignOutput
from amphora_agent_planning.campaign_output.checkpoint import CheckpointOutput
from amphora_agent_planning.context import AttemptBinding
from amphora_agent_planning.persistence.records import verified_observation
from amphora_agent_planning.providers import observe
from amphora_agent_planning.providers.wire import observation_document
from amphora_contracts_planning import checkpoint_draft_schema

from ..context.test_snapshot import bind
from ..providers.test_task_output import Response
from .test_output import output, request


def checkpoint_request():
    data = request('adjustment').document().model_dump(mode='json')
    data['context']['output_schema'] = checkpoint_draft_schema().model_dump(mode='json')
    return bind(data)


def checkpoint_output():
    data = output('adjustment')
    data['schema_version'] = '2'
    data['candidate'].update(kind='materialization_adjustment', checkpoint_seed_sha256='b' * 64,
        changes=[{'target': {'schema_version': '2', 'node_id': 'pack', 'occurrences': []}, 'field_name': 'a',
                  'previous_value_sha256': 'c' * 64, 'proposed': {'kind': 'number', 'value': '0.1234567890123456789'}}])
    return data


def test_checkpoint_capture_reconstructs_exact_typed_proposal():
    snapshot = checkpoint_request()
    binding = AttemptBinding(snapshot, 1)
    raw = json.dumps(checkpoint_output(), indent=2).encode()
    observed = observe(binding, Response(raw))
    wire = observed.document()
    assert wire.status == 'proposed'
    assert wire.proposal == CheckpointOutput.parse(raw, snapshot).proposal()
    assert verified_observation(binding, observed) == observed
    assert observation_document(observed.canonical) == wire
    with pytest.raises(ValueError, match='campaign_output_profile'):
        CampaignOutput.parse(raw, snapshot)


@pytest.mark.parametrize('case,reason', [
    ('duplicate', 'checkpoint_duplicate_field'), ('cut', 'checkpoint_adjustment_cut'),
    ('empty', 'campaign_missing_candidate'), ('purpose', 'checkpoint_output_purpose'),
])
def test_checkpoint_candidate_boundaries(case, reason):
    data = checkpoint_output()
    snapshot = checkpoint_request()
    if case == 'duplicate':
        data['candidate']['changes'] *= 2
    elif case == 'cut':
        data['candidate']['cut']['revision'] += 1
    elif case == 'empty':
        data['candidate'] = None
    else:
        changed = snapshot.document().model_dump(mode='json')
        changed['purpose'] = 'campaign_proposal'
        snapshot = bind(changed)
    with pytest.raises(ValueError, match=reason):
        CheckpointOutput.parse(json.dumps(data).encode(), snapshot)


@pytest.mark.parametrize('name', ['abstain', 'evidence', 'future'])
def test_nonadjustment_actions_stay_proposals(name):
    data = output(name)
    data['schema_version'] = '2'
    snapshot = checkpoint_request()
    assert CheckpointOutput.parse(json.dumps(data).encode(), snapshot).document().action == data['action']
