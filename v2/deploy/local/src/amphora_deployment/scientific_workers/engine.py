"""Bounded CLI observations with no raw environments, logs or private Docker output."""

import json
import os
import subprocess
from dataclasses import dataclass

from ..installation.inventory import digest
from ..profile import ProfileError, require

LABEL = 'amphora.local-deployment'
BINDING = 'amphora.worker-binding'
TURN = 'amphora.worker-turn'
WORKER = 'amphora.worker-name'

# Only these fields may cross the Docker boundary. In particular Config.Env,
# labels outside the ownership vocabulary and raw State.Error are never read.
OBSERVATION = ('{"id":{{json .Id}},"name":{{json .Name}},"image":{{json .Image}},'
    '"status":{{json .State.Status}},"started_at":{{json .State.StartedAt}},"exit_code":{{json .State.ExitCode}},'
    '"deployment":{{json (index .Config.Labels "' + LABEL + '")}},'
    '"binding":{{json (index .Config.Labels "' + BINDING + '")}},'
    '"turn":{{json (index .Config.Labels "' + TURN + '")}},'
    '"worker":{{json (index .Config.Labels "' + WORKER + '")}}}')


def name_for(record):
    return 'amphora-turn-' + record['deployment_id'] + '-' + record['worker'] + '-' + record['turn_id']


@dataclass(frozen=True)
class ContainerObservation:
    container_id: str
    status: str
    started: bool
    exit_code: int

    @classmethod
    def bind(cls, record, expected, image_id):
        require(type(record) is dict and record.get('name') == '/' + name_for(expected)
                and record.get('image') == image_id and record.get('deployment') == expected['deployment_id']
                and record.get('binding') == expected['binding_sha256'] and record.get('turn') == expected['turn_id']
                and record.get('worker') == expected['worker'], 'container_ownership_mismatch')
        container_id = digest(record.get('id'), 'container_observed_id')
        require(expected['container_id'] is None or expected['container_id'] == container_id, 'container_identity_changed')
        status = record.get('status')
        require(status in {'created', 'running', 'exited'}, 'container_state_unsupported')
        started_at, code = record.get('started_at'), record.get('exit_code')
        require(type(started_at) is str and bool(started_at) and type(code) is int and 0 <= code <= 255,
                'container_observation_shape')
        started = not started_at.startswith('0001-01-01T00:00:00')
        require((status == 'created') != started, 'container_start_observation')
        return cls(container_id, status, started, code)


class ContainerEngine:
    def _run(self, *arguments, environment=None):
        inherited = {key: value for key, value in os.environ.items() if key.upper() in {
            'SYSTEMROOT', 'WINDIR', 'PATH', 'TEMP', 'TMP', 'COMSPEC', 'USERPROFILE', 'LOCALAPPDATA', 'APPDATA'}}
        inherited.update(environment or {})
        try:
            result = subprocess.run(['docker', *arguments], env=inherited, capture_output=True, text=True,
                encoding='utf-8', timeout=5, check=False, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        except (OSError, subprocess.TimeoutExpired):
            raise ProfileError('container_engine_unavailable') from None
        require(result.returncode == 0 and len(result.stdout) <= 16384, 'container_engine_operation_failed')
        return result.stdout.strip()

    def verify_image(self, profile):
        raw = self._run('image', 'inspect', profile.image_id, '--format',
            '{"id":{{json .Id}},"os":{{json .Os}},"arch":{{json .Architecture}},'
            '"entrypoint":{{json .Config.Entrypoint}},"user":{{json .Config.User}}}')
        record = json.loads(raw)
        require(record == {'id': profile.image_id, 'os': 'linux', 'arch': 'amd64',
                           'entrypoint': list(profile.entrypoint), 'user': '65532:65532'}, 'container_image_profile')

    def observe(self, record, profile):
        name = name_for(record)
        found = self._run('container', 'ls', '-a', '--no-trunc', '--filter', 'name=^/' + name + '$', '--format', '{{.ID}}')
        if not found:
            return None
        digest(found, 'container_discovery_id')
        raw = self._run('container', 'inspect', found, '--format', OBSERVATION)
        return ContainerObservation.bind(json.loads(raw), record, profile.image_id)

    def create(self, record, profile, environment):
        profile.verify()
        self.verify_image(profile)
        require(type(environment) is dict and set(environment) == {'AMPHORA_RUNTIME_TOKEN', 'AMPHORA_ARTIFACT_TOKEN'}
                and all(type(value) is str and bool(value) and '\x00' not in value for value in environment.values()),
                'container_environment')
        arguments = ['container', 'create', '--name', name_for(record), '--read-only', '--cap-drop', 'ALL',
            '--security-opt', 'no-new-privileges', '--network', 'bridge', '--restart', 'no', '--user', '65532:65532',
            '--pids-limit', '128', '--cpus', '2', '--memory', '1g', '--log-driver', 'none',
            '--env', 'AMPHORA_RUNTIME_TOKEN', '--env', 'AMPHORA_ARTIFACT_TOKEN',
            '--env', 'SSL_CERT_FILE=/amphora/certificate.pem']
        for key, value in ((LABEL, record['deployment_id']), (BINDING, record['binding_sha256']),
                           (TURN, record['turn_id']), (WORKER, record['worker'])):
            arguments += ['--label', key + '=' + value]
        for source, target in ((profile.configuration, '/amphora/worker.json'), (profile.certificate, '/amphora/certificate.pem')):
            require(',' not in str(source), 'container_mount_path')
            arguments += ['--mount', 'type=bind,source=' + str(source) + ',target=' + target + ',readonly']
        arguments += [profile.image_id, *profile.arguments]
        return digest(self._run(*arguments, environment=environment), 'container_created_id')

    def start(self, container_id):
        digest(container_id, 'container_id')
        self._run('container', 'start', container_id)

    def remove_exited(self, record, profile):
        observed = self.observe(record, profile)
        if observed is None:
            require(record['phase'] == 'exited', 'container_removal_uncertain')
            return
        require(observed.status == 'exited' and observed.exit_code == record['exit_code'], 'container_removal_requires_exit')
        # No force, name, volume deletion or raw container logs.
        self._run('container', 'rm', observed.container_id)
