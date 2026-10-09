"""Capture a cold, local-only snapshot after verified controller/worker drain."""

import argparse
import hashlib
import json
import os
import socket
import time
import uuid
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from amphora_deployment.backup_restore import BackupManifest, verify_inventory
from amphora_deployment.campaign_launch.backup import require_launches_drained
from amphora_deployment.credentials import CredentialVault
from amphora_deployment.installation.inventory import OwnerInstallation
from amphora_deployment.lifecycle.routes import Routes
from amphora_deployment.persistence.docker import Docker
from amphora_deployment.persistence.state import LocalState
from amphora_deployment.persistence.stores import POSTGRES, QDRANT, owned, qdrant_ready
from amphora_deployment.scientific_workers.ownership import require_released

from local_backup_io import (
    configuration_inputs,
    copy_file,
    copy_tree,
    inventory_row,
    merge_artifact_tree,
    volume_export,
)
from local_numeric_configuration import write

SCHEMAS = {'runtime': '0028', 'artifact': '0012', 'planning': '0020',
           'research': '0016', 'knowledge': '0007', 'registry': '0001'}


def require_stopped(routes):
    for _, port in routes.ports:
        with socket.socket() as probe:
            probe.settimeout(.2)
            assert probe.connect_ex(('127.0.0.1', port)) != 0, 'Owner/control listener remains live'


def capture(root, artifact_root, configuration, output, readbacks, additional_artifact_roots=()):
    started = time.monotonic()
    assert not output.exists() and output.parent.is_dir()
    assert output != root and not output.is_relative_to(root) and not root.is_relative_to(output)
    assert not output.is_relative_to(artifact_root) and not artifact_root.is_relative_to(output)
    output.mkdir()
    backup_id = uuid.uuid4().hex
    owners = json.loads((configuration / 'owners.json').read_bytes())['owners']
    assert set(owners) == set(SCHEMAS)
    evidence = []
    for source in readbacks:
        value = json.loads(source.read_bytes())
        assert value['status'] in ('passed', 'readback_passed')
        assert all(row['exit_code'] == 0 and row['drain'] == 'drained' for row in value['final']['owners'].values())
        evidence.append({'sha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'run_id': value['run_id'],
                         'timestamp_local': value['timestamp_local']})
    assert len(evidence) == 3 and len({row['run_id'] for row in evidence}) == 3
    docker = Docker()
    restarted, stopped, snapshots = [], [], {}
    with LocalState(root) as state:
        assert state.record['phase'] == 'stores_ready'
        routes = Routes.from_record(state.record['routes'])
        require_stopped(routes)
        require_released(root, state.identity)
        require_launches_drained(root)
        before = json.loads(json.dumps(state.record))
        for kind, expected in (('postgres', POSTGRES), ('qdrant', QDRANT)):
            row = before[kind]
            info = docker.inspect('container', row['container'])
            owned(info, state.identity, container=True)
            assert info['Config']['Image'] == expected and info['State']['Running']
            assert len(info['Mounts']) == 1 and info['Mounts'][0]['Name'] == row['volume']
            snapshots[kind] = {'id': info['Id'], 'volume': row['volume'], 'image': expected,
                               'mounts': info['Mounts'], 'ports': info['HostConfig']['PortBindings']}
        owner_snapshots = []
        copy_file(configuration / 'owners.json', output / 'installation' / 'owners.json')
        for name, row in sorted(owners.items()):
            installation = OwnerInstallation.from_directory(name, row['installation'], row['source_lock'])
            owner_snapshots.append({'owner': name, 'release': installation.release, 'schema': SCHEMAS[name],
                                    'checkpoint_sha256': installation.installation_manifest_sha256})
            directory = output / 'installation' / 'owners' / name
            directory.mkdir(parents=True)
            for source, dest in [(Path(row['configuration']), 'configuration.json'),
                                 (Path(row['source_lock']), 'source.lock'),
                                 (Path(row['installation']) / 'manifest.json', 'manifest.json')]:
                copy_file(source, directory / dest)
            for wheel in installation.wheels:
                copy_file(Path(row['installation']) / 'wheels' / wheel.filename, directory / 'wheels' / wheel.filename)
        try:
            print('Stopping exactly the two active demo stores for cold capture', flush=True)
            for kind in ('qdrant', 'postgres'):
                identifier = snapshots[kind]['id']
                stopped.append(identifier)  # recover even if CLI loses its stop reply
                docker.run('stop', '--time', '30', identifier)
                assert not docker.inspect('container', identifier)['State']['Running']
            require_stopped(routes)
            require_released(root, state.identity)
            launch_count = require_launches_drained(root)
            cut = {'timestamp_local': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                   'mode': 'all_owners_stopped', 'readbacks': evidence, 'containers': snapshots,
                   'owner_control_ports_unavailable': True, 'scientific_journals_released': True,
                   'stores_confirmed_stopped': True, 'owner_schemas': 'reviewed installed release pins; semantic restore checks required'}
            cut['artifact_roots'] = [str(artifact_root), *(str(path) for path in additional_artifact_roots)]
            cut['launch_journal'] = {'terminal_records': launch_count, 'active_records': 0}
            (output / 'evidence').mkdir()
            write(output / 'evidence' / 'drain.json', cut)
            for kind in ('postgres', 'qdrant'):
                row = snapshots[kind]
                print('Exporting cold ' + kind + ' volume', flush=True)
                volume_export(row['volume'], POSTGRES, output / kind / 'volume.tar', state.identity, backup_id, kind)
            print('Copying immutable bytes and protected installation state', flush=True)
            copy_tree(artifact_root, output / 'artifacts')
            for additional in additional_artifact_roots:
                assert additional != artifact_root and not output.is_relative_to(additional)
                merge_artifact_tree(additional, output / 'artifacts')
            copy_tree(root, output / 'installation' / 'state', excluded=('.operation.lock', 'logs'))
            configuration_inputs([Path(row['configuration']) for row in owners.values()],
                                 output / 'installation' / 'configuration-inputs',
                                 [Path.cwd(), root.parent, Path(os.environ['LOCALAPPDATA']) / 'Amphora/local-v2'])
            assert state.record == before and LocalState.snapshot(root) == before
        finally:
            print('Restoring original store container IDs', flush=True)
            for identifier in reversed(stopped):
                try:
                    docker.run('start', identifier)
                    restarted.append(identifier)
                except Exception:
                    # Attempt every original start even when one recovery fails.
                    pass
            assert set(restarted) == set(stopped), 'Original storage recovery requires attention'
        deadline = time.monotonic() + 90
        while docker.run('exec', snapshots['postgres']['id'], 'pg_isready', '-h', '127.0.0.1',
                         '-U', 'postgres', '-d', 'amphora_local', allow_failure=True) is None:
            assert time.monotonic() < deadline, 'Original PostgreSQL not ready'
            time.sleep(.25)
        key = CredentialVault(root / 'credentials.dpapi', state.identity).load().environment(['QDRANT_API_KEY'])['QDRANT_API_KEY']
        while not qdrant_ready('http://127.0.0.1:' + str(before['qdrant']['port']), key):
            assert time.monotonic() < deadline, 'Original Qdrant not ready'
            time.sleep(.25)
        for row in snapshots.values():
            info = docker.inspect('container', row['id'])
            assert info['State']['Running'] and info['Mounts'] == row['mounts']
            assert info['HostConfig']['PortBindings'] == row['ports']
        files = []
        for directory, role in [('postgres', 'postgres'), ('qdrant', 'qdrant'), ('artifacts', 'artifact'),
                                ('installation', 'installation'), ('evidence', 'cut_evidence')]:
            for path in sorted((output / directory).rglob('*')):
                if path.is_file():
                    files.append(inventory_row(output, path, role))
        record = {'profile': 'local-offline-backup-v1', 'backup_id': backup_id,
                  'source_deployment_id': state.identity, 'captured_at': cut['timestamp_local'],
                  'cut': {'mode': 'all_owners_stopped', 'evidence_path': 'evidence/drain.json'},
                  'owners': owner_snapshots, 'files': files}
        manifest = BackupManifest.from_bytes(json.dumps(record).encode())
        raw = manifest.canonical_bytes()
        (output / 'manifest.json').write_bytes(raw)
        sha = hashlib.sha256(raw).hexdigest()
        result = verify_inventory(output, sha, {r.owner: (r.release, r.schema) for r in manifest.owners}, uuid.uuid4().hex)
        return {'timestamp_local': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'status': 'cold_backup_verified', 'verification': asdict(result),
                'source_stores_restored': True, 'capture_seconds': time.monotonic() - started,
                'objective': 'last fully drained backup; measure recovery time without hard limit',
                'limits': ['Same-machine protected local backup; no host-loss or online snapshot guarantee',
                           'Cold bytes and release/schema pins verified; restored owner semantics remain B2']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('root', 'artifact-root', 'configuration', 'output', 'evidence'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--readback', type=Path, action='append', required=True)
    parser.add_argument('--additional-artifact-root', type=Path, action='append', default=[])
    args = parser.parse_args()
    try:
        result = capture(*(getattr(args, name).absolute() for name in ('root', 'artifact_root', 'configuration', 'output')),
                         [path.absolute() for path in args.readback],
                         [path.absolute() for path in args.additional_artifact_root])
        write(args.evidence.absolute(), result)
        print('Cold backup verified; original stores restored; no owner workers or provider calls', flush=True)
    except Exception as error:
        # File/configuration/driver exceptions may contain sensitive local values.
        raise SystemExit('Cold backup failed (' + type(error).__name__ + '); inspect retained capture journal, not raw secrets.') from None
