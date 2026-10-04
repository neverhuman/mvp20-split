"""Hand-authored proposal boundary examples, not an accepted scientific answer."""

import copy
import json
from pathlib import Path

import pytest
from amphora_contracts_planning import ResearchProposalSet
from pydantic import ValidationError


def fixture():
    value = json.loads((Path(__file__).parent / 'fixtures/extraction.json').read_bytes())
    context = value['request']['context']['objective']
    attribution = value['draft']['entities'][0]['attribution']
    reference = {'scope': context['scope'], 'question_id': 'proposed-question', 'revision': 1}
    grounding = {'spans': [quote['span'] for quote in attribution['quotations']],
                 'conversion_traces': value['task']['sources'][0]['conversion_traces'], 'interpretation_artifacts': [context]}
    return {'wire_version': '1', 'authority': 'proposal_only', 'validation': 'quotation_and_structure_only',
        'task_sha256': 'a' * 64, 'candidate_sha256': 'b' * 64, 'interpretation': context, 'outcome': 'proposed',
        'questions': [{'local_id': 'q', 'source_path': '/questions/0', 'model_attribution': attribution,
            'grounding': grounding, 'question': {'wire_version': '1', 'reference': reference, 'objective': 'Synthetic question',
                'applicability': context, 'criteria': [{'criterion_id': 'c', 'description': 'Synthetic criterion'}], 'supersedes': None}}],
        'answers': [{'local_id': 'a', 'source_path': '/answers/0', 'model_attribution': attribution,
            'grounding': grounding, 'question': reference, 'answer': 'Unverified synthetic candidate answer',
            'validation_method': context['schema_ref'], 'context': context}],
        'evidence_needs': [], 'findings': [], 'withheld': []}


def test_proposed_records_and_grounding_roundtrip_without_scientific_authority():
    record = ResearchProposalSet.model_validate_json(json.dumps(fixture()))
    assert ResearchProposalSet.model_validate_json(record.model_dump_json()) == record
    assert record.authority == 'proposal_only'
    assert record.questions[0].question.reference == record.answers[0].question


@pytest.mark.parametrize('case', ['accepted', 'scientific', 'missing_grounding', 'loose_revision', 'too_many', 'extra'])
def test_wire_cannot_inject_authority_or_drop_required_provenance(case):
    value = copy.deepcopy(fixture())
    if case == 'accepted':
        value['authority'] = 'accepted'
    elif case == 'scientific':
        value['validation'] = 'scientifically_valid'
    elif case == 'missing_grounding':
        del value['answers'][0]['grounding']
    elif case == 'loose_revision':
        value['questions'][0]['question']['reference']['revision'] = True
    elif case == 'too_many':
        value['answers'] *= 33
    else:
        value['answers'][0]['accepted'] = True
    with pytest.raises(ValidationError):
        ResearchProposalSet.model_validate_json(json.dumps(value))
