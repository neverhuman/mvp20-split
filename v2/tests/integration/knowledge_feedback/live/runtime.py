"""Exact public receipt consumption, retained artifact and Runtime restart proof."""
import json
import secrets
import socket
import subprocess
import uuid
from pathlib import Path

from .process import Owner, base_environment


class CampaignScenario:
    def __init__(self, directory, scope, python, environment):
        self.directory, self.scope, self.python = directory, scope, python
        self.environment = dict(environment, ISSUER_TOKEN=secrets.token_hex(24), OUTCOME_TOKEN=secrets.token_hex(24),
            RETENTION_TOKEN=secrets.token_hex(24), CURSOR_KEY=secrets.token_hex(32))
        with socket.socket() as listener:
            listener.bind(('127.0.0.1', 0)); self.port = listener.getsockname()[1]
        self.endpoint = f'http://127.0.0.1:{self.port}'
        self.owner, self.run_id = None, None
        self.path = directory / 'campaign_runtime.json'

    def configure_data(self, config, environment):
        environment.update({key: self.environment[key] for key in ('OUTCOME_TOKEN', 'RETENTION_TOKEN')})
        config['runtime'] = {'owner': 'runtime', 'endpoint': self.endpoint + '/v1/completion-intents/outcome', 'token_env': 'OUTCOME_TOKEN'}
        config['principals'].append({'token_env': 'RETENTION_TOKEN', 'actor_id': 'runtime', 'scope': self.scope, 'actions': ['read', 'retention']})

    def command(self, family, payload, actor='admin'):
        return {'identity': {'scope': self.scope, 'actor_id': actor, 'command_family': family,
            'command_id': uuid.uuid4().hex}, 'payload': payload}

    def start(self):
        if self.owner is not None:
            self.owner.close()
        self.owner = Owner(self.python, 'amphora_campaign_runtime', self.path, self.environment,
            self.environment['OWNER_TOKEN'], port=self.port)

    def close(self):
        if self.owner is not None:
            try:
                if self.run_id is not None and self.owner.process.poll() is None:
                    graph = self.owner.request('/v2/graph-runs/' + self.run_id)
                    if graph['status'] == 'running':
                        self.owner.request('/v1/runs/cancel', self.command('runtime.cancel',
                            {'run_id': self.run_id, 'reason_code': 'test_failure_cleanup'}))
            finally:
                self.owner.close()

    def consume(self, data, receipt):
        subject, output = receipt['subject'], receipt['outcome']['output']
        (self.directory / 'context-schema.json').write_bytes(b'{"type":"string"}')
        input_type = {'kind': 'artifact', 'schema_ref': subject['schema_ref'], 'representation': 'domain-context', 'unit': '1', 'media_type': subject['media_type']}
        output_type = {'kind': 'artifact', 'schema_ref': output['artifact']['schema_ref'], 'representation': output['representation'], 'unit': output['unit'], 'media_type': output['artifact']['media_type']}
        definition = {'schema_version': '3', 'profile': 'deterministic-v2', 'campaign_id': 'feedback-baseline', 'revision': 1,
            'scope': self.scope, 'context': [], 'body': {'inputs': [{'name': 'subject', 'value_type': input_type}],
            'outputs': [{'name': 'result', 'value_type': output_type}], 'nodes': [
                {'kind': 'await', 'node_id': 'evidence', 'issuer_id': receipt['issuer_id'], 'purpose': receipt['purpose'],
                 'expected_revision': receipt['revision'], 'subject': {'kind': 'input', 'name': 'subject'},
                 'output': {'name': 'result', 'value_type': output_type}, 'timeout_seconds': 120, 'on_timeout': 'abstained'},
                {'kind': 'finish', 'node_id': 'finish', 'outputs': [{'port': 'result', 'source': {'kind': 'output', 'node_id': 'evidence', 'port': 'result'}}]}],
            'edges': [{'source': 'evidence', 'target': 'finish', 'route': 'next'}]}}
        (self.directory / 'campaign.json').write_text(json.dumps(definition), encoding='utf-8')
        config = {'database_url_env': 'OWNER_DATABASE', 'inspection': {'cursor_key_env': 'CURSOR_KEY'}, 'fixtures': [],
            'principals': [{'token_env': 'OWNER_TOKEN', 'actor_id': 'admin', 'scope': self.scope, 'actions': ['admit', 'maintain', 'read', 'deliver', 'cancel']},
                {'token_env': 'ISSUER_TOKEN', 'actor_id': receipt['issuer_id'], 'scope': self.scope, 'actions': ['submit_receipt', 'read']},
                {'token_env': 'OUTCOME_TOKEN', 'actor_id': 'artifact-service', 'scope': self.scope, 'actions': ['outcome']}],
            'artifacts': {'runtime_owner': 'runtime', 'reserve_endpoint': data.endpoint + '/v1/reservations', 'token_env': 'RETENTION_TOKEN'},
            'graphs': [{'definition': 'campaign.json', 'releases': [], 'schemas': [
                {'schema_ref': subject['schema_ref'], 'path': 'context-schema.json'},
                {'schema_ref': output['artifact']['schema_ref'], 'path': 'reasoning.json'}]}]}
        self.path.write_text(json.dumps(config), encoding='utf-8')
        compiled = subprocess.run([str(self.python), '-I', str(Path(__file__).with_name('compile_plan.py')), str(self.path)],
            env=base_environment(), capture_output=True, timeout=30, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        assert compiled.returncode == 0, 'Isolated Runtime compilation failed'
        plan = json.loads(compiled.stdout)['feedback-baseline']
        self.start()
        admitted = self.owner.request('/v1/graph-runs', self.command('graph.admit', {'plan_sha256': plan['sha256'],
            'inputs': [{'port': 'subject', 'value': {'kind': 'artifact', 'artifact': subject, 'representation': 'domain-context', 'unit': '1'}}], 'budget': {'limit': 1}}))
        assert admitted['outcome']['status'] == 'accepted'
        self.run_id = admitted['outcome']['committed']['object_id']
        self.owner.request('/v1/graph-runs/advance', self.command('graph.advance', {'run_id': self.run_id}))
        graph = self.owner.request('/v2/graph-runs/' + self.run_id)
        activation = next(node['activation_id'] for node in graph['nodes'] if node['kind'] == 'await')
        wait_path = '/v1/graph-runs/' + self.run_id + '/waits/' + activation
        opened = self.owner.request(wait_path)
        assert opened['closure'] is None
        command = self.command('graph.submit_receipt', {'run_id': self.run_id, 'activation_id': activation,
            'wait_revision': opened['expectation']['wait_revision'], 'expectation_sha256': opened['expectation_sha256'], 'receipt': receipt}, receipt['issuer_id'])
        accepted = self.owner.request('/v1/graph-receipts', command, token=self.environment['ISSUER_TOKEN'])
        assert accepted['outcome']['status'] == 'accepted'
        closed = self.owner.request(wait_path)
        assert closed['closure']['outcome']['receipt'] == receipt
        self.owner.request('/v1/graph-runs/advance', self.command('graph.advance', {'run_id': self.run_id}))
        completed = self.owner.request('/v2/graph-runs/' + self.run_id)
        assert completed['status'] == 'completed' and completed['spent'] == completed['reserved'] == 0
        delivery = subprocess.run([str(self.python), '-I', '-m', 'amphora_campaign_runtime', 'deliver', '--config', str(self.path),
            '--actor', 'admin', '--tenant', self.scope['tenant_id'], '--project', self.scope['project_id'], '--limit', '100', '--time-budget', '5'],
            env=self.environment, capture_output=True, timeout=30, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        assert delivery.returncode == 0, 'Runtime delivery failed'
        deliveries = json.loads(delivery.stdout)
        assert deliveries['acknowledged'] == 1
        self.start()
        assert self.owner.request(wait_path) == closed
        assert self.owner.request('/v1/graph-receipts', command, token=self.environment['ISSUER_TOKEN']) == accepted
        content = data.request('/v1/artifacts/' + output['artifact']['artifact_id'] + '/content', binary=True)
        import hashlib
        assert hashlib.sha256(content).hexdigest() == output['artifact']['sha256']
        snapshot = self.owner.request('/v1/graph-observations/' + self.run_id + '/nodes')
        return {'opened': opened, 'closed': closed, 'accepted': accepted, 'graph': completed,
            'snapshot': snapshot, 'delivery': deliveries, 'replacement_replay': True}
