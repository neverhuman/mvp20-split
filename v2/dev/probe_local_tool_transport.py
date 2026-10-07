"""Read-only Linux SDK/TLS reproduction; no claims, commands or scientific writes."""

import argparse
import json
import os
import subprocess
import uuid
from pathlib import Path

from amphora_deployment.credentials import CredentialVault
from amphora_deployment.lifecycle.routes import Routes
from amphora_deployment.persistence.state import LocalState

from local_demo_controller import Controller
from local_numeric_configuration import write

PROBE = '''
import json,time,sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from amphora_contracts_core import ArtifactRef
from amphora_tool_protocol import WorkerConfig,WorkerIdentity,RuntimeClient,ArtifactClient,ProtocolError
config=WorkerConfig.model_validate_json(Path('/amphora/worker.json').read_bytes())
reference=ArtifactRef.model_validate_json(sys.argv[1])
def lane(number):
    identity=WorkerIdentity(config.actor_id,config.scope)
    runtime=RuntimeClient(config.runtime.transport(),identity)
    artifact=ArtifactClient(config.artifacts.transport(),identity)
    started=time.monotonic()
    for index in range(50):
        stage='runtime_read'
        try:
            runtime.run(config.run_id)
            stage='artifact_read'
            artifact.read(reference)
        except ProtocolError as error:
            allowed={'transport_lost','run_unavailable','artifact_reference_mismatch','artifact_integrity_mismatch'}
            cause=error.__cause__
            reason=getattr(cause,'reason',None)
            kinds={'URLError','TimeoutError','ConnectionResetError','ConnectionRefusedError','RemoteDisconnected','SSLError'}
            return dict(lane=number,completed=index,status='failed',stage=stage,
                code=str(error) if str(error) in allowed else 'other_protocol_failure',
                cause=type(cause).__name__ if type(cause).__name__ in kinds else 'other',
                reason=type(reason).__name__ if type(reason).__name__ in kinds else 'other',
                elapsed=time.monotonic()-started)
    return dict(lane=number,completed=50,status='passed',elapsed=time.monotonic()-started)
with ThreadPoolExecutor(max_workers=5) as pool:
    print(json.dumps(list(pool.map(lane,range(5)))))
'''


def probe(root, configuration, readback, output):
    output.mkdir(parents=True, exist_ok=False)
    state = LocalState.snapshot(root)
    tokens = CredentialVault(root / 'credentials.dpapi', state['deployment_id']).load().environment(
        ['REGISTRY_OPERATOR_TOKEN', 'WORKER_RUNTIME_TOKEN', 'WORKER_ARTIFACT_TOKEN'])
    manifest = json.loads((configuration / 'admitted-scientific.json').read_bytes())
    worker = manifest['workers']['synthetic-objectives-rebuilt']
    reference = json.loads(readback.read_bytes())['completions'][0]['result']['outcome']['outputs'][0]['artifact']
    controller = Controller(root, configuration, Routes.load(root), 'admitted')
    container = 'amphora-readonly-transport-' + uuid.uuid4().hex
    environment = {key: value for key, value in os.environ.items() if key.upper() in {
        'SYSTEMROOT', 'WINDIR', 'PATH', 'TEMP', 'TMP', 'COMSPEC', 'USERPROFILE', 'LOCALAPPDATA', 'APPDATA'}}
    environment.update(AMPHORA_RUNTIME_TOKEN=tokens['WORKER_RUNTIME_TOKEN'],
                       AMPHORA_ARTIFACT_TOKEN=tokens['WORKER_ARTIFACT_TOKEN'])
    drained = False
    try:
        controller.start_owners(tokens['REGISTRY_OPERATOR_TOKEN'])
        command = ['docker', 'run', '--rm', '--name', container, '--read-only', '--network', 'bridge',
            '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges', '--pids-limit', '128',
            '--cpus', '2', '--memory', '1g', '--log-driver', 'none',
            '--env', 'AMPHORA_RUNTIME_TOKEN', '--env', 'AMPHORA_ARTIFACT_TOKEN',
            '--env', 'SSL_CERT_FILE=/amphora/certificate.pem',
            '--mount', 'type=bind,source=' + worker['configuration'] + ',target=/amphora/worker.json,readonly',
            '--mount', 'type=bind,source=' + worker['certificate'] + ',target=/amphora/certificate.pem,readonly',
            '--entrypoint', 'python', worker['image_id'], '-I', '-c', PROBE, json.dumps(reference)]
        result = subprocess.run(command, env=environment, capture_output=True, timeout=180,
                                creationflags=subprocess.CREATE_NO_WINDOW)
        assert result.returncode == 0 and len(result.stdout) < 8192, 'Read-only transport probe failed'
        rows = json.loads(result.stdout)
        status = controller.control('/status')
        final = controller.drain()
        drained = True
        assert LocalState.snapshot(root) == state
        write(output / 'evidence.json', {'status': 'observed', 'lanes': rows,
            'transport': status['tool_access'], 'final': final, 'claims': 0, 'provider_calls': 0})
        print(json.dumps({'lanes': rows, 'transport': status['tool_access']}), flush=True)
    except subprocess.TimeoutExpired:
        # Exact unique container allocated by this call; never touch other containers.
        subprocess.run(['docker', 'stop', '--time', '5', container], capture_output=True, timeout=15)
        raise
    finally:
        try:
            if not drained:
                controller.drain()
        finally:
            controller.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('root', 'configuration', 'readback', 'output'):
        parser.add_argument('--' + name, required=True, type=Path)
    args = parser.parse_args()
    probe(*(getattr(args, name).absolute() for name in ('root', 'configuration', 'readback', 'output')))
