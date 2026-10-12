import json
from types import SimpleNamespace

import pytest

from amphora_deployment.lifecycle import configuration
from amphora_deployment.lifecycle.planning_configuration import planning_environment
from amphora_deployment.profile import ProfileError


def settings():
    return {'principals': [{'actor_id': 'operator', 'scope': {'tenant_id': 't', 'project_id': 'p'},
        'token_env': 'AMPHORA_PLANNING_OPERATOR_TOKEN', 'actions': ['record_curations', 'read_curations']}]}


def test_legacy_mapping_is_unchanged_and_has_no_curation_opt_in():
    value = settings()
    value['topology_configuration'] = 'C:/owned/topology.json'
    result = planning_environment(value, {'AMPHORA_PLANNING_OPERATOR_TOKEN': 'original-secret'})
    assert result == {'AMPHORA_PLANNING_SUPERVISION_CREDENTIALS': json.dumps([{
        'actor_id': 'operator', 'scope': {'tenant_id': 't', 'project_id': 'p'},
        'actions': ['record_curations', 'read_curations'], 'token': 'original-secret'}]),
        'AMPHORA_PLANNING_TOPOLOGY_CONFIG': 'C:/owned/topology.json'}


@pytest.mark.parametrize('policies', [[], ['internal-curation-v1'], ['tenant:policy', 'other.v2']])
def test_explicit_reviewed_ids_are_the_only_added_environment(policies):
    value = settings() | {'curation_policies': policies}
    result = planning_environment(value, {'AMPHORA_PLANNING_OPERATOR_TOKEN': 'secret'})
    assert json.loads(result.pop('AMPHORA_PLANNING_CURATION_POLICIES')) == policies
    assert set(result) == {'AMPHORA_PLANNING_SUPERVISION_CREDENTIALS'}


@pytest.mark.parametrize('policies', ['arbitrary-env', None, {}, ['x'] * 2, [''], ['x' * 129],
    ['bad\n'], [1], [True], ['https://provider.example'], ['a'] * 33])
def test_unbounded_or_unreviewed_policy_configuration_rejects(policies):
    with pytest.raises(ProfileError):
        planning_environment(settings() | {'curation_policies': policies},
                             {'AMPHORA_PLANNING_OPERATOR_TOKEN': 'secret'})


def test_actual_manifest_binding_carries_policy_ids_without_extra_authority(tmp_path, monkeypatch):
    config = tmp_path / 'planning.json'
    config.write_text(json.dumps(settings() | {'curation_policies': ['internal-curation-v1']}), encoding='utf-8')
    manifest = tmp_path / 'owners.json'
    manifest.write_text(json.dumps({'profile': 'local-supervisor-v1', 'owners': {'planning': {
        'installation': str(tmp_path / 'installation'), 'source_lock': str(tmp_path / 'uv.lock'),
        'configuration': str(config), 'secret_references': ['PLANNING_OPERATOR_TOKEN']}}}), encoding='utf-8')
    monkeypatch.setattr(configuration.LocalState, 'snapshot', lambda _root: {
        'phase': 'stores_ready', 'deployment_id': 'isolated', 'postgres': {'host': '127.0.0.1', 'port': 12345}})
    bundle = SimpleNamespace(environment=lambda names: {name: 'test-only' for name in names})
    monkeypatch.setattr(configuration, 'CredentialVault', lambda *_args: SimpleNamespace(load=lambda: bundle))
    monkeypatch.setattr(configuration.OwnerInstallation, 'from_directory', lambda *_args: 'pinned-installation')
    result = configuration.load_bindings(tmp_path, manifest, SimpleNamespace(port=lambda _owner: 23456))['planning']
    assert json.loads(result.environment['AMPHORA_PLANNING_CURATION_POLICIES']) == ['internal-curation-v1']
    assert 'planning_service:' in result.environment['AMPHORA_PLANNING_DATABASE_URL']
    assert not any('MIGRAT' in name or 'OPENAI' in name for name in result.environment)
