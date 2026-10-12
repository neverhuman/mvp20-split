import json
from dataclasses import replace

import pytest
from amphora_agent_planning.campaign_knowledge_access import CampaignGraphSelection, CampaignKnowledgeReader
from amphora_agent_planning.campaign_knowledge_access.reader import CampaignGraphResult
from amphora_agent_planning.campaign_packet import prepare
from amphora_agent_planning.campaign_preparations import CampaignPreparation
from ..curation_input.test_profile import curation_plan
from ..campaign_knowledge_access.test_reader import selected
from ..campaign_packet.test_assembly import plan


def graphs(source, count=8):
    selection, peer = selected(False)
    selection = CampaignGraphSelection.bind(source.request, *selection.parts())
    first = CampaignKnowledgeReader(peer).read(selection)
    assert first.failure is None
    result = [first]
    pins, _, _ = selection.parts()
    for index in range(1, count):
        changed = replace(pins, graph=pins.graph.model_copy(update={'graph_id': 'graph-' + str(index)}))
        chosen = CampaignGraphSelection.bind(source.request, changed)
        result.append(CampaignGraphResult(chosen, None, 'knowledge_access_denied', 1, 0))
    return tuple(result)


def test_eight_distinct_graphs_survive_exact_packet_and_preparation_replay():
    source = curation_plan()
    values = graphs(source)
    combined = source.with_graphs(values)
    rows = [row.document() for row in combined.slices if row.lane == 'graph']
    assert len(rows) == 8 and all(row['required'] for row in rows)
    assert rows[0]['payload']['status'] == 'available'
    assert all(row['payload']['reason'] == 'knowledge_access_denied' for row in rows[1:])
    packet = prepare(combined).packet
    assert packet is not None
    retained = CampaignPreparation.bind(combined, packet)
    replay = CampaignPreparation.from_bytes(source.request, retained.canonical, packet.canonical)
    assert replay == retained
    slices = json.loads(replay.packet.canonical)['untrusted_context']['slices']
    assert len([row for row in slices if row['lane'] == 'graph']) == 8
    assert [row['identity']['selection'] for row in rows] == [value.selection.sha256 for value in values]


def test_collection_is_profile_bounded_unique_and_cannot_overwrite_family():
    source = curation_plan()
    values = graphs(source)
    for supplied in [(), (*values, values[0]), list(values)]:
        with pytest.raises(ValueError, match='collection_bound'): source.with_graphs(supplied)
    with pytest.raises(ValueError, match='collection_duplicate'): source.with_graphs((values[0], values[0]))
    with pytest.raises(ValueError, match='family_duplicate'): source.with_graph(values[0]).with_graphs(values)
    with pytest.raises(ValueError, match='family_duplicate'): source.with_graphs(values).with_graph(values[0])
    with pytest.raises(ValueError, match='collection_profile'): plan().with_graphs(values)


def test_same_scope_different_request_is_not_a_valid_graph_collection():
    source = curation_plan()
    other = curation_plan(maximum=190000)
    with pytest.raises(ValueError, match='campaign_slice_request'):
        source.with_graphs(graphs(other))


def test_single_graph_new_entry_point_preserves_old_canonical_plan_bytes():
    source = curation_plan()
    value = graphs(source, 1)[0]
    assert source.with_graph(value).canonical == source.with_graphs((value,)).canonical
