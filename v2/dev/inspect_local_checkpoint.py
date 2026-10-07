"""Public readback of one retained model checkpoint; never loads a provider key."""

import argparse
import hashlib
import json
import os
import urllib.request
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

from amphora_deployment.credentials import CredentialVault
from amphora_deployment.lifecycle.routes import Routes
from amphora_deployment.persistence.state import LocalState
from local_numeric_configuration import write
from local_records_controller import RecordsController
from verify_local_owner_records import Scenario


def inspect(configuration, retained, output):
    output.mkdir(parents=True, exist_ok=False)
    original = json.loads((retained / 'evidence.json').read_bytes())
    admission = json.loads((retained / 'admission.json').read_bytes())
    root = Path(os.environ['LOCALAPPDATA']) / 'Amphora/local-v2/installation'
    routes = Routes.load(root)
    tokens = CredentialVault(root / 'credentials.dpapi', LocalState.snapshot(root)['deployment_id']).load().environment(
        ['RUNTIME_OPERATOR_TOKEN', 'ARTIFACT_OPERATOR_TOKEN', 'RUNTIME_PLANNING_TOKEN'])
    controller = RecordsController(root, configuration, routes)
    try:
        controller.start()
        scenario = Scenario(controller, tokens, original['scope'], output)
        run_id = original['run_id']
        assert scenario.call('runtime', '/v3/graph-runs/' + run_id) == original['graph']
        assert scenario.call('runtime', '/v1/graph-runs/supervised', admission['command']) == admission['receipt']
        page = scenario.call('runtime', '/v1/supervision/runs/' + run_id + '/checkpoints')
        decision_id = page['items'][0]['reference']['decision_id']
        query = '?snapshot_token=' + quote(page['snapshot']['snapshot_token'], safe='')
        requests = scenario.call('runtime', '/v1/supervision/runs/' + run_id + '/checkpoints/' + decision_id + '/requests' + query)
        responses = []
        for request in requests['items']:
            result = scenario.call('runtime', '/v1/supervision/runs/' + run_id + '/checkpoints/' + decision_id +
                '/requests/' + request['request_sha256'] + '/responses' + query)
            for item in result['items']:
                response = scenario.call('runtime', '/v1/supervision/responses/' + item['response_id'])
                responses.append({'selected': item['selected_by_winner'], 'response': response})
        nodes = scenario.call('runtime', '/v1/graph-observations/' + run_id + '/nodes')
        # The canonical graph names the exact materialization activation.
        target = next(row for row in original['graph']['nodes'] if row['path']['node_id'] == 'pack')
        values = scenario.call('runtime', '/v1/graph-observations/' + run_id + '/nodes/' + target['activation_id'] +
            '/outputs/result?snapshot_token=' + quote(nodes['snapshot']['snapshot_token'], safe=''))
        artifacts = {}
        def collect(value):
            if isinstance(value, dict):
                if 'artifact_id' in value and 'sha256' in value:
                    artifacts[value['artifact_id']] = value
                for child in value.values():
                    collect(child)
            elif isinstance(value, list):
                for child in value:
                    collect(child)
        collect(values)
        assert len(artifacts) == 1
        artifact = next(iter(artifacts.values()))
        request = urllib.request.Request(routes.endpoint('artifact') + '/v1/artifacts/' + artifact['artifact_id'] + '/content',
            headers={'Authorization': 'Bearer ' + tokens['ARTIFACT_OPERATOR_TOKEN']})
        with controller.opener.open(request, timeout=3) as stream:
            content = stream.read(1048577)
        assert len(content) == artifact['size_bytes'] and hashlib.sha256(content).hexdigest() == artifact['sha256']
        assert json.loads(content) == {'a': 7}
        assert len(responses) == 1 and responses[0]['selected']
        final = controller.drain()
        write(output / 'evidence.json', {'timestamp_local': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'passed', 'run_id': run_id, 'scope': original['scope'], 'responses': responses,
            'artifact': artifact, 'materialized_content': json.loads(content), 'original_admission_replay': True,
            'original_graph_unchanged': True, 'final': final, 'additional_model_calls': 0,
            'limits': ['Public owner readback and original receipt replay; no worker started or provider key loaded']})
        print('Retained selected response, actual a=7 artifact bytes and original graph/receipt replay verified', flush=True)
    finally:
        controller.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('configuration', 'retained', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    inspect(args.configuration.absolute(), args.retained.absolute(), args.output.absolute())
