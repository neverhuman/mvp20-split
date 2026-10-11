"""Exact compiler projection and fail-closed public reconstruction."""

import json
from dataclasses import replace

import pytest
from amphora_agent_planning.access import Principal
from amphora_agent_planning.campaign_dispatch import CompilerEffect, CompilerObservation, CompilerSelection
from amphora_agent_planning.campaign_eligibility import EligibilityConfiguration
from amphora_agent_planning.campaign_origin import OriginProjection
from amphora_agent_planning.campaign_origin.projection import MAX_RESPONSE_BYTES, digest
from amphora_agent_planning.campaign_context.records import canonical
from amphora_contracts_planning import CampaignOriginV2 as CampaignOrigin

from ..campaign_authoring.test_values import plan, saved, receipt


@pytest.fixture(scope='module')
def origin_inputs():
    authoring = plan(tools=True, research={})
    original = authoring.review.composition.evidence.proposal.attempt.request.document()
    principal = Principal(original.actor_id, original.reference.scope,
                          frozenset({'read_attempts', 'record_attempts'}))
    eligibility = EligibilityConfiguration.bind(owner_id='registry', actor_id='planning-agent', policy_sha256='e' * 64)
    selection = CompilerSelection.bind(principal, authoring, eligibility)
    effect = CompilerEffect.authoring(selection, principal, authoring, eligibility)
    accepted = saved(authoring)
    observation = CompilerObservation.bind(selection, effect, accepted.request, accepted.receipt, accepted.readback)
    return principal, selection, authoring, eligibility, observation


@pytest.fixture(scope='module')
def projection(origin_inputs):
    return OriginProjection.bind(*origin_inputs)


def test_exact_original_proposal_and_save(projection, origin_inputs):
    value = projection.document()
    assert OriginProjection.restore(projection.canonical, value.origin.draft) == projection
    assert value.origin.proposal.actor_id == origin_inputs[0].actor_id
    assert value.origin.save.receipt == origin_inputs[-1].outcome.receipt
    assert value.origin.tools
    assert value.origin.research.selection is not None
    assert value.origin.research.records
    assert value.origin.proposal.capture_publication == 'not_published'
    assert 'scientific_authority_not_established' in value.origin.limitations
    assert len(projection.canonical) < MAX_RESPONSE_BYTES


@pytest.mark.parametrize('field,value', [('draft_id', 'different'), ('revision', 2), ('content_sha256', '0' * 64)])
def test_no_head_or_similar_graph_fallback(projection, field, value):
    expected = projection.document().origin.draft.model_copy(update={field: value})
    with pytest.raises(ValueError, match='origin_draft_mismatch'):
        OriginProjection.restore(projection.canonical, expected)


def test_denied_producer_reconstruction(origin_inputs):
    principal, *rest = origin_inputs
    with pytest.raises(PermissionError):
        OriginProjection.bind(replace(principal, actions=frozenset()), *rest)


def test_read_origin_grant_does_not_grant_write_or_attempt_access(origin_inputs):
    principal = replace(origin_inputs[0], actor_id='viewer', actions=frozenset({'read_campaign_origin'}))
    principal.require('read_campaign_origin', principal.scope)
    for action in ('record_attempts', 'record_requests', 'read_attempts'):
        with pytest.raises(PermissionError):
            principal.require(action, principal.scope)


@pytest.mark.parametrize('status', ['pending', 'rejected'])
def test_pending_and_rejected_saves_have_no_origin(origin_inputs, status):
    principal, selection, authoring, eligibility, _ = origin_inputs
    effect = CompilerEffect.authoring(selection, principal, authoring, eligibility)
    request = authoring.save()
    observed = CompilerObservation.bind(selection, effect, request, receipt(request, status))
    with pytest.raises(ValueError, match='origin_saved_required'):
        OriginProjection.bind(principal, selection, authoring, eligibility, observed)


def test_accepted_without_readback_has_no_origin(origin_inputs):
    principal, selection, authoring, eligibility, _ = origin_inputs
    effect = CompilerEffect.authoring(selection, principal, authoring, eligibility)
    request = authoring.save()
    observed = CompilerObservation.bind(selection, effect, request, receipt(request))
    with pytest.raises(ValueError, match='origin_saved_required'):
        OriginProjection.bind(principal, selection, authoring, eligibility, observed)


@pytest.mark.parametrize('case', ['hash', 'scope', 'receipt', 'selection', 'extra', 'noncanonical', 'oversize'])
def test_invalid_public_chain_fails_closed(projection, case):
    value = json.loads(projection.canonical)
    expected = projection.document().origin.draft
    if case == 'hash':
        value['origin_sha256'] = '0' * 64
    elif case == 'scope':
        value['origin']['proposal']['context']['scope']['project_id'] = 'foreign'
    elif case == 'receipt':
        value['origin']['save']['receipt']['outcome']['committed']['content_sha256'] = '0' * 64
    elif case == 'selection':
        value['origin']['research']['selection']['request_sha256'] = '0' * 64
    elif case == 'extra':
        value['origin']['proposal']['prompt_text'] = 'must not be disclosed'
    if case in {'scope', 'receipt', 'selection'}:
        parsed = CampaignOrigin.model_validate_json(json.dumps(value))
        value['origin_sha256'] = digest(parsed.origin)
    raw = canonical(value)
    if case == 'noncanonical':
        raw += b'\n'
    if case == 'oversize':
        raw = b' ' * (MAX_RESPONSE_BYTES + 1)
    with pytest.raises(ValueError):
        OriginProjection.restore(raw, expected)


@pytest.mark.parametrize('research,expected', [(None, 0), ({'omitted': ('question', 'need', 'assessment')}, 3)])
def test_absent_research_and_selected_gaps_are_distinct(research, expected):
    authoring = plan(research=research)
    prepared = authoring.review.composition.evidence.proposal
    result = OriginProjection.research(prepared)
    assert len(result.records) == expected
    assert (result.selection is None) == (research is None)
    assert all(row.record_sha256 is None and row.unavailable == 'not_provided' and not row.criterion_ids
               for row in result.records)


@pytest.mark.parametrize('case', ['missing_record', 'duplicate_record', 'gap_and_hash', 'gap_criteria', 'duplicate_criteria'])
def test_research_projection_cannot_invent_completeness(projection, case):
    value = json.loads(projection.canonical)
    records = value['origin']['research']['records']
    if case == 'missing_record':
        records.pop()
    elif case == 'duplicate_record':
        records.append(records[0])
    elif case == 'gap_and_hash':
        records[0]['unavailable'] = 'denied'
    elif case == 'gap_criteria':
        records[0].update(record_sha256=None, unavailable='denied', criterion_ids=['invented'])
    elif case == 'duplicate_criteria':
        records[0]['criterion_ids'] = ['duplicate', 'duplicate']
    value['origin_sha256'] = digest(CampaignOrigin.model_validate_json(json.dumps(value)).origin)
    with pytest.raises(ValueError, match='origin_research_'):
        OriginProjection.restore(canonical(value), projection.document().origin.draft)
