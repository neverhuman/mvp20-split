import os

import pytest
from amphora_deployment.credentials import CredentialVault, SecretBundle
from amphora_deployment.persistence.state import LocalState
from amphora_deployment.profile import ProfileError
from amphora_deployment.tool_catalog.credentials import (
    provision_worker_credential,
    worker_credential,
    worker_vault,
)

pytestmark = pytest.mark.skipif(os.name != 'nt', reason='Selected Windows DPAPI profile')


def installation(tmp_path):
    with LocalState(tmp_path) as state:
        state.record['phase'] = 'stores_ready'
        state.save()
        CredentialVault(tmp_path / 'credentials.dpapi', state.identity).create(SecretBundle({'ORIGINAL': 'private-original'}))
        return state.identity


def test_heartbeat_credential_is_separate_repeatable_and_never_replaces_original(tmp_path):
    identity = installation(tmp_path)
    original = (tmp_path / 'credentials.dpapi').read_bytes()
    first = provision_worker_credential(tmp_path)
    protected = (tmp_path / 'tool-catalog.dpapi').read_bytes()
    assert first == provision_worker_credential(tmp_path)
    assert (tmp_path / 'credentials.dpapi').read_bytes() == original
    assert (tmp_path / 'tool-catalog.dpapi').read_bytes() == protected
    bundle = worker_credential(tmp_path, identity)
    assert bundle.names == ('WORKER_REGISTRY_TOKEN',)
    secret = bundle.environment(bundle.names)['WORKER_REGISTRY_TOKEN']
    assert secret not in repr(bundle) and secret not in str(first) and secret.encode() not in protected
    assert set(first) == {'status', 'reference', 'original_vault_changed'}


def test_corrupt_existing_sidecar_is_not_silently_regenerated(tmp_path):
    installation(tmp_path)
    path = tmp_path / 'tool-catalog.dpapi'
    path.write_bytes(b'incomplete')
    with pytest.raises(ProfileError):
        provision_worker_credential(tmp_path)
    assert path.read_bytes() == b'incomplete'


def test_sidecar_rejects_extra_credentials_and_wrong_deployment(tmp_path):
    identity = installation(tmp_path)
    worker_vault(tmp_path, identity).create(SecretBundle({'WORKER_REGISTRY_TOKEN': 'synthetic', 'UNRELATED': 'private'}))
    with pytest.raises(ProfileError, match='credential_scope'):
        worker_credential(tmp_path, identity)
    with pytest.raises(ProfileError):
        worker_credential(tmp_path, 'foreign-deployment')
