import hashlib
import json

import pytest
from amphora_deployment.backup_restore.manifest import OWNERS


@pytest.fixture
def backup_record():
    files = [{'path': role + '/payload.bin', 'role': role, 'size': len(role),
              'sha256': hashlib.sha256(role.encode()).hexdigest()}
             for role in ('postgres', 'qdrant', 'installation', 'artifact', 'cut_evidence')]
    return {'profile': 'local-offline-backup-v1', 'backup_id': 'a' * 32,
            'source_deployment_id': 'b' * 32, 'captured_at': '2026-10-07 08:00:00',
            'cut': {'mode': 'all_owners_stopped', 'evidence_path': 'cut_evidence/payload.bin'},
            'owners': [{'owner': owner, 'release': '1.0.0', 'schema': '0001',
                        'checkpoint_sha256': 'c' * 64} for owner in sorted(OWNERS)], 'files': files}


@pytest.fixture
def backup_bundle(tmp_path, backup_record):
    for row in backup_record['files']:
        path = tmp_path / row['path']
        path.parent.mkdir()
        path.write_bytes(row['role'].encode())
    raw = json.dumps(backup_record).encode()
    (tmp_path / 'manifest.json').write_bytes(raw)
    expected = {row['owner']: (row['release'], row['schema']) for row in backup_record['owners']}
    return tmp_path, hashlib.sha256(raw).hexdigest(), expected, 'd' * 32
