"""Actual installed Runtime/Registry compatibility for Planning compiler clients."""

import argparse
import hashlib
import json
import os
import secrets
import shutil
import subprocess
import uuid
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from sqlalchemy import URL

from campaign_context_fixture import configuration
from campaign_context_fixture.data import command
from campaign_context_fixture.support import Owner, environment
from postgres_fixture import owned_state

ROOT = Path(__file__).absolute().parents[1]


def verify(args):
    assert os.environ.get('AMPHORA_TEST_POSTGRES') == '1'
    output, installation = args.output.absolute(), args.installation.absolute()
    output.mkdir(parents=True, exist_ok=False)
    proof = json.loads((installation / 'manifest.json').read_bytes())
    assert proof['status'] == 'passed' and proof['planning'] == '0.61.0' and proof['scope'] == 'compiler'
    pythons = {'planning': installation / 'environment/Scripts/python.exe',
               'runtime': args.runtime_python.absolute(), 'registry': args.registry_python.absolute()}
    versions = {'planning': ('amphora-agent-planning', '0.61.0'),
                'runtime': ('amphora-campaign-runtime', '0.20.2'), 'registry': ('amphora-capability-registry', '0.1.0')}
    env = environment()
    for name, python in pythons.items():
        package, version = versions[name]
        subprocess.run([str(python), '-I', '-c',
            f'from importlib.metadata import version; assert version({package!r}) == {version!r}'],
            env=env, cwd=output, check=True, timeout=20, capture_output=True)
    state = owned_state()
    host, port = state['endpoint'].split(':')
    for key, role in [('CTX_RUNTIME_DB', 'runtime_service'), ('CTX_REGISTRY_DB', 'registry_service')]:
        env[key] = URL.create('postgresql+psycopg', username=role, password=state['password'], host=host,
            port=int(port), database=state['database']).render_as_string(hide_password=False)
    env.update(CTX_TOKEN=secrets.token_hex(32), CTX_DENIED=secrets.token_hex(32), CTX_FOREIGN=secrets.token_hex(32))
    scope = {'tenant_id': 'compiler-owners', 'project_id': uuid.uuid4().hex}
    configs = {'registry': configuration.registry(ROOT, output, scope)}
    configs['runtime'], lock, descriptor = configuration.runtime(ROOT, output, scope)
    for name, actions in [('runtime', ['read', 'author', 'validate']),
                          ('registry', ['read', 'register', 'activate', 'deploy', 'heartbeat', 'resolve', 'drain'])]:
        value = json.loads(configs[name].read_bytes())
        value['principals'][0]['actions'] = actions
        if name == 'registry':
            # Synthetic deployment metadata matches the reviewed Linux tool;
            # no worker is launched or target-host support claimed here.
            value['resources']['operating_system'] = 'linux'
        configuration.write(configs[name], value)
    registry_config = json.loads(configs['registry'].read_bytes())
    # Independently specified public policy fingerprint; do not trust a reply
    # to select the policy under which that same reply is accepted.
    policy = {'profile': 'amphora-tool-selection-v1', 'scientific_profile': 'synthetic-only-v1', 'scope': scope,
              'resources': registry_config['resources'], 'permissions': {'allowed_egress_hosts': [], 'effects': ['pure']}}
    policy_sha = hashlib.sha256(json.dumps(policy, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()).hexdigest()
    tests = output / 'tests'
    shutil.copytree(installation / 'tests/service', tests / 'service')
    shutil.copyfile(ROOT / 'services/agent_planning/tests/acceptance/test_compiler_owners.py',
                    tests / 'service/acceptance/test_compiler_owners.py')
    owners, pids, results = {}, {}, {}

    def start(name):
        module = 'amphora_campaign_runtime' if name == 'runtime' else 'amphora_capability_registry'
        owners[name] = Owner(pythons[name], module, configs[name], env, env['CTX_TOKEN'], output)
        pids.setdefault(name, []).append(owners[name].process.pid)

    def registry(action, identifier, payload):
        return owners['registry'].call('POST', '/v1/registry/' + action,
            command(scope, 'registry.' + action, identifier, payload))

    def probe(stage, release):
        case = configuration.write(output / (stage + '-case.json'),
            {'stage': stage, 'scope': scope, 'release': release, 'policy_sha256': policy_sha})
        result_path = output / (stage + '-result.json')
        worker = dict(environment(), CTX_TOKEN=env['CTX_TOKEN'], CTX_DENIED=env['CTX_DENIED'],
            COMPILER_OWNER_CASE=str(case), COMPILER_OWNER_RESULT=str(result_path),
            COMPILER_RUNTIME=owners['runtime'].endpoint, COMPILER_REGISTRY=owners['registry'].endpoint)
        result = subprocess.run([str(pythons['planning']), '-I', '-m', 'pytest',
            str(tests / 'service/acceptance/test_compiler_owners.py'), '--import-mode=importlib', '--tb=short', '-q',
            '--junitxml=' + str(output / (stage + '.xml'))], cwd=output, env=worker,
            capture_output=True, text=True, encoding='utf-8', timeout=60,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        (output / (stage + '.log')).write_text(result.stdout + result.stderr, encoding='utf-8')
        assert result.returncode == 0, 'Actual compiler owner probe failed; inspect stage log'
        results[stage] = json.loads(result_path.read_bytes())

    try:
        for name in configs:
            start(name)
        registered = registry('register', 'register', {'scope': scope, 'descriptor': descriptor, 'expected_lock': lock})
        assert registered['reason_code'] == 'registered'
        release = registry('activate', 'activate', {'release': lock, 'expected_revision': 1})['release']
        registry('deploy', 'deploy', {'deployment_id': 'compiler', 'release': lock, 'architecture': 'x86_64',
            'operating_system': 'linux', 'workers': ['fixture']})
        registry('heartbeat', 'heartbeat', {'deployment_id': 'compiler', 'replica_id': 'replica', 'expected_revision': 0,
            'free_slots': 1, 'ttl_seconds': 60})
        probe('original', release)
        for name in configs:
            owners[name].close()
            start(name)
        probe('restarted', release)
        assert results['original'] == results['restarted']
        registry('drain', 'drain', {'release': lock, 'expected_revision': 2})
        probe('drained', release)
        assert results['original'] == results['drained']
    finally:
        for owner in owners.values():
            owner.close()
    manifest = {'verified_at': datetime.now(ZoneInfo('America/Chicago')).strftime('%Y-%m-%d %H:%M:%S'),
        'status': 'passed', 'versions': versions, 'scope': scope, 'stages': list(results), 'owner_processes': pids,
        'limits': ['Synthetic test-owned primitive dispatch; no durable production coordinator or provider call',
                   'Scalar campaign authoring and separate exact tool eligibility; no combined tool campaign execution',
                   'No Data/Research/Knowledge revalidation claim; prior owner proofs remain separate',
                   'Restart of installed owners, not an independent implementation rewrite; no migrations or resets']}
    configuration.write(output / 'manifest.json', manifest)
    print(json.dumps({'status': 'passed', 'stages': list(results)}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for option in ('installation', 'output', 'runtime-python', 'registry-python'):
        parser.add_argument('--' + option, type=Path, required=True)
    verify(parser.parse_args())
