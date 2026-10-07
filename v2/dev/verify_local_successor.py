"""Public draft-successor admission carries a real retained result; no new scientific claim."""

import argparse
import json
import os
import shutil
import uuid
from datetime import datetime
from pathlib import Path

from amphora_deployment.credentials import CredentialVault
from amphora_deployment.lifecycle.routes import Routes
from amphora_deployment.persistence.state import LocalState

from local_authoring_controller import AuthoringController
from local_numeric_configuration import write


class Requests:
    def __init__(self, controller, routes, token, scope, output):
        self.controller, self.routes, self.token = controller, routes, token
        self.scope, self.output = scope, output

    def read(self, path):
        code, value = self.controller.request(self.routes.endpoint('runtime'), path, token=self.token)
        assert code == 200, 'Public successor read failed: ' + str(code)
        return value

    def command(self, name, family, payload, path):
        file = self.output / (name + '-command.json')
        if file.exists():
            command = json.loads(file.read_bytes())
            assert command['identity']['scope'] == self.scope and command['identity']['command_family'] == family
            assert command['payload'] == payload, 'Original intent changed; do not retry with a new identity'
        else:
            command = {'identity': {'scope': self.scope,
                'actor_id': 'admin', 'command_id': uuid.uuid4().hex, 'command_family': family}, 'payload': payload}
            if family in {'definition.save', 'graph.admit_draft_successor'}:
                command['encoding'] = 'amphora-command-v2'
            write(file, command)
        code, receipt = self.controller.request(self.routes.endpoint('runtime'), path, token=self.token, body=command)
        if code != 200:
            write(self.output / (name + '-http-failure.json'), {'status': code, 'response': receipt})
        assert code == 200, 'Public successor command failed: ' + str(code)
        previous = self.output / (name + '-receipt.json')
        if previous.exists():
            assert receipt == json.loads(previous.read_bytes())
        else:
            write(previous, receipt)
        assert receipt['outcome']['status'] == 'accepted', 'Successor command rejected; retained receipt is authoritative'
        return receipt


def verify(source, retained, output, resume=False):
    if not resume:
        output.mkdir(parents=True, exist_ok=False)
        for path in source.glob('*.json'):
            shutil.copyfile(path, output / path.name)
        original = json.loads((retained / 'evidence.json').read_bytes())
        assert original['status'] == 'passed'
        write(output / 'successor-intent.json', {'predecessor': original['run_id'], 'scope': original['scope'],
              'draft_id': 'retained-result-' + uuid.uuid4().hex})
    intent = json.loads((output / 'successor-intent.json').read_bytes())
    root = Path(os.environ['LOCALAPPDATA']) / 'Amphora/local-v2/installation'
    state, vault = LocalState.snapshot(root), (root / 'credentials.dpapi').read_bytes()
    routes = Routes.load(root)
    tokens = CredentialVault(root / 'credentials.dpapi', state['deployment_id']).load().environment(
        ['RUNTIME_OPERATOR_TOKEN', 'REGISTRY_OPERATOR_TOKEN'])
    controller = AuthoringController(root, output, routes, registry_token=tokens['REGISTRY_OPERATOR_TOKEN'])
    try:
        controller.start()
        api = Requests(controller, routes, tokens['RUNTIME_OPERATOR_TOKEN'], intent['scope'], output)
        predecessor = api.read('/v3/graph-runs/' + intent['predecessor'])
        sources = api.read('/v1/graph-runs/' + intent['predecessor'] + '/carry-sources')
        assert predecessor['status'] == 'completed' and sources['predecessor_ready']
        assert sources['scope'] == intent['scope']
        selected = [row for row in sources['sources'] if row['source'] == {'kind': 'run_output', 'port': 'result'}]
        assert len(selected) == 1
        value_type = json.loads((source / 'graph.json').read_bytes())['body']['outputs'][0]['value_type']
        definition = {'schema_version': '4', 'profile': 'deterministic-v3', 'scope': intent['scope'],
            'campaign_id': 'retained-result-successor', 'revision': 1, 'context': [], 'body': {
                'inputs': [{'name': 'previous_result', 'value_type': value_type}],
                'outputs': [{'name': 'result', 'value_type': value_type}], 'edges': [],
                'nodes': [{'kind': 'finish', 'node_id': 'retain',
                           'outputs': [{'port': 'result', 'source': {'kind': 'input', 'name': 'previous_result'}}]}]}}
        api.command('successor-save', 'definition.save', {'draft_id': intent['draft_id'], 'expected_revision': 0,
            'title': 'Retained-result successor (engineering fixture)', 'definition': definition}, '/v1/definition-drafts/save')
        draft = api.read('/v1/definition-drafts/' + intent['draft_id'] + '?revision=1')
        validated = api.command('successor-validate-v1', 'definition.validate', {'draft_id': intent['draft_id'],
            'revision': 1, 'content_sha256': draft['head']['content_sha256']}, '/v1/definition-drafts/validate')
        validation = api.read('/v1/definition-validations/' + validated['outcome']['committed']['object_id'])
        assert validation['structurally_valid'] and validation['scientific_acceptance'] == 'not_established'
        payload = {'plan_sha256': validation['plan_sha256'], 'inputs': [], 'budget': {'limit': 1},
            'predecessor': sources['predecessor'], 'carried': [{'target_port': 'previous_result',
                'source': selected[0]['source'], 'expected_value_sha256': selected[0]['value_sha256']}],
            'draft': {key: validation[key] for key in ('draft_id', 'revision', 'content_sha256', 'validation_id', 'universe_sha256')}}
        receipt = api.command('successor-admit', 'graph.admit_draft_successor', payload, '/v1/graph-runs/draft-successors')
        run = receipt['outcome']['committed']['object_id']
        api.command('successor-advance', 'graph.advance', {'run_id': run}, '/v1/graph-runs/advance')
        result = api.read('/v3/graph-runs/' + run)
        child_sources = api.read('/v1/graph-runs/' + run + '/carry-sources')
        lineage = api.read('/v1/graph-runs/' + run + '/lineage')
        assert result['status'] == 'completed' and result['node_count'] == 1 and result['spent'] == 0
        assert child_sources['sources'] == selected and child_sources['predecessor_ready']
        assert lineage['predecessor'] == sources['predecessor'] and lineage['carried'] == payload['carried']
        assert api.read('/v3/graph-runs/' + intent['predecessor']) == predecessor
        assert api.command('successor-admit', 'graph.admit_draft_successor', payload, '/v1/graph-runs/draft-successors') == receipt
        final = controller.drain()
        assert LocalState.snapshot(root) == state and (root / 'credentials.dpapi').read_bytes() == vault
        write(output / 'successor-evidence.json', {'timestamp_local': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'passed', 'scope': intent['scope'], 'run_id': run, 'predecessor': predecessor,
            'sources': sources, 'result': result, 'child_sources': child_sources, 'lineage': lineage,
            'draft': draft, 'validation': validation, 'receipt': receipt, 'final': final,
            'provider_calls': 0, 'scientific_invocations': 0,
            'limits': ['Actual existing search checkpoint carried atomically into a validated tool-free successor',
                       'One pure Runtime finish transition; no repeated science or scientific improvement claimed']})
        print('Actual draft successor completed; exact carried value/history/receipt retained', flush=True)
    finally:
        controller.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('source', 'retained', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    verify(args.source.absolute(), args.retained.absolute(), args.output.absolute(), args.resume)
