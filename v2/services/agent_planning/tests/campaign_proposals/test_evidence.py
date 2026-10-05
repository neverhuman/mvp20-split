"""Evidence purposes use consumed exact references, never model-created evidence."""

import copy
import hashlib
import json
from dataclasses import replace

import pytest
from amphora_agent_planning.campaign_context import ResearchContext, ResearchSelection
from amphora_agent_planning.campaign_context.records import canonical
from amphora_agent_planning.campaign_proposals import (
    EvidencePurposeReview,
    PreparedCampaignProposal,
)
from amphora_agent_planning.campaign_slice_plan.slices import ContextSlice
from amphora_agent_planning.context import AttemptBinding
from amphora_agent_planning.providers import observe

from ..campaign_context.test_records import values, wire
from ..campaign_output.test_output import output
from ..providers.test_task_output import Response
from .test_prepared import record, source


def inputs(*, omitted=(), posture='unknown', other_question=False, additional_question=False, selected=None):
    selected = source(extras=(('science', b'synthetic Research context', True),)) if selected is None else selected
    artifact = next(entry.artifact for entry in selected.request.document().context.entries
                    if entry.artifact.artifact_id == 'science').model_dump(mode='json')
    data = values()

    def rebind_artifacts(value):
        if isinstance(value, dict):
            if set(value) == set(artifact):
                value.clear()
                value.update(copy.deepcopy(artifact))
            else:
                for child in value.values():
                    rebind_artifacts(child)
        elif isinstance(value, list):
            for child in value:
                rebind_artifacts(child)

    rebind_artifacts(data)
    data['assessment']['outcome']['assessment']['disposition'] = posture
    questions = [data['question']]
    if other_question or additional_question:
        second = copy.deepcopy(data['question'])
        second['reference']['question_id'] = 'another-question'
        questions.append(second)
        if other_question:
            data['need']['question'] = second['reference']
    declaration = {'schema_version': '1', 'engagement': selected.request.document().reference.model_dump(mode='json'),
        'request_sha256': selected.request.sha256, 'questions': [item['reference'] for item in questions],
        'needs': [data['need']['reference']], 'assessments': [] if other_question else [
            {'request': data['assessment']['request'], 'status_sha256': hashlib.sha256(canonical(data['assessment'])).hexdigest()}]}
    selection = ResearchSelection.from_bytes(canonical(declaration), selected.request)
    context = ResearchContext.bind(selection,
        questions=() if 'question' in omitted else tuple(wire('question', item) for item in questions),
        needs=() if 'need' in omitted else (wire('need', data['need']),),
        assessments=() if 'assessment' in omitted or other_question else (wire('assessment', data['assessment']),))
    selected = selected.with_research(context)
    value = output('future')
    intent = value['candidate']['expected_evidence'][0]
    intent.update(question=declaration['questions'][0], needs=declaration['needs'], assessments=declaration['assessments'])
    return selected, value


def prepared(selected, value):
    preparation = record(selected)
    attempt = AttemptBinding(selected.request, 1)
    observed = observe(attempt, Response(json.dumps(value).encode()))
    assert observed.document().status in {'proposed', 'abstained'}
    return PreparedCampaignProposal.bind(preparation, attempt, observed)


@pytest.mark.parametrize('posture', ['supported', 'contradicted', 'unknown'])
def test_scientific_posture_is_preserved_without_promoting_or_vetoing(posture):
    selected, value = inputs(posture=posture)
    review = EvidencePurposeReview.bind(prepared(selected, value))
    assert not review.findings
    assert len(review.read_set.entries) == 3
    status = review.research.context.records[-1].document()
    assert status.outcome.assessment.disposition == posture
    assert not status.outcome.assessment.scientifically_established
    assert review.proposal.output.document().scientific_authority == 'not_established'
    assert all(entry.key.lane == 'research' for entry in review.read_set.entries)


@pytest.mark.parametrize('omitted', [('question',), ('need',), ('assessment',), ('question', 'need', 'assessment')])
def test_missing_science_remains_an_explicit_selected_gap(omitted):
    selected, value = inputs(omitted=omitted)
    review = EvidencePurposeReview.bind(prepared(selected, value))
    assert {finding.code for finding in review.findings} == {name + '_unavailable' for name in omitted}
    assert len(review.read_set.entries) == 3
    assert len(review.research.context.gaps) == len(omitted)


@pytest.mark.parametrize('case,code', [
    ('question_revision', 'campaign_evidence_reference_unselected'),
    ('need_revision', 'campaign_evidence_reference_unselected'),
    ('assessment_request', 'campaign_evidence_reference_unselected'),
    ('assessment_hash', 'campaign_evidence_assessment_pin'),
    ('duplicate_need', 'campaign_evidence_duplicate_need'),
    ('duplicate_assessment', 'campaign_evidence_duplicate_assessment'),
    ('unresolved_need', 'campaign_evidence_reference_unselected'),
])
def test_exact_reference_membership_and_hashes_are_required(case, code):
    selected, value = inputs()
    intent = value['candidate']['expected_evidence'][0]
    if case == 'question_revision':
        intent['question']['revision'] += 1
    elif case == 'need_revision':
        intent['needs'][0]['revision'] += 1
    elif case == 'assessment_request':
        intent['assessments'][0]['request']['assessment_id'] = 'invented'
    elif case == 'assessment_hash':
        intent['assessments'][0]['status_sha256'] = '0' * 64
    elif case == 'duplicate_need':
        intent['needs'] *= 2
    elif case == 'duplicate_assessment':
        intent['assessments'] *= 2
    else:
        value['unresolved'][0]['need']['need_id'] = 'invented'
    with pytest.raises(ValueError, match=code):
        EvidencePurposeReview.bind(prepared(selected, value))


def test_a_real_selected_need_for_another_question_is_not_a_matching_evidence_purpose():
    selected, value = inputs(other_question=True)
    with pytest.raises(ValueError, match='campaign_evidence_need_question'):
        EvidencePurposeReview.bind(prepared(selected, value))


def test_selected_assessment_cannot_be_claimed_as_evidence_for_another_selected_question():
    selected, value = inputs(additional_question=True)
    intent = value['candidate']['expected_evidence'][0]
    intent['question'] = dict(intent['question'], question_id='another-question')
    intent['needs'] = []
    with pytest.raises(ValueError, match='campaign_evidence_assessment_question'):
        EvidencePurposeReview.bind(prepared(selected, value))


def test_producer_address_is_explicitly_pending_composition_policy():
    selected, value = inputs()
    value['candidate']['expected_evidence'][0]['producer'] = {'scope_path': [], 'node_id': 'convert'}
    review = EvidencePurposeReview.bind(prepared(selected, value))
    assert review.findings[0].code == 'producer_resolution_required'


def test_request_evidence_and_anonymous_abstention_have_distinct_dependencies():
    selected, value = inputs()
    value.update(action='request_evidence', evidence_requests=value['candidate']['expected_evidence'], candidate=None)
    assert len(EvidencePurposeReview.bind(prepared(selected, value)).read_set.entries) == 3
    value = output('abstain')
    value['unresolved'][0].update(question=None, need=None)
    review = EvidencePurposeReview.bind(prepared(source(), value))
    assert review.research is None and review.read_set.entries == ()
    with pytest.raises(ValueError, match='campaign_evidence_context_missing'):
        EvidencePurposeReview.bind(prepared(source(), output('abstain')))


@pytest.mark.parametrize('case', ['findings', 'identity', 'fields', 'count', 'observation', 'slice_identity', 'gap_reason'])
def test_rehashed_packet_does_not_make_altered_research_context_authoritative(case):
    selected, value = inputs(omitted=('question',))
    original = next(row for row in selected.slices if row.lane == 'research')
    document = original.document()
    payload = document['payload']
    if case == 'findings':
        payload['context']['findings'] = []
    elif case == 'identity':
        payload['context']['records'][0]['identity']['reference']['need_id'] = 'forged'
    elif case == 'fields':
        del payload['context']['records']
    elif case == 'count':
        payload['context']['gaps'] *= 161
    elif case == 'observation':
        document['observations'][0]['sha256'] = '0' * 64
    elif case == 'gap_reason':
        payload['context']['gaps'][0]['reason'] = []
    else:
        document['identity']['selection'] = '0' * 64
    changed = ContextSlice._capture('research', document['identity'], payload, True, document['observations'])
    selected = replace(selected, slices=tuple(changed if row is original else row for row in selected.slices))
    with pytest.raises(ValueError):
        EvidencePurposeReview.bind(prepared(selected, value))
