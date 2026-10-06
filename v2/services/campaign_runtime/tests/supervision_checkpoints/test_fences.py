"""Actual retained observations and scope membership are the freshness authority."""

import copy
import json

import pytest
from amphora_campaign_runtime.compiler.addresses import ActivationAddress
from amphora_campaign_runtime.coordinator import (
    GraphAdmission,
    PlanCatalog,
    ReviewedPlan,
)
from amphora_campaign_runtime.coordinator.advance import GraphAdvancer
from amphora_campaign_runtime.coordinator.frontier import FrontierPlanner, ScopeAddress
from amphora_campaign_runtime.coordinator.storage import GraphStorage
from amphora_campaign_runtime.coordinator.values import BoundValues
from amphora_campaign_runtime.graph_inspection.policy import node_view
from amphora_campaign_runtime.lifecycle.authority import AuthorityCommands
from amphora_campaign_runtime.lifecycle.claims import RuntimeLeases
from amphora_campaign_runtime.supervision_checkpoints.storage import CheckpointStore
from amphora_campaign_runtime.supervision_checkpoints.values import ValueCheckpointSeed
from amphora_campaign_runtime.supervision_journal.current import verify_footprint
from amphora_campaign_runtime.supervision_policy import PolicyRecord, ReviewedPolicy
from amphora_campaign_runtime.supervision_policy.catalog import PolicyCatalog
from amphora_campaign_runtime.supervision_scope import NodeObservation
from amphora_campaign_runtime.supervision_scope.checkpoints import CheckpointFootprint
from amphora_contracts_campaigns import ActivationPath
from amphora_contracts_graph_runtime import GraphBinding, GraphReadCut
from sqlalchemy import text

from ..compiler.conftest import definition
from ..supervision_policy.support import plan, policy
from ..supervision_policy.test_admission import command, reviewed, service
from .test_coordinator import slots


def parallel(graph, *, selected):
    raw = copy.deepcopy(graph.raw)
    other = copy.deepcopy(next(node for node in raw['body']['nodes'] if node['kind'] == 'invoke'))
    other['node_id'] = 'other'
    raw['body']['nodes'].append(other)
    raw['body']['edges'].append({'source': 'other', 'target': 'finish'})
    graph.entry = ReviewedPlan.compile(definition(raw), graph.source.tools, graph.source.schemas)
    graph.payload['plan_sha256'] = graph.entry.plan.sha256
    data = reviewed(graph).document().model_dump(mode='json')
    if selected:
        data['checkpoints'][0]['reads'] = [{'scope_path': [], 'node_id': 'other'}]
    admitted_policy = ReviewedPolicy.bind(graph.entry.plan, PolicyRecord.model_validate_json(json.dumps(data)))
    receipt = service(graph, admitted_policy).admit_supervised(graph.env.principal, command(graph, admitted_policy))
    params = {'tenant': graph.env.principal.scope.tenant_id, 'project': graph.env.principal.scope.project_id,
              'run': receipt.outcome.committed.object_id}
    return params, slots(graph, params['run'], admitted_policy)[0]


def current(conn, params, original):
    run = conn.execute(text('SELECT * FROM runtime.runs WHERE run_id=:run FOR UPDATE'), params).mappings().one()
    graph = conn.execute(text('SELECT * FROM runtime.graph_runs WHERE run_id=:run'), params).mappings().one()
    old = original.seed.footprint()
    rows = conn.execute(text('SELECT * FROM runtime.graph_nodes WHERE run_id=:run AND activation_id=ANY(:ids)'),
        {**params, 'ids': [item.identity for item in old.observations]}).mappings().all()
    observations = tuple(NodeObservation.capture(old.cut.plan_sha256, node_view(row), state=row['state'], outputs=row['outputs'])
                         for row in rows)
    cut = GraphReadCut(scope=old.cut.scope, run_id=params['run'], plan_sha256=old.cut.plan_sha256,
                       revision=run['revision'], frontier_revision=graph['frontier_revision'])
    return run, CheckpointFootprint(cut, old.checkpoints, observations)


def test_relevant_change_requires_explicit_refresh_without_overwriting_original_slot(graph_env):
    graph = graph_env
    params, original = parallel(graph, selected=True)
    with graph.env.engine.begin() as conn:
        run, latest = current(conn, params, original)
        assert original.seed.footprint().compare(latest.cut, latest.observations).stale
        with pytest.raises(ValueError, match='selected_observation_changed'):
            verify_footprint(conn, params, run, original.seed.footprint())
        verify_footprint(conn, params, run, latest)
        refreshed = ValueCheckpointSeed.capture(original.seed.policy, latest, original.seed.document().original_fields)
        assert refreshed.decision_id == original.seed.decision_id and refreshed.sha256 != original.seed.sha256
        assert refreshed.original_fields_sha256 == original.seed.original_fields_sha256
        replay = CheckpointStore.ensure(conn, params, latest.observations[
            next(i for i, item in enumerate(latest.observations) if item.identity == latest.targets[0])].view.path)
        assert replay.checkpoint == original and not replay.created
    assert slots(graph, params['run'], original.seed.policy) == (original,)


def test_unrelated_real_worker_claim_progress_does_not_stale_target(graph_env):
    graph = graph_env
    params, original = parallel(graph, selected=False)
    claim = RuntimeLeases(graph.env.engine).claim(graph.env.principal, graph.command('runtime.claim', {
        'run_id': params['run'], 'worker_id': graph.env.principal.actor_id,
        'tool': graph.entry.descriptors[0].binding.model_dump(mode='json'), 'lease_seconds': 30}))
    assert claim.outcome.status == 'claimed'
    with graph.env.engine.begin() as conn:
        run, latest = current(conn, params, original)
        assert latest.cut.revision > original.seed.footprint().cut.revision
        assert not original.seed.footprint().compare(latest.cut, latest.observations).stale
        verify_footprint(conn, params, run, original.seed.footprint())
    receipt = AuthorityCommands(graph.env.engine).cancel(graph.env.principal, graph.command('runtime.cancel', {
        'run_id': params['run'], 'reason_code': 'test_complete'}))
    assert receipt.outcome.status == 'accepted'


def test_issued_worker_row_cannot_hide_behind_ready_graph_projection(graph_env):
    graph = graph_env
    params, original = parallel(graph, selected=False)
    with graph.env.engine.begin() as conn:
        conn.execute(text("INSERT INTO runtime.activations (tenant_id,project_id,run_id,activation_id,invocation_id,"
            "specification,status) VALUES (:tenant,:project,:run,:activation,'injected-issued-work','{}','queued')"),
            {**params, 'activation': original.seed.footprint().targets[0]})
        run, _ = current(conn, params, original)
        with pytest.raises(ValueError, match='target_already_materialized'):
            verify_footprint(conn, params, run, original.seed.footprint())


def test_forged_future_loop_scope_and_inactive_ancestor_reject(graph_env):
    graph = graph_env
    compiled = plan(nested=True, scope=graph.env.principal.scope.model_dump(mode='json'))
    graph.entry = ReviewedPlan(compiled, ())
    graph.payload = {'plan_sha256': compiled.sha256, 'inputs': [], 'budget': {'limit': 2}}
    admitted_policy = ReviewedPolicy.bind(compiled, policy(compiled, nested=True))
    admission = GraphAdmission(graph.env.engine, PlanCatalog([graph.entry]), bindings_enabled=True,
                               policies=PolicyCatalog([admitted_policy]))
    run = admission.admit_supervised(graph.env.principal, command(graph, admitted_policy)).outcome.committed.object_id
    GraphAdvancer(graph.env.engine).advance(graph.env.principal, graph.command('graph.advance', {'run_id': run}))
    original = slots(graph, run, admitted_policy)[0]
    params = {'tenant': graph.env.principal.scope.tenant_id, 'project': graph.env.principal.scope.project_id, 'run': run}
    future = ActivationPath.model_validate_json(json.dumps({'schema_version': '2', 'node_id': 'pack',
        'occurrences': [{'kind': 'loop', 'node_id': 'loop', 'index': 1}]}))
    with graph.env.engine.begin() as conn:
        with pytest.raises(ValueError, match='checkpoint_target_not_ready'):
            CheckpointStore.ensure(conn, params, future)
        address = ScopeAddress(compiled.sha256, future.occurrences)
        parent = ActivationAddress.for_plan(compiled, ActivationPath(schema_version='2', node_id='loop', occurrences=())).key
        values = BoundValues((GraphBinding.model_validate({'port': 'n', 'value': {'kind': 'integer', 'value': 0}}),))
        GraphStorage.create_scope(conn, params, address, values, FrontierPlanner().scope(compiled, address), parent=parent)
        with pytest.raises(ValueError, match='target_occurrence_mismatch'):
            CheckpointStore.ensure(conn, params, future)
        conn.execute(text("UPDATE runtime.graph_scopes SET status='blocked' WHERE run_id=:run AND scope_key=:scope"),
            {**params, 'scope': ScopeAddress(compiled.sha256).key})
        stored_run = conn.execute(text('SELECT * FROM runtime.runs WHERE run_id=:run'), params).mappings().one()
        with pytest.raises(ValueError, match='inactive_target_scope'):
            verify_footprint(conn, params, stored_run, original.seed.footprint())
        assert conn.execute(text('SELECT count(*) FROM runtime.supervision_checkpoints WHERE run_id=:run'), params).scalar_one() == 1
