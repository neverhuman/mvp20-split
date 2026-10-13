import os

import pytest
from amphora_deployment.credentials import CredentialVault, SecretBundle
from amphora_deployment.lifecycle.configuration import allowed_reference
from amphora_deployment.persistence.state import LocalState
from amphora_deployment.profile import ProfileError
from amphora_deployment.curation_access import (
    provision_curation_credentials,
    curation_credentials,
    curation_vault,
)

pytestmark = pytest.mark.skipif(os.name != 'nt', reason='Selected Windows DPAPI profile')


def installation(root):
    with LocalState(root) as state:
        state.record['phase'] = 'stores_ready'
        state.save()
        CredentialVault(root / 'credentials.dpapi', state.identity).create(SecretBundle({'ORIGINAL': 'synthetic-original'}))
        return state.identity


def test_repeatable_peer_identity_preserves_original_and_never_discloses_values(tmp_path):
    identity = installation(tmp_path)
    original = (tmp_path / 'credentials.dpapi').read_bytes()
    first = provision_curation_credentials(tmp_path)
    protected = (tmp_path / 'planning-readers.dpapi').read_bytes()
    assert provision_curation_credentials(tmp_path) == first
    assert (tmp_path / 'credentials.dpapi').read_bytes() == original
    assert (tmp_path / 'planning-readers.dpapi').read_bytes() == protected
    bundle = curation_credentials(tmp_path, identity)
    assert set(bundle.names) == {'PLANNING_KNOWLEDGE_TOKEN', 'PLANNING_RESEARCH_TOKEN'}
    assert len(set(bundle.environment(bundle.names).values())) == 2
    secret = bundle.environment(bundle.names)['PLANNING_KNOWLEDGE_TOKEN']
    assert len(secret) >= 32
    assert secret not in repr(bundle) and secret not in str(first) and secret.encode() not in protected
    assert first == {'status': 'ready', 'references': ['PLANNING_KNOWLEDGE_TOKEN', 'PLANNING_RESEARCH_TOKEN'], 'original_vault_changed': False}


def test_corrupt_peer_identity_is_not_regenerated(tmp_path):
    installation(tmp_path)
    path = tmp_path / 'planning-readers.dpapi'
    path.write_bytes(b'incomplete')
    with pytest.raises(ProfileError):
        provision_curation_credentials(tmp_path)
    assert path.read_bytes() == b'incomplete'


def test_membership_and_deployment_are_exact(tmp_path):
    identity = installation(tmp_path)
    curation_vault(tmp_path, identity).create(SecretBundle({'PLANNING_KNOWLEDGE_TOKEN': 'synthetic', 'UNRELATED': 'synthetic'}))
    with pytest.raises(ProfileError, match='curation_reader_credential_scope'):
        curation_credentials(tmp_path, identity)
    with pytest.raises(ProfileError):
        curation_credentials(tmp_path, 'foreign-deployment')


@pytest.mark.parametrize('owner', ['artifact', 'runtime', 'research', 'gateway', 'registry'])
def test_peer_reference_never_reaches_other_owners(owner):
    assert not allowed_reference(owner, 'PLANNING_KNOWLEDGE_TOKEN')


def test_only_endpoint_owners_can_receive_peer_reference():
    assert allowed_reference('planning', 'PLANNING_KNOWLEDGE_TOKEN')
    assert allowed_reference('knowledge', 'PLANNING_KNOWLEDGE_TOKEN')
    assert not allowed_reference('runtime', 'REGISTRY_OPERATOR_TOKEN')


def test_provision_requires_ready_readable_original_identity(tmp_path):
    with LocalState(tmp_path):
        pass
    with pytest.raises(ProfileError, match='stores_required'):
        provision_curation_credentials(tmp_path)
    assert not (tmp_path / 'planning-readers.dpapi').exists()
