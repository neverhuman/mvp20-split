import json
from types import SimpleNamespace

import pytest

from amphora_deployment.campaign_launch import configuration as module
from amphora_deployment.campaign_launch.configuration import LaunchInstallation, LaunchManifest
from amphora_deployment.campaign_launch.intent import LaunchError
from amphora_deployment.campaign_launch.profile import profile_digest
from amphora_deployment.scientific_workers.configuration import ScientificBinding
from amphora_deployment.scientific_workers.profiles import ToolProfile


@pytest.fixture
def startup_setup(tmp_path, monkeypatch, make_intent):
    certificate = tmp_path / 'certificate.pem'; certificate.write_bytes(b'fixture-trust')
    config = tmp_path / 'tool.json'
    scope = {'tenant_id': 'internal', 'project_id': 'demo'}
    config.write_text(json.dumps({'actor_id': 'worker', 'scope': scope, 'run_id': 'template-run',
        'image_sha256': 'a' * 64,
        'runtime': {'endpoint': 'https://host.docker.internal:57118', 'token_env': 'AMPHORA_RUNTIME_TOKEN'},
        'artifacts': {'endpoint': 'https://host.docker.internal:57112', 'token_env': 'AMPHORA_ARTIFACT_TOKEN'}}))
    profile = ToolProfile.pin('hansen-solvency', 'sha256:' + 'a' * 64, config, certificate, 57118, 57112)
    binding = ScientificBinding.pin(tmp_path, 'b' * 32, profile,
        {'AMPHORA_RUNTIME_TOKEN': 'private-runtime', 'AMPHORA_ARTIFACT_TOKEN': 'private-artifact'})
    monkeypatch.setattr(module, 'load_scientific_templates', lambda *args: {'hansen-solvency': binding})
    policy = {'reference': {'profile_id': 'scientific', 'version': '1', 'sha256': '0' * 64},
        'scope': scope, 'title': 'Installed science', 'tools': [{'capability_id': 'materials.hansen-solvency',
            'release': '0.1.0', 'contract_version': '1', 'image_sha256': 'a' * 64}],
        'maximum_invocations': 8, 'maximum_deadline_seconds': 3600}
    policy['reference']['sha256'] = profile_digest(policy)
    policy_path = tmp_path / 'launch-profile.json'; policy_path.write_text(json.dumps(policy))
    science = tmp_path / 'science.json'; science.write_text('{}')
    catalog = tmp_path / 'catalog.json'
    catalog.write_text(json.dumps({'profile': 'local-tool-catalog-v1', 'scope': scope, 'worker_id': 'worker',
        'replicas': {'hansen-solvency': {'deployment_id': 'installed', 'replica_id': 'replica',
                                       'binding_sha256': profile.fingerprint}}}))
    manifest_path = tmp_path / 'launch.json'
    manifest_path.write_text(json.dumps({'profile': 'local-campaign-launch-v1', 'actor_id': 'researcher',
        'launch_profile': str(policy_path), 'scientific_manifest': str(science), 'catalog_manifest': str(catalog)}))
    access = {'runtime': SimpleNamespace(port=57118), 'artifact': SimpleNamespace(port=57112)}
    manifest = LaunchManifest.load(manifest_path)
    installation = LaunchInstallation(tmp_path, 'b' * 32, manifest, access)
    return installation, make_intent(profile=policy['reference']['sha256']), access


def test_startup_recovers_admitted_binding_before_pending_container_check(startup_setup, admission_receipt, clock, monkeypatch):
    installation, intent, access = startup_setup
    journal = installation.journal
    journal.submit(intent, installation.policy.check, now=clock)
    installation.pin_intent(intent)
    journal.change(intent.key, 0, lambda s: s.move('admission_unresolved', clock()))
    state = journal.change(intent.key, 1, lambda s: s.observe_admission(admission_receipt(intent), clock()))
    expected = installation.store.prepare(state)['hansen-solvency']
    checked = []
    def guard(root, identity, profiles):
        checked.append([profile.fingerprint for profile in profiles])
        assert checked[-1] == [expected.profile.fingerprint]
    monkeypatch.setattr(module, 'require_configured_pending', guard)
    restarted = LaunchInstallation(installation.root, installation.deployment_id, installation.manifest, access)
    actual = restarted.startup_bindings()['hansen-solvency']
    assert actual.profile == expected.profile and len(checked) == 1
    assert actual.profile != installation.templates['hansen-solvency'].profile


def test_unresolved_admission_requires_original_installation_pin(startup_setup, clock):
    installation, intent, _ = startup_setup
    installation.journal.submit(intent, installation.policy.check, now=clock)
    installation.journal.change(intent.key, 0, lambda s: s.move('admission_unresolved', clock()))
    with pytest.raises(LaunchError, match='launch_installation_pin_missing'):
        installation.startup_bindings()


def test_catalog_rebinding_preserves_replica_identity(startup_setup, admission_receipt, clock, monkeypatch):
    installation, intent, _ = startup_setup
    from amphora_deployment.campaign_launch.state import LaunchState
    state = LaunchState.initial(intent, clock()).move('admission_unresolved', clock())
    state = state.observe_admission(admission_receipt(intent), clock())
    bindings = installation.store.prepare(state)
    monkeypatch.setattr(module, 'load_catalog', lambda path, *args: json.loads(path.read_bytes()))
    result = installation.catalog(object(), bindings, object())
    row = result['replicas']['hansen-solvency']
    assert (row['deployment_id'], row['replica_id']) == ('installed', 'replica')
    assert row['binding_sha256'] == bindings['hansen-solvency'].profile.fingerprint
    assert result == installation.catalog(object(), bindings, object())


def test_changed_operator_configuration_is_not_silently_reloaded(startup_setup):
    installation, intent, _ = startup_setup
    installation.manifest.catalog_path.write_text('{}')
    with pytest.raises(LaunchError, match='launch_installation_configuration_changed'):
        installation.pin_intent(intent)
