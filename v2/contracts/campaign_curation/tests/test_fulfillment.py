import json

import pytest
from amphora_contracts_campaign_curation import parse_fulfillment
from amphora_contracts_commands import CommandEncodingError


def request():
    scope = {'tenant_id': 'internal', 'project_id': 'demo'}
    return {'encoding': 'amphora-command-v2', 'identity': {'command_family': 'planning.fulfill_capability',
        'command_id': 'fulfillment-1', 'actor_id': 'owner', 'scope': scope}, 'payload': {
        'request': {'scope': scope, 'request_id': 'gap-1'},
        'release': {'tool': {'capability_id': 'combine', 'release': '1.0.0', 'image_sha256': 'a' * 64,
                           'contract_version': '1'}, 'descriptor_sha256': 'b' * 64, 'input_schemas': [],
                    'output_schemas': [], 'checkpoint_schema': None},
        'acceptance_evidence': [{'artifact_id': 'acceptance', 'scope': scope, 'sha256': 'c' * 64,
            'media_type': 'application/json', 'size_bytes': 120,
            'schema_ref': {'schema_id': 'acceptance', 'version': '1', 'sha256': 'd' * 64}}]}}


def test_fulfillment_has_an_original_canonical_receipt_identity():
    command = parse_fulfillment(json.dumps(request()))
    assert parse_fulfillment(command.canonical_bytes) == command


@pytest.mark.parametrize('case', ['request_scope', 'evidence_scope', 'no_evidence', 'no_release',
                                 'status', 'encoding', 'family'])
def test_model_or_unbound_release_cannot_self_fulfill(case):
    raw = request()
    foreign = {'tenant_id': 'other', 'project_id': 'demo'}
    if case == 'request_scope': raw['payload']['request']['scope'] = foreign
    if case == 'evidence_scope': raw['payload']['acceptance_evidence'][0]['scope'] = foreign
    if case == 'no_evidence': raw['payload']['acceptance_evidence'] = []
    if case == 'no_release': del raw['payload']['release']
    if case == 'status': raw['payload']['status'] = 'verified'
    if case == 'encoding': del raw['encoding']
    if case == 'family': raw['identity']['command_family'] = 'planning.curate_campaign'
    with pytest.raises(CommandEncodingError): parse_fulfillment(json.dumps(raw))
