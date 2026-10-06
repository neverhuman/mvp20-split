"""Actual Runtime SQL with a labeled scripted Artifact peer proves effective source-cut parity."""

import json
import time
from dataclasses import replace

import pytest
from amphora_campaign_runtime.artifact_bindings.coordinator import BindingCoordinator
from amphora_campaign_runtime.artifact_bindings.effective import resolve_effective
from amphora_campaign_runtime.compiler import (
    PinnedSchema,
    SchemaCatalog,
    SchemaIdentity,
)
from amphora_campaign_runtime.coordinator import PlanCatalog
from amphora_campaign_runtime.coordinator.advance import GraphAdvancer
from amphora_campaign_runtime.coordinator.projections import ProjectionUnavailable
from amphora_campaign_runtime.coordinator.state import ScopeState
from amphora_campaign_runtime.lifecycle.model import TransitionError
from sqlalchemy import text

from ..supervision_winners.support import prepare, setup
from .support import MemoryArtifacts


def coordinator(graph, actor, peer):
    node = next(node for node in graph.entry.plan.document.definition.body.nodes if node.node_id == 'pack')
    raw = b'{"additionalProperties":false,"properties":{"a":{"type":"integer"}},"required":["a"],"type":"object"}'
    schemas = SchemaCatalog([PinnedSchema(SchemaIdentity.from_wire(node.output.value_type.schema_ref), raw)])
    entry = replace(graph.entry, schemas=schemas)
    return BindingCoordinator(graph.env.engine, PlanCatalog([entry]), peer, peer)


def advance(graph, ref, bindings):
    return GraphAdvancer(graph.env.engine, bindings=bindings).advance(graph.env.principal,
        graph.command('graph.advance', {'run_id': ref.run_id}))


def intent(graph, ref):
    with graph.env.engine.connect() as conn:
        return conn.execute(text('SELECT * FROM runtime.binding_intents WHERE run_id=:run'),
            {'run': ref.run_id}).mappings().one()


def test_selected_scalar_opens_and_revalidates_identical_conversion_after_replacement(graph_env):
    store, actor, ref, slot = setup(graph_env)
    peer = MemoryArtifacts(actor.scope)
    bindings = coordinator(graph_env, actor, peer)
    # A recorded response is insufficient: the graph still has no conversion.
    response = prepare(graph_env, actor, ref, slot)
    assert advance(graph_env, ref, bindings).outcome.status == 'accepted'
    with graph_env.env.engine.connect() as conn:
        assert conn.execute(text('SELECT count(*) FROM runtime.binding_intents WHERE run_id=:run'),
            {'run': ref.run_id}).scalar_one() == 0
    winner = store.resolve(actor, ref, response_id=response)
    assert advance(graph_env, ref, bindings).outcome.status == 'accepted'
    opened = intent(graph_env, ref)
    assert opened['inputs'] == [{'port': 'a', 'value': {'kind': 'integer', 'value': 2, 'unit': '1'}}]
    assert opened['node']['fields'][0]['source']['value'] == 1
    assert opened['status'] == 'prepared'
    replacement = coordinator(graph_env, actor, peer)
    assert advance(graph_env, ref, replacement).outcome.status == 'accepted'
    closed = intent(graph_env, ref)
    assert closed['status'] == 'committed'
    assert closed['intent_id'] == opened['intent_id'] and closed['semantic_sha256'] == opened['semantic_sha256']
    assert list(peer.documents.values()) == [b'{"a":2}']
    assert store.read(actor, ref) == winner


def test_publication_denial_does_not_rewrite_selected_effect_as_execution_success(graph_env):
    store, actor, ref, slot = setup(graph_env)
    response = prepare(graph_env, actor, ref, slot)
    winner = store.resolve(actor, ref, response_id=response)
    peer = MemoryArtifacts(actor.scope)
    def denied(*args):
        raise TransitionError('fixture_publication_denied')
    peer.publish = denied
    bindings = coordinator(graph_env, actor, peer)
    advance(graph_env, ref, bindings)
    advance(graph_env, ref, bindings)
    closed = intent(graph_env, ref)
    assert closed['status'] == 'aborted' and closed['outputs'] is None
    assert closed['outcome']['reason_code'] == 'fixture_publication_denied'
    assert peer.documents == {} and store.read(actor, ref) == winner


def test_lost_publication_response_reuses_original_selected_cut(graph_env):
    store, actor, ref, slot = setup(graph_env)
    response = prepare(graph_env, actor, ref, slot)
    store.resolve(actor, ref, response_id=response)
    peer = MemoryArtifacts(actor.scope)
    bindings = coordinator(graph_env, actor, peer)
    advance(graph_env, ref, bindings)
    opened = intent(graph_env, ref)
    publish = peer.publish
    def lost(*args):
        publish(*args)
        peer.publish = publish
        raise ProjectionUnavailable('fixture_lost_publication')
    peer.publish = lost
    with pytest.raises(ProjectionUnavailable, match='fixture_lost_publication'):
        bindings.tick(actor)
    assert intent(graph_env, ref)['status'] == 'prepared'
    replacement = coordinator(graph_env, actor, peer)
    advance(graph_env, ref, replacement)
    closed = intent(graph_env, ref)
    assert closed['status'] == 'committed' and closed['semantic_sha256'] == opened['semantic_sha256']
    assert list(peer.documents.values()) == [b'{"a":2}']


def resolve_current(graph, ref, slot, *, original_value=None):
    params = {'tenant': ref.scope.tenant_id, 'project': ref.scope.project_id, 'run': ref.run_id}
    with graph.env.engine.connect() as conn:
        row = conn.execute(text("SELECT * FROM runtime.graph_nodes WHERE run_id=:run AND node_id='pack'"),
                           params).mappings().one()
        state = ScopeState.load(conn, params, slot.seed.policy.plan, row['scope_key'])
        node = state.definition(row)
        if original_value is not None:
            data = node.model_dump(mode='json')
            data['fields'][0]['source']['value'] = original_value
            node = type(node).model_validate_json(json.dumps(data))
        return resolve_effective(conn, params, row['activation_id'], node, state.environment)


def test_direct_conversion_cannot_bypass_pending_or_blocked_checkpoint(graph_env):
    store, actor, ref, slot = setup(graph_env, timeout=1, fallback='block_target')
    with pytest.raises(TransitionError, match='binding_checkpoint_pending'):
        resolve_current(graph_env, ref, slot)
    time.sleep(max(0, slot.deadline.timestamp() - time.time()) + 0.02)
    store.resolve(actor, ref)
    with pytest.raises(TransitionError, match='binding_checkpoint_blocked'):
        resolve_current(graph_env, ref, slot)


def test_overlay_rechecks_original_before_conversion(graph_env):
    store, actor, ref, slot = setup(graph_env)
    response = prepare(graph_env, actor, ref, slot)
    store.resolve(actor, ref, response_id=response)
    with pytest.raises(TransitionError, match='binding_supervision_original_changed'):
        resolve_current(graph_env, ref, slot, original_value=3)


def test_unchanged_fallback_materializes_original_value(graph_env):
    store, actor, ref, slot = setup(graph_env, timeout=1)
    time.sleep(max(0, slot.deadline.timestamp() - time.time()) + 0.02)
    store.resolve(actor, ref)
    peer = MemoryArtifacts(actor.scope)
    bindings = coordinator(graph_env, actor, peer)
    advance(graph_env, ref, bindings)
    advance(graph_env, ref, bindings)
    assert intent(graph_env, ref)['status'] == 'committed'
    assert list(peer.documents.values()) == [b'{"a":1}']
