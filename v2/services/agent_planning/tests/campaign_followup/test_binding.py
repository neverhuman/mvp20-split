"""Exact criterion membership, gaps and future intent without provider/SQL authority."""

import copy
import hashlib
import json
from pathlib import Path

import pytest
from amphora_agent_planning.campaign_context import ResearchContext, ResearchSelection
from amphora_agent_planning.campaign_followup.policy import CriterionBindings, canonical
from amphora_agent_planning.context import RequestSnapshot
from amphora_contracts_core import Scope
from amphora_contracts_planning import CheckpointFollowupDraft, checkpoint_followup_draft_schema
from amphora_contracts_research import EvidenceAssessmentStatus, EvidenceNeed, ResearchQuestion

FIXTURES = Path(__file__).absolute().parents[1] / 'campaign_context/fixtures'


def setup(assessed=True):
    original = json.loads((FIXTURES / 'request.json').read_bytes())
    original['context']['output_schema'] = checkpoint_followup_draft_schema().model_dump(mode='json')
    request = RequestSnapshot.from_bytes(canonical(original), actor_id='fixture',
                                        scope=Scope(tenant_id='planning-fixture', project_id='context'))
    value = json.loads((FIXTURES / 'selection.json').read_bytes())
    records = json.loads((FIXTURES / 'records.json').read_bytes())
    question = ResearchQuestion.model_validate_json(json.dumps(records['question']))
    need = EvidenceNeed.model_validate_json(json.dumps(records['need']))
    status = EvidenceAssessmentStatus.model_validate_json(json.dumps(records['assessment']))
    value['assessments'][0]['status_sha256'] = hashlib.sha256(canonical(status.model_dump(mode='json'))).hexdigest()
    value.update(schema_version='2', request_sha256=request.sha256, focus_artifact=None)
    value['criteria'] = [{'question': copy.deepcopy(value['questions'][0]), 'need': copy.deepcopy(value['needs'][0]),
                          'criterion_id': need.criterion_ids[0],
                          'assessment': copy.deepcopy(value['assessments'][0]) if assessed else None}]
    return request, value, {'questions': (question,), 'needs': (need,), 'assessments': (status,)}


def bound(assessed=True):
    request, value, records = setup(assessed)
    selection = ResearchSelection.from_bytes(canonical(value), request)
    context = ResearchContext.bind(selection, **records)
    return CriterionBindings.bind(selection.document(), **records), context


def output(binding):
    value = binding.document()
    ref = value.criteria[0].model_dump(mode='json')
    return {'schema_version': '3', 'authority': 'proposal_only', 'scientific_authority': 'not_established',
            'action': 'request_evidence', 'rationale': 'Resolve the exact selected disagreement',
            'decision_scope': 'a' * 64, 'candidate': None, 'alternatives': [], 'focus_artifact': None,
            'evidence_requests': [{'question': ref['question'], 'needs': [ref['need']],
                'assessments': [] if ref['assessment'] is None else [ref['assessment']], 'producer': None,
                'expected_evidence': 'New applicable evidence', 'uncertainty': 'Still unresolved'}],
            'targets': [{'criterion': ref, 'improvement': 'Test applicability', 'expected_learning': 'Which evidence applies'}],
            'unresolved': [{'criterion': ref, 'posture': 'contradictory', 'description': 'Conflict remains'}]}


def test_weak_science_and_unassessed_points_remain_eligible_as_future_targets():
    for assessed in (True, False):
        binding, context = bound(assessed)
        assert context.records
        assert (binding.document().criteria[0].assessment is not None) == assessed
        draft = CheckpointFollowupDraft.model_validate_json(json.dumps(output(binding)))
        assert binding.validate_output(draft) == draft
        assert draft.scientific_authority == 'not_established'


@pytest.mark.parametrize('case,code', [
    ('duplicate', 'followup_duplicate_criterion'), ('question_unselected', 'followup_reference_unselected'),
    ('assessment_unselected', 'followup_assessment_unselected'), ('focus_unselected', 'followup_focus_unselected'),
    ('profile', 'followup_profile'),
])
def test_selection_requires_explicit_original_profile_and_exact_selected_references(case, code):
    request, value, _ = setup()
    if case == 'duplicate': value['criteria'].append(copy.deepcopy(value['criteria'][0]))
    elif case == 'question_unselected': value['criteria'][0]['question']['revision'] += 1
    elif case == 'assessment_unselected': value['criteria'][0]['assessment']['status_sha256'] = 'f' * 64
    elif case == 'focus_unselected':
        value['focus_artifact'] = request.document().context.entries[0].artifact.model_dump(mode='json')
        value['focus_artifact']['artifact_id'] = 'different'
    else:
        original = request.document().model_dump(mode='json')
        original['context']['output_schema']['sha256'] = 'f' * 64
        request = RequestSnapshot.from_bytes(canonical(original), actor_id='fixture', scope=request.document().reference.scope)
        value['request_sha256'] = request.sha256
    with pytest.raises(ValueError, match=code):
        ResearchSelection.from_bytes(canonical(value), request)


@pytest.mark.parametrize('case,code', [
    ('missing_question', 'followup_criterion_record_unavailable'),
    ('missing_need', 'followup_criterion_record_unavailable'),
    ('unknown_criterion', 'followup_criterion_missing'),
    ('missing_assessment', 'followup_assessment_record_unavailable'),
])
def test_record_membership_cannot_be_inferred_from_labels_or_selection_alone(case, code):
    request, value, records = setup()
    if case == 'missing_question': records['questions'] = ()
    elif case == 'missing_need': records['needs'] = ()
    elif case == 'missing_assessment': records['assessments'] = ()
    else: value['criteria'][0]['criterion_id'] = 'not-in-question'
    selection = ResearchSelection.from_bytes(canonical(value), request)
    with pytest.raises(ValueError, match=code):
        ResearchContext.bind(selection, **records)


@pytest.mark.parametrize('case,code', [
    ('omitted', 'followup_output_omitted'), ('foreign', 'followup_output_unselected'),
    ('assessment', 'followup_output_unselected'), ('duplicate', 'followup_output_duplicate'),
    ('blank', 'followup_empty_intent'), ('abstain_targets', 'followup_abstention_targets'),
    ('focus', 'followup_focus_mismatch'),
])
def test_output_keeps_selected_weaknesses_and_cannot_claim_target_adoption(case, code):
    binding, context = bound()
    value = output(binding)
    if case == 'omitted': value.update(targets=[], unresolved=[])
    elif case == 'foreign': value['targets'][0]['criterion']['criterion_id'] = 'different'
    elif case == 'assessment': value['targets'][0]['criterion']['assessment'] = None
    elif case == 'duplicate': value['targets'] *= 2
    elif case == 'blank': value['targets'][0]['expected_learning'] = '  '
    elif case == 'abstain_targets': value['action'] = 'abstain'
    else: value['focus_artifact'] = context.selection.request.document().context.entries[0].artifact.model_dump(mode='json')
    with pytest.raises(ValueError, match=code):
        binding.validate_output(CheckpointFollowupDraft.model_validate_json(json.dumps(value)))


def test_human_focus_is_an_included_exact_artifact_and_returned_values_do_not_mutate_binding():
    request, value, records = setup()
    value['focus_artifact'] = request.document().context.entries[0].artifact.model_dump(mode='json')
    selected = ResearchSelection.from_bytes(canonical(value), request)
    binding = CriterionBindings.bind(selected.document(), **records)
    snapshot = binding.selection_bytes
    value['criteria'].clear()
    assert binding.selection_bytes == snapshot and len(binding.document().criteria) == 1
    draft = output(binding); draft['focus_artifact'] = selected.document().focus_artifact.model_dump(mode='json')
    draft.update(action='abstain', targets=[], evidence_requests=[])
    assert binding.validate_output(CheckpointFollowupDraft.model_validate_json(json.dumps(draft))).action == 'abstain'
