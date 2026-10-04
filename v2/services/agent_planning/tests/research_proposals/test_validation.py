import copy
from dataclasses import replace

import pytest
from amphora_agent_planning.research_proposals import QuestionContext, ResearchProposalValidator

from .support import ResearchCase


def test_distinct_proposals_preserve_negation_unknown_quality_and_interpretation_without_acceptance():
    case = ResearchCase()
    case.draft['answers'][0]['attribution'].update(origin='inferred', confidence='unknown')
    result = case.validate()
    assert result.authority == 'proposal_only' and result.validation == 'quotation_and_structure_only'
    assert result.outcome == 'proposed'
    question, answer, need = result.questions[0], result.answers[0], result.evidence_needs[0]
    assert answer.question == need.need.question == question.question.reference
    assert answer.answer == 'A does not cause B.'
    assert answer.model_attribution.origin == 'inferred' and answer.model_attribution.confidence == 'unknown'
    assert question.grounding.interpretation_artifacts == (result.interpretation,)
    assert answer.validation_method.model_dump(mode='json') == case.method
    assert need.need.criterion_ids == ('association',)
    assert case.validate() == result
    candidate, _ = case.bindings()
    assert not hasattr(candidate, 'knowledge')


@pytest.mark.parametrize('group,field,reason', [
    ('questions', 'applicability', 'required_context_missing'),
    ('answers', 'validation_method', 'answer_method_missing'),
    ('answers', 'context', 'required_context_missing'),
    ('evidence_needs', 'method', 'need_method_missing'),
    ('evidence_needs', 'required_context', 'required_context_missing'),
])
def test_missing_required_fields_withhold_only_item_and_its_dependents(group, field, reason):
    case = ResearchCase()
    case.draft[group][0][field] = None
    result = case.validate()
    assert any(f.code == reason for f in result.findings)
    if group == 'questions':
        assert result.outcome == 'unresolved'
        assert not (result.questions or result.answers or result.evidence_needs)
    else:
        assert result.outcome == 'partial' and len(result.questions) == 1


def test_duplicate_local_questions_never_choose_one_for_dependent_items():
    case = ResearchCase()
    case.draft['questions'].append(copy.deepcopy(case.draft['questions'][0]))
    result = case.validate()
    assert not (result.questions or result.answers or result.evidence_needs)
    assert result.withheld == ('/answers/0', '/evidence_needs/0', '/questions/0', '/questions/1')


@pytest.mark.parametrize('criteria,reason', [(['absent'], 'unknown_need_criterion'),
                                           (['association', 'association'], 'duplicate_need_criterion')])
def test_need_criteria_use_exact_target_definition(criteria, reason):
    case = ResearchCase()
    case.draft['evidence_needs'][0]['criterion_ids'] = criteria
    result = case.validate()
    assert not result.evidence_needs and result.answers and result.questions
    assert result.findings[0].code == reason


def test_selected_owner_question_binds_exact_revision_and_criteria():
    case = ResearchCase()
    known = case.known_question()
    for group in ('answers', 'evidence_needs'):
        case.draft[group][0].update(question=known.reference.model_dump(mode='json'), question_local_id=None)
    result = case.validate()
    assert result.answers[0].question == result.evidence_needs[0].need.question == known.reference
    case.known.clear()
    missing = case.validate()
    assert missing.questions and not missing.answers and not missing.evidence_needs
    assert {f.code for f in missing.findings} == {'question_reference_unavailable'}


@pytest.mark.parametrize('both', [False, True])
def test_question_target_must_be_exactly_one_local_or_owner_reference(both):
    case = ResearchCase()
    known = case.known_question()
    case.draft['answers'][0].update(question=known.reference.model_dump(mode='json') if both else None,
                                    question_local_id='q' if both else None)
    result = case.validate()
    assert result.questions and result.evidence_needs and not result.answers
    assert result.findings[0].code == 'question_target_ambiguous'


def test_fabricated_quote_does_not_contaminate_unrelated_proposals():
    case = ResearchCase()
    case.draft['answers'][0]['attribution']['quotations'][0]['text'] = 'invented quotation'
    result = case.validate()
    assert result.questions and result.evidence_needs and not result.answers
    assert result.findings[0].code == 'quotation_bytes'


def test_conflicting_answers_and_model_diagnostics_do_not_create_global_veto():
    case = ResearchCase()
    opposite = copy.deepcopy(case.draft['answers'][0])
    opposite.update(local_id='opposite', answer='A causes B.')
    case.draft['answers'].append(opposite)
    case.draft['diagnostics'] = [{'code': 'conflict', 'target_path': '/answers', 'kind': 'contradiction',
                                  'description': 'Synthetic incompatible answers'}]
    result = case.validate()
    assert result.outcome == 'proposed' and len(result.answers) == 2 and not result.withheld
    assert result.findings[0].code == 'model_reported_contradiction'


def test_question_context_is_byte_owned_and_cannot_hide_duplicate_or_foreign_records():
    case = ResearchCase()
    record = case.known_question()
    candidate, context = case.bindings()
    context.index().clear()
    assert len(context.index()) == 1
    with pytest.raises(ValueError, match='research_question_duplicate'):
        ResearchProposalValidator().validate(candidate, replace(context, records=context.records * 2))
    with pytest.raises(ValueError, match='research_context_task_binding'):
        ResearchProposalValidator().validate(candidate, replace(context, task_sha256='f' * 64))
    with pytest.raises(ValueError, match='research_question_not_selected'):
        QuestionContext.bind(candidate.task, (record.model_copy(update={'reference': record.reference.model_copy(update={'revision': 2})}),))


def test_explicit_abstention_does_not_create_question_or_answer():
    case = ResearchCase()
    case.draft.update(action='abstain', questions=[], answers=[], evidence_needs=[])
    result = case.validate()
    assert result.outcome == 'abstained' and not result.findings


def test_invalid_local_criteria_withhold_dependents_but_keep_independent_question():
    case = ResearchCase()
    independent = copy.deepcopy(case.draft['questions'][0])
    independent['local_id'] = 'independent'
    case.draft['questions'].append(independent)
    case.draft['questions'][0]['criteria'] *= 2
    result = case.validate()
    assert [question.local_id for question in result.questions] == ['independent']
    assert not result.answers and not result.evidence_needs
    assert any(f.code == 'duplicate_question_criterion' for f in result.findings)


def test_unselected_question_is_unresolved_even_when_it_has_a_well_formed_reference():
    case = ResearchCase()
    known = case.known_question()
    case.draft['answers'][0].update(question=dict(known.reference.model_dump(mode='json'), question_id='not-selected'),
                                   question_local_id=None)
    result = case.validate()
    assert result.questions and result.evidence_needs and not result.answers
    assert result.findings[0].code == 'question_reference_not_selected'


@pytest.mark.parametrize('group,field,reason', [('questions', 'objective', 'empty_question_objective'),
                                             ('answers', 'answer', 'empty_answer_text')])
def test_blank_required_content_does_not_pass_as_a_useful_proposal(group, field, reason):
    case = ResearchCase()
    case.draft[group][0][field] = ' '
    result = case.validate()
    assert any(f.code == reason for f in result.findings)
