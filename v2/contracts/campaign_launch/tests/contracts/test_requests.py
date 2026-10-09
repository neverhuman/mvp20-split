import copy
import json

import pytest
from amphora_contracts_campaign_launch import LaunchRequest, parse_launch
from amphora_contracts_commands import CommandEncodingError
from amphora_contracts_graph_runtime import parse_graph_command


def request():
    identity = {'command_family': 'campaign.launch', 'command_id': 'launch-1',
        'actor_id': 'researcher', 'scope': {'tenant_id': 'internal', 'project_id': 'demo'}}
    admission = {'identity': {**identity, 'command_family': 'graph.admit_draft'}, 'payload': {
        'plan_sha256': 'a' * 64, 'inputs': [], 'budget': {'limit': 8, 'max_attempts_per_activation': 2},
        'draft': {'draft_id': 'draft', 'revision': 1, 'content_sha256': 'b' * 64,
            'validation_id': 'validation', 'universe_sha256': 'c' * 64}}}
    return {'encoding': 'amphora-command-v2', 'identity': identity, 'payload': {
        'profile': {'profile_id': 'scientific', 'version': '1', 'sha256': 'd' * 64}, 'admission': admission}}


def test_outer_normalization_preserves_exact_runtime_command_identity_and_hash():
    raw = request()
    launch, admission = parse_launch(json.dumps(raw))
    expected = parse_graph_command('graph.admit_draft', json.dumps(raw['payload']['admission']))
    assert admission == expected
    assert parse_launch(launch.canonical_bytes) == (launch, admission)
    assert LaunchRequest.model_validate_json(launch.canonical_bytes).identity.command_id == 'launch-1'


def test_numeric_runtime_admission_keeps_its_explicit_profile():
    raw = request()
    raw['payload']['admission']['encoding'] = 'amphora-command-v2'
    launch, admission = parse_launch(json.dumps(raw))
    assert admission.profile == 'amphora-command-v2'
    assert parse_launch(launch.canonical_bytes)[1].sha256 == admission.sha256


@pytest.mark.parametrize('mutation', ['scope', 'actor', 'command', 'family', 'extra', 'coerce', 'encoding'])
def test_untrusted_identity_or_envelope_cannot_change_authority(mutation):
    raw = copy.deepcopy(request())
    identity = raw['payload']['admission']['identity']
    if mutation == 'scope': identity['scope'] = {**identity['scope'], 'project_id': 'other'}
    if mutation == 'actor': identity['actor_id'] = 'other'
    if mutation == 'command': identity['command_id'] = 'other'
    if mutation == 'family': identity['command_family'] = 'runtime.cancel'
    if mutation == 'extra': raw['payload']['executable'] = 'arbitrary'
    if mutation == 'coerce': raw['payload']['admission']['payload']['budget']['limit'] = '8'
    if mutation == 'encoding': del raw['encoding']
    with pytest.raises(CommandEncodingError): parse_launch(json.dumps(raw))


def test_duplicate_keys_and_oversized_inputs_fail_closed():
    with pytest.raises(CommandEncodingError): parse_launch('{"payload":{},"payload":{}}')
    with pytest.raises(CommandEncodingError): parse_launch(b' ' * 262145)
