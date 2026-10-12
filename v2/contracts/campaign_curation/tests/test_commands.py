import copy
import json

import pytest
from amphora_contracts_commands import CommandEncodingError
from amphora_contracts_campaign_curation import parse_curation


def request():
    scope = {'tenant_id': 'internal', 'project_id': 'demo'}
    return {'encoding': 'amphora-command-v2', 'identity': {'command_family': 'planning.curate_campaign',
        'command_id': 'curation-1', 'actor_id': 'researcher', 'scope': scope}, 'payload': {
        'direction': 'Add a reviewed comparison step', 'policy_id': 'synthetic-demo', 'context': {
            'predecessor': {'run_id': 'previous', 'plan_sha256': 'a' * 64, 'revision': 2},
            'draft': {'scope': scope, 'draft_id': 'original', 'revision': 1, 'content_sha256': 'b' * 64},
            'knowledge': [], 'questions': [], 'needs': [], 'artifacts': []}}}


def test_canonical_replay_and_changed_intent_identity():
    raw = request()
    command = parse_curation(json.dumps(raw))
    assert parse_curation(command.canonical_bytes) == command
    changed = copy.deepcopy(raw)
    changed['payload']['direction'] = 'Add heating after convergence'
    other = parse_curation(json.dumps(changed))
    assert other.identity == command.identity
    assert other.sha256 != command.sha256  # journal must conflict, not schedule another call


@pytest.mark.parametrize('case', ['family', 'encoding', 'scope', 'revision', 'provider', 'budget',
                                 'prompt', 'schema', 'empty', 'long', 'unknown'])
def test_closed_intent_does_not_delegate_authority(case):
    raw = request()
    if case == 'family': raw['identity']['command_family'] = 'planning.supervise'
    if case == 'encoding': del raw['encoding']
    if case == 'scope': raw['payload']['context']['draft']['scope'] = {'tenant_id': 'other', 'project_id': 'demo'}
    if case == 'revision': raw['payload']['context']['draft']['revision'] = True
    if case in ('provider', 'budget', 'prompt', 'schema', 'unknown'): raw['payload'][case] = 'untrusted'
    if case == 'empty': raw['payload']['direction'] = ' \n '
    if case == 'long': raw['payload']['direction'] = 'x' * 4097
    with pytest.raises(CommandEncodingError): parse_curation(json.dumps(raw))


@pytest.mark.parametrize('raw', ['{"payload":{},"payload":{}}', ' ' * 262145,
                                '{"payload":NaN}', '[' * 65 + ']' * 65], ids=['duplicate', 'oversized', 'nonfinite', 'deep'])
def test_raw_body_bounds(raw):
    with pytest.raises(CommandEncodingError): parse_curation(raw)
