import json

import pytest
from amphora_contracts_core import Scope
from amphora_deployment.campaign_launch.intent import LaunchError, LaunchIntent


def body():
    identity = {'command_family': 'campaign.launch', 'command_id': 'launch-1',
        'actor_id': 'researcher', 'scope': {'tenant_id': 'internal', 'project_id': 'demo'}}
    return {'encoding': 'amphora-command-v2', 'identity': identity, 'payload': {
        'profile': {'profile_id': 'scientific', 'version': '1', 'sha256': 'd' * 64},
        'admission': {'identity': {**identity, 'command_family': 'graph.admit_draft'},
            'payload': {'plan_sha256': 'a' * 64, 'inputs': [],
                'budget': {'limit': 8, 'max_attempts_per_activation': 2},
                'draft': {'draft_id': 'draft', 'revision': 1, 'content_sha256': 'b' * 64,
                    'validation_id': 'validation', 'universe_sha256': 'c' * 64}}}}}


def intent():
    return LaunchIntent.parse(json.dumps(body()).encode())


def test_grant_must_match_actor_and_scope_even_for_well_formed_requests():
    value = intent()
    value.authorize('researcher', Scope(tenant_id='internal', project_id='demo'))
    for actor, project in [('other', 'demo'), ('researcher', 'other')]:
        with pytest.raises(LaunchError, match='launch_scope_denied'):
            value.authorize(actor, Scope(tenant_id='internal', project_id=project))


def test_replay_fingerprint_changes_with_profile_without_mutating_original():
    first = intent()
    changed = body()
    changed['payload']['profile']['sha256'] = 'e' * 64
    second = LaunchIntent.parse(json.dumps(changed).encode())
    assert first.key == second.key
    assert first.request.sha256 != second.request.sha256
    assert first.admission.sha256 == second.admission.sha256
    assert first.profile.sha256 == 'd' * 64
