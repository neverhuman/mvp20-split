import os
import pytest

from amphora_deployment.campaign_launch.credentials import launch_credential, launch_vault, provision_launch_credential
from amphora_deployment.credentials import CredentialVault, SecretBundle
from amphora_deployment.lifecycle.configuration import allowed_reference
from amphora_deployment.persistence.state import LocalState
from amphora_deployment.profile import ProfileError

pytestmark = pytest.mark.skipif(os.name != 'nt', reason='Selected Windows DPAPI profile')


def installation(root):
    with LocalState(root) as state:
        state.record['phase'] = 'stores_ready'; state.save()
        CredentialVault(root / 'credentials.dpapi', state.identity).create(SecretBundle({'ORIGINAL': 'fixture-original'}))
        return state.identity


def test_create_once_launch_grant_preserves_original_vault_and_has_no_control_authority(tmp_path):
    identity = installation(tmp_path)
    original = (tmp_path / 'credentials.dpapi').read_bytes()
    first = provision_launch_credential(tmp_path)
    protected = launch_vault(tmp_path, identity).path.read_bytes()
    assert provision_launch_credential(tmp_path) == first
    assert (tmp_path / 'credentials.dpapi').read_bytes() == original
    assert launch_vault(tmp_path, identity).path.read_bytes() == protected
    bundle = launch_credential(tmp_path, identity)
    secret = bundle.environment(['LAUNCH_GATEWAY_TOKEN'])['LAUNCH_GATEWAY_TOKEN']
    assert len(secret) >= 32 and secret.encode() not in protected and secret not in str(first)
    assert allowed_reference('gateway', 'LAUNCH_GATEWAY_TOKEN')
    for owner in ('runtime', 'artifact', 'registry', 'research', 'knowledge', 'planning'):
        assert not allowed_reference(owner, 'LAUNCH_GATEWAY_TOKEN')


def test_corrupt_launch_grant_is_never_regenerated(tmp_path):
    identity = installation(tmp_path)
    path = launch_vault(tmp_path, identity).path
    path.write_bytes(b'incomplete')
    with pytest.raises(ProfileError): provision_launch_credential(tmp_path)
    assert path.read_bytes() == b'incomplete'
