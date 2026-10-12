import json

import pytest
from amphora_contracts_campaign_launch import parse_launch
from amphora_contracts_commands import CommandEncodingError
from amphora_contracts_draft_successor import parse_draft_successor
from amphora_contracts_campaign_successor_launch import parse_successor_launch


def request():
    identity = {'scope': {'tenant_id': 'internal', 'project_id': 'demo'},
                'actor_id': 'owner', 'command_family': 'campaign.launch_successor', 'command_id': 'next'}
    return {'encoding': 'amphora-command-v2', 'identity': identity, 'payload': {
        'profile': {'profile_id': 'synthetic', 'version': '1', 'sha256': 'a' * 64},
        'admission': {'encoding': 'amphora-command-v2',
            'identity': {**identity, 'command_family': 'graph.admit_draft_successor'}, 'payload': {
                'plan_sha256': 'b' * 64, 'inputs': [], 'budget': {'limit': 3},
                'draft': {'draft_id': 'draft', 'revision': 2, 'content_sha256': 'c' * 64,
                          'validation_id': 'validated', 'universe_sha256': 'd' * 64},
                'predecessor': {'run_id': 'parent', 'plan_sha256': 'e' * 64, 'revision': 4},
                'carried': [{'target_port': 'value', 'source': {'kind': 'run_output', 'port': 'value'},
                             'expected_value_sha256': 'f' * 64}]}}}}


def test_exact_original_runtime_command_and_no_fresh_fallback():
    raw = request()
    command, admission = parse_successor_launch(json.dumps(raw))
    assert admission == parse_draft_successor(json.dumps(raw['payload']['admission']))
    assert parse_successor_launch(command.canonical_bytes) == (command, admission)
    with pytest.raises(CommandEncodingError): parse_launch(json.dumps(raw))


@pytest.mark.parametrize('case', ['scope', 'actor', 'id', 'family', 'fresh', 'outer_encoding',
                                 'inner_encoding', 'draft', 'predecessor', 'carried', 'duplicate'])
def test_identity_and_predecessor_cannot_be_dropped(case):
    raw = request()
    admission = raw['payload']['admission']
    if case == 'scope': admission['identity']['scope'] = {'tenant_id': 'other', 'project_id': 'demo'}
    if case == 'actor': admission['identity']['actor_id'] = 'other'
    if case == 'id': admission['identity']['command_id'] = 'other'
    if case == 'family': raw['identity']['command_family'] = 'campaign.launch'
    if case == 'fresh': admission['identity']['command_family'] = 'graph.admit_draft'
    if case == 'outer_encoding': del raw['encoding']
    if case == 'inner_encoding': del admission['encoding']
    if case in ('draft', 'predecessor', 'carried'): del admission['payload'][case]
    if case == 'duplicate': admission['payload']['carried'] *= 2
    with pytest.raises(CommandEncodingError): parse_successor_launch(json.dumps(raw))


@pytest.mark.parametrize('raw', ['{"payload":{},"payload":{}}', ' ' * 262145], ids=['duplicate', 'oversize'])
def test_closed_raw_boundary(raw):
    with pytest.raises(CommandEncodingError): parse_successor_launch(raw)
