"""Four isolated owner processes; public exchange and owner-scoped credentials."""

import json
import secrets
import socket
from contextlib import ExitStack
from pathlib import Path
from urllib.parse import urlsplit

from sqlalchemy import URL

from campaign_context_fixture.support import Owner as RecordOwner, environment
from postgres_fixture import owned_state
from supervision_owner_fixture.hosts import Owner
from .materials import prepare, profiles, run_owner, write


class Session:
    @classmethod
    def retained(cls, installation, records_directory, output):
        """Resume only public successor work; preserve compiled materials and model history."""
        self = cls.__new__(cls)
        self.resources, self.output, self.steps = ExitStack(), output, []
        self.records = json.loads((records_directory / 'records.json').read_bytes())
        self.scope = self.records['scope']
        manifest = json.loads((installation / 'manifest.json').read_bytes())
        self.pythons = {name: Path(value['python']) for name, value in manifest['owners'].items()}
        self.tokens = {name: secrets.token_hex(32) for name in self.pythons}
        state = owned_state(); host, port = state['endpoint'].split(':')
        self.envs = {}
        for name, role in [('artifact', 'artifact'), ('research', 'research'), ('runtime', 'runtime')]:
            database = URL.create('postgresql+psycopg', username=role + '_service', password=state['password'], host=host,
                port=int(port), database=state['database']).render_as_string(hide_password=False)
            self.envs[name] = {**environment(), 'PROOF_DATABASE_URL': database, 'PROOF_OWNER_TOKEN': self.tokens[name]}
        self.envs['artifact']['PROOF_RUNTIME_TOKEN'] = self.tokens['runtime']
        self.envs['runtime'].update(PROOF_DATA_TOKEN=self.tokens['artifact'], PROOF_CURSOR_KEY=secrets.token_hex(32))
        self.runtime_config = output / 'runtime.json'
        runtime = json.loads(self.runtime_config.read_bytes())
        data = json.loads((output / 'artifact.json').read_bytes())
        assert all(row['scope'] == self.scope for row in runtime['principals'])
        try:
            self.data = self.owner('artifact', 'amphora_data_artifacts', output / 'artifact.json', port=urlsplit(runtime['bindings']['endpoint']).port)
            self.research = self.owner('research', 'amphora_research', output / 'research.json')
            self.runtime = self.owner('runtime', 'amphora_campaign_runtime', self.runtime_config, port=urlsplit(data['runtime']['endpoint']).port)
        except BaseException:
            self.close(); raise
        return self

    def __init__(self, installation, records_directory, output):
        self.resources = ExitStack()
        self.output = output
        self.records = json.loads((records_directory / 'records.json').read_bytes())
        self.scope = self.records['scope']
        manifest = json.loads((installation / 'manifest.json').read_bytes())
        assert manifest['status'] == 'installed_only'
        self.pythons = {name: Path(value['python']) for name, value in manifest['owners'].items()}
        self.tokens = {name: secrets.token_hex(32) for name in self.pythons}
        self.steps = []
        try:
            self.start(records_directory)
        except BaseException:
            self.close()
            raise

    def owner(self, name, module, configuration, *, port=None):
        klass = RecordOwner if name == 'research' else Owner
        args = {} if port is None else {'port': port}
        instance = klass(self.pythons[name], module, configuration, self.envs[name], self.tokens[name], self.output, **args)
        self.resources.callback(instance.close)
        return instance

    def start(self, records_directory):
        state = owned_state()
        host, port = state['endpoint'].split(':')
        self.envs = {}
        for name, role in [('artifact', 'artifact'), ('research', 'research'), ('planning', 'planning'), ('runtime', 'runtime')]:
            database = URL.create('postgresql+psycopg', username=role + '_service', password=state['password'], host=host,
                port=int(port), database=state['database']).render_as_string(hide_password=False)
            self.envs[name] = {**environment(), 'PROOF_DATABASE_URL': database, 'PROOF_OWNER_TOKEN': self.tokens[name]}
        self.envs['planning']['AMPHORA_PLANNING_DATABASE_URL'] = self.envs['planning']['PROOF_DATABASE_URL']
        hold = socket.socket(); self.resources.callback(hold.close); hold.bind(('127.0.0.1', 0))
        runtime_port = hold.getsockname()[1]
        admitted = profiles(self.pythons['runtime'], self.output)
        data_config = json.loads((records_directory / 'artifact.json').read_bytes())
        data_config.update(database_url_env='PROOF_DATABASE_URL', profiles=data_config['profiles'] + admitted,
            limits={'max_bytes': 1048576, 'scope_bytes': 16777216},
            runtime={'owner': 'operator', 'endpoint': f'http://127.0.0.1:{runtime_port}/v1/completion-intents/outcome', 'token_env': 'PROOF_RUNTIME_TOKEN'})
        data_config['principals'][0].update(token_env='PROOF_OWNER_TOKEN', actions=['read', 'upload', 'finalize', 'retention', 'source_history'])
        self.envs['artifact']['PROOF_RUNTIME_TOKEN'] = self.tokens['runtime']
        self.data = self.owner('artifact', 'amphora_data_artifacts', write(self.output / 'artifact.json', data_config))
        research_config = json.loads((records_directory / 'research.json').read_bytes())
        research_config['database_url_env'] = 'PROOF_DATABASE_URL'; research_config['principals'][0]['token_env'] = 'PROOF_OWNER_TOKEN'
        self.research = self.owner('research', 'amphora_research', write(self.output / 'research.json', research_config))
        for path, key in [('questions', 'question'), ('evidence-needs', 'need')]:
            assert self.research.call('POST', '/v1/' + path + '/read', self.records[key]['reference']) == self.records[key]
        self.compiled, template = prepare(self.data, self.records, admitted, self.pythons, self.output)
        self.envs['planning']['AMPHORA_PLANNING_SUPERVISION_CREDENTIALS'] = json.dumps([
            {'token': self.tokens['planning'], 'actor_id': 'operator', 'scope': self.scope, 'actions': ['record_requests', 'read_attempts']}])
        self.planning = self.owner('planning', 'amphora_agent_planning.supervision_api', None)
        peer = {'endpoint': self.data.endpoint, 'token_env': 'PROOF_DATA_TOKEN'}
        for name in ['runtime', 'planning']:
            self.envs[name]['PROOF_DATA_TOKEN'] = self.tokens['artifact']
        self.envs['runtime']['PROOF_PLANNING_TOKEN'] = self.tokens['planning']
        self.envs['runtime']['PROOF_CURSOR_KEY'] = secrets.token_hex(32)
        self.envs['planning'].update(PROOF_RUNTIME_TOKEN=self.tokens['runtime'], PROOF_RESEARCH_TOKEN=self.tokens['research'])
        self.runtime_config = write(self.output / 'runtime.json', {'database_url_env': 'PROOF_DATABASE_URL',
            'principals': [{'token_env': 'PROOF_OWNER_TOKEN', 'actor_id': 'operator', 'scope': self.scope,
                'actions': ['admit', 'maintain', 'read', 'deliver', 'outcome', 'supervise_respond', 'author', 'validate']}],
            'fixtures': [], 'graphs': [self.compiled['graph']], 'authoring': True,
            'artifacts': {'runtime_owner': 'operator', 'reserve_endpoint': self.data.endpoint + '/v1/reservations', 'token_env': 'PROOF_DATA_TOKEN'},
            'inspection': {'cursor_key_env': 'PROOF_CURSOR_KEY'},
            'bindings': peer, 'projections': peer, 'supervision': {'capture_data': peer},
            'supervision_admission': {'policies': ['policy.json'], 'recipes': ['recipe.json']}})
        hold.close()
        self.runtime = self.owner('runtime', 'amphora_campaign_runtime', self.runtime_config, port=runtime_port)
        self.runtime_worker = write(self.output / 'runtime-worker.json', {'database_url_env': 'PROOF_DATABASE_URL',
            'actor_id': 'operator', 'scope': self.scope, 'data': dict(peer, actor_id='operator'),
            'planning': {'endpoint': self.planning.endpoint, 'token_env': 'PROOF_PLANNING_TOKEN', 'actor_id': 'operator'}})
        self.planning_worker = write(self.output / 'planning-worker.json', {'database_url_env': 'PROOF_DATABASE_URL',
            'actor_id': 'operator', 'scope': self.scope, 'publisher_id': 'followup-data', 'data': peer,
            'runtime': {'endpoint': self.runtime.endpoint, 'token_env': 'PROOF_RUNTIME_TOKEN'},
            'templates': [{'reference': template, 'path': 'template.json'}], 'provider': 'fixture_abstain', 'timeout_seconds': 30,
            'followup': {'research': {'endpoint': self.research.endpoint, 'token_env': 'PROOF_RESEARCH_TOKEN'}, 'seeds': ['followup-seed.json']}})

    def command(self, owner, arguments):
        raw = run_owner(self.pythons[owner], arguments, self.output, self.envs[owner])
        self.steps.append({'owner': owner, 'result': json.loads(raw)})

    def advance(self):
        for action, extra in [('coordinate', ['--time-budget', '0.2', '--poll-interval', '0.05']), ('deliver', ['--time-budget', '1', '--limit', '100'])]:
            self.command('runtime', ['-m', 'amphora_campaign_runtime', action, '--config', self.runtime_config,
                '--actor', 'operator', '--tenant', self.scope['tenant_id'], '--project', self.scope['project_id'], *extra])

    def close(self):
        self.resources.close()
