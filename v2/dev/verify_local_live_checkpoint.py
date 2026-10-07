"""One bounded actual-model checkpoint through managed local owner processes."""

import argparse
import json
import os
import time
import uuid
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

from amphora_deployment.credentials import CredentialVault
from amphora_deployment.lifecycle.routes import Routes
from amphora_deployment.persistence.state import LocalState
from local_numeric_configuration import write
from local_records_controller import RecordsController
from verify_local_owner_records import Scenario


def key_from_authorized_file(path):
    # Read only the explicitly authorized OpenAI assignment; never evaluate shell syntax.
    matches = []
    for line in path.read_text(encoding='utf-8-sig').splitlines():
        name, separator, value = line.strip().removeprefix('export ').partition('=')
        if separator and name.strip() == 'OPENAI_API_KEY':
            value = value.strip()
            if value.startswith(('"', "'")):
                assert len(value) >= 2 and value[-1] == value[0], 'Quoted OpenAI key assignment malformed'
                value = value[1:-1]
            else:
                value = value.split(' #', 1)[0].strip()
            assert value and '\n' not in value and '\r' not in value, 'OpenAI key assignment empty'
            matches.append(value)
    assert len(matches) == 1, 'Exactly one OPENAI_API_KEY assignment required in authorized file'
    return matches[0]


def verify(configuration, output, key_file):
    output.mkdir(parents=True, exist_ok=False)
    material = json.loads((configuration / 'prepared.json').read_bytes())
    root = Path(os.environ['LOCALAPPDATA']) / 'Amphora/local-v2/installation'
    original, vault = LocalState.snapshot(root), (root / 'credentials.dpapi').read_bytes()
    routes = Routes.load(root)
    scope = material['scope']
    tokens = CredentialVault(root / 'credentials.dpapi', original['deployment_id']).load().environment(
        ['RUNTIME_OPERATOR_TOKEN', 'ARTIFACT_OPERATOR_TOKEN', 'PLANNING_OPERATOR_TOKEN', 'RUNTIME_PLANNING_TOKEN'])
    key = key_from_authorized_file(key_file)
    controller, scenario, run_id, final = None, None, None, None
    try:
        controller = RecordsController(root, configuration, routes, workers=True, model_key=key)
        key = None
        controller.start()
        scenario = Scenario(controller, tokens, scope, output)
        command = {'encoding': 'amphora-command-v2', 'identity': {'scope': scope, 'actor_id': 'operator',
            'command_id': 'checkpoint-' + uuid.uuid4().hex, 'command_family': 'graph.admit_supervised'},
            'payload': {'admission': {'plan_sha256': material['compiled']['plan_sha256'], 'inputs': [], 'budget': {'limit': 2}},
                        'policy_sha256': material['compiled']['policy_sha256']}}
        write(output / 'admission-command.json', command)
        admission = scenario.call('runtime', '/v1/graph-runs/supervised', command)
        assert admission['outcome']['status'] == 'accepted'
        run_id = admission['outcome']['committed']['object_id']
        write(output / 'admission.json', {'run_id': run_id, 'command': command, 'receipt': admission})
        for name in ('runtime-deliver', 'runtime-checkpoint', 'planning-checkpoint', 'runtime-coordinate'):
            controller.control('/workers/' + name + '/start', 'POST')
        started, previous = time.monotonic(), None
        while True:
            graph = scenario.call('runtime', '/v3/graph-runs/' + run_id)
            state = controller.control('/status')
            checkpoints = scenario.call('runtime', '/v1/supervision/runs/' + run_id + '/checkpoints')
            write(output / 'latest.json', {'graph': graph, 'controller': state, 'checkpoints': checkpoints})
            observed = (graph['status'], tuple((r['requests'], r['winner_kind']) for r in checkpoints['items']))
            if observed != previous:
                print(json.dumps({'graph': observed[0], 'checkpoints': observed[1]}), flush=True)
                previous = observed
            if graph['status'] != 'running':
                break
            assert not any(row['faulted'] for row in state['workers'].values()), 'Managed native worker faulted'
            assert time.monotonic() - started < 360, 'Live checkpoint exceeded predeclared360second bound'
            time.sleep(1)
        assert graph['status'] == 'completed' and checkpoints['total'] == 1
        item = checkpoints['items'][0]
        reference = item['reference']
        decision = scenario.call('runtime', '/v1/supervision/decisions/' + run_id + '/' + reference['decision_id'])
        requests = scenario.call('runtime', '/v1/supervision/runs/' + run_id + '/checkpoints/' + reference['decision_id'] +
            '/requests?snapshot_token=' + quote(checkpoints['snapshot']['snapshot_token'], safe=''))
        reports = []
        for request in requests['items']:
            # Exact engagement belongs to the authenticated Planning worker actor.
            code, report = controller.request(routes.endpoint('planning'), '/v2/supervision/execution/' + request['engagement']['engagement_id'],
                token=tokens['RUNTIME_PLANNING_TOKEN'])
            assert code == 200
            reports.append(report)
        assert scenario.call('runtime', '/v1/graph-runs/supervised', command) == admission
        final = controller.drain()
        assert LocalState.snapshot(root) == original and (root / 'credentials.dpapi').read_bytes() == vault
        record = {'timestamp_local': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'passed' if item['winner_kind'] == 'model_accepted' else 'model_gate_not_passed',
            'scope': scope, 'run_id': run_id, 'graph': graph, 'checkpoints': checkpoints, 'decision': decision,
            'requests': requests, 'reports': reports, 'final': final, 'elapsed_seconds': time.monotonic() - started,
            'execution_limit_seconds': 360, 'campaign_call_limit': 1, 'scope_call_limit': 6, 'scope_usd_limit': '0.50',
            'original_installation_unchanged': True,
            'limits': ['Actual selected OpenAI provider; synthetic parameter checkpoint only',
                       'Source/Research/Knowledge records are retained but not yet consumed by this minimal checkpoint',
                       'No scientific worker, browser walkthrough or scientific efficacy claim; no retry with a new request']}
        write(output / 'evidence.json', record)
        assert record['status'] == 'passed', 'Runtime fallback preserved; inspect retained model outcome before further calls'
        print('Actual model checkpoint accepted by Runtime; original admission replay retained', flush=True)
    except BaseException as error:
        failure = {'error_type': type(error).__name__, 'run_id': run_id}
        if controller is not None and controller.process.poll() is None and final is None:
            try:
                if run_id is not None:
                    failure['cancel'] = scenario.call('runtime', '/v1/runs/cancel', {'identity': {'scope': scope,
                        'actor_id': 'operator', 'command_id': 'cancel-' + uuid.uuid4().hex, 'command_family': 'runtime.cancel'},
                        'payload': {'run_id': run_id, 'reason_code': 'checkpoint_probe_failed'}})
                failure['drain'] = controller.drain()
            except Exception as cleanup:
                failure['cleanup_error_type'] = type(cleanup).__name__
        write(output / 'failure.json', failure)
        raise
    finally:
        if controller is not None:
            controller.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('configuration', 'output', 'key-file'):
        parser.add_argument('--' + name, required=True, type=Path)
    args = parser.parse_args()
    verify(args.configuration.absolute(), args.output.absolute(), args.key_file.absolute())
