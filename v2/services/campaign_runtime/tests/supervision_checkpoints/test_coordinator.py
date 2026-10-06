"""Real coordinator creates concrete slots while independent graph work proceeds."""

import copy
import json

from amphora_campaign_runtime.coordinator import (
    GraphAdmission,
    PlanCatalog,
    ReviewedPlan,
)
from amphora_campaign_runtime.coordinator.advance import GraphAdvancer
from amphora_campaign_runtime.supervision_checkpoints.storage import StoredCheckpoint
from amphora_campaign_runtime.supervision_policy import PolicyRecord, ReviewedPolicy
from amphora_campaign_runtime.supervision_policy.catalog import PolicyCatalog
from sqlalchemy import text

from ..compiler.conftest import definition
from ..supervision_policy.support import plan, policy
from ..supervision_policy.test_admission import command, reviewed, service


def slots(graph, run, admitted_policy):
    with graph.env.engine.connect() as conn:
        rows = conn.execute(text('SELECT * FROM runtime.supervision_checkpoints WHERE run_id=:run ORDER BY ordinal'),
                            {'run': run}).mappings().all()
    return tuple(StoredCheckpoint.from_row(row, admitted_policy) for row in rows)


def advance(graph, run):
    receipt = GraphAdvancer(graph.env.engine).advance(graph.env.principal,
        graph.command('graph.advance', {'run_id': run}))
    assert receipt.outcome.status == 'accepted'


def test_initial_checkpoint_does_not_hold_independent_ready_tool(graph_env):
    graph = graph_env
    raw = copy.deepcopy(graph.raw)
    other = copy.deepcopy(next(node for node in raw['body']['nodes'] if node['kind'] == 'invoke'))
    other['node_id'] = 'other'
    raw['body']['nodes'].append(other)
    raw['body']['edges'].append({'source': 'other', 'target': 'finish'})
    graph.entry = ReviewedPlan.compile(definition(raw), graph.source.tools, graph.source.schemas)
    graph.payload['plan_sha256'] = graph.entry.plan.sha256
    admitted_policy = reviewed(graph)
    receipt = service(graph, admitted_policy).admit_supervised(graph.env.principal, command(graph, admitted_policy))
    run = receipt.outcome.committed.object_id
    original = slots(graph, run, admitted_policy)
    assert len(original) == 1
    with graph.env.engine.connect() as conn:
        rows = conn.execute(text("SELECT node_id,status FROM runtime.graph_nodes WHERE run_id=:run AND kind='invoke'"),
                            {'run': run}).all()
        assert dict(rows) == {'affine': 'ready', 'other': 'issued'}
        assert conn.execute(text('SELECT count(*) FROM runtime.activations WHERE run_id=:run'), {'run': run}).scalar_one() == 1
    advance(graph, run)
    assert slots(graph, run, admitted_policy) == original


def test_scatter_members_get_distinct_slots_and_policy_ceiling_remains_campaign_wide(graph_env):
    graph = graph_env
    raw = copy.deepcopy(graph.source.raw[2])
    raw['scope'] = graph.env.principal.scope.model_dump(mode='json')
    graph.entry = ReviewedPlan.compile(definition(raw), graph.source.tools, graph.source.schemas)
    item = graph.payload['inputs'][0]['value']
    graph.payload = {'plan_sha256': graph.entry.plan.sha256, 'inputs': [
        {'port': 'items', 'value': {'kind': 'collection', 'items': [item, copy.deepcopy(item)]}}], 'budget': {'limit': 4}}
    record = PolicyRecord.model_validate_json(json.dumps({'scope': raw['scope'], 'plan_sha256': graph.entry.plan.sha256,
        'ceilings': {'max_checkpoints': 1, 'max_requests': 1, 'max_model_calls': 1}, 'checkpoints': [{
            'checkpoint_id': 'member-review', 'target': {'scope_path': ['batch'], 'node_id': 'map'}, 'kind': 'invoke',
            'timeout_seconds': 30, 'max_requests': 1, 'max_model_calls': 1, 'fallback': 'continue_unchanged'}]}))
    admitted_policy = ReviewedPolicy.bind(graph.entry.plan, record)
    receipt = service(graph, admitted_policy).admit_supervised(graph.env.principal, command(graph, admitted_policy))
    run = receipt.outcome.committed.object_id
    assert slots(graph, run, admitted_policy) == ()
    advance(graph, run)
    original = slots(graph, run, admitted_policy)
    assert len(original) == 2 and len({slot.seed.decision_id for slot in original}) == 2
    assert [slot.eligibility for slot in original] == ['requestable', 'fallback_required']
    assert {slot.seed.footprint().observations[0].view.path.occurrences[0].index for slot in original} == {0, 1}
    advance(graph, run)
    assert slots(graph, run, admitted_policy) == original
    with graph.env.engine.connect() as conn:
        assert conn.execute(text('SELECT count(*) FROM runtime.activations WHERE run_id=:run'), {'run': run}).scalar_one() == 0


def test_loop_materialization_is_checkpointed_after_actual_scope_expansion(graph_env):
    graph = graph_env
    compiled = plan(nested=True, scope=graph.env.principal.scope.model_dump(mode='json'))
    graph.entry = ReviewedPlan(compiled, ())
    graph.payload = {'plan_sha256': compiled.sha256, 'inputs': [], 'budget': {'limit': 2}}
    admitted_policy = ReviewedPolicy.bind(compiled, policy(compiled, nested=True))
    admission = GraphAdmission(graph.env.engine, PlanCatalog([graph.entry]), bindings_enabled=True,
                               policies=PolicyCatalog([admitted_policy]))
    receipt = admission.admit_supervised(graph.env.principal, command(graph, admitted_policy))
    run = receipt.outcome.committed.object_id
    advance(graph, run)
    original = slots(graph, run, admitted_policy)
    assert len(original) == 1
    target = original[0].seed.footprint().observations[0].view
    assert target.kind == 'artifact_materialize' and target.path.occurrences[0].index == 0
    assert original[0].seed.document().profile == 'runtime-supervision-checkpoint.v2'
    assert original[0].seed.document().original_fields[0].value.value == 1
    assert len(original[0].seed.original_fields_sha256) == 64
    advance(graph, run)
    assert slots(graph, run, admitted_policy) == original
    with graph.env.engine.connect() as conn:
        assert conn.execute(text('SELECT count(*) FROM runtime.binding_intents WHERE run_id=:run'), {'run': run}).scalar_one() == 0
