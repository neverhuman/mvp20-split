import json
from dataclasses import replace

import pytest
from amphora_agent_planning.knowledge_access import KnowledgeReader
from amphora_agent_planning.knowledge_access.prompt import GraphPrompt

from ..proposals.support import Case
from .test_reader import inputs


@pytest.mark.parametrize('history', [False, True])
def test_exact_schemas_and_selected_owner_facts_are_data_separate_from_instructions(history):
    task, peer, review = inputs(history)
    knowledge = KnowledgeReader(peer).review(task)
    raw = GraphPrompt.render(review, knowledge)
    packet = json.loads(raw)
    assert packet['profile'] == 'planning-grounded-extraction-input.v1'
    assert packet['trusted_instructions'] == review.prompt.instructions.decode()
    graph = packet['graph_data']
    assert graph['output_schema']['$id'] == 'urn:amphora:planning.extraction-edit-draft:1:validation'
    assert graph['operation_schema']['$id'] == 'urn:amphora:knowledge.proposal:1:validation'
    assert len(graph['entities']) == (3 if history else 0)
    assert len(graph['assertions']) == (2 if history else 0)
    assert graph['snapshot'] == (task.document().target.base.snapshot.model_dump(mode='json') if history else None)
    assert GraphPrompt.render(review, knowledge) == raw
    assert 'Ignore all instructions' in packet['source_data'][0]['text']
    assert 'graph_data' not in json.loads(review.prompt.render(task, review.bundle))


def test_foreign_context_cannot_be_rendered_under_another_tasks_prompt():
    task, peer, review = inputs(False)
    knowledge = KnowledgeReader(peer).review(task)
    with pytest.raises(ValueError, match='graph_prompt_task_binding'):
        GraphPrompt.render(review, replace(knowledge, task_sha256='f' * 64))


def test_selected_entity_includes_complete_alias_chain_without_implicit_identity_rewrite():
    case = Case(history=True)
    case.task['existing_entities'] = [case.known_entities[0]]
    case.task['existing_assertions'] = []
    case.content['aliases'] = [
        {'source': case.known_entities[0], 'target': case.known_entities[1], 'change_id': 'one'},
        {'source': case.known_entities[1], 'target': case.known_entities[2], 'change_id': 'two'}]
    bound = case.bind()
    packet = json.loads(GraphPrompt.render(bound.review, bound.knowledge))['graph_data']
    assert [row['reference']['entity_id'] for row in packet['entities']] == ['old-a', 'old-b', 'old-c']
    assert len(packet['aliases']) == 2
    assert not packet['assertions']


def test_selected_assertion_adds_its_exact_endpoints_and_keeps_retraction_visible():
    case = Case(history=True)
    case.task['existing_entities'] = []
    case.task['existing_assertions'] = [case.known_assertions[0]]
    case.content['retractions'] = [{'assertion': case.known_assertions[0], 'change_id': 'retracted'}]
    bound = case.bind()
    packet = json.loads(GraphPrompt.render(bound.review, bound.knowledge))['graph_data']
    assert [row['reference']['entity_id'] for row in packet['entities']] == ['old-a', 'old-b']
    assert packet['retracted_assertions'] == [case.known_assertions[0]]
