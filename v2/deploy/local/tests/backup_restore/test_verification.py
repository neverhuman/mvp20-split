import pytest
from amphora_deployment.backup_restore import verify_inventory
from amphora_deployment.profile import ProfileError


def test_readonly_inventory_is_not_service_readiness(backup_bundle):
    root, *_ = backup_bundle
    before = {str(p): p.read_bytes() for p in root.rglob('*') if p.is_file()}
    result = verify_inventory(*backup_bundle)
    assert result.status == 'inventory_verified_not_restore_ready'
    assert result.file_count == 5
    assert result.total_bytes == sum(len(x) for x in ('postgres', 'qdrant', 'installation', 'artifact', 'cut_evidence'))
    assert before == {str(p): p.read_bytes() for p in root.rglob('*') if p.is_file()}


@pytest.mark.parametrize('fault,reason', [
    ('missing', 'backup_file_missing_or_size'), ('truncated', 'backup_file_missing_or_size'),
    ('changed', 'backup_file_digest'), ('manifest_changed', 'backup_manifest_digest'),
    ('manifest_missing', 'backup_io'), ('schema', 'backup_owner_incompatible'),
    ('release', 'backup_owner_incompatible'), ('same_target', 'backup_target_is_source'),
])
def test_partial_corrupt_or_incompatible_backup_cannot_verify(backup_bundle, fault, reason):
    root, fingerprint, expected, target = backup_bundle
    path = root / 'artifact/payload.bin'
    if fault == 'missing':
        path.unlink()
    elif fault == 'truncated':
        path.write_bytes(b'')
    elif fault == 'changed':
        path.write_bytes(b'X' * len(path.read_bytes()))
    elif fault == 'manifest_changed':
        (root / 'manifest.json').write_bytes(b'{}')
    elif fault == 'manifest_missing':
        (root / 'manifest.json').unlink()
    elif fault == 'schema':
        expected['runtime'] = ('1.0.0', '0002')
    elif fault == 'release':
        expected['runtime'] = ('2.0.0', '0001')
    elif fault == 'same_target':
        target = 'b' * 32
    with pytest.raises(ProfileError, match='^' + reason + '$'):
        verify_inventory(root, fingerprint, expected, target)


@pytest.mark.parametrize('kind', ['link', 'junction'])
def test_link_or_junction_never_opens_external_bytes(backup_bundle, monkeypatch, kind):
    root, *_ = backup_bundle
    path_type = type(root)
    original = getattr(path_type, 'is_symlink' if kind == 'link' else 'is_junction')
    monkeypatch.setattr(path_type, 'is_symlink' if kind == 'link' else 'is_junction',
                        lambda p: p.name == 'artifact' or original(p))
    with pytest.raises(ProfileError, match='^backup_link$'):
        verify_inventory(*backup_bundle)
