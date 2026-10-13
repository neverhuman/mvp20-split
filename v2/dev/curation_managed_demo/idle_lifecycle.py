"""Installed supervisor idle/stop/recovery proof; not peer or live-provider acceptance."""
import argparse
import json
import shutil
import time
from pathlib import Path
from datetime import datetime
from campaign_curation_fixture.session import session
from campaign_curation_fixture.recovery import read, retained
from local_numeric_configuration import write
from curation_live_qualification.configuration import planning_python, worker_environment
from curation_live_qualification.run import owned_process


def verify(root, serving, qualification, deployment, output):
    output.mkdir(parents=True, exist_ok=False)
    manifest = read(deployment / 'manifest.json')
    assert manifest['packages']['amphora-deployment'] == '0.20.0'
    for name in ('owners.json', 'access.json', 'native.json', 'launch.json', 'launch-prepared.json'):
        shutil.copyfile(serving / name, output / name)
    prepared = read(output / 'launch-prepared.json')
    prepared['deployment_python'] = str(deployment / 'environment/Scripts/python.exe')
    write(output / 'launch-prepared.json', prepared)
    owners = read(output / 'owners.json')
    if 'PLANNING_REGISTRY_TOKEN' not in owners['owners']['planning']['secret_references']:
        owners['owners']['planning']['secret_references'].append('PLANNING_REGISTRY_TOKEN')
    write(output / 'owners.json', owners)
    policy = read(qualification / 'curation-policy.json')
    policy['policy_id'] = 'internal-curation-idle-probe'
    write(output / 'idle-policy.json', policy)
    config = read(qualification / 'curation-worker.json')
    config.update(provider='disabled', live=None, database_url_env='AMPHORA_PLANNING_DATABASE_URL', worker_id='managed-curation-idle-probe', policies=['idle-policy.json'])
    for name in ('data', 'runtime', 'registry'):
        config[name]['token_env'] = 'AMPHORA_PLANNING_' + name.upper() + '_TOKEN'
    for name in ('knowledge', 'research'):
        config[name]['token_env'] = 'AMPHORA_PLANNING_OPERATOR_TOKEN'  # Unused sentinel, not authorized for these peers.
    write(output / 'idle-worker.json', config)
    native = read(output / 'native.json')
    native['workers']['planning-curation'] = {'configuration': str(output / 'idle-worker.json'), 'source_lock': owners['owners']['planning']['source_lock'], 'scope': None}
    write(output / 'native.json', native)
    baseline = read(serving / 'integrated-evidence.json')
    script = Path(__file__).absolute().parents[1] / 'curation_live_qualification/allowance.py'
    with session(root, output) as api:
        retained(api, serving, baseline)
        environment = worker_environment(root, api)
        def allowance(name):
            assert owned_process([planning_python(output), '-I', script, qualification / 'curation-worker.json', output / (name + '.json')], environment, output / 'allowance.log', timeout=60) == 0
            return read(output / (name + '.json'))
        before = allowance('before')
        control = api.controller.control
        path = '/workers/planning-curation'
        def state(): return control('/status')['workers']['planning-curation']
        def wait(predicate):
            deadline = time.monotonic() + 60
            while True:
                value = state()
                if predicate(value): return value
                assert time.monotonic() < deadline, 'Managed curation state did not reach expected condition'
                time.sleep(.1)
        assert state()['state'] == 'quiescent'
        control(path + '/start', 'POST')
        running = wait(lambda row: row['state'] == 'running')
        quiescing = control(path + '/quiesce', 'POST')
        drained = wait(lambda row: row['state'] == 'quiescent')
        assert drained['completed_turns'] >= 1 and drained['exit_code'] == 0 and not drained['faulted']
        control(path + '/start', 'POST')
        wait(lambda row: row['state'] == 'running')
        forced = control(path + '/force-stop', 'POST')
        failed = wait(lambda row: row['state'] == 'failed')
        assert failed['faulted']
        control(path + '/recover', 'POST')
        assert state()['state'] == 'quiescent'
        control(path + '/start', 'POST')
        wait(lambda row: row['state'] == 'running')
        control(path + '/quiesce', 'POST')
        recovered = wait(lambda row: row['state'] == 'quiescent')
        assert recovered['exit_code'] == 0 and not recovered['faulted']
        after = allowance('after')
        assert before == after
        retained(api, serving, baseline)
        write(output / 'lifecycle-evidence.json', {'status': 'passed', 'timestamp_local': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'deployment_release': '0.20.0', 'planning_release': '0.136.0', 'running': running, 'quiescing': quiescing, 'drained': drained, 'forced': forced, 'recovered': recovered, 'original_reservations_unchanged': True, 'provider_calls': 0, 'new_campaigns': 0, 'peer_readiness': 'not_exercised; probe-only sentinel references must not be promoted', 'scope': 'installed idle lifecycle only'})
    print('Installed managed curation idle/force-stop/recovery passed and drained; no provider', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('root', 'serving', 'qualification', 'deployment', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    verify(*(getattr(args, name).absolute() for name in ('root','serving','qualification','deployment','output')))
