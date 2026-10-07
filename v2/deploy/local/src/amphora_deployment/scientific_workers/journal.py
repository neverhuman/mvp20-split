"""Atomic current-turn intent; a Docker start can never silently become a restart."""

import json
import os
import re
import uuid
from datetime import datetime
from pathlib import Path

from ..installation.inventory import digest
from ..profile import fields, label, require

PHASES = {'intent', 'created', 'starting', 'started', 'exited', 'released'}


class ContainerJournal:
    """Caller must hold the deployment writer lease and serialize this binding.

    No PID, raw Docker inspect output, environment, key or scientific payload is
    accepted. Starting is persisted BEFORE the sole docker start call. A replay
    in that phase may observe the same container but must never start it again.
    """

    def __init__(self, path, deployment_id, worker, binding_sha256):
        self.path = Path(path)
        require(type(deployment_id) is str and re.fullmatch(r'[0-9a-f]{32}', deployment_id),
                'container_deployment_identity')
        self.deployment_id = deployment_id
        self.worker = label(worker, 'container_worker_name')
        self.binding_sha256 = digest(binding_sha256, 'container_binding_digest')

    def read(self):
        if not self.path.exists():
            return None
        with self.path.open('rb') as stream:
            raw = stream.read(8193)
        require(len(raw) <= 8192, 'container_journal_size')
        record = fields(json.loads(raw),
            'profile deployment_id worker binding_sha256 turn_id sequence phase container_id exit_code updated_at',
            'container_journal')
        require(record['profile'] == 'local-tool-turn-v1' and record['deployment_id'] == self.deployment_id
                and record['worker'] == self.worker and record['binding_sha256'] == self.binding_sha256,
                'container_journal_binding')
        require(type(record['turn_id']) is str and re.fullmatch(r'[0-9a-f]{32}', record['turn_id'])
                and type(record['sequence']) is int and record['sequence'] > 0,
                'container_journal_turn')
        phase = record['phase']
        require(phase in PHASES, 'container_journal_phase')
        require(record['container_id'] is None if phase == 'intent' else
                type(record['container_id']) is str and re.fullmatch(r'[0-9a-f]{64}', record['container_id']),
                'container_journal_id')
        require(type(record['exit_code']) is int and 0 <= record['exit_code'] <= 255 if phase in {'exited', 'released'}
                else record['exit_code'] is None, 'container_journal_exit')
        require(type(record['updated_at']) is str and re.fullmatch(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', record['updated_at']),
                'container_journal_time')
        return record

    def _write(self, record):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_name('.turn-' + uuid.uuid4().hex + '.tmp')
        record = dict(record, updated_at=datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S'))
        try:
            with temporary.open('xb') as stream:
                stream.write(json.dumps(record, sort_keys=True, separators=(',', ':')).encode())
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.path)
        finally:
            temporary.unlink(missing_ok=True)
        return self.read()

    def intent(self):
        previous = self.read()
        require(previous is None or previous['phase'] == 'released', 'container_unresolved_turn')
        return self._write({'profile': 'local-tool-turn-v1', 'deployment_id': self.deployment_id,
            'worker': self.worker, 'binding_sha256': self.binding_sha256, 'turn_id': uuid.uuid4().hex,
            'sequence': 1 if previous is None else previous['sequence'] + 1,
            'phase': 'intent', 'container_id': None, 'exit_code': None})

    def created(self, container_id):
        digest(container_id, 'container_id')
        record = self.read()
        require(record is not None and record['phase'] == 'intent', 'container_create_transition')
        return self._write(dict(record, phase='created', container_id=container_id))

    def starting(self):
        record = self.read()
        require(record is not None and record['phase'] == 'created', 'container_start_once')
        return self._write(dict(record, phase='starting'))

    def started(self):
        record = self.read()
        require(record is not None and record['phase'] in {'starting', 'started'}, 'container_start_transition')
        return self._write(dict(record, phase='started'))

    def exited(self, code):
        require(type(code) is int and 0 <= code <= 255, 'container_exit_code')
        record = self.read()
        require(record is not None and record['phase'] in {'starting', 'started', 'exited'}, 'container_exit_transition')
        require(record['exit_code'] is None or record['exit_code'] == code, 'container_exit_changed')
        return self._write(dict(record, phase='exited', exit_code=code))

    def released(self):
        record = self.read()
        require(record is not None and record['phase'] in {'exited', 'released'}, 'container_release_requires_exit')
        return self._write(dict(record, phase='released'))
