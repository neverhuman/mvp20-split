"""Actual public draft/managed launch setup; retain original commands for recovery."""
import json
import time
import uuid

from local_numeric_configuration import write
from amphora_contracts_campaign_launch import parse_launch
from amphora_contracts_campaign_successor_launch import parse_successor_launch
from amphora_deployment.campaign_launch.intent import LaunchIntent
from amphora_deployment.campaign_launch.profile import LaunchProfilePolicy
from amphora_deployment.campaign_successor.intent import SuccessorIntent


class Campaign:
    def __init__(self, api, output, scope):
        self.api, self.output, self.scope = api, output, scope

    def original(self, name, family, payload, *, numeric=True, command_id=None):
        path = self.output / (name + '-command.json')
        if path.exists():
            value = json.loads(path.read_bytes())
            assert value['identity']['command_family'] == family and value['identity']['scope'] == self.scope
            assert value['payload'] == payload, 'Original intent changed'
            assert command_id is None or value['identity']['command_id'] == command_id
            return value
        value = {'identity': {'scope': self.scope, 'actor_id': 'admin', 'command_id': command_id or uuid.uuid4().hex,
                              'command_family': family}, 'payload': payload}
        if numeric:
            value['encoding'] = 'amphora-command-v2'
        write(path, value)
        return value

    def save(self, definition, name='original'):
        draft_id = 'curation-fixture-' + self.output.parent.name + '-' + name
        command = self.original(name + '-save', 'definition.save', {'draft_id': draft_id, 'expected_revision': 0,
            'title': 'Synthetic curation integration ' + name, 'definition': definition})
        receipt = self.api.call('runtime', '/v1/definition-drafts/save', command)
        write(self.output / (name + '-save-receipt.json'), receipt)
        assert receipt['outcome']['status'] == 'accepted', receipt['outcome']
        draft = self.api.call('runtime', '/v1/definition-drafts/' + draft_id + '?revision=1')
        command = self.original(name + '-validate', 'definition.validate', {'draft_id': draft_id,
            'revision': 1, 'content_sha256': draft['head']['content_sha256']}, numeric=False)
        receipt = self.api.call('runtime', '/v1/definition-drafts/validate', command)
        write(self.output / (name + '-validate-receipt.json'), receipt)
        assert receipt['outcome']['status'] == 'accepted', receipt['outcome']
        validation = self.api.call('runtime', '/v1/definition-validations/' + receipt['outcome']['committed']['object_id'])
        write(self.output / (name + '-draft.json'), draft)
        write(self.output / (name + '-validation.json'), validation)
        assert validation['structurally_valid']
        return draft, validation

    @staticmethod
    def admission(validation):
        return {'draft': {key: validation[key] for key in
                ('draft_id', 'revision', 'content_sha256', 'validation_id', 'universe_sha256')},
                'plan_sha256': validation['plan_sha256'], 'inputs': [], 'budget': {'limit': 4},
                'limits': {'deadline_seconds': 600}}

    def launch(self, validation, profile, *, predecessor=None, carried=None):
        successor = predecessor is not None
        label = 'successor' if successor else 'original'
        payload = self.admission(validation)
        if successor:
            payload.update(predecessor=predecessor, carried=carried)
        admission = self.original(label + '-admission-v3',
            'graph.admit_draft_successor' if successor else 'graph.admit_draft', payload)
        command = self.original(label + '-launch-v3', 'campaign.launch_successor' if successor else 'campaign.launch',
            {'profile': profile, 'admission': admission}, command_id=admission['identity']['command_id'])
        (parse_successor_launch if successor else parse_launch)(json.dumps(command))
        intent = (SuccessorIntent if successor else LaunchIntent).parse(json.dumps(command).encode())
        LaunchProfilePolicy.from_bytes((self.output / 'launch-profile.json').read_bytes()).check(intent)
        route = '/v1/campaign-successor-launches' if successor else '/v1/campaign-launches'
        receipt = self.api.call('deployment', route, command, allowed=(200, 202))
        write(self.output / (label + '-initial-launch-receipt.json'), receipt)
        deadline = time.monotonic() + 240
        while receipt['phase'] != 'released':
            write(self.output / (label + '-launch-receipt.json'), receipt)
            assert receipt['phase'] not in {'rejected', 'recovery_required'}, receipt
            assert time.monotonic() < deadline, 'Launch did not drain within qualification deadline'
            time.sleep(1)
            receipt = self.api.call('deployment', route + '/' + command['identity']['command_id'])
        write(self.output / (label + '-launch-receipt.json'), receipt)
        run = self.api.call('runtime', '/v3/graph-runs/' + receipt['run_id'])
        write(self.output / (label + '-run.json'), run)
        assert run['status'] == 'completed' and run['spent'] == 1
        sources = self.api.call('runtime', '/v1/graph-runs/' + receipt['run_id'] + '/carry-sources')
        write(self.output / (label + '-carry-sources.json'), sources)
        assert sources['predecessor_ready']
        return receipt, run, sources


def seed_definition(scope, runtime, specification):
    tool = next(row for row in runtime['tools'] if row['binding']['capability_id'] == 'numeric.search-seed')
    output = tool['outputs'][0]
    value_type = {'kind': 'artifact', 'media_type': 'application/json', **{
        key: output[key] for key in ('schema_ref', 'representation', 'unit')}}
    value = {'kind': 'artifact', 'artifact': specification, 'representation': 'search.specification', 'unit': '1'}
    return {'schema_version': '4', 'profile': 'deterministic-v3', 'scope': scope,
        'campaign_id': 'synthetic-curation-seed', 'revision': 1, 'context': [], 'body': {
            'inputs': [], 'outputs': [{'name': 'result', 'value_type': value_type}],
            'nodes': [{'kind': 'invoke', 'node_id': 'seed', 'tool': tool['binding'],
                'inputs': [{'port': 'parameters', 'source': value}], 'timeout_seconds': 60},
                {'kind': 'finish', 'node_id': 'finish', 'outputs': [
                    {'port': 'result', 'source': {'kind': 'output', 'node_id': 'seed', 'port': 'result'}}]}],
            'edges': [{'source': 'seed', 'target': 'finish', 'route': 'next'}]}}
