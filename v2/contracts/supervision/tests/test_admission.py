"""Exact policy identity and closed predecessor admission namespace."""

import json

import pytest
from amphora_contracts_commands import CommandEncodingError
from amphora_contracts_graph_runtime import parse_graph_command
from amphora_contracts_supervision import parse_supervised_admission


def request():
    return {'encoding': 'amphora-command-v2', 'identity': {
        'scope': {'tenant_id': 'test', 'project_id': 'policy'}, 'actor_id': 'owner',
        'command_family': 'graph.admit_supervised', 'command_id': 'admission'},
        'payload': {'admission': {'plan_sha256': 'a' * 64, 'inputs': [], 'budget': {'limit': 2}},
                    'policy_sha256': 'b' * 64}}


def test_exact_policy_is_bound_into_command_identity():
    raw = request()
    command = parse_supervised_admission(json.dumps(raw))
    assert parse_supervised_admission(command.canonical_bytes) == command
    raw['payload']['policy_sha256'] = 'c' * 64
    assert parse_supervised_admission(json.dumps(raw)).sha256 != command.sha256
    with pytest.raises(CommandEncodingError, match='unknown_family'):
        parse_graph_command('graph.admit_supervised', command.canonical_bytes)


@pytest.mark.parametrize('change', ['encoding', 'family', 'policy', 'extra', 'unbounded'])
def test_invalid_admission_rejects(change):
    raw = request()
    if change == 'encoding':
        raw.pop('encoding')
    elif change == 'family':
        raw['identity']['command_family'] = 'graph.admit'
    elif change == 'policy':
        raw['payload']['policy_sha256'] = 'latest'
    elif change == 'extra':
        raw['payload']['policy'] = {'instructions': 'arbitrary'}
    else:
        raw['payload']['admission']['limits'] = {'max_activations': 100001}
    with pytest.raises(CommandEncodingError):
        parse_supervised_admission(json.dumps(raw))


@pytest.mark.parametrize('collection', [False, True])
def test_input_artifact_scope_cannot_escape_admission(collection):
    raw = request()
    artifact = {'kind': 'artifact', 'representation': 'fixture', 'unit': '1', 'artifact': {
        'artifact_id': 'input', 'scope': {'tenant_id': 'other', 'project_id': 'policy'},
        'sha256': 'd' * 64, 'schema_ref': {'schema_id': 'fixture', 'version': '1', 'sha256': 'e' * 64},
        'media_type': 'application/json', 'size_bytes': 2}}
    raw['payload']['admission']['inputs'] = [{'port': 'input', 'value':
        {'kind': 'collection', 'items': [artifact]} if collection else artifact}]
    with pytest.raises(CommandEncodingError, match='scope_mismatch'):
        parse_supervised_admission(json.dumps(raw))
    artifact['artifact']['scope'] = raw['identity']['scope']
    assert parse_supervised_admission(json.dumps(raw))
