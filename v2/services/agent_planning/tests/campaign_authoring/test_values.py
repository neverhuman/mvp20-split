"""Public owner acknowledgements must match exact original command and content."""

import json
from dataclasses import replace

import pytest
from amphora_agent_planning.campaign_authoring import (
    AuthoringOutcome,
    AuthoringPlan,
    AuthoringRequest,
)
from amphora_agent_planning.campaign_decisions import CampaignDecisionReview
from amphora_contracts_graph_runtime import (
    DraftCommandReceipt,
    DraftRevision,
    DraftValidation,
)

from ..campaign_decisions.test_policy import fixture


def plan(**kwargs):
    proposal, declaration, budget = fixture(**kwargs)
    return AuthoringPlan.bind(CampaignDecisionReview.bind(proposal, declaration, budget), budget,
                             owner_id='runtime-fixture', actor_id='planning-agent')


@pytest.fixture(scope='module')
def authoring():
    return plan()


def receipt(request, status='accepted', **changes):
    command = request.command()
    saving = command.identity.command_family == 'definition.save'
    payload = request.payload()
    outcome = {'status': status, 'binding': {'identity': command.identity.model_dump(mode='json'),
                'request_sha256': command.sha256, 'operation_id': 'operation-1'}}
    if status == 'accepted':
        outcome['committed'] = {'kind': 'draft_revision' if saving else 'draft_validation',
            'object_id': payload.draft_id if saving else 'validation-1', 'revision': 1,
            'content_sha256': 'a' * 64}
    elif status == 'rejected':
        outcome['reason_code'] = 'revision_conflict'
    outcome.update(changes)
    return DraftCommandReceipt.model_validate_json(json.dumps({'outcome': outcome}))


def saved(authoring):
    request = authoring.save()
    payload = request.payload()
    readback = DraftRevision(scope=payload.definition.scope, head={
        'draft_id': payload.draft_id, 'revision': 1, 'content_sha256': 'a' * 64, 'title': payload.title},
        parent_revision=0, definition=payload.definition)
    return AuthoringOutcome.bind(request, receipt(request), readback)


def validation(request, *, valid=True):
    command, payload = request.command(), request.payload()
    return DraftValidation(scope=command.identity.scope, validation_id='validation-1', draft_id=payload.draft_id,
        revision=payload.revision, content_sha256=payload.content_sha256, universe_sha256='b' * 64,
        structurally_valid=valid, plan_sha256='c' * 64 if valid else None, findings=(),
        pending_checks=('current_eligibility', 'activation'))


def test_exact_save_and_validate_use_distinct_command_profiles(authoring):
    result = saved(authoring)
    assert result.status == 'saved'
    request = result.request
    assert request.command().profile == 'amphora-command-v2'
    assert request.payload().expected_revision == 0
    verify = authoring.validate(result)
    assert verify.command().profile == 'amphora-command-v1'
    assert verify.payload().content_sha256 == result.readback.head.content_sha256
    assert verify.command().identity.command_id != request.command().identity.command_id
    assert authoring.save() == request and authoring.validate(result) == verify


def test_changed_generated_payload_retains_slot_for_owner_conflict(authoring):
    changed = plan(change=lambda value: value['candidate'].update(title='A changed proposal'))
    before, after = authoring.save(), changed.save()
    assert before.command().identity == after.command().identity
    assert before.payload().draft_id == after.payload().draft_id
    assert before.command().sha256 != after.command().sha256


@pytest.mark.parametrize('status', ['pending', 'rejected'])
def test_nonaccepted_receipt_is_not_a_saved_draft(authoring, status):
    request = authoring.save()
    result = AuthoringOutcome.bind(request, receipt(request, status))
    assert result.status == status and result.readback is None
    with pytest.raises(ValueError, match='authoring_saved_readback_required'):
        authoring.validate(result)
    with pytest.raises(ValueError, match='authoring_unaccepted_readback'):
        AuthoringOutcome.bind(request, result.receipt, saved(authoring).readback)


def test_accepted_without_readback_is_not_ready_for_validation(authoring):
    request = authoring.save()
    result = AuthoringOutcome.bind(request, receipt(request))
    assert result.status == 'awaiting_readback'
    with pytest.raises(ValueError, match='authoring_saved_readback_required'):
        authoring.validate(result)


@pytest.mark.parametrize('valid', [True, False])
def test_accepted_validation_preserves_structural_result_and_pending_authority(authoring, valid):
    request = authoring.validate(saved(authoring))
    outcome = AuthoringOutcome.bind(request, receipt(request), validation(request, valid=valid))
    assert outcome.status == ('compiled' if valid else 'structural_invalid')
    assert outcome.readback.scientific_acceptance == 'not_established'
    assert outcome.readback.pending_checks == ('current_eligibility', 'activation')


@pytest.mark.parametrize('field', ['request_sha256', 'actor_id', 'command_id', 'scope'])
def test_foreign_receipts_are_rejected(authoring, field):
    request = authoring.save()
    raw = receipt(request).model_dump(mode='json')
    binding = raw['outcome']['binding']
    if field == 'request_sha256':
        binding[field] = 'f' * 64
    elif field == 'scope':
        binding['identity']['scope']['project_id'] = 'foreign'
    else:
        binding['identity'][field] = 'foreign'
    with pytest.raises(ValueError, match='authoring_receipt_binding'):
        AuthoringOutcome.bind(request, DraftCommandReceipt.model_validate_json(json.dumps(raw)))


@pytest.mark.parametrize(('field', 'value', 'error'), [
    ('kind', 'draft_validation', 'authoring_commit_kind'),
    ('object_id', 'other', 'authoring_commit_identity'),
    ('revision', 2, 'authoring_commit_revision'),
])
def test_save_commit_must_be_the_expected_new_draft(authoring, field, value, error):
    request = authoring.save()
    raw = receipt(request).model_dump(mode='json')
    raw['outcome']['committed'][field] = value
    with pytest.raises(ValueError, match=error):
        AuthoringOutcome.bind(request, DraftCommandReceipt.model_validate_json(json.dumps(raw)))


@pytest.mark.parametrize('field', ['title', 'definition', 'digest'])
def test_save_readback_must_match_complete_original_content(authoring, field):
    result = saved(authoring)
    raw = result.readback.model_dump(mode='json')
    if field == 'definition':
        raw['definition']['revision'] = 2
    elif field == 'title':
        raw['head']['title'] = 'Unrequested title'
    else:
        raw['head']['content_sha256'] = 'f' * 64
    with pytest.raises(ValueError, match='authoring_saved_content|authoring_readback_commit'):
        AuthoringOutcome.bind(result.request, result.receipt, DraftRevision.model_validate_json(json.dumps(raw)))


def test_forged_plan_result_or_command_cannot_be_reused(authoring):
    with pytest.raises(ValueError, match='authoring_review_binding'):
        replace(authoring, review=replace(authoring.review, next_step='abstained')).save()
    request = authoring.save()
    with pytest.raises(ValueError, match='authoring_request_canonical'):
        replace(request, canonical=b' ' + request.canonical).command()
    result = saved(authoring)
    with pytest.raises(ValueError, match='authoring_saved_readback_required'):
        authoring.validate(replace(result, status='compiled'))
    assert AuthoringRequest.bind(request.owner_id, request.command()) == request


def test_adjustment_cannot_be_dispatched_as_a_draft():
    with pytest.raises(ValueError, match='authoring_future_required'):
        plan(name='adjustment')


@pytest.mark.parametrize('number', [1.0, 1.25, 1e-8, -0.0])
def test_authored_numbers_use_versioned_command_encoding(number):
    def change(value):
        value['candidate']['definition']['body'] = {
            'inputs': [], 'outputs': [{'name': 'result', 'value_type': {'kind': 'scalar', 'scalar': 'number', 'unit': '1'}}],
            'nodes': [{'kind': 'finish', 'node_id': 'finish', 'outputs': [
                {'port': 'result', 'source': {'kind': 'number', 'value': number, 'unit': '1'}}]}], 'edges': []}
    request = plan(change=change).save()
    assert request.command().profile == 'amphora-command-v2'
    assert request.payload().definition.body.nodes[0].outputs[0].source.value == number
    if number == 0:
        assert b'-0.0' not in request.canonical


@pytest.mark.parametrize('field', ['validation_id', 'draft_id', 'content_sha256', 'revision', 'scope'])
def test_validation_readback_is_exactly_pinned(authoring, field):
    request = authoring.validate(saved(authoring))
    raw = validation(request).model_dump(mode='json')
    if field == 'scope':
        raw[field]['project_id'] = 'foreign'
    elif field == 'revision':
        raw[field] = 2
    else:
        raw[field] = 'f' * 64 if field == 'content_sha256' else 'foreign'
    with pytest.raises(ValueError, match='authoring_readback_scope|authoring_readback_commit'):
        AuthoringOutcome.bind(request, receipt(request), DraftValidation.model_validate_json(json.dumps(raw)))


def test_validation_receipt_must_refer_to_original_content(authoring):
    request = authoring.validate(saved(authoring))
    raw = receipt(request).model_dump(mode='json')
    raw['outcome']['committed']['content_sha256'] = 'f' * 64
    with pytest.raises(ValueError, match='authoring_commit_content'):
        AuthoringOutcome.bind(request, DraftCommandReceipt.model_validate_json(json.dumps(raw)))


def test_owner_configuration_is_part_of_the_slot(authoring):
    changed = AuthoringPlan.bind(authoring.review, authoring.budget, owner_id='replacement-owner', actor_id=authoring.actor_id)
    assert changed.save().command().identity != authoring.save().command().identity
    # A later journal must prohibit replacing configuration of an existing slot;
    # these pure values alone neither authenticate nor authorize either owner.
