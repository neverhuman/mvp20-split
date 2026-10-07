"""Outstanding managed turns remain blockers after the Windows controller exits."""

import json
from pathlib import Path

from ..installation.inventory import digest
from ..profile import require
from .journal import ContainerJournal
from .profiles import PROFILES


def journal_path(root, profile):
    return Path(root) / 'scientific-workers' / (profile.name + '-' + profile.fingerprint + '.json')


def retained_turns(root, deployment_id):
    directory = Path(root) / 'scientific-workers'
    if not directory.exists():
        return ()
    paths = list(directory.glob('*.json'))
    require(len(paths) <= 256, 'container_retained_binding_limit')
    result = []
    for path in sorted(paths):
        with path.open('rb') as stream:
            raw = stream.read(8193)
        require(len(raw) <= 8192, 'container_journal_size')
        metadata = json.loads(raw)
        require(type(metadata) is dict and metadata.get('worker') in PROFILES, 'container_retained_worker')
        fingerprint = digest(metadata.get('binding_sha256'), 'container_binding_digest')
        require(path.name == metadata['worker'] + '-' + fingerprint + '.json', 'container_retained_filename')
        journal = ContainerJournal(path, deployment_id, metadata['worker'], fingerprint)
        result.append(journal.read())
    return tuple(result)


def require_released(root, deployment_id):
    require(all(record['phase'] == 'released' for record in retained_turns(root, deployment_id)),
            'migration_requires_reconciled_containers')


def require_configured_pending(root, deployment_id, profiles):
    configured = {(profile.name, profile.fingerprint) for profile in profiles}
    require(all(record['phase'] == 'released' or (record['worker'], record['binding_sha256']) in configured
                for record in retained_turns(root, deployment_id)), 'container_pending_binding_not_configured')
