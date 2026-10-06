"""Versioned original recipe identity, admission atomicity and replacement."""

import json

import pytest
from amphora_campaign_runtime.coordinator import GraphAdmission, PlanCatalog
from amphora_campaign_runtime.coordinator.storage import GraphStorage
from amphora_campaign_runtime.lifecycle.model import TransitionError
from amphora_campaign_runtime.supervision_policy import PolicyRecord, ReviewedPolicy
from amphora_campaign_runtime.supervision_policy.catalog import PolicyCatalog
from amphora_campaign_runtime.supervision_policy.records import RecipePolicyRecord
from amphora_campaign_runtime.supervision_policy.storage import PolicyPins
from amphora_campaign_runtime.supervision_preparation.catalog import RecipeCatalog
from amphora_campaign_runtime.supervision_preparation.storage import RecipePins
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from ..supervision_policy.test_admission import command, reviewed
from .test_recipe import bind, document


def configuration(graph):
    data = document()
    scope = graph.env.principal.scope.model_dump(mode='json')
    data['scope'] = scope
    for ref in (data['objective'], data['prompt'], data['budget_policy'], data['model']['configuration'],
                *(item['artifact'] for item in (*data['entries'], *data['omissions']))):
        ref['scope'] = scope
    data['limits']['max_attempts'] = 1
    recipe = bind(data)
    original = reviewed(graph)
    record = original.document().model_dump(mode='json')
    record.update(profile='runtime-supervision-policy.v2', context_recipe_sha256=recipe.sha256)
    policy = ReviewedPolicy.bind(graph.entry.plan, RecipePolicyRecord.model_validate_json(json.dumps(record)))
    return recipe, policy


def service(graph, policy, recipes):
    return GraphAdmission(graph.env.engine, PlanCatalog([graph.entry]), policies=PolicyCatalog([policy]), recipes=recipes)


def test_profile_v1_stays_closed_and_recipe_is_exact(graph_env):
    recipe, policy = configuration(graph_env)
    with pytest.raises(ValueError):
        PolicyRecord.model_validate_json(policy.canonical)
    assert ReviewedPolicy.from_bytes(policy.plan, policy.canonical) == policy
    assert RecipeCatalog([recipe]).require(policy) == recipe
    with pytest.raises(TransitionError, match='duplicate_reviewed_recipe'):
        RecipeCatalog([recipe, recipe])
    with pytest.raises(TransitionError, match='supervision_recipe_unavailable'):
        RecipeCatalog([]).require(policy)
    with pytest.raises(ValueError, match='recipe_policy_profile'):
        recipe.require_policy(reviewed(graph_env))
    data = recipe.document().model_dump(mode='json')
    data['model']['model_revision'] = 'changed'
    with pytest.raises(ValueError, match='recipe_policy_binding'):
        bind(data).require_policy(policy)


def test_pins_survive_replacement_and_original_receipt_ignores_configuration(graph_env):
    graph = graph_env
    recipe, policy = configuration(graph)
    request = command(graph, policy)
    receipt = service(graph, policy, RecipeCatalog([recipe])).admit_supervised(graph.env.principal, request)
    assert receipt.outcome.status == 'accepted'
    params = {'tenant': graph.env.principal.scope.tenant_id, 'project': graph.env.principal.scope.project_id,
              'run': receipt.outcome.committed.object_id}
    with graph.env.engine.begin() as conn:
        assert PolicyPins.load(conn, params, graph.entry.plan) == policy
        assert RecipePins.load(conn, params, policy) == recipe
        for sql in ['UPDATE runtime.supervision_recipes SET recipe_sha256=recipe_sha256',
                    'DELETE FROM runtime.supervision_recipes']:
            with pytest.raises(DBAPIError), conn.begin_nested():
                conn.execute(text(sql))
        assert conn.execute(text('SELECT count(*) FROM runtime.activations WHERE run_id=:run'), params).scalar_one() == 0
    replacement = GraphAdmission(graph.env.engine, PlanCatalog([]))
    assert replacement.admit_supervised(graph.env.principal, request) == receipt


@pytest.mark.parametrize('enabled', [True, False])
def test_missing_recipe_fails_before_run_and_does_not_reconsider_receipt(graph_env, enabled):
    graph = graph_env
    recipe, policy = configuration(graph)
    request = command(graph, policy)
    receipt = service(graph, policy, RecipeCatalog([]) if enabled else None).admit_supervised(graph.env.principal, request)
    assert receipt.outcome.reason_code == 'supervision_recipe_unavailable'
    assert service(graph, policy, RecipeCatalog([recipe])).admit_supervised(graph.env.principal, request) == receipt
    with graph.env.engine.connect() as conn:
        assert conn.execute(text('SELECT count(*) FROM runtime.runs WHERE project_id=:project'),
                            {'project': graph.env.principal.scope.project_id}).scalar_one() == 0


def test_recipe_and_policy_and_frontier_rollback_together(graph_env, monkeypatch):
    graph = graph_env
    recipe, policy = configuration(graph)
    request = command(graph, policy)
    admission = service(graph, policy, RecipeCatalog([recipe]))
    create = GraphStorage.create_scope

    def fail(*args):
        create(*args)
        raise RuntimeError('recipe-frontier-abort')

    monkeypatch.setattr(GraphStorage, 'create_scope', fail)
    with pytest.raises(RuntimeError, match='recipe-frontier-abort'):
        admission.admit_supervised(graph.env.principal, request)
    with graph.env.engine.connect() as conn:
        for table in ['supervision_policies', 'supervision_recipes', 'runs']:
            assert conn.execute(text(f'SELECT count(*) FROM runtime.{table} WHERE project_id=:project'),
                                {'project': graph.env.principal.scope.project_id}).scalar_one() == 0
    monkeypatch.setattr(GraphStorage, 'create_scope', create)
    assert admission.admit_supervised(graph.env.principal, request).outcome.status == 'accepted'


def test_recipe_call_allowance_must_fit_original_slot(graph_env):
    recipe, policy = configuration(graph_env)
    data = recipe.document().model_dump(mode='json')
    data['limits']['max_attempts'] = 2
    too_large = bind(data)
    record = policy.document().model_dump(mode='json')
    record['context_recipe_sha256'] = too_large.sha256
    policy = ReviewedPolicy.bind(policy.plan, RecipePolicyRecord.model_validate_json(json.dumps(record)))
    with pytest.raises(TransitionError, match='recipe_policy_attempts'):
        RecipeCatalog([too_large]).require(policy)


@pytest.mark.parametrize('missing', [True, False])
def test_inconsistent_retained_recipe_prevents_frontier_exposure(graph_env, monkeypatch, missing):
    graph = graph_env
    recipe, policy = configuration(graph)

    def corrupt(conn, params, policy, recipe):
        if not missing:
            conn.execute(text('INSERT INTO runtime.supervision_recipes '
                '(tenant_id,project_id,run_id,recipe_sha256,canonical_recipe) '
                'VALUES (:tenant,:project,:run,:digest,:raw)'),
                {**params, 'digest': 'f' * 64, 'raw': recipe.canonical})

    monkeypatch.setattr(RecipePins, 'pin', corrupt)
    with pytest.raises(TransitionError, match='stored_supervision_recipe_' + ('missing' if missing else 'mismatch')):
        service(graph, policy, RecipeCatalog([recipe])).admit_supervised(graph.env.principal, command(graph, policy))
    with graph.env.engine.connect() as conn:
        assert conn.execute(text('SELECT count(*) FROM runtime.runs WHERE project_id=:project'),
                            {'project': graph.env.principal.scope.project_id}).scalar_one() == 0
