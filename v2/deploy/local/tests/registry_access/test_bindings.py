import json
import os
from types import SimpleNamespace

import pytest
from amphora_deployment.credentials import CredentialVault, SecretBundle
from amphora_deployment.installation import SERVING_HOSTS
from amphora_deployment.lifecycle.configuration import load_bindings
from amphora_deployment.persistence.state import LocalState
from amphora_deployment.profile import ProfileError
from amphora_deployment.registry_access import provision_registry_credential

pytestmark = pytest.mark.skipif(os.name != 'nt', reason='Selected Windows DPAPI profile')


def installation(root, monkeypatch):
    with LocalState(root) as state:
        state.record.update(phase='stores_ready', postgres={'host': '127.0.0.1', 'port': 15432})
        state.save()
        values = {'PG_' + SERVING_HOSTS[owner].service_role.upper() + '_PASSWORD': 'synthetic-password'
                  for owner in ('runtime', 'registry')}
        CredentialVault(root / 'credentials.dpapi', state.identity).create(SecretBundle(values))
    # This test qualifies credential selection, not package inventory verification.
    monkeypatch.setattr('amphora_deployment.lifecycle.configuration.OwnerInstallation.from_directory',
                        lambda *args: SimpleNamespace(owner=args[0]))
    return SimpleNamespace(port=lambda owner: 18080)


def manifest(root, reference=None, owners=('runtime', 'registry')):
    configuration = root / 'owner.json'
    configuration.write_text('{}')
    value = {'profile': 'local-supervisor-v1', 'owners': {
        owner: {'installation': str(root / 'installation'), 'source_lock': str(root / 'uv.lock'),
                'configuration': str(configuration), 'secret_references': [] if reference is None else [reference]}
        for owner in owners}}
    path = root / 'owners.json'
    path.write_text(json.dumps(value))
    return path


def test_actual_decryption_selects_same_peer_only_for_endpoint_owners(tmp_path, monkeypatch):
    routes = installation(tmp_path, monkeypatch)
    original = (tmp_path / 'credentials.dpapi').read_bytes()
    provision_registry_credential(tmp_path)
    bindings = load_bindings(tmp_path, manifest(tmp_path, 'RUNTIME_REGISTRY_TOKEN'), routes)
    runtime = bindings['runtime'].environment
    registry = bindings['registry'].environment
    assert runtime['AMPHORA_RUNTIME_REGISTRY_TOKEN'] == registry['AMPHORA_RUNTIME_REGISTRY_TOKEN']
    assert set(runtime) == {'AMPHORA_RUNTIME_REGISTRY_TOKEN', SERVING_HOSTS['runtime'].database_environment}
    assert set(registry) == {'AMPHORA_RUNTIME_REGISTRY_TOKEN', SERVING_HOSTS['registry'].database_environment}
    assert (tmp_path / 'credentials.dpapi').read_bytes() == original


def test_legacy_manifest_never_requires_peer_sidecar(tmp_path, monkeypatch):
    routes = installation(tmp_path, monkeypatch)
    bindings = load_bindings(tmp_path, manifest(tmp_path), routes)
    assert set(bindings) == {'runtime', 'registry'}
    assert not (tmp_path / 'runtime-registry.dpapi').exists()
    assert all('AMPHORA_RUNTIME_REGISTRY_TOKEN' not in binding.environment for binding in bindings.values())


@pytest.mark.parametrize('owner', ['artifact', 'knowledge', 'planning', 'gateway'])
def test_manifest_rejects_peer_reference_before_disclosing_to_other_owner(tmp_path, monkeypatch, owner):
    routes = installation(tmp_path, monkeypatch)
    provision_registry_credential(tmp_path)
    with pytest.raises(ProfileError, match='lifecycle_credential_scope'):
        load_bindings(tmp_path, manifest(tmp_path, 'RUNTIME_REGISTRY_TOKEN', (owner,)), routes)
