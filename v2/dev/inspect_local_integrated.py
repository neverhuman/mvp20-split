"""Read retained model/context/scientific outcomes without workers or provider credentials."""

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


def inspect(configuration, retained, output, root=None):
    output.mkdir(parents=True, exist_ok=False)
    prepared = json.loads((configuration / 'prepared.json').read_bytes())
    admission = json.loads((retained / 'admission.json').read_bytes())
    original = json.loads((retained / 'latest.json').read_bytes())['graph']
    owners = json.loads((configuration / 'owners.json').read_bytes())['owners']
    write(output / 'owners.json', {'profile': 'local-supervisor-v1', 'owners':
        {name: value for name, value in owners.items() if name != 'registry'}})
    root = root or Path(os.environ['LOCALAPPDATA']) / 'Amphora/local-v2/installation'
    routes = Routes.load(root)
    tokens = CredentialVault(root / 'credentials.dpapi', LocalState.snapshot(root)['deployment_id']).load().environment([
        'RUNTIME_OPERATOR_TOKEN', 'ARTIFACT_OPERATOR_TOKEN', 'RUNTIME_ARTIFACT_TOKEN', 'RUNTIME_PLANNING_TOKEN',
        'RESEARCH_OPERATOR_TOKEN', 'KNOWLEDGE_OPERATOR_TOKEN'])
    controller = RecordsController(root, output, routes)
    try:
        controller.start()
        scenario = Scenario(controller, tokens, prepared['scope'], output)
        def content(artifact):
            request = urllib.request.Request(routes.endpoint('artifact') + '/v1/artifacts/' + artifact['artifact_id'] + '/content',
                headers={'Authorization': 'Bearer ' + tokens['ARTIFACT_OPERATOR_TOKEN']})
            with controller.opener.open(request, timeout=3) as stream:
                raw = stream.read(1048577)
            assert len(raw) == artifact['size_bytes'] and hashlib.sha256(raw).hexdigest() == artifact['sha256']
            return json.loads(raw)
        run_id = admission['run_id']
        assert scenario.call('runtime', '/v3/graph-runs/' + run_id) == original
        assert scenario.call('runtime', '/v1/graph-runs/supervised', admission['command']) == admission['receipt']
        records = json.loads((configuration / 'owner-readback.json').read_bytes())
        for owner, path, name in [('research', 'questions', 'question'), ('research', 'evidence-needs', 'need'),
                                  ('knowledge', 'graph-snapshots', 'snapshot')]:
            assert scenario.call(owner, '/v1/' + path + '/read', records[name]['reference']) == records[name]
        context = content(prepared['context'])
        assert context == json.loads((configuration / 'owner-context.json').read_bytes())
        page = scenario.call('runtime', '/v1/supervision/runs/' + run_id + '/checkpoints')
        item, = page['items']
        decision_id = item['reference']['decision_id']
        decision = scenario.call('runtime', '/v1/supervision/decisions/' + run_id + '/' + decision_id)
        query = '?snapshot_token=' + quote(page['snapshot']['snapshot_token'], safe='')
        requests = scenario.call('runtime', '/v1/supervision/runs/' + run_id + '/checkpoints/' + decision_id + '/requests' + query)
        responses, reports = [], []
        for request in requests['items']:
            endpoint = '/v2/supervision/execution/' + request['engagement']['engagement_id']
            code, report = controller.request(routes.endpoint('planning'), endpoint, token=tokens['RUNTIME_PLANNING_TOKEN'])
            assert code == 200
            reports.append(report)
            response_page = scenario.call('runtime', '/v1/supervision/runs/' + run_id + '/checkpoints/' + decision_id +
                '/requests/' + request['request_sha256'] + '/responses' + query)
            for row in response_page['items']:
                response = scenario.call('runtime', '/v1/supervision/responses/' + row['response_id'])
                responses.append({'selected': row['selected_by_winner'], 'response': response})
        nodes = scenario.call('runtime', '/v1/graph-observations/' + run_id + '/nodes?limit=100')
        assert nodes['next_cursor'] is None
        query = '?snapshot_token=' + quote(nodes['snapshot']['snapshot_token'], safe='')
        invocations = []
        for node in nodes['nodes']:
            if node['kind'] != 'invoke':
                continue
            detail = scenario.call('runtime', '/v1/graph-observations/' + run_id + '/nodes/' + node['activation_id'] + query)
            assert detail['next_cursor'] is None
            completions = []
            for attempt in detail['attempts']:
                if not attempt['canonical_result']:
                    continue
                completion = scenario.call('runtime', '/v1/runs/' + run_id + '/completions/' + attempt['completion_id'])
                outputs = [{'artifact': value['artifact'], 'content': content(value['artifact'])}
                    for value in completion['result']['outcome'].get('outputs', [])]
                retained_outputs = []
                for reservation in completion['retention_reservation_ids']:
                    code, record = controller.request(routes.endpoint('artifact'), '/v1/reservations/' + reservation,
                                                      token=tokens['RUNTIME_ARTIFACT_TOKEN'])
                    assert code == 200
                    retained_outputs.append(record)
                completions.append({'completion': completion, 'outputs': outputs, 'retention': retained_outputs})
            invocations.append({'node': node, 'detail': detail, 'completions': completions})
        final = controller.drain()
        write(output / 'evidence.json', {'timestamp_local': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'readback_passed', 'run_id': run_id, 'scope': prepared['scope'], 'graph': original,
            'decision': decision, 'responses': responses, 'reports': reports, 'context': context,
            'invocations': invocations, 'original_graph_and_admission_unchanged': True,
            'exact_owner_context_unchanged': True, 'final': final, 'additional_model_calls': 0,
            'limits': ['Retained outcome inspection; failed invocations remain failures, no scientific acceptance inferred']})
        print('Exact owner context, original graph/admission and model/scientific outcomes read back; zero calls', flush=True)
    finally:
        controller.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('configuration', 'retained', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--root', type=Path, help='Explicit separately restored installation; default preserves original profile')
    args = parser.parse_args()
    inspect(args.configuration.absolute(), args.retained.absolute(), args.output.absolute(), root=args.root.absolute() if args.root else None)
