"""Restore verified cold bytes to new labeled resources; do not enable owner traffic."""

import argparse
import json
import time
import uuid
from datetime import datetime
from pathlib import Path

from amphora_deployment.backup_restore import BackupManifest, verify_inventory
from amphora_deployment.credentials import CredentialVault
from amphora_deployment.lifecycle.configuration import control_token
from amphora_deployment.lifecycle.routes import Routes
from amphora_deployment.persistence.docker import Docker
from amphora_deployment.persistence.postgres import sql
from amphora_deployment.persistence.state import LocalState
from amphora_deployment.persistence.stores import POSTGRES, QDRANT, ensure_store, qdrant_ready
from amphora_deployment.registry_access import registry_vault
from amphora_deployment.tool_catalog.credentials import worker_vault

from local_backup_io import check_archive, copy_tree, volume_import
from local_numeric_configuration import write


def remap_endpoints(value, endpoints):
    if isinstance(value, dict):
        return {key: remap_endpoints(item, endpoints) for key, item in value.items()}
    if isinstance(value, list):
        return [remap_endpoints(item, endpoints) for item in value]
    if isinstance(value, str):
        for source, target in endpoints.items():
            if value == source or value.startswith(source + '/'):
                return target + value[len(source):]
    return value


def restore(backup, trusted_evidence, target, output, expected_owners):
    started = time.monotonic()
    assert not target.exists() and not output.exists()
    assert not target.is_relative_to(backup) and not backup.is_relative_to(target)
    # Caller supplies the previously retained digest; never trust a hash inside this backup.
    trusted = json.loads(trusted_evidence.read_bytes())['verification']
    verified = verify_inventory(backup, trusted['manifest_sha256'], expected_owners, uuid.uuid4().hex)
    assert verified.backup_id == trusted['backup_id']
    manifest = BackupManifest.from_bytes((backup / 'manifest.json').read_bytes())
    source = backup / 'installation' / 'state'
    source_state = LocalState.snapshot(source)
    assert source_state['deployment_id'] == manifest.source_deployment_id
    source_routes = Routes.from_record(source_state['routes'])
    configuration_index = json.loads((backup / 'installation/configuration-inputs/index.json').read_bytes())
    owners = json.loads((backup / 'installation' / 'owners.json').read_bytes())
    assert set(owners['owners']) == set(expected_owners)
    for kind in ('postgres', 'qdrant'):
        check_archive(backup / kind / 'volume.tar')
    output.mkdir(parents=True)
    docker = Docker()
    with LocalState(target) as state:
        assert state.identity != manifest.source_deployment_id and state.record['phase'] == 'declared'
        state.record.update(phase='restoring', restore={'backup_id': manifest.backup_id,
            'manifest_sha256': trusted['manifest_sha256'], 'source_deployment_id': manifest.source_deployment_id,
            'traffic': 'disabled', 'owner_semantics': 'unverified'})
        state.save()
        bundle = CredentialVault(source / 'credentials.dpapi', manifest.source_deployment_id).load()
        CredentialVault(target / 'credentials.dpapi', state.identity).create(bundle)
        for factory in (registry_vault, worker_vault):
            prior = factory(source, manifest.source_deployment_id)
            if prior.path.exists():
                factory(target, state.identity).create(prior.load())
        for kind in ('postgres', 'qdrant'):
            assert state.name(kind + '-data') != source_state[kind]['volume']
            assert docker.inspect('container', state.name(kind)) is None
            volume_import(state.name(kind + '-data'), POSTGRES, backup / kind / 'volume.tar',
                          state.identity, manifest.backup_id, kind)
        pg_password = bundle.environment(['PG_ADMIN_PASSWORD'])['PG_ADMIN_PASSWORD']
        pg = ensure_store(docker, state, 'postgres', POSTGRES, 5432, '/var/lib/postgresql/data',
                          {'POSTGRES_PASSWORD': pg_password, 'POSTGRES_DB': 'amphora_local'})
        state.record['postgres'] = pg
        state.save()
        deadline = time.monotonic() + 90
        while docker.run('exec', pg['container'], 'pg_isready', '-h', '127.0.0.1', '-U', 'postgres',
                         '-d', 'amphora_local', allow_failure=True) is None:
            assert time.monotonic() < deadline, 'Restored PostgreSQL unavailable'
            time.sleep(.25)
        # Only Deployment's administrative marker is rebound, never owner schema/data.
        assert sql(docker, pg['container'], 'SELECT deployment_id FROM deployment.bootstrap;') == manifest.source_deployment_id
        command = "BEGIN; UPDATE deployment.bootstrap SET deployment_id='" + state.identity
        command += "' WHERE deployment_id='" + manifest.source_deployment_id + "'; COMMIT;"
        sql(docker, pg['container'], command)
        assert sql(docker, pg['container'], 'SELECT deployment_id FROM deployment.bootstrap;') == state.identity
        key = bundle.environment(['QDRANT_API_KEY'])['QDRANT_API_KEY']
        qdrant = ensure_store(docker, state, 'qdrant', QDRANT, 6333, '/qdrant/storage', {'QDRANT__SERVICE__API_KEY': key})
        while not qdrant_ready('http://127.0.0.1:' + str(qdrant['port']), key):
            assert time.monotonic() < deadline, 'Restored Qdrant unavailable'
            time.sleep(.25)
        copy_tree(backup / 'artifacts', target / 'artifacts')
        # Historical released journals stay in the immutable backup; no native/tool worker
        # configuration is enabled on the target. Its lifecycle starts with new identity.
        state.record.update(qdrant=qdrant, phase='stores_ready', migrations=source_state['migrations'])
        state.save()
        identity = state.identity
    routes = Routes.ensure(target)
    endpoints = {source_routes.endpoint(name): routes.endpoint(name) for name, _ in source_routes.ports}
    endpoints['http://127.0.0.1:' + str(source_state['qdrant']['port'])] = 'http://127.0.0.1:' + str(qdrant['port'])
    inputs = output / 'configuration-inputs'
    inputs.mkdir()
    endpoints.update({source: str(inputs / name) for source, name in configuration_index.items()})
    for name in sorted(set(configuration_index.values())):
        assert Path(name).name == name
        raw = (backup / 'installation/configuration-inputs' / name).read_bytes()
        value = json.loads(raw)
        changed = remap_endpoints(value, endpoints)
        if changed == value:
            (inputs / name).write_bytes(raw)  # preserve exact schema/descriptor digests
        else:
            write(inputs / name, changed)
    for name, row in owners['owners'].items():
        settings = json.loads((backup / 'installation' / 'owners' / name / 'configuration.json').read_bytes())
        settings = remap_endpoints(settings, endpoints)
        if name == 'artifact':
            settings['storage_root'] = str(target / 'artifacts')
        path = output / (name + '.json')
        write(path, settings)
        row['configuration'] = str(path)
    write(output / 'owners.json', owners)
    control_token(target, create=True)
    return {'timestamp_local': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'stores_restored_owner_acceptance_pending', 'target_deployment_id': identity,
            'backup_id': manifest.backup_id, 'manifest_sha256': trusted['manifest_sha256'],
            'restore_seconds': time.monotonic() - started, 'routes': routes.to_record(),
            'resources': {'postgres': pg, 'qdrant': qdrant}, 'traffic_enabled': False,
            'owner_workers_started': False, 'provider_calls': 0,
            'limits': ['Same host/user DPAPI, preserved pinned images and independently installed owner binaries required',
                       'Infrastructure readiness only; public history/reference/schema acceptance remains required']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('backup', 'trusted-evidence', 'target', 'output', 'expected-owners'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    expected = {name: tuple(values) for name, values in json.loads(args.expected_owners.read_bytes()).items()}
    try:
        result = restore(*(getattr(args, name).absolute() for name in ('backup', 'trusted_evidence', 'target', 'output')), expected)
        write(args.output.absolute() / 'restore.json', result)
        print('Separate resources restored; owner acceptance pending; no source changes or provider calls', flush=True)
    except Exception as error:
        raise SystemExit('Isolated restore failed (' + type(error).__name__ + '); retain target journal for inspection.') from None
