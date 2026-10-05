"""Installed compiler with actual Data/Registry/Runtime and owned worker termination."""

import argparse
import hashlib
import json
import os
import secrets
import shutil
import subprocess
import time
import tomllib
import uuid
from datetime import UTC, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from sqlalchemy import URL

from campaign_context_fixture import configuration
from campaign_context_fixture.data import command
from campaign_context_fixture.support import Owner, environment
from campaign_packet_fixture.sources import roots, text_profile
from planning_dispatch_rights import verify_rights
from postgres_fixture import owned_state, planning_owner

ROOT = Path(__file__).absolute().parents[1]


def kill_owned(process):
    if process.poll() is None:
        if os.name == 'nt':
            # The venv launcher owns the Python worker child on Windows.
            subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'],
                           check=True, capture_output=True, timeout=10)
        else:
            process.kill()
        process.wait(timeout=10)


class DispatchOwner(Owner):
    def close(self):
        kill_owned(self.process)
        self.log.close()


def verify(args):
    assert os.environ.get('AMPHORA_TEST_POSTGRES') == '1'
    output, installation = args.output.absolute(), args.installation.absolute()
    output.mkdir(parents=True, exist_ok=False)
    proof = json.loads((installation / 'manifest.json').read_bytes())
    current = tomllib.loads((ROOT / 'services/agent_planning/pyproject.toml').read_text())['project']['version']
    assert proof['status'] == 'passed' and proof['planning'] == current and proof['scope'] in {'dispatch', 'compiler', 'semantic'}
    pythons = {'planning': installation / 'environment/Scripts/python.exe',
        'data': args.data_python.absolute(), 'runtime': args.runtime_python.absolute(), 'registry': args.registry_python.absolute()}
    versions = {'planning': ('amphora-agent-planning', current), 'data': ('amphora-data-artifacts', '0.29.0'),
        'runtime': ('amphora-campaign-runtime', '0.20.2'), 'registry': ('amphora-capability-registry', '0.1.0')}
    env = environment()
    for name, python in pythons.items():
        package, version = versions[name]
        subprocess.run([str(python), '-I', '-c',
            f'from importlib.metadata import version; assert version({package!r}) == {version!r}'],
            env=env, cwd=output, check=True, timeout=20, capture_output=True)
    state = owned_state()
    planning_owner(state)
    host, port = state['endpoint'].split(':')
    for key, role in [('CTX_DATA_DB', 'artifact_service'), ('CTX_RUNTIME_DB', 'runtime_service'),
                      ('CTX_REGISTRY_DB', 'registry_service'), ('DISPATCH_DB', 'planning_service'),
                      ('DISPATCH_MIGRATOR', 'planning_migrator')]:
        env[key] = URL.create('postgresql+psycopg', username=role, password=state['password'], host=host,
            port=int(port), database=state['database']).render_as_string(hide_password=False)
    subprocess.run([str(pythons['planning']), '-I', '-c',
        "import os; from amphora_agent_planning.persistence.migrate import upgrade; upgrade(os.environ['DISPATCH_MIGRATOR'])"],
        env=env, cwd=output, check=True, timeout=30, capture_output=True)
    env.update(CTX_TOKEN=secrets.token_hex(32), CTX_DENIED=secrets.token_hex(32), CTX_FOREIGN=secrets.token_hex(32))
    scope = {'tenant_id': 'compiler-dispatch', 'project_id': uuid.uuid4().hex}
    configs = {'registry': configuration.registry(ROOT, output, scope)}
    configs['runtime'], lock, descriptor = configuration.runtime(ROOT, output, scope)
    for name, actions in [('runtime', ['read', 'author', 'validate']),
                          ('registry', ['read', 'register', 'activate', 'deploy', 'heartbeat', 'resolve'])]:
        value = json.loads(configs[name].read_bytes())
        value['principals'][0]['actions'] = actions
        if name == 'registry':
            value['resources']['operating_system'] = 'linux'
        configuration.write(configs[name], value)
    storage = output / 'bytes'
    storage.mkdir()
    configs['data'] = configuration.write(output / 'data.json', {'database_url_env': 'CTX_DATA_DB',
        'storage_root': str(storage), 'profiles': [text_profile()], 'acquisition': True, 'representations': False,
        'principals': configuration.principals(scope,
            ['upload', 'finalize', 'read', 'acquire', 'source_history', 'manage_source_rights'], ['upload'])})
    policy = {'profile': 'amphora-tool-selection-v1', 'scientific_profile': 'synthetic-only-v1', 'scope': scope,
        'resources': json.loads(configs['registry'].read_bytes())['resources'],
        'permissions': {'allowed_egress_hosts': [], 'effects': ['pure']}}
    policy_sha = hashlib.sha256(json.dumps(policy, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()).hexdigest()
    tests = output / 'tests/service'
    shutil.copytree(installation / 'tests/service', tests)
    source = ROOT / 'services/agent_planning/tests/campaign_dispatch_acceptance'
    # Explicit current test overlay onto a verified unchanged implementation.
    shutil.copytree(source, tests / 'campaign_dispatch_acceptance', dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    test_hashes = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in source.glob('*.py')}
    owners, pids, results, crashes = {}, {}, {}, []
    modules = {'runtime': 'amphora_campaign_runtime', 'registry': 'amphora_capability_registry', 'data': 'amphora_data_artifacts'}

    def start(name):
        owners[name] = DispatchOwner(pythons[name], modules[name], configs[name], env, env['CTX_TOKEN'], output)
        pids.setdefault(name, []).append(owners[name].process.pid)

    def registry(action, identifier, payload):
        return owners['registry'].call('POST', '/v1/registry/' + action,
            command(scope, 'registry.' + action, identifier, payload))

    heartbeat_revision = 0
    def heartbeat():
        nonlocal heartbeat_revision
        registry('heartbeat', 'heartbeat-' + str(heartbeat_revision), {'deployment_id': 'compiler',
            'replica_id': 'replica', 'expected_revision': heartbeat_revision, 'free_slots': 1, 'ttl_seconds': 60})
        heartbeat_revision += 1

    case = {'scope': scope, 'policy_sha256': policy_sha}
    def worker(stage, *, denied=False, crash=False):
        number = len(results) + len(crashes)
        name = f'{number}-{stage}'
        case_path = configuration.write(output / (name + '-case.json'), dict(case, stage=stage, denied=denied))
        result_path, marker = output / (name + '-result.json'), output / (name + '-marker.json')
        worker_env = dict(env, DISPATCH_CASE=str(case_path), DISPATCH_RESULT=str(result_path), DISPATCH_MARKER=str(marker),
            **{'DISPATCH_' + name.upper(): owner.endpoint for name, owner in owners.items()})
        with (output / (name + '.log')).open('wb') as log:
            process = subprocess.Popen([str(pythons['planning']), '-I', '-m', 'pytest',
                str(tests / 'campaign_dispatch_acceptance/test_worker.py'), '--import-mode=importlib', '--tb=short', '-q'],
                cwd=output, env=worker_env, stdout=log, stderr=log, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            try:
                deadline = time.monotonic() + 90
                while time.monotonic() < deadline and process.poll() is None:
                    if crash and marker.exists():
                        evidence = json.loads(marker.read_bytes())
                        assert evidence['pid'] == process.pid or evidence['parent_pid'] == process.pid
                        kill_owned(process)
                        evidence.update(returncode=process.returncode, name=name)
                        crashes.append(evidence)
                        print(json.dumps({'killed': name}), flush=True)
                        # Wait only for this owned20s DB-clock lease, not300s.
                        while datetime.now(UTC) <= datetime.fromisoformat(evidence['expires_at']):
                            time.sleep(0.1)
                        return None
                    time.sleep(0.05)
                assert process.poll() == 0, 'Installed worker failed/timed out; inspect ' + name + '.log'
                result = json.loads(result_path.read_bytes())
                results[name] = result
                print(json.dumps({'stage': stage, 'state': result.get('state', 'seeded')}), flush=True)
                return result
            finally:
                kill_owned(process)

    try:
        for name in configs:
            start(name)
        registry('register', 'register', {'scope': scope, 'descriptor': descriptor, 'expected_lock': lock})
        registry('activate', 'activate', {'release': lock, 'expected_revision': 1})
        registry('deploy', 'deploy', {'deployment_id': 'compiler', 'release': lock, 'architecture': 'x86_64',
            'operating_system': 'linux', 'workers': ['fixture']})
        heartbeat()
        case['roots'] = roots(owners['data'], scope)
        case.update(worker('seed'))
        if args.scenario == 'rights':
            recovered, compiled = verify_rights(worker, heartbeat, owners['data'], scope)
        else:
            assert worker('eligibility')['state'] == 'candidate'
            for stage in ('crash-before-post', 'crash-after-commit'):
                for _ in range(3):
                    heartbeat()
                    result = worker(stage, crash=True)
                    if result is None:
                        break
                    assert result['state'] == 'candidate', 'Expected bounded freshness renewal before crash point'
                else:
                    raise AssertionError('Crash boundary was not reached')
                if stage == 'crash-before-post':
                    assert worker('assert-absent')['state'] == 'absent'
            recovered = worker('recover-save', denied=True)
            assert recovered['state'] == 'saved'
            denied = worker('deny-new-validation', denied=True)
            assert denied['pause_reason'] == 'input_unavailable' and not denied['terminal']
            for _ in range(4):
                heartbeat()
                compiled = worker('compile')
                if compiled['terminal']:
                    break
                assert compiled['state'] == 'candidate'
        assert compiled['state'] == 'compiled', compiled.get('pause_reason')
        for name in configs:
            owners[name].close()
            start(name)
        case.update(saved_observation=recovered['observation'], compiled_observation=compiled['observation'])
        assert worker('peer-history', denied=True)['state'] == 'peer_history_exact'
        replay = worker('replay', denied=True)
        assert replay == compiled
    finally:
        for owner in owners.values():
            owner.close()
    configuration.write(output / 'manifest.json', {'verified_at': datetime.now(ZoneInfo('America/Chicago')).strftime('%Y-%m-%d %H:%M:%S'),
        'status': 'passed', 'scenario': args.scenario, 'versions': versions, 'scope': scope, 'owner_processes': pids, 'worker_results': results,
        'crashes': crashes, 'test_sha256': test_hashes, 'installation_manifest': str(installation / 'manifest.json'),
        'limits': ['Actual installed public Data/Registry/Runtime and Planning-owned SQL; scenario identifies rights or crash proof',
            'Synthetic proposal and declared Linux tool capacity; no scientific tool execution or admission',
            'No provider, Research latest-head or target-host qualification claim; rights scenario changes actual source rights only',
            'Current Planning migration only; retained peer fixtures, no reset or cross-owner SQL']})
    print(json.dumps({'status': 'passed', 'workers': len(results), 'crashes': len(crashes)}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('installation', 'output', 'data-python', 'runtime-python', 'registry-python'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--scenario', choices=['crash', 'rights'], default='crash')
    verify(parser.parse_args())
