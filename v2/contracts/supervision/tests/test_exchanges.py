"""Closed recording commands and owner readbacks cannot promote model authority."""

import hashlib
import json
from pathlib import Path

import pytest
from amphora_contracts_commands import CommandEncodingError
from amphora_contracts_supervision import (
    SupervisionDecision,
    SupervisionResponse,
    parse_supervision_command,
)
from pydantic import ValidationError

FIXTURES = Path(__file__).parent / 'fixtures'


def envelope(family='runtime.supervision.respond'):
    request = json.loads((FIXTURES / 'request.json').read_bytes())
    response = json.loads((FIXTURES / 'response-adjustment.json').read_bytes())
    payload = {'planning.supervision.request': request, 'runtime.supervision.respond': response,
               'runtime.supervision.cancel': {'schema_version': '1', 'cancellation_id': 'cancel-1',
                  'reference': request['reference'], 'request_sha256': response['request_sha256'],
                  'reason_code': 'declared_deadline'}}[family]
    return {'encoding': 'amphora-command-v2', 'identity': {'schema_version': '1', 'command_family': family,
        'command_id': 'command-1', 'scope': request['reference']['scope'],
        'actor_id': request['planning_request']['actor_id']}, 'payload': payload}


@pytest.mark.parametrize('family', ['planning.supervision.request', 'runtime.supervision.respond',
                                    'runtime.supervision.cancel'])
def test_exact_numeric_command_replay(family):
    command = parse_supervision_command(family, json.dumps(envelope(family)))
    assert command.profile == 'amphora-command-v2'
    assert parse_supervision_command(family, command.canonical_bytes) == command
    label = {'planning.supervision.request': 'request', 'runtime.supervision.respond': 'response',
             'runtime.supervision.cancel': 'cancel'}[family]
    literal = (FIXTURES / f'{label}-command.json').read_bytes()
    pins = json.loads((FIXTURES / 'command-pins.json').read_bytes())
    assert command.canonical_bytes == literal and command.sha256 == pins[label]
    assert hashlib.sha256(literal).hexdigest() == pins[label]


@pytest.mark.parametrize('mutation,reason', [
    (lambda x: x.pop('encoding'), 'invalid_encoding'),
    (lambda x: x['identity'].update(command_family='unregistered'), 'family_mismatch'),
    (lambda x: x['identity']['scope'].update(project_id='foreign'), 'scope_mismatch'),
    (lambda x: x['payload'].update(accepted=True), 'schema_invalid'),
])
def test_command_rejects_wrong_profile_scope_family_or_acceptance_input(mutation, reason):
    value = envelope()
    mutation(value)
    with pytest.raises(CommandEncodingError, match=reason):
        parse_supervision_command('runtime.supervision.respond', json.dumps(value))


def test_request_actor_unknown_family_and_duplicate_key_reject():
    value = envelope('planning.supervision.request')
    value['identity']['actor_id'] = 'other'
    with pytest.raises(CommandEncodingError, match='actor_mismatch'):
        parse_supervision_command('planning.supervision.request', json.dumps(value))
    with pytest.raises(CommandEncodingError, match='unknown_family'):
        parse_supervision_command('runtime.supervision.accept', '{}')
    with pytest.raises(CommandEncodingError, match='duplicate_key'):
        parse_supervision_command('runtime.supervision.respond', '{"identity":{},"identity":{}}')


@pytest.mark.parametrize('name', ['abstain', 'evidence', 'adjustment', 'unknown'])
def test_observations_keep_proposal_only_or_explicit_unknown_usage(name):
    response = SupervisionResponse.model_validate_json((FIXTURES / f'response-{name}.json').read_bytes())
    assert SupervisionResponse.model_validate_json(response.model_dump_json()) == response
    if name == 'unknown':
        assert response.observation.usage.accounting_units is None and response.capture is None
    else:
        payload = json.loads(response.observation.proposal.payload_json)
        assert payload['authority'] == 'proposal_only' and payload['scientific_authority'] == 'not_established'


@pytest.mark.parametrize('outcome', [
    {'status': 'pending', 'stage': 'requested'}, {'status': 'pending', 'stage': 'dispatched'},
    {'status': 'pending', 'stage': 'proposed'},
    {'status': 'accepted', 'source': 'fallback', 'effect': {'kind': 'continued'}},
    *({'status': status, 'source': 'policy', 'reason_code': 'bounded_outcome'}
      for status in ('rejected', 'stale', 'expired', 'failed', 'cancelled')),
])
def test_decision_readback_keeps_distinct_terminal_and_pending_states(outcome):
    request = json.loads((FIXTURES / 'request.json').read_bytes())
    record = SupervisionDecision.model_validate_json(json.dumps({'reference': request['reference'],
        'revision': 1, 'request_sha256': 'a' * 64, 'outcome': outcome}))
    assert record.outcome.status == outcome['status']
    response = json.loads((FIXTURES / 'response-abstain.json').read_bytes())
    response['decision'] = record.model_dump(mode='json')
    with pytest.raises(ValidationError):
        SupervisionResponse.model_validate_json(json.dumps(response))


@pytest.mark.parametrize('kind', ['adjusted_inputs', 'future_campaign', 'evidence_request', 'abstained'])
def test_accepted_effect_shapes_remain_typed_owner_readbacks(kind):
    request = json.loads((FIXTURES / 'request.json').read_bytes())
    response = json.loads((FIXTURES / 'response-adjustment.json').read_bytes())
    if kind == 'adjusted_inputs':
        effect = {'kind': kind, 'changes': [{'target': {'schema_version': '2', 'node_id': 'evaluate', 'occurrences': []},
            'input_name': 'temperature', 'previous_value_sha256': 'b' * 64,
            'value': {'kind': 'number', 'value': 1.25, 'unit': '1'}}]}
    else:
        effect = {'kind': kind, 'proposal': response['capture'], 'content_sha256': 'b' * 64}
    document = {'reference': request['reference'], 'revision': 1, 'request_sha256': 'a' * 64,
                'outcome': {'status': 'accepted', 'source': 'model', 'effect': effect}}
    assert SupervisionDecision.model_validate_json(json.dumps(document)).outcome.effect.kind == kind
    if kind == 'adjusted_inputs':
        for value in (True, float('inf'), '1.25'):
            effect['changes'][0]['value']['value'] = value
            with pytest.raises(ValidationError):
                SupervisionDecision.model_validate_json(json.dumps(document))
