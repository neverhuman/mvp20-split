import json

import pytest
from amphora_contracts_core import Scope
from amphora_agent_planning.access import Principal
from amphora_agent_planning.curation_intake import CurationCommand, FulfillmentCommand


def request():
    scope = {'tenant_id': 'internal', 'project_id': 'demo'}
    return {'encoding': 'amphora-command-v2', 'identity': {'command_family': 'planning.curate_campaign',
        'command_id': 'intent-1', 'actor_id': 'owner', 'scope': scope}, 'payload': {
        'direction': 'Improve the next campaign', 'policy_id': 'synthetic', 'context': {
            'predecessor': {'run_id': 'previous', 'plan_sha256': 'a' * 64, 'revision': 1},
            'draft': {'scope': scope, 'draft_id': 'original', 'revision': 1, 'content_sha256': 'b' * 64},
            'knowledge': [], 'questions': [], 'needs': [], 'artifacts': []}}}


def principal(actor='owner', project='demo', actions=('record_curations', 'read_curations')):
    return Principal(actor, Scope(tenant_id='internal', project_id=project), frozenset(actions))


def bind(raw=None, who=None, policies=('synthetic',)):
    return CurationCommand.bind(who or principal(), json.dumps(raw or request()), policies)


def test_original_slot_and_reconciliation():
    original = bind()
    assert original.reconcile(original.command.canonical_bytes) == original.curation_id
    changed = request()
    changed['payload']['direction'] = 'Try a different graph'
    revision = bind(changed)
    assert revision.curation_id == original.curation_id
    with pytest.raises(ValueError, match='curation_command_conflict'):
        revision.reconcile(original.command.canonical_bytes)


@pytest.mark.parametrize('who', [principal(actor='other'), principal(project='other'),
                                principal(actions=('record_requests', 'read_attempts')),
                                principal(actions=('read_curations',))])
def test_scoped_authority_is_independent_of_wire_identity(who):
    with pytest.raises(PermissionError): bind(who=who)


def test_operator_policy_not_client_authority():
    with pytest.raises(ValueError, match='curation_policy_unavailable'): bind(policies=())


def test_read_only_recovery_needs_no_write_grant():
    value = bind()
    value.require_read(principal(actions=('read_curations',)))
    for who in (principal(actor='other'), principal(project='other'), principal(actions=('record_curations',))):
        with pytest.raises(PermissionError): value.require_read(who)


@pytest.mark.parametrize('kind,id_key', [('questions', 'question_id'), ('needs', 'need_id')])
def test_conflicting_selected_revisions_reject(kind, id_key):
    raw = request()
    pin = {'scope': raw['identity']['scope'], id_key: 'same', 'revision': 1}
    raw['payload']['context'][kind] = [pin, {**pin, 'revision': 2}]
    with pytest.raises(ValueError, match='duplicate_curation_'): bind(raw)


def fulfillment():
    scope = request()['identity']['scope']
    return {'encoding': 'amphora-command-v2', 'identity': {**request()['identity'],
        'command_family': 'planning.fulfill_capability'}, 'payload': {
        'request': {'scope': scope, 'request_id': 'gap'}, 'release': {
            'tool': {'capability_id': 'combine', 'release': '1.0.0', 'image_sha256': 'a' * 64,
                     'contract_version': '1'}, 'descriptor_sha256': 'b' * 64,
            'input_schemas': [], 'output_schemas': [], 'checkpoint_schema': None},
        'acceptance_evidence': [{'artifact_id': 'proof', 'scope': scope, 'sha256': 'c' * 64,
            'media_type': 'application/json', 'size_bytes': 10,
            'schema_ref': {'schema_id': 'proof', 'version': '1', 'sha256': 'd' * 64}}]}}


def test_fulfillment_requires_separate_write_and_read_authority():
    raw = json.dumps(fulfillment())
    with pytest.raises(PermissionError): FulfillmentCommand.bind(principal(), raw)
    value = FulfillmentCommand.bind(principal(actions=('fulfill_capabilities',)), raw)
    value.reconcile(value.command.canonical_bytes)
    value.require_read(principal(actions=('read_capabilities',)))
    with pytest.raises(PermissionError): value.require_read(principal())
    changed = fulfillment()
    changed['payload']['release']['descriptor_sha256'] = 'e' * 64
    with pytest.raises(ValueError, match='fulfillment_command_conflict'):
        value.reconcile(json.dumps(changed))
    duplicated = fulfillment()
    duplicated['payload']['acceptance_evidence'] *= 2
    with pytest.raises(ValueError, match='duplicate_fulfillment_evidence'):
        FulfillmentCommand.bind(principal(actions=('fulfill_capabilities',)), json.dumps(duplicated))
