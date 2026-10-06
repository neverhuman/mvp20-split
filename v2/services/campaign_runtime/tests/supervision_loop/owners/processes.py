"""Separate current owner processes and public clients; no Planning/Data private imports."""

import json
import secrets
import socket
import subprocess
import sys
from contextlib import ExitStack
from dataclasses import replace
from pathlib import Path
from urllib.parse import urlsplit

from amphora_contracts_supervision import parse_supervised_admission
from campaign_context_fixture.support import environment
from postgres_fixture import owned_state, planning_owner
from sqlalchemy import URL
from supervision_owner_fixture.hosts import Owner

from .installations import Installations
from .materials import materials, profiles, write


class Owners:
    def __init__(self, graph, root, variant, *, independent=False):
        self.resources, self.graph, self.root = ExitStack(), graph, root
        self.python = Path(sys.executable).absolute()
        self.records = []
        self.installations = Installations.configured()
        self.label, self.host_specs, self.host_processes = 'initial', {}, []
        try:
            self._start(variant, independent=independent)
        except BaseException:
            self.close()
            raise

    def _owner(self, module, config, token, *, port=None):
        python = self.python_for(module)
        owner = Owner(python, module, config, self.env, token, self.root, port=port)
        self.host_specs[module] = (config, token, urlsplit(owner.endpoint).port)
        self.host_processes.append({'module': module, 'pid': owner.process.pid, 'python': str(python),
                                    'label': self.label, 'endpoint': owner.endpoint})
        self.resources.callback(owner.close)
        return owner

    def python_for(self, module):
        return self.python if self.installations is None else self.installations.python(module, self.label)

    def replace_hosts(self):
        assert self.installations is not None and self.label == 'initial'
        hosts = [('data', 'amphora_data_artifacts'), ('planning', 'amphora_agent_planning.supervision_api'),
                 ('runtime', 'amphora_campaign_runtime')]
        for name, _ in hosts:
            getattr(self, name).close()
        self.label = 'replacement'
        for name, module in hosts:
            config, token, port = self.host_specs[module]
            setattr(self, name, self._owner(module, config, token, port=port))

    def _command(self, args, *, timeout=60):
        assert args[0] == '-m'
        result = subprocess.run([str(self.python_for(args[1])), '-I', *args], env=self.env, cwd=self.root,
            capture_output=True, text=True, encoding='utf-8', timeout=timeout, check=False,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        with (self.root / 'workers.log').open('a', encoding='utf-8') as log:
            log.write(result.stdout + result.stderr)
        assert result.returncode == 0, 'Current owner process failed; inspect fixture workers.log'
        return result.stdout

    def _start(self, variant, *, independent=False):
        graph, root = self.graph, self.root
        graph.env.principal = replace(graph.env.principal, actor_id='runtime-worker')
        self.scope = graph.env.principal.scope.model_dump(mode='json')
        state = owned_state()
        planning_owner(state)
        host, port = state['endpoint'].split(':')
        def url(role):
            return URL.create('postgresql+psycopg', username=role, password=state['password'], host=host,
                port=int(port), database=state['database']).render_as_string(hide_password=False)
        self.tokens = {name: secrets.token_hex(32) for name in ('data', 'planning', 'runtime', 'response')}
        self.env = dict(environment(), CHECKPOINT_DATA_SQL=url('artifact_service'),
            CHECKPOINT_RUNTIME_SQL=url('runtime_service'), AMPHORA_PLANNING_DATABASE_URL=url('planning_service'),
            AMPHORA_PLANNING_MIGRATION_URL=url('planning_migrator'),
            **{'CHECKPOINT_' + key.upper() + '_TOKEN': value for key, value in self.tokens.items()})
        self._command(['-m', 'amphora_agent_planning.persistence.migrate'])
        self.env.pop('AMPHORA_PLANNING_MIGRATION_URL')
        port_hold = socket.socket()
        self.resources.callback(port_hold.close)
        port_hold.bind(('127.0.0.1', 0))
        runtime_port = port_hold.getsockname()[1]
        admitted_profiles = profiles(root)
        storage = root / 'bytes'
        storage.mkdir()
        data_config = write(root / 'data.json', {'database_url_env': 'CHECKPOINT_DATA_SQL', 'storage_root': str(storage),
            'profiles': admitted_profiles, 'limits': {'max_bytes': 1048576, 'scope_bytes': 16777216},
            'runtime': {'owner': 'fixture', 'endpoint': f'http://127.0.0.1:{runtime_port}/v1/completion-intents/outcome',
                        'token_env': 'CHECKPOINT_RESPONSE_TOKEN'},
            'principals': [{'token_env': 'CHECKPOINT_DATA_TOKEN', 'actor_id': 'fixture', 'scope': self.scope,
                            'actions': ['upload', 'finalize', 'read', 'retention']}]})
        self.data = self._owner('amphora_data_artifacts', data_config, self.tokens['data'])
        compiled, recipe, policy, definition = materials(self.data, self.scope, root, admitted_profiles, independent=independent)
        self.compiled, self.recipe, self.policy = compiled, recipe, policy
        self.env['AMPHORA_PLANNING_SUPERVISION_CREDENTIALS'] = json.dumps([{'token': self.tokens['planning'],
            'actor_id': 'fixture', 'scope': self.scope, 'actions': ['record_requests', 'read_attempts']}])
        self.planning = self._owner('amphora_agent_planning.supervision_api', None, self.tokens['planning'])
        data_peer = {'endpoint': self.data.endpoint, 'token_env': 'CHECKPOINT_DATA_TOKEN'}
        raw = {'database_url_env': 'CHECKPOINT_RUNTIME_SQL', 'principals': [
            {'token_env': 'CHECKPOINT_RUNTIME_TOKEN', 'actor_id': 'runtime-worker', 'scope': self.scope,
             'actions': ['admit', 'maintain', 'read', 'deliver']},
            {'token_env': 'CHECKPOINT_RESPONSE_TOKEN', 'actor_id': 'fixture', 'scope': self.scope,
             'actions': ['read', 'supervise_respond', 'outcome']}], 'fixtures': [], 'graphs': [definition],
            'artifacts': {'runtime_owner': 'fixture', 'reserve_endpoint': self.data.endpoint + '/v1/reservations',
                          'token_env': 'CHECKPOINT_DATA_TOKEN'},
            'bindings': data_peer, 'projections': data_peer,
            'supervision': {'capture_data': data_peer},
            'supervision_admission': {'policies': ['policy.json'], 'recipes': ['recipe.json']}}
        self.runtime_config = write(root / 'runtime.json', raw)
        port_hold.close()
        self.runtime = self._owner('amphora_campaign_runtime', self.runtime_config, self.tokens['runtime'], port=runtime_port)
        self.runtime_worker = write(root / 'runtime-worker.json', {'database_url_env': 'CHECKPOINT_RUNTIME_SQL',
            'actor_id': 'runtime-worker', 'scope': self.scope, 'data': dict(data_peer, actor_id='fixture'),
            'planning': {'endpoint': self.planning.endpoint, 'token_env': 'CHECKPOINT_PLANNING_TOKEN', 'actor_id': 'fixture'}})
        self.planning_worker = write(root / 'planning-worker.json', {'database_url_env': 'AMPHORA_PLANNING_DATABASE_URL',
            'actor_id': 'fixture', 'scope': self.scope, 'publisher_id': 'data-owner', 'data': data_peer,
            'runtime': {'endpoint': self.runtime.endpoint, 'token_env': 'CHECKPOINT_RESPONSE_TOKEN'},
            'templates': [{'reference': recipe.document().budget_policy.model_dump(mode='json'), 'path': 'template.json'}],
            'provider': variant, 'timeout_seconds': 30})
        self.admission = parse_supervised_admission(json.dumps({'encoding': 'amphora-command-v2', 'identity': {
            'scope': self.scope, 'actor_id': 'runtime-worker', 'command_family': 'graph.admit_supervised',
            'command_id': 'original-campaign'}, 'payload': {'admission': {'plan_sha256': compiled.sha256,
                'inputs': [], 'budget': {'limit': 2}}, 'policy_sha256': policy.sha256}}))
        receipt = self.runtime.call('POST', '/v1/graph-runs/supervised', self.admission.canonical_bytes)
        assert receipt['outcome']['status'] == 'accepted'
        self.run = receipt['outcome']['committed']['object_id']

    def round(self):
        for module, config in [('amphora_campaign_runtime.supervision_loop', self.runtime_worker),
                               ('amphora_agent_planning.supervision_scheduling', self.planning_worker)]:
            result = self._command(['-m', module, 'run', '--config', str(config), '--seconds', '0.2', '--interval', '0.05'])
            self.records.append({'owner': module, 'stages': json.loads(result)})
        return self.graph_round()

    def graph_round(self):
        self._command(['-m', 'amphora_campaign_runtime', 'coordinate', '--config', str(self.runtime_config),
            '--actor', 'runtime-worker', '--tenant', self.scope['tenant_id'], '--project', self.scope['project_id'],
            '--time-budget', '0.2', '--poll-interval', '0.05'])
        delivered = self._command(['-m', 'amphora_campaign_runtime', 'deliver', '--config', str(self.runtime_config),
            '--actor', 'runtime-worker', '--tenant', self.scope['tenant_id'], '--project', self.scope['project_id'],
            '--time-budget', '1', '--limit', '100'])
        self.records.append({'owner': 'runtime_retention_delivery', 'result': json.loads(delivered)})
        return self.runtime.call('GET', '/v3/graph-runs/' + self.run)

    def close(self):
        self.resources.close()
