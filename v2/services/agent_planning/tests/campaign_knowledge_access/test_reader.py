import hashlib
import json
from dataclasses import replace

import pytest
from amphora_agent_planning.campaign_knowledge_access import (
    CampaignGraphSelection,
    CampaignKnowledgeReader,
)
from amphora_agent_planning.graph_context import GraphPins
from amphora_agent_planning.graph_context.records import canonical
from amphora_agent_planning.knowledge_access.transport import KnowledgeReadWindow

from ..campaign_context.test_selection import SCOPE, request
from ..knowledge_access.test_reader import inputs


def selected(history=True):
    task, peer, _ = inputs(history, scope=SCOPE)
    target = task.document().target
    selection = CampaignGraphSelection.bind(request(), GraphPins(target.graph, target.base, target.vocabulary, target.policy),
        task.document().existing_entities, task.document().existing_assertions)
    return selection, peer


def repin(selection, peer, content):
    pins, entities, assertions = selection.parts()
    snapshot = peer.records['/v1/graph-snapshots/read']
    ref = snapshot.reference.model_copy(update={'sha256': hashlib.sha256(canonical(content)).hexdigest()})
    peer.records['/v1/graph-snapshots/read'] = snapshot.model_copy(update={'content': content, 'reference': ref})
    change = peer.records['/v1/graph-changes/read']
    content = change.content.model_copy(update={'resulting_snapshot': ref})
    change_ref = change.reference.model_copy(update={'sha256': hashlib.sha256(canonical(content)).hexdigest()})
    peer.records['/v1/graph-changes/read'] = change.model_copy(update={'content': content, 'reference': change_ref})
    return CampaignGraphSelection.bind(selection.request,
        replace(pins, base=pins.base.model_copy(update={'snapshot': ref, 'change': change_ref})), entities, assertions)


@pytest.mark.parametrize('history', [False, True], ids=['genesis', 'historical'])
def test_exact_original_pins_without_extraction_task_or_latest_lookup(history):
    selection, peer = selected(history)
    result = CampaignKnowledgeReader(peer).read(selection)
    assert result.failure is None and result.context is not None and result.selection == selection
    assert result.calls == (3 if history else 1)
    assert [path for path, _ in peer.calls] == list(peer.records)
    assert result.context.snapshot_bytes is None if not history else result.context.snapshot().reference == selection.parts()[0].base.snapshot
    assert CampaignGraphSelection.bind(selection.request, *selection.parts()).sha256 == selection.sha256
    if history:
        assert peer.calls[1][1] == selection.parts()[0].base.snapshot
        assert peer.calls[2][1] == selection.parts()[0].base.change


def test_historical_retracted_and_aliased_selected_records_remain_visible():
    selection, peer = selected()
    content = peer.records['/v1/graph-snapshots/read'].content
    # Use public snapshot record types, retaining old revisions beside their successors.
    from amphora_contracts_knowledge.snapshots import AssertionRetraction, EntityAlias
    old = content.entities[0]
    newer = old.model_copy(update={'reference': old.reference.model_copy(update={'revision': 2}), 'supersedes': old.reference})
    content = content.model_copy(update={
        'entities': (*content.entities, newer),
        'aliases': (EntityAlias(source=content.entities[1].reference, target=content.entities[2].reference, change_id='fixture-alias'),),
        'retractions': (AssertionRetraction(assertion=content.assertions[0].reference, change_id='fixture-retraction'),),
    })
    selection = repin(selection, peer, content)
    result = CampaignKnowledgeReader(peer).read(selection)
    assert result.failure is None
    facts = result.context.index()
    assert old.reference in facts.entities and newer.reference in facts.entities
    assert facts.retracted == {content.assertions[0].reference}
    assert facts.resolve(content.entities[1].reference) == content.entities[2].reference
    with pytest.raises(ValueError, match='stale_entity_revision'):
        facts.entity(old.reference, editable=True)
    with pytest.raises(ValueError, match='assertion_retracted'):
        facts.assertion(content.assertions[0].reference)


@pytest.mark.parametrize('reason', [
    'knowledge_access_denied', 'knowledge_reference_unavailable', 'knowledge_peer_unavailable', 'knowledge_peer_media',
    'knowledge_response_limit', 'knowledge_peer_protocol', 'knowledge_read_expired', 'knowledge_read_call_limit', 'knowledge_read_byte_limit',
])
def test_explicit_failure_never_returns_partial_graph(reason):
    selection, peer = selected()
    original = peer.read
    def read(path, reference, window):
        if path.endswith('snapshots/read'):
            window.start()
            raise ValueError(reason)
        return original(path, reference, window)
    peer.read = read
    result = CampaignKnowledgeReader(peer).read(selection)
    assert result.context is None and result.failure == reason and result.calls == 2


@pytest.mark.parametrize('variant', ['profile', 'snapshot', 'change', 'boolean_revision', 'missing_entity', 'missing_assertion'])
def test_untrustworthy_owner_records_are_explicitly_invalid(variant):
    selection, peer = selected()
    if variant in {'missing_entity', 'missing_assertion'}:
        pins, entities, assertions = selection.parts()
        if variant == 'missing_entity':
            entities = (entities[0].model_copy(update={'entity_id': 'absent'}),)
        else:
            assertions = (assertions[0].model_copy(update={'assertion_id': 'absent'}),)
        selection = CampaignGraphSelection.bind(selection.request, pins, entities, assertions)
    else:
        path = '/v1/graph-' + {'profile': 'profiles', 'snapshot': 'snapshots', 'change': 'changes', 'boolean_revision': 'snapshots'}[variant] + '/read'
        record = peer.records[path]
        if variant == 'profile':
            record = record.model_copy(update={'policy': record.policy.model_copy(update={'sha256': 'f' * 64})})
        elif variant == 'boolean_revision':
            record = record.model_copy(update={'content': record.content.model_copy(update={'revision': True})})
        else:
            record = record.model_copy(update={'reference': record.reference.model_copy(update={'sha256': 'f' * 64})})
        peer.records[path] = record
    result = CampaignKnowledgeReader(peer).read(selection)
    assert result.context is None and result.failure == 'campaign_graph_invalid'


def test_final_deadline_includes_validation_and_no_unknown_bug_is_swallowed():
    selection, peer = selected(False)
    window = KnowledgeReadWindow()
    original = peer.read
    def read(path, reference, window):
        record = original(path, reference, window)
        window.deadline = 0
        return record
    peer.read = read
    assert CampaignKnowledgeReader(peer).read(selection, window).failure == 'knowledge_read_expired'
    def broken(*args):
        raise ValueError('unexpected bug')
    peer.read = broken
    with pytest.raises(ValueError, match='unexpected bug'):
        CampaignKnowledgeReader(peer).read(selection)


@pytest.mark.parametrize('variant,reason', [
    ('foreign_graph', 'campaign_graph_scope'), ('foreign_entity', 'campaign_graph_scope'),
    ('duplicate', 'campaign_graph_duplicate'), ('count', 'campaign_graph_count'),
    ('list', 'campaign_graph_count'), ('genesis', 'campaign_graph_genesis'),
    ('head', 'graph_pin_head'), ('boolean', 'int'),
])
def test_selection_rejects_malformed_or_foreign_pins(variant, reason):
    selection, _ = selected()
    pins, entities, assertions = selection.parts()
    if variant == 'foreign_graph':
        pins = replace(pins, graph=pins.graph.model_copy(update={'scope': SCOPE.model_copy(update={'project_id': 'foreign'})}), base=None)
    elif variant == 'foreign_entity':
        entities = (entities[0].model_copy(update={'graph': pins.graph.model_copy(update={'graph_id': 'foreign'})}),)
    elif variant == 'duplicate':
        entities = (entities[0], entities[0])
    elif variant == 'count':
        entities = (entities[0],) * 257
    elif variant == 'list':
        entities = list(entities)
    elif variant == 'genesis':
        pins = replace(pins, base=None)
    elif variant == 'head':
        pins = replace(pins, base=pins.base.model_copy(update={'change': pins.base.change.model_copy(update={'position': 2})}))
    else:
        entities = (entities[0].model_copy(update={'revision': True}),)
    with pytest.raises(ValueError, match=reason):
        CampaignGraphSelection.bind(selection.request, pins, entities, assertions)


@pytest.mark.parametrize('variant,reason', [('shape', 'campaign_graph_shape'), ('count', 'campaign_graph_count'), ('size', 'campaign_graph_size')])
def test_forged_selection_revalidated_before_io(variant, reason):
    selection, peer = selected()
    value = json.loads(selection.canonical)
    if variant == 'shape':
        value['ignored'] = 'no'
    elif variant == 'count':
        value['entities'] = {}
    raw = b'x' * 262145 if variant == 'size' else json.dumps(value).encode()
    with pytest.raises(ValueError, match=reason):
        CampaignKnowledgeReader(peer).read(replace(selection, canonical=raw))
    assert not peer.calls


def test_request_identity_and_purpose_are_not_interchangeable():
    selection, _ = selected()
    value = selection.request.document().model_dump(mode='json')
    value['reference']['engagement_id'] = 'next-campaign'
    successor = CampaignGraphSelection.bind(request(value), *selection.parts())
    assert successor.canonical == selection.canonical and successor.sha256 != selection.sha256
    value['purpose'] = 'knowledge_decomposition'
    with pytest.raises(ValueError, match='campaign_graph_purpose'):
        CampaignGraphSelection.bind(request(value), *selection.parts())
