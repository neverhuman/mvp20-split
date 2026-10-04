import copy
from dataclasses import replace

import pytest
from amphora_agent_planning.proposals.context import KnowledgeContext
from amphora_agent_planning.proposals.inputs import ProposalInputs
from amphora_agent_planning.proposals.validator import GraphCandidateValidator

from .support import Case


def validate(case):
    return GraphCandidateValidator().validate(case.bind().inputs)


@pytest.mark.parametrize('mutation,reason', [
    ('profile', 'graph_profile_binding'),
    ('vocabulary', 'graph_vocabulary_digest'),
    ('duplicate', 'graph_vocabulary_duplicate'),
    ('endpoint', 'graph_vocabulary_endpoints'),
    ('snapshot', 'graph_snapshot_digest'),
    ('missing', 'graph_snapshot_missing'),
])
def test_pinned_context_rejects_corruption(mutation, reason):
    bound = Case(history=True).bind()
    profile, snapshot = bound.knowledge.profile(), bound.knowledge.snapshot()
    if mutation == 'profile':
        profile = profile.model_copy(update={'policy': profile.policy.model_copy(update={'sha256': 'f' * 64})})
    elif mutation == 'vocabulary':
        profile = profile.model_copy(update={'vocabulary': profile.vocabulary.model_copy(update={'version': 'different'})})
    elif mutation == 'duplicate':
        profile = profile.model_copy(update={'vocabulary': profile.vocabulary.model_copy(update={'entity_types': ('fixture', 'fixture')})})
    elif mutation == 'endpoint':
        predicate = profile.vocabulary.predicates[0].model_copy(update={'subject_types': ('unknown',)})
        profile = profile.model_copy(update={'vocabulary': profile.vocabulary.model_copy(update={'predicates': (predicate,)})})
    elif mutation == 'snapshot':
        first, *others = snapshot.content.entities
        content = snapshot.content.model_copy(update={'entities': (first.model_copy(update={'label': 'changed'}), *others)})
        snapshot = snapshot.model_copy(update={'content': content})
    else:
        snapshot = None
    with pytest.raises(ValueError, match=reason):
        KnowledgeContext.bind(bound.task, profile, snapshot)


@pytest.mark.parametrize('mutation,reason', [
    ('graph', 'validation_graph_binding'),
    ('pending', 'interpretation_not_published'),
    ('missing_receipt', 'interpretation_receipt_missing'),
])
def test_publication_binding_rejects_incomplete_or_foreign_state(mutation, reason):
    bound = Case().bind()
    knowledge, publication = bound.knowledge, bound.publication
    if mutation == 'graph':
        knowledge = replace(knowledge, task_sha256='f' * 64)
    elif mutation == 'pending':
        publication = replace(publication, attempt=replace(publication.attempt, stage='finalizing'))
    else:
        publication = replace(publication, attempt=replace(publication.attempt, result=None))
    with pytest.raises(ValueError, match=reason):
        ProposalInputs.from_publication(bound.task, bound.observation, bound.review, knowledge, publication)


def test_context_records_are_byte_owned_and_indexes_are_independent():
    bound = Case(history=True).bind()
    first = bound.knowledge.index()
    first.entities.clear()
    assert len(bound.knowledge.index().entities) == 3
    assert bound.knowledge.snapshot().content.entities[0].label == 'A'


def test_missing_and_multiply_owned_replacements_are_not_added():
    case = Case(history=True)
    case.draft['edits'] = [case.edit('correct_assertion', prior=case.known_assertions[0], replacement_local_id='absent')]
    result = validate(case)
    assert any(f.code == 'replacement_candidate_missing' for f in result.findings)
    case.draft['edits'] = []
    for prior in case.known_assertions:
        case.draft['edits'].append(case.edit('correct_assertion', prior=prior, replacement_local_id='claim'))
    result = validate(case)
    assert any(f.code == 'conflicting_replacement_ownership' for f in result.findings)
    assert all(op.operation == 'add_entity' for op in result.proposal().operations)


def test_stale_assertion_is_not_corrected_or_resurrected_as_an_addition():
    case = Case(history=True)
    newer = copy.deepcopy(case.content['assertions'][0])
    newer['supersedes'] = copy.deepcopy(newer['reference'])
    newer['reference']['revision'] = 2
    case.content['assertions'].append(newer)
    case.draft['edits'] = [case.edit('correct_assertion', prior=case.known_assertions[0], replacement_local_id='claim')]
    result = validate(case)
    assert any(f.code == 'stale_assertion_revision' for f in result.findings)
    assert all(op.operation == 'add_entity' for op in result.proposal().operations)


def test_explicit_existing_match_reuses_exact_record_without_new_entity():
    case = Case(history=True)
    case.draft['entities'][0].update(label='A', matches=[case.known_entities[0]])
    result = validate(case)
    assert [op.operation for op in result.proposal().operations] == ['add_entity', 'add_assertion']
    assert result.proposal().operations[-1].assertion.subject.entity_id == 'old-a'


@pytest.mark.parametrize('action,outcome', [('abstain', 'abstained'), ('request_evidence', 'unresolved')])
def test_other_actions_cannot_accidentally_produce_graph_operations(action, outcome):
    case = Case()
    if action not in case.request['context']['allowed_actions']:
        case.request['context']['allowed_actions'].append(action)
    case.draft.update(action=action, entities=[], assertions=[], edits=[])
    result = validate(case)
    assert result.proposal() is None and result.outcome == outcome


def test_legacy_profile_uses_explicit_task_applicability_without_inventing_context():
    bound = Case().bind(legacy=True)
    result = GraphCandidateValidator().validate(bound.inputs)
    assert result.outcome == 'proposed'
    assert result.proposal().operations[0].entity.context == bound.task.document().target.applicability


def test_retracted_assertion_cannot_be_corrected():
    case = Case(history=True)
    case.content['retractions'] = [{'assertion': case.known_assertions[0], 'change_id': 'retraction'}]
    case.draft['edits'] = [case.edit('correct_assertion', prior=case.known_assertions[0], replacement_local_id='claim')]
    result = validate(case)
    assert any(f.code == 'assertion_retracted' for f in result.findings)
    assert all(op.operation == 'add_entity' for op in result.proposal().operations)


def test_aliases_preserve_history_but_prevent_editing_merged_source():
    case = Case(history=True)
    case.content['aliases'] = [{'source': case.known_entities[0], 'target': case.known_entities[1], 'change_id': 'merge'}]
    case.draft['edits'] = [case.edit('merge_entities', source=case.known_entities[0], target=case.known_entities[2])]
    result = validate(case)
    assert any(f.code == 'entity_already_merged' for f in result.findings)
    bound = case.bind()
    facts = bound.knowledge.index()
    source = bound.task.document().existing_entities[0]
    assert facts.resolve(source).entity_id == 'old-b'
    assert facts.entity(source).label == 'A'


def test_cyclic_aliases_are_invalid_owner_context():
    case = Case(history=True)
    case.content['aliases'] = [
        {'source': case.known_entities[0], 'target': case.known_entities[1], 'change_id': 'one'},
        {'source': case.known_entities[1], 'target': case.known_entities[0], 'change_id': 'two'}]
    with pytest.raises(ValueError, match='graph_alias_cycle'):
        case.bind()


def test_stale_entity_match_withholds_its_dependent_assertion():
    case = Case(history=True)
    newer = copy.deepcopy(case.content['entities'][0])
    newer['supersedes'] = copy.deepcopy(newer['reference'])
    newer['reference']['revision'] = 2
    case.content['entities'].append(newer)
    case.draft['entities'][0].update(label='A', matches=[case.known_entities[0]])
    result = validate(case)
    assert any(f.code == 'stale_entity_revision' for f in result.findings)
    assert [op.operation for op in result.proposal().operations] == ['add_entity']


@pytest.mark.parametrize('field,value,reason', [
    ('predicate', 'invented', 'unknown_predicate'),
    ('applicability', None, 'required_context_missing'),
])
def test_assertion_requirements_leave_unrelated_entities_usable(field, value, reason):
    case = Case()
    case.draft['assertions'][0][field] = value
    result = validate(case)
    assert any(f.code == reason for f in result.findings)
    assert all(op.operation == 'add_entity' for op in result.proposal().operations)
