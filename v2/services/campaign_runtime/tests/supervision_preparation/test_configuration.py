"""Exact file allowlists and opt-in authenticated supervised HTTP admission."""

import json

import pytest
from amphora_campaign_runtime.coordinator import PlanCatalog
from amphora_campaign_runtime.hosting import Host
from amphora_campaign_runtime.supervision_preparation.configuration import (
    admission_catalogs,
)
from fastapi.testclient import TestClient

from ..lifecycle.test_host_reads import config
from ..supervision_policy.test_admission import command
from .test_policy_pins import configuration


def files(graph, tmp_path):
    recipe, policy = configuration(graph)
    (tmp_path / 'policy.json').write_bytes(policy.canonical)
    (tmp_path / 'recipe.json').write_bytes(recipe.canonical)
    return {'policies': ['policy.json'], 'recipes': ['recipe.json']}, policy, recipe


def test_exact_allowlists_bind_scoped_plan_and_recipe(graph_env, tmp_path):
    raw, policy, recipe = files(graph_env, tmp_path)
    policies, recipes = admission_catalogs(raw, tmp_path, PlanCatalog([graph_env.entry]))
    assert policies.require(graph_env.env.principal.scope, policy.plan.sha256, policy.sha256) == policy
    assert recipes.require(policy) == recipe
    with pytest.raises(ValueError, match='graph_plan_unavailable'):
        admission_catalogs(raw, tmp_path, PlanCatalog([]))
    with pytest.raises(ValueError, match='supervision_admission_bounds'):
        admission_catalogs({**raw, 'recipes': []}, tmp_path, PlanCatalog([graph_env.entry]))


def test_configured_host_exposes_authenticated_replayable_admission(graph_env, tmp_path, monkeypatch):
    from amphora_campaign_runtime import hosting
    path, raw = config(graph_env.env, tmp_path, monkeypatch)
    allowlist, policy, _ = files(graph_env, tmp_path)
    # Compiler-input loading has its own real-file tests. This probe owns host wiring.
    monkeypatch.setattr(hosting, 'load_graphs', lambda *_: ((graph_env.entry, (), ()),))
    raw.update(graphs=[{}], supervision_admission=allowlist,
        artifacts={'runtime_owner': 'fixture', 'reserve_endpoint': 'http://127.0.0.1:1',
                   'token_env': 'TEST_RUNTIME_TOKEN'})
    path.write_text(json.dumps(raw), encoding='utf-8')
    host = Host.load(path)
    try:
        original = command(graph_env, policy)
        with TestClient(host.app()) as client:
            route = '/v1/graph-runs/supervised'
            assert client.post(route, content=original.canonical_bytes).status_code == 401
            headers = {'Authorization': 'Bearer ' + 'x' * 32}
            first = client.post(route, content=original.canonical_bytes, headers=headers)
            assert first.status_code == 200 and first.json()['outcome']['status'] == 'accepted'
            assert client.post(route, content=original.canonical_bytes, headers=headers).json() == first.json()
    finally:
        host.close()
