"""Actual admission pins before issuance; replay ignores replacement configuration."""

import json
import uuid

import pytest
from amphora_campaign_runtime.coordinator import (
    GraphAdmission,
    PlanCatalog,
    ReviewedPlan,
)
from amphora_campaign_runtime.coordinator.advance import GraphAdvancer
from amphora_campaign_runtime.coordinator.storage import GraphStorage
from amphora_campaign_runtime.supervision_policy import PolicyRecord, ReviewedPolicy
from amphora_campaign_runtime.supervision_policy.catalog import PolicyCatalog
from amphora_campaign_runtime.supervision_policy.storage import PolicyPins
from amphora_contracts_supervision import parse_supervised_admission
from sqlalchemy import text

from .support import plan, policy


def reviewed(graph):
    node = next(node for node in graph.entry.plan.document.definition.body.nodes if node.kind == 'invoke')
    record = PolicyRecord.model_validate_json(json.dumps({
        'scope': graph.env.principal.scope.model_dump(mode='json'), 'plan_sha256': graph.entry.plan.sha256,
        'ceilings': {'max_checkpoints': 5, 'max_requests': 5, 'max_model_calls': 5}, 'checkpoints': [{
            'checkpoint_id': 'review', 'target': {'scope_path': [], 'node_id': node.node_id}, 'kind': 'invoke',
            'timeout_seconds': 30, 'max_requests': 1, 'max_model_calls': 1, 'fallback': 'continue_unchanged'}]}))
    return ReviewedPolicy.bind(graph.entry.plan, record)


def command(graph, policy):
    return parse_supervised_admission(json.dumps({'encoding': 'amphora-command-v2', 'identity': {
        'scope': graph.env.principal.scope.model_dump(mode='json'), 'actor_id': graph.env.principal.actor_id,
        'command_family': 'graph.admit_supervised', 'command_id': uuid.uuid4().hex},
        'payload': {'admission': graph.payload, 'policy_sha256': policy.sha256}}))


def service(graph, policy):
    return GraphAdmission(graph.env.engine, PlanCatalog([graph.entry]), policies=PolicyCatalog([policy]))


def test_exact_policy_pinned_before_initial_issuance_and_survives_advancer_replacement(graph_env):
    graph = graph_env
    policy = reviewed(graph)
    original = command(graph, policy)
    receipt = service(graph, policy).admit_supervised(graph.env.principal, original)
    run = receipt.outcome.committed.object_id
    params = {'tenant': graph.env.principal.scope.tenant_id, 'project': graph.env.principal.scope.project_id, 'run': run}
    for _ in range(2):
        result = GraphAdvancer(graph.env.engine).advance(graph.env.principal,
            graph.command('graph.advance', {'run_id': run}))
        assert result.outcome.status == 'accepted'
        with graph.env.engine.connect() as conn:
            assert PolicyPins.load(conn, params, graph.entry.plan) == policy
            assert conn.execute(text('SELECT count(*) FROM runtime.activations WHERE run_id=:run'), params).scalar_one() == 0
            assert conn.execute(text("SELECT status FROM runtime.graph_nodes WHERE run_id=:run AND kind='invoke'"), params).scalar_one() == 'ready'
    replacement = GraphAdmission(graph.env.engine, PlanCatalog([]), policies=PolicyCatalog([]))
    assert replacement.admit_supervised(graph.env.principal, original) == receipt


@pytest.mark.parametrize('enabled', [False, True])
def test_missing_policy_rejection_leaves_no_run_and_replays_after_configuration_change(graph_env, enabled):
    graph = graph_env
    policy = reviewed(graph)
    original = command(graph, policy)
    admission = GraphAdmission(graph.env.engine, PlanCatalog([graph.entry]), policies=PolicyCatalog([]) if enabled else None)
    receipt = admission.admit_supervised(graph.env.principal, original)
    assert receipt.outcome.reason_code == ('supervision_policy_unavailable' if enabled else 'supervised_admission_not_enabled')
    assert service(graph, policy).admit_supervised(graph.env.principal, original) == receipt
    with graph.env.engine.connect() as conn:
        assert conn.execute(text('SELECT count(*) FROM runtime.runs WHERE project_id=:project'),
            {'project': graph.env.principal.scope.project_id}).scalar_one() == 0


def test_frontier_failure_rolls_back_policy_and_same_command_recovers(graph_env, monkeypatch):
    graph = graph_env
    policy = reviewed(graph)
    original = command(graph, policy)
    create = GraphStorage.create_scope

    def fail(*args, **kwargs):
        create(*args, **kwargs)
        raise RuntimeError('after-policy-and-frontier')

    monkeypatch.setattr(GraphStorage, 'create_scope', fail)
    with pytest.raises(RuntimeError, match='after-policy-and-frontier'):
        service(graph, policy).admit_supervised(graph.env.principal, original)
    with graph.env.engine.connect() as conn:
        for table in ('runs', 'graph_plans', 'graph_nodes', 'supervision_policies', 'audit_events'):
            assert conn.execute(text(f'SELECT count(*) FROM runtime.{table} WHERE project_id=:project'),
                {'project': graph.env.principal.scope.project_id}).scalar_one() == 0
    monkeypatch.setattr(GraphStorage, 'create_scope', create)
    assert service(graph, policy).admit_supervised(graph.env.principal, original).outcome.status == 'accepted'


def test_materialization_target_never_opens_binding_intent_before_checkpoint(graph_env):
    graph = graph_env
    compiled = plan(scope=graph.env.principal.scope.model_dump(mode='json'))
    graph.entry = ReviewedPlan(compiled, ())
    graph.payload = {'plan_sha256': compiled.sha256, 'inputs': [], 'budget': {'limit': 2}}
    reviewed_policy = ReviewedPolicy.bind(compiled, policy(compiled))
    admission = GraphAdmission(graph.env.engine, PlanCatalog([graph.entry]), bindings_enabled=True,
                               policies=PolicyCatalog([reviewed_policy]))
    receipt = admission.admit_supervised(graph.env.principal, command(graph, reviewed_policy))
    run = receipt.outcome.committed.object_id
    for _ in range(2):
        result = GraphAdvancer(graph.env.engine).advance(graph.env.principal,
            graph.command('graph.advance', {'run_id': run}))
        assert result.outcome.status == 'accepted'
        with graph.env.engine.connect() as conn:
            assert conn.execute(text('SELECT count(*) FROM runtime.binding_intents WHERE run_id=:run'),
                {'run': run}).scalar_one() == 0
            assert conn.execute(text("SELECT status FROM runtime.graph_nodes WHERE run_id=:run AND node_id='pack'"),
                {'run': run}).scalar_one() == 'ready'
