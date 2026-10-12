import json
from dataclasses import replace

import pytest
from amphora_agent_planning.curation_context import CurationIntent
from amphora_agent_planning.curation_intake.commands import CurationCommand
from amphora_agent_planning.curation_knowledge import CurationKnowledgeReader
from amphora_agent_planning.campaign_packet import prepare
from amphora_agent_planning.campaign_preparations import CampaignPreparation
from ..curation_context.test_intent import source
from ..campaign_knowledge_access.test_reader import selected


def case():
    plan, _, incoming = source()
    selection, peer = selected()
    value = json.loads(incoming.command.canonical_bytes)
    value['payload']['context']['knowledge'] = [selection.parts()[0].base.model_dump(mode='json')]
    incoming = CurationCommand.restore(json.dumps(value))
    intent = CurationIntent.from_template(plan.request, incoming, 'synthetic')
    return replace(plan, request=intent.request), intent, peer


def test_exact_owner_reads_preserve_all_selected_records_and_replay():
    plan, intent, peer = case()
    context = CurationKnowledgeReader(peer).read(intent)
    projections, summary = context.rows()
    assert len(peer.calls) == 3 and summary['graphs'][0]['status'] == 'available'
    value = json.loads(projections[0].canonical)
    assert len(value['entities']) == len(peer.records['/v1/graph-snapshots/read'].content.entities)
    assert len(value['assertions']) == len(peer.records['/v1/graph-snapshots/read'].content.assertions)
    combined = plan.with_curation(intent).with_curation_knowledge(context)
    packet = prepare(combined).packet
    assert packet is not None
    saved = CampaignPreparation.bind(combined, packet)
    assert CampaignPreparation.from_bytes(plan.request, saved.canonical, packet.canonical) == saved


def test_denial_is_explicit_original_head_gap_and_never_empty_success():
    plan, intent, _ = case()
    class Denied:
        def read(self, path, ref, window):
            window.start()
            raise ValueError('knowledge_access_denied')
    context = CurationKnowledgeReader(Denied()).read(intent)
    projections, summary = context.rows()
    assert not projections and summary['graphs'][0]['status'] == 'unavailable'
    assert summary['graphs'][0]['reason'] == 'knowledge_access_denied'
    assert summary['graphs'][0]['calls'] == 1
    combined = plan.with_curation(intent).with_curation_knowledge(context)
    assert prepare(combined).packet is not None
    assert not any(row.lane == 'graph' for row in combined.slices)


def test_wrong_head_bytes_are_not_replaced_by_peer_latest():
    _, intent, peer = case()
    old = peer.records['/v1/graph-snapshots/read']
    peer.records['/v1/graph-snapshots/read'] = old.model_copy(update={
        'reference': old.reference.model_copy(update={'sha256': '0' * 64})})
    result = CurationKnowledgeReader(peer).read(intent)
    assert result.reads[0].failure == 'campaign_graph_invalid'
    assert not result.rows()[0]


def test_changed_coverage_is_rejected_before_slice_assembly():
    plan, intent, peer = case()
    result = CurationKnowledgeReader(peer).read(intent)
    with pytest.raises(ValueError, match='curation_knowledge_coverage'):
        plan.with_curation_knowledge(replace(result, reads=()))


def test_oversized_head_is_a_gap_instead_of_a_partial_graph():
    from ..campaign_knowledge_access.test_reader import repin, selected
    plan, intent, _ = case()
    selection, peer = selected()
    content = peer.records['/v1/graph-snapshots/read'].content
    original = content.entities[0]
    extra = tuple(original.model_copy(update={'reference': original.reference.model_copy(
        update={'entity_id': 'extra-' + str(index)})}) for index in range(257))
    selection = repin(selection, peer, content.model_copy(update={'entities': (*content.entities, *extra)}))
    value = json.loads(intent.canonical)['command']
    value['payload']['context']['knowledge'] = [selection.parts()[0].base.model_dump(mode='json')]
    incoming = CurationCommand.restore(json.dumps(value))
    intent = CurationIntent.from_template(plan.request, incoming, 'synthetic')
    result = CurationKnowledgeReader(peer).read(intent)
    assert result.reads[0].failure == 'campaign_graph_projection_limit'
    assert not result.rows()[0]


def test_collection_deadline_exhaustion_never_starts_another_read(monkeypatch):
    import amphora_agent_planning.curation_knowledge.reader as module
    _, intent, peer = case()
    clock = iter((0, 31))
    monkeypatch.setattr(module.time, 'monotonic', lambda: next(clock))
    result = CurationKnowledgeReader(peer).read(intent)
    assert result.reads[0].failure == 'knowledge_read_expired'
    assert not peer.calls


def test_retained_summary_cannot_omit_or_relabel_an_original_head():
    from amphora_agent_planning.curation_knowledge.validation import validate_knowledge
    plan, intent, peer = case()
    context = CurationKnowledgeReader(peer).read(intent)
    combined = plan.with_curation(intent).with_curation_knowledge(context)
    packet = prepare(combined).packet
    slices = json.loads(packet.canonical)['untrusted_context']['slices']
    validate_knowledge(plan.request, slices)
    summary = next(row for row in slices if row['lane'] == 'curation_knowledge')
    summary['payload']['graphs'].clear()
    with pytest.raises(ValueError, match='curation_knowledge_coverage'):
        validate_knowledge(plan.request, slices)
