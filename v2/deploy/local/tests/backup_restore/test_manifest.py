import json

import pytest
from amphora_deployment.backup_restore import BackupManifest
from amphora_deployment.profile import ProfileError


def parse(backup_record):
    return BackupManifest.from_bytes(json.dumps(backup_record).encode())


def test_immutable_roundtrip_preserves_exact_owner_cut_and_inventory(backup_record):
    manifest = parse(backup_record)
    assert BackupManifest.from_bytes(manifest.canonical_bytes()) == manifest
    backup_record['files'][0]['sha256'] = 'd' * 64
    assert manifest.files[0].sha256 != backup_record['files'][0]['sha256']
    with pytest.raises(AttributeError):
        manifest.cut.mode = 'live'


@pytest.mark.parametrize('path', ['../escape', '/root', 'C:/root', 'a\\b', 'a//b',
    'a/../b', 'con', 'a/NUL.txt', 'lpt1.dat', 'a.', 'file:stream', 'manifest.json', '', 'a/' + 'x' * 101])
def test_cross_platform_path_escape_and_aliases_reject(backup_record, path):
    backup_record['files'][0]['path'] = path
    with pytest.raises(ProfileError, match='backup_(path|reserved_path)'):
        parse(backup_record)


@pytest.mark.parametrize('change,reason', [
    ('duplicate_path', 'backup_duplicate_path'), ('case_alias', 'backup_duplicate_path'),
    ('parent_file', 'backup_path_conflict'), ('owner_duplicate', 'backup_owner_set'),
    ('owner_missing', 'backup_owners'), ('missing_postgres', 'backup_required_file'),
    ('missing_qdrant', 'backup_required_file'), ('missing_cut', 'backup_required_file'),
    ('missing_installation', 'backup_installation_missing'), ('wrong_cut', 'backup_cut_reference'),
    ('live_cut', 'backup_cut_mode'), ('unknown', 'backup_manifest_fields'),
    ('wrong_profile', 'backup_profile'), ('bad_date', 'backup_timestamp'),
    ('bad_identity', 'backup_identity'), ('boolean_size', 'backup_file_size'),
    ('bad_digest', 'backup_digest'), ('bad_role', 'backup_file_role'),
])
def test_incomplete_or_ambiguous_manifest_rejects(backup_record, change, reason):
    if change == 'duplicate_path':
        backup_record['files'].append(backup_record['files'][0].copy())
    elif change == 'case_alias':
        backup_record['files'][1]['path'] = backup_record['files'][0]['path'].upper()
    elif change == 'parent_file':
        backup_record['files'][1]['path'] = 'postgres'
    elif change == 'owner_duplicate':
        backup_record['owners'][1] = backup_record['owners'][0]
    elif change == 'owner_missing':
        backup_record['owners'].pop()
    elif change.startswith('missing_'):
        role = {'missing_cut': 'cut_evidence'}.get(change, change[8:])
        backup_record['files'] = [row for row in backup_record['files'] if row['role'] != role]
    elif change == 'wrong_cut':
        backup_record['cut']['evidence_path'] = backup_record['files'][0]['path']
    elif change == 'live_cut':
        backup_record['cut']['mode'] = 'live'
    elif change == 'unknown':
        backup_record['secret'] = 'not-accepted'
    elif change == 'wrong_profile':
        backup_record['profile'] = '2'
    elif change == 'bad_date':
        backup_record['captured_at'] = '2026-02-30 00:00:00'
    elif change == 'bad_identity':
        backup_record['backup_id'] = 'not-id'
    elif change == 'boolean_size':
        backup_record['files'][0]['size'] = True
    elif change == 'bad_digest':
        backup_record['files'][0]['sha256'] = 'F' * 64
    elif change == 'bad_role':
        backup_record['files'][0]['role'] = []
    with pytest.raises(ProfileError, match='^' + reason + '$'):
        parse(backup_record)


@pytest.mark.parametrize('raw,reason', [
    (b'{"x":1,"x":2}', 'backup_duplicate_key'), (b'{', 'backup_manifest_json'),
    (b'\xff', 'backup_manifest_json'), (b'[]', 'backup_manifest_fields'),
    (b'[' * 2000 + b']' * 2000, 'backup_manifest_(json|fields)'),
    (b'x' * (8 * 1024 * 1024 + 1), 'backup_manifest_bytes'),
], ids=['duplicate', 'broken', 'encoding', 'array', 'deep', 'oversize'])
def test_strict_json_and_bounds(raw, reason):
    with pytest.raises(ProfileError, match='^' + reason + '$'):
        BackupManifest.from_bytes(raw)


def test_empty_artifact_inventory_not_missing_snapshot(backup_record):
    backup_record['files'] = [row for row in backup_record['files'] if row['role'] != 'artifact']
    assert len(parse(backup_record).files) == 4
