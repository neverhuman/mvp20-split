import json
from dataclasses import replace

import pytest
from amphora_agent_planning.campaign_graph_context import (
    CampaignGraphProjection,
    GraphObservation,
)
from amphora_agent_planning.campaign_knowledge_access import (
    CampaignGraphSelection,
    CampaignKnowledgeReader,
)
from amphora_contracts_knowledge.records import AssertionRetraction, EntityAlias

from ..campaign_knowledge_access.test_reader import repin, selected


def project(selection, peer):
    return CampaignGraphProjection.from_result(CampaignKnowledgeReader(peer).read(selection))


def minimal():
    selection, peer = selected()
    pins, _, assertions = selection.parts()
    return CampaignGraphSelection.bind(selection.request, pins, (), assertions[:1]), peer


def test_exact_selected_assertion_brings_endpoints_but_not_unrelated_records():
    selection, peer = minimal()
    projection = project(selection, peer)
    value = json.loads(projection.canonical)
    assert value['status'] == 'available' and value['authority'] == 'selected_metadata_only'
    assert value['selection']['entities'] == []
    assert [row['reference']['entity_id'] for row in value['entities']] == ['old-a', 'old-b']
    assert [row['reference']['assertion_id'] for row in value['assertions']] == ['old-claim']
    assert not value['aliases'] and not value['retractions']
    assert len([row for row in projection.observations if row.kind == 'alias']) == 2
    assert len([row for row in projection.observations if row.kind == 'retraction']) == 1
    assert not projection.changes(project(selection, peer)) and len(projection.sha256) == 64
    value['entities'].clear()
    assert len(json.loads(projection.canonical)['entities']) == 2


def test_alias_closure_preserves_actual_source_revision_and_complete_chain():
    selection, peer = minimal()
    content = peer.records['/v1/graph-snapshots/read'].content
    old = content.entities[0]
    newer = old.model_copy(update={'reference': old.reference.model_copy(update={'revision': 2}), 'supersedes': old.reference})
    aliases = (EntityAlias(source=newer.reference, target=content.entities[1].reference, change_id='merge-a'),
               EntityAlias(source=content.entities[1].reference, target=content.entities[2].reference, change_id='merge-b'))
    selection = repin(selection, peer, content.model_copy(update={'entities': (*content.entities, newer), 'aliases': aliases}))
    projection = project(selection, peer)
    value = json.loads(projection.canonical)
    assert [(row['reference']['entity_id'], row['reference']['revision']) for row in value['entities']] == [
        ('old-a', 1), ('old-a', 2), ('old-b', 1), ('old-c', 1)]
    assert value['aliases'] == [row.model_dump(mode='json') for row in aliases]
    assert value['aliases'][0]['source']['revision'] == 2


def test_unrelated_record_change_alters_provenance_without_relevant_invalidation():
    selection, peer = minimal()
    original = project(selection, peer)
    content = peer.records['/v1/graph-snapshots/read'].content
    unrelated = content.entities[2].model_copy(update={'label': 'Changed unrelated point'})
    revised = repin(selection, peer, content.model_copy(update={'entities': (*content.entities[:2], unrelated)}))
    future = project(revised, peer)
    assert original.sha256 != future.sha256
    assert json.loads(original.canonical)['context_sha256'] != json.loads(future.canonical)['context_sha256']
    assert not original.changes(future)


def test_absent_retraction_becomes_visible_changed_point_without_rejecting_science():
    selection, peer = minimal()
    original = project(selection, peer)
    content = peer.records['/v1/graph-snapshots/read'].content
    row = AssertionRetraction(assertion=content.assertions[0].reference, change_id='future-correction')
    revised = repin(selection, peer, content.model_copy(update={'retractions': (row,)}))
    future = project(revised, peer)
    assert [item.kind for item in original.changes(future)] == ['retraction']
    assert json.loads(future.canonical)['retractions'] == [row.model_dump(mode='json')]
    assert json.loads(future.canonical)['assertions'] == json.loads(original.canonical)['assertions']
    assert not original.changes(original)


def test_absent_alias_and_missing_context_are_relevant_changes():
    selection, peer = minimal()
    original = project(selection, peer)
    content = peer.records['/v1/graph-snapshots/read'].content
    row = EntityAlias(source=content.entities[0].reference, target=content.entities[2].reference, change_id='merge')
    revised = repin(selection, peer, content.model_copy(update={'aliases': (row,)}))
    assert [item.kind for item in original.changes(project(revised, peer))] == ['alias']
    unavailable = CampaignGraphProjection.unavailable(selection, 'knowledge_reference_unavailable')
    assert len(original.changes(unavailable)) == len(original.observations)
    assert [item.kind for item in unavailable.changes(original)] == ['availability']


def test_genesis_and_owner_read_failure_remain_explicit():
    selection, peer = selected(False)
    value = json.loads(project(selection, peer).canonical)
    assert value['selection']['base'] is None and not value['entities'] and not value['assertions']
    result = CampaignKnowledgeReader(peer).read(selection)
    failed = replace(result, context=None, failure='knowledge_access_denied')
    value = json.loads(CampaignGraphProjection.from_result(failed).canonical)
    assert value['status'] == 'unavailable' and value['reason'] == 'knowledge_access_denied'
    assert 'profile' not in value and 'entities' not in value
    with pytest.raises(ValueError, match='campaign_graph_result_shape'):
        CampaignGraphProjection.from_result(replace(result, failure='knowledge_access_denied'))
    with pytest.raises(ValueError, match='campaign_graph_unavailable_reason'):
        CampaignGraphProjection.unavailable(selection, 'unexpected secret error')
    with pytest.raises(ValueError, match='campaign_graph_observation_kind'):
        GraphObservation.capture('arbitrary', {}, {})


def test_oversized_graph_is_explicit_unavailable_without_truncation():
    selection, peer = selected()
    content = peer.records['/v1/graph-snapshots/read'].content
    assertion = content.assertions[0]
    rows = tuple(assertion.model_copy(update={'reference': assertion.reference.model_copy(update={'assertion_id': f'claim-{n}'}),
        'statement': 'x' * 4096}) for n in range(256))
    selection = repin(selection, peer, content.model_copy(update={'assertions': rows}))
    pins, entities, _ = selection.parts()
    selection = CampaignGraphSelection.bind(selection.request, pins, entities, tuple(row.reference for row in rows))
    read = CampaignKnowledgeReader(peer).read(selection)
    assert read.failure is None
    result = CampaignGraphProjection.from_result(read)
    assert json.loads(result.canonical)['reason'] == 'campaign_graph_projection_limit'
    with pytest.raises(ValueError, match='campaign_graph_projection_limit'):
        CampaignGraphProjection.bind(selection, read.context)


@pytest.mark.parametrize('kind', ['entity', 'assertion'])
def test_pure_projection_revalidates_selected_existence(kind):
    selection, peer = selected()
    read = CampaignKnowledgeReader(peer).read(selection)
    pins, entities, assertions = selection.parts()
    if kind == 'entity':
        entities = (entities[0].model_copy(update={'entity_id': 'absent'}),)
    else:
        assertions = (assertions[0].model_copy(update={'assertion_id': 'absent'}),)
    forged = CampaignGraphSelection.bind(selection.request, pins, entities, assertions)
    with pytest.raises(ValueError, match='campaign_graph_projection_' + kind):
        CampaignGraphProjection.from_result(replace(read, selection=forged))
