"""Corrupt separate copies of the qualified cold backup; reject before allocation."""

import argparse
import json
import shutil
import subprocess
import uuid
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from amphora_deployment.backup_restore import verify_inventory
from amphora_deployment.profile import ProfileError

from local_numeric_configuration import write
from restore_local_backup import restore


def resources():
    result = {}
    for name, command in (('containers', ['docker', 'ps', '-aq', '--no-trunc']),
                          ('volumes', ['docker', 'volume', 'ls', '-q'])):
        response = subprocess.run(command, capture_output=True, check=True, timeout=10)
        result[name] = sorted(response.stdout.decode().splitlines())
    return result


def verify(backup, trusted_evidence, expected_path, copies, output):
    expected = {name: tuple(values) for name, values in json.loads(expected_path.read_bytes()).items()}
    trusted = json.loads(trusted_evidence.read_bytes())['verification']
    baseline = verify_inventory(backup, trusted['manifest_sha256'], expected, uuid.uuid4().hex)
    assert not copies.exists() and not output.exists()
    assert not copies.is_relative_to(backup) and not backup.is_relative_to(copies)
    copies.mkdir(parents=True)
    output.mkdir(parents=True)
    manifest = json.loads((backup / 'manifest.json').read_bytes())
    artifact = next(row for row in manifest['files'] if row['role'] == 'artifact' and row['size'] > 0)
    postgres = next(row for row in manifest['files'] if row['role'] == 'postgres')
    before = resources()
    cases = []
    for fault, reason in [('missing_artifact', 'backup_file_missing_or_size'),
                          ('corrupt_artifact', 'backup_file_digest'),
                          ('partial_snapshot', 'backup_file_missing_or_size'),
                          ('wrong_schema', 'backup_owner_incompatible')]:
        case = copies / fault
        selected = case / 'backup'
        shutil.copytree(backup, selected)
        # Mutate only newly copied, manifest-validated files; no hardlinks or source changes.
        path = selected / artifact['path']
        if fault == 'missing_artifact':
            path.unlink()
        elif fault == 'corrupt_artifact':
            content = path.read_bytes()
            path.write_bytes(bytes([content[0] ^ 1]) + content[1:])
        elif fault == 'partial_snapshot':
            (selected / postgres['path']).write_bytes(b'partial-snapshot-fixture')
        compatible = dict(expected)
        if fault == 'wrong_schema':
            compatible['runtime'] = (expected['runtime'][0], 'unreviewed-schema')
        target, evidence = case / 'target', case / 'restore-evidence'
        try:
            restore(selected, trusted_evidence, target, evidence, compatible)
        except ProfileError as error:
            assert str(error) == reason, 'Unexpected backup rejection category'
        else:
            raise AssertionError('Corrupt backup was not rejected')
        assert not target.exists() and not evidence.exists()
        assert resources() == before, 'Failure allocated or changed Docker resources'
        cases.append({'fault': fault, 'reason': reason, 'target_created': False,
                      'resource_inventory_unchanged': True})
    after = verify_inventory(backup, trusted['manifest_sha256'], expected, uuid.uuid4().hex)
    assert after == baseline
    record = {'timestamp_local': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'status': 'passed',
        'backup': asdict(baseline), 'cases': cases, 'original_backup_unchanged': True,
        'provider_calls': 0, 'limits': ['Pre-allocation cold restore rejection only',
            'Does not inject corruption into the accepted live restore or original source stores']}
    write(output / 'evidence.json', record)
    print('Four actual backup-copy faults rejected before target/resource allocation', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('backup', 'trusted-evidence', 'expected-path', 'copies', 'output'):
        parser.add_argument('--' + name, required=True, type=Path)
    args = parser.parse_args()
    verify(*(getattr(args, name).absolute() for name in ('backup', 'trusted_evidence', 'expected_path', 'copies', 'output')))
