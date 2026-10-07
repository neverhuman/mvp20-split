"""Cold-volume stream and sealed local file helpers; never log archive contents."""

import hashlib
import json
import os
import shutil
import subprocess
import tarfile
from pathlib import Path, PurePosixPath

from amphora_deployment.backup_restore.manifest import relative_path
from amphora_deployment.persistence.docker import Docker
from amphora_deployment.persistence.state import LABEL


def fingerprint(path):
    value, size = hashlib.sha256(), 0
    with Path(path).open('rb') as stream:
        while block := stream.read(1024 * 1024):
            value.update(block)
            size += len(block)
    return size, value.hexdigest()


def inventory_row(root, path, role):
    relative = path.relative_to(root).as_posix()
    relative_path(relative)
    size, sha = fingerprint(path)
    return {'path': relative, 'role': role, 'size': size, 'sha256': sha}


def copy_file(source, target):
    assert source.is_file() and not source.is_symlink() and not source.is_junction()
    target.parent.mkdir(parents=True, exist_ok=True)
    with source.open('rb') as reader, target.open('xb') as writer:
        shutil.copyfileobj(reader, writer, 1024 * 1024)
        writer.flush()
        os.fsync(writer.fileno())
    assert fingerprint(source) == fingerprint(target)


def copy_tree(source, target, excluded=()):
    """Explicit selected owner roots only; reject reparse paths before descending."""
    assert source.is_dir() and not source.is_symlink() and not source.is_junction()
    target.mkdir(parents=True, exist_ok=False)
    for entry in sorted(source.iterdir()):
        if entry.name in excluded:
            continue
        assert not entry.is_symlink() and not entry.is_junction()
        if entry.is_dir():
            copy_tree(entry, target / entry.name)
        else:
            copy_file(entry, target / entry.name)


def merge_artifact_tree(source, target):
    """Merge explicitly selected immutable Data roots; conflicting keys fail closed."""
    assert source.is_dir() and not source.is_symlink() and not source.is_junction()
    assert target.is_dir() and not target.is_symlink() and not target.is_junction()
    for entry in sorted(source.iterdir()):
        assert entry.is_file() and not entry.is_symlink() and not entry.is_junction()
        relative_path(entry.name)
        destination = target / entry.name
        if destination.exists():
            assert fingerprint(destination) == fingerprint(entry), 'Conflicting immutable storage key'
        else:
            copy_file(entry, destination)


def configuration_inputs(configurations, destination, allowed_roots):
    """Snapshot absolute JSON inputs named by reviewed owner configurations, within owned roots."""
    destination.mkdir(parents=True)
    pending, visited, mapping = list(configurations), set(), {}
    roots = [str(path.absolute()).casefold().rstrip('\\/') for path in allowed_roots]

    def values(value):
        if isinstance(value, dict):
            for item in value.values():
                yield from values(item)
        elif isinstance(value, list):
            for item in value:
                yield from values(item)
        elif isinstance(value, str) and len(value) <= 4096:
            yield value

    while pending:
        source = pending.pop()
        marker = str(source.absolute()).casefold()
        if marker in visited:
            continue
        visited.add(marker)
        assert len(visited) <= 1000
        record = json.loads(source.read_bytes())
        for value in values(record):
            path = Path(value)
            if not path.is_absolute() or path.suffix.lower() != '.json':
                continue
            assert '..' not in path.parts, 'Configuration input traversal is unsupported'
            candidate = str(path.absolute()).casefold()
            assert any(candidate.startswith(root + os.sep) for root in roots), 'Configuration input outside owned roots'
            assert path.is_file() and not path.is_symlink() and not path.is_junction()
            target = destination / (fingerprint(path)[1] + '.json')
            if not target.exists():
                copy_file(path, target)
            mapping[value] = target.name
            pending.append(path)
    (destination / 'index.json').write_text(json.dumps(mapping, sort_keys=True, indent=2) + '\n', encoding='utf-8')
    return mapping


def check_archive(path):
    count = 0
    with tarfile.open(path, 'r:') as archive:
        for member in archive:
            name = PurePosixPath(member.name)
            assert not name.is_absolute() and '..' not in name.parts and '\\' not in member.name
            assert member.isfile() or member.isdir(), 'Linked/special archive member is unsupported'
            count += 1
    assert count > 0
    return count


def volume_export(volume, image, target, deployment_id, backup_id, kind):
    docker = Docker()
    name = 'amphora-backup-' + backup_id + '-' + kind
    assert docker.inspect('container', name) is None
    command = ['docker', 'run', '--rm', '--name', name, '--label', LABEL + '=' + deployment_id,
        '--label', 'amphora.backup=' + backup_id, '--network', 'none', '--read-only',
        '--security-opt', 'no-new-privileges', '--cap-drop', 'ALL', '--cap-add', 'DAC_OVERRIDE',
        '--mount', 'type=volume,source=' + volume + ',target=/snapshot,readonly',
        '--entrypoint', 'tar', image, '-C', '/snapshot', '-cf', '-', '.']
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        with target.open('xb') as stream:
            result = subprocess.run(command, stdout=stream, stderr=subprocess.DEVNULL, timeout=300,
                                    creationflags=subprocess.CREATE_NO_WINDOW)
            assert result.returncode == 0, 'Cold volume export failed'
            stream.flush()
            os.fsync(stream.fileno())
    finally:
        info = docker.inspect('container', name)
        if info is not None:
            assert info['Config']['Labels'].get('amphora.backup') == backup_id
            assert info['Config']['Labels'].get(LABEL) == deployment_id
            docker.run('stop', '--time', '10', info['Id'])
    return check_archive(target)


def volume_import(volume, image, archive, deployment_id, backup_id, kind):
    """Extract trusted, checked cold bytes only into an explicitly new owned volume."""
    check_archive(archive)
    docker = Docker()
    assert docker.inspect('volume', volume) is None, 'Restore never reuses an existing volume'
    docker.run('volume', 'create', '--label', LABEL + '=' + deployment_id,
               '--label', 'amphora.restored-backup=' + backup_id, volume)
    name = 'amphora-restore-' + deployment_id + '-' + kind
    assert docker.inspect('container', name) is None
    command = ['docker', 'run', '--rm', '-i', '--name', name,
        '--label', LABEL + '=' + deployment_id, '--label', 'amphora.restore=' + backup_id,
        '--network', 'none', '--read-only', '--security-opt', 'no-new-privileges',
        '--cap-drop', 'ALL', '--cap-add', 'DAC_OVERRIDE', '--cap-add', 'CHOWN', '--cap-add', 'FOWNER',
        '--mount', 'type=volume,source=' + volume + ',target=/snapshot',
        '--entrypoint', 'tar', image, '-C', '/snapshot', '-xf', '-']
    try:
        with archive.open('rb') as stream:
            result = subprocess.run(command, stdin=stream, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                    timeout=300, creationflags=subprocess.CREATE_NO_WINDOW)
        assert result.returncode == 0, 'Cold volume restore failed'
    finally:
        info = docker.inspect('container', name)
        if info is not None:
            assert info['Config']['Labels'].get('amphora.restore') == backup_id
            assert info['Config']['Labels'].get(LABEL) == deployment_id
            docker.run('stop', '--time', '10', info['Id'])
