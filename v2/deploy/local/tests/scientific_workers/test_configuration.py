import json
from types import SimpleNamespace

import pytest
from amphora_deployment.profile import ProfileError
from amphora_deployment.scientific_workers.configuration import load_scientific


def test_manifest_binds_tls_identity_and_only_scientific_credentials(tmp_path, profile, monkeypatch):
    bundle = SimpleNamespace(environment=lambda names: {name: 'private-' + name for name in names})
    monkeypatch.setattr('amphora_deployment.scientific_workers.configuration.CredentialVault',
                        lambda *args: SimpleNamespace(load=lambda: bundle))
    identity = SimpleNamespace(certificate_sha256=profile.certificate_sha256)
    access = {'runtime': SimpleNamespace(port=23457, identity=identity),
              'artifact': SimpleNamespace(port=23458, identity=identity)}
    path = tmp_path / 'manifest.json'
    path.write_text(json.dumps({'profile': 'local-scientific-workers-v1', 'workers': {profile.name: {
        'image_id': profile.image_id, 'configuration': str(profile.configuration), 'certificate': str(profile.certificate)}}}))
    binding = load_scientific(path, tmp_path, 'a' * 32, access)[profile.name]
    assert set(binding.environment) == {'AMPHORA_RUNTIME_TOKEN', 'AMPHORA_ARTIFACT_TOKEN'}
    assert 'private-' not in repr(binding)
    assert binding.turn().journal is binding.journal
    binding.journal.intent()
    with pytest.raises(ProfileError, match='pending_binding_not_configured'):
        load_scientific(None, tmp_path, 'a' * 32, {})
    identity.certificate_sha256 = 'c' * 64
    with pytest.raises(ProfileError, match='tls_identity_mismatch'):
        load_scientific(path, tmp_path, 'a' * 32, access)


def test_no_worker_profile_preserves_no_pending_installation(tmp_path):
    assert load_scientific(None, tmp_path, 'a' * 32, {}) == {}
