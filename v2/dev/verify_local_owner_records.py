"""Public Data/Research/Knowledge synthetic records on the retained local installation."""

import argparse
import copy
import hashlib
import json
import os
import uuid
from datetime import datetime
from pathlib import Path

from amphora_deployment.credentials import CredentialVault
from amphora_deployment.lifecycle.routes import Routes
from amphora_deployment.persistence.state import LocalState
from local_numeric_configuration import write
from local_records_controller import RecordsController


def configure(output, source_manifest, scope, routes, fixture):
    source = json.loads(source_manifest.read_bytes())
    owners = {name: dict(source['owners'][name]) for name in ('artifact', 'research', 'knowledge')}

    def principal(reference, actor, actions):
        return {'token_env': 'AMPHORA_' + reference, 'actor_id': actor, 'scope': scope, 'actions': actions}

    profile = {'media_type': 'application/octet-stream', 'schema_id': 'demo.synthetic-document',
               'version': '1', 'sha256': hashlib.sha256(b'{"type":"string","contentEncoding":"base64"}').hexdigest()}
    configs = {
        'artifact': {'database_url_env': 'AMPHORA_ARTIFACT_DATABASE_URL',
            'storage_root': json.loads(Path(owners['artifact']['configuration']).read_bytes())['storage_root'],
            'acquisition': True, 'profiles': [profile], 'principals': [
                principal('ARTIFACT_OPERATOR_TOKEN', 'operator', ['read', 'upload', 'finalize', 'acquire', 'source_history', 'manage_source_rights']),
                principal('KNOWLEDGE_DATA_TOKEN', 'knowledge', ['read', 'source_history'])]},
        'research': {'database_url_env': 'AMPHORA_RESEARCH_DATABASE_URL', 'declarations': True, 'principals': [
            principal('RESEARCH_OPERATOR_TOKEN', 'operator', ['declare_question', 'declare_evidence_need', 'read_declarations']),
            principal('KNOWLEDGE_RESEARCH_TOKEN', 'knowledge', ['read_declarations'])]},
        'knowledge': {'database_url_env': 'AMPHORA_KNOWLEDGE_DATABASE_URL', 'principals': [
            principal('KNOWLEDGE_OPERATOR_TOKEN', 'operator', ['read_graph', 'propose_graph', 'rebuild_graph'])],
            'vocabulary': fixture['vocabulary'],
            'policy': {'policy_id': 'synthetic-structural', 'version': '1', 'authority': 'structural_only',
                       'max_entities': 4096, 'max_assertions': 8192, 'max_aliases': 4096, 'max_retractions': 8192},
            'data': {'endpoint': routes.endpoint('artifact'), 'token_env': 'AMPHORA_KNOWLEDGE_DATA_TOKEN'},
            'research': {'endpoint': routes.endpoint('research'), 'token_env': 'AMPHORA_KNOWLEDGE_RESEARCH_TOKEN'}}}
    references = {'artifact': ['ARTIFACT_OPERATOR_TOKEN', 'KNOWLEDGE_DATA_TOKEN'],
                  'research': ['RESEARCH_OPERATOR_TOKEN', 'KNOWLEDGE_RESEARCH_TOKEN'],
                  'knowledge': ['KNOWLEDGE_OPERATOR_TOKEN', 'KNOWLEDGE_DATA_TOKEN', 'KNOWLEDGE_RESEARCH_TOKEN']}
    for owner, configuration in configs.items():
        owners[owner]['configuration'] = str(write(output / (owner + '.json'), configuration))
        owners[owner]['secret_references'] = references[owner]
    write(output / 'owners.json', {'profile': 'local-supervisor-v1', 'owners': owners})
    return {key: value for key, value in profile.items() if key != 'media_type'}


class Scenario:
    def __init__(self, controller, tokens, scope, output):
        self.controller, self.tokens, self.scope, self.output = controller, tokens, scope, output

    def call(self, owner, path, body=None, *, method=None):
        code, record = self.controller.request(self.controller.routes.endpoint(owner), path,
            token=self.tokens[owner.upper() + '_OPERATOR_TOKEN'], body=body, method=method)
        if code != 200:
            write(self.output / 'last-api-failure.json', {'owner': owner, 'path': path, 'status': code, 'response': record})
        assert code == 200, 'Owner record API failed: ' + owner + path + ' ' + str(code)
        return record

    def publish(self, content, schema, media_type='application/json'):
        descriptor = {'sha256': hashlib.sha256(content).hexdigest(), 'size_bytes': len(content),
                      'media_type': media_type, 'schema_ref': schema}

        def command(family, payload):
            return {'identity': {'scope': self.scope, 'actor_id': 'operator', 'command_id': uuid.uuid4().hex,
                                 'command_family': family}, 'payload': payload}

        request = command('artifacts.begin_upload', {'content': descriptor})
        write(self.output / ('upload-' + request['identity']['command_id'] + '.json'), request)
        upload = self.call('artifact', '/v1/uploads', request)
        self.call('artifact', '/v1/uploads/' + upload['upload_id'] + '/content', content, method='PUT')
        request = command('artifacts.finalize', {'upload_id': upload['upload_id'], 'content': descriptor})
        write(self.output / ('finalize-' + request['identity']['command_id'] + '.json'), request)
        return self.call('artifact', '/v1/artifacts/finalize', request)['artifact']

    def create(self, fixture, schema):
        raw = b'Synthetic engineering hypothesis: bounded numeric search may improve a declared objective. No scientific validation is claimed.'
        artifact = self.publish(raw, schema, 'application/octet-stream')
        rights = {'wire_version': '1', 'reference': {'scope': self.scope, 'rights_id': 'synthetic-demo', 'revision': 1},
                  'supersedes': None, 'status': 'granted', 'allowed_uses': ['read', 'process'],
                  'expires_at': None, 'retention': 'retain_audit_payload'}
        self.call('artifact', '/v1/acquisition/rights', rights)
        source = {'wire_version': '1', 'reference': {'scope': self.scope, 'source_id': 'synthetic-objective',
                  'revision_id': 'r1', 'raw': artifact}, 'delivery': {'issuer_id': 'internal-demo', 'delivery_id': 'first'},
                  'method': {'connector_id': 'authored-synthetic', 'connector_version': '1',
                             'configuration_sha256': hashlib.sha256(b'{}').hexdigest(), 'format': 'utf8_document'},
                  'rights': rights['reference'], 'supersedes': None, 'completeness': 'complete'}
        prepared = self.call('artifact', '/v1/acquisition/prepare', source)
        converted = self.publish(prepared['content_json_utf8'].encode(), prepared['schema_ref'])
        trace = self.call('artifact', '/v1/acquisition/retain', {'wire_version': '1', 'source': source,
            'trace_id': 'synthetic-document-conversion', 'output': converted})
        proposal = copy.deepcopy(fixture['proposal'])

        def patch(value):
            if isinstance(value, dict):
                if 'tenant_id' in value and 'project_id' in value:
                    value.update(self.scope)
                elif 'artifact_id' in value:
                    value.clear()
                    value.update(copy.deepcopy(artifact))
                elif 'trace_id' in value:
                    value.clear()
                    value.update(copy.deepcopy(trace))
                elif 'source_id' in value and 'revision_id' in value:
                    value.clear()
                    value.update(copy.deepcopy(source['reference']))
                if value.get('unit') == 'byte':
                    value.update(start=0, end=len(raw), sha256=hashlib.sha256(raw).hexdigest())
                for child in value.values():
                    patch(child)
            elif isinstance(value, list):
                for child in value:
                    patch(child)

        patch(proposal)
        profile = self.call('knowledge', '/v1/graph-profiles/read', proposal['graph'])
        proposal.update(vocabulary=profile['vocabulary_reference'], policy=profile['policy'])
        claim = proposal['operations'][2]['assertion']
        proposal['operations'][0]['entity']['label'] = 'Bounded numeric search'
        proposal['operations'][1]['entity']['label'] = 'Declared objective improvement'
        claim.update(predicate='hypothesized_to', statement=raw.decode())
        link = claim['research_links'][0]
        link['validation_method'] = schema
        question = {'wire_version': '1', 'reference': link['question'],
                    'objective': 'Explore bounded synthetic numeric optimization; no scientific efficacy claim.',
                    'applicability': artifact, 'criteria': [{'criterion_id': 'declared',
                    'description': 'Record repeatable synthetic objective observations under the exact policy.'}], 'supersedes': None}
        need = {'wire_version': '1', 'reference': link['need'], 'question': question['reference'],
                'criterion_ids': ['declared'], 'method': schema, 'required_context': artifact, 'supersedes': None}
        for path, record in [('questions', question), ('evidence-needs', need)]:
            write(self.output / (path + '.json'), record)
            self.call('research', '/v1/' + path, record)
            assert self.call('research', '/v1/' + path + '/read', record['reference']) == record
        write(self.output / 'proposal.json', proposal)
        accepted = self.call('knowledge', '/v1/graph-proposals', proposal)
        write(self.output / 'decision.json', accepted)
        assert accepted['decision']['outcome'] == 'accepted', 'Structural proposal was not accepted'
        head = accepted['decision']['head']
        snapshot = self.call('knowledge', '/v1/graph-snapshots/read', head['snapshot'])
        assert len(snapshot['content']['entities']) == 2 and len(snapshot['content']['assertions']) == 1
        assert snapshot['content']['assertions'][0]['posture'] == 'hypothesis'
        assert snapshot['content']['assertions'][0]['research_links'][0]['need'] == need['reference']
        rebuild_request = {'wire_version': '1', 'graph': proposal['graph'], 'rebuild_id': 'replay-authored-log'}
        rebuilt = self.call('knowledge', '/v1/graph-rebuilds', rebuild_request)
        assert rebuilt['result']['outcome'] == 'published' and rebuilt['result']['head'] == head
        assert self.call('knowledge', '/v1/graph-snapshots/read', head['snapshot']) == snapshot
        record = {'artifact': artifact, 'source': source, 'rights': rights, 'converted': converted, 'trace': trace,
                  'question': question, 'need': need, 'proposal': proposal, 'accepted': accepted,
                  'snapshot': snapshot, 'rebuild_request': rebuild_request, 'rebuilt': rebuilt}
        write(self.output / 'records.json', record)
        return record

    def replay(self, record):
        for path, name in [('questions', 'question'), ('evidence-needs', 'need')]:
            self.call('research', '/v1/' + path, record[name])
            assert self.call('research', '/v1/' + path + '/read', record[name]['reference']) == record[name]
        assert self.call('knowledge', '/v1/graph-proposals', record['proposal']) == record['accepted']
        assert self.call('knowledge', '/v1/graph-snapshots/read', record['snapshot']['reference']) == record['snapshot']
        assert self.call('knowledge', '/v1/graph-rebuilds', record['rebuild_request']) == record['rebuilt']
        foreign = copy.deepcopy(record['question']['reference'])
        foreign['scope']['project_id'] = 'foreign-project'
        code, _ = self.controller.request(self.controller.routes.endpoint('research'), '/v1/questions/read',
            token=self.tokens['RESEARCH_OPERATOR_TOKEN'], body=foreign)
        assert code == 403, 'Foreign scope was not denied'
        changed = copy.deepcopy(record['question'])
        changed['objective'] = 'Changed immutable declaration'
        code, _ = self.controller.request(self.controller.routes.endpoint('research'), '/v1/questions',
            token=self.tokens['RESEARCH_OPERATOR_TOKEN'], body=changed)
        assert code == 409, 'Changed immutable declaration was not rejected'
        assert self.call('research', '/v1/questions/read', record['question']['reference']) == record['question']


def verify(output, source_manifest, fixture_path):
    output.mkdir(parents=True, exist_ok=False)
    root = Path(os.environ['LOCALAPPDATA']) / 'Amphora/local-v2/installation'
    original, vault = LocalState.snapshot(root), (root / 'credentials.dpapi').read_bytes()
    routes = Routes.load(root)
    scope = {'tenant_id': 'internal', 'project_id': 'owner-records-' + uuid.uuid4().hex}
    fixture = json.loads(fixture_path.read_bytes())
    schema = configure(output, source_manifest, scope, routes, fixture)
    tokens = CredentialVault(root / 'credentials.dpapi', original['deployment_id']).load().environment(
        ['ARTIFACT_OPERATOR_TOKEN', 'RESEARCH_OPERATOR_TOKEN', 'KNOWLEDGE_OPERATOR_TOKEN'])
    controller = None
    try:
        controller = RecordsController(root, output, routes)
        controller.start()
        scenario = Scenario(controller, tokens, scope, output)
        records = scenario.create(fixture, schema)
        first = controller.drain()
        controller.close()
        controller = RecordsController(root, output, routes)
        controller.start()
        Scenario(controller, tokens, scope, output).replay(records)
        final = controller.drain()
        assert LocalState.snapshot(root) == original and (root / 'credentials.dpapi').read_bytes() == vault
        write(output / 'evidence.json', {'timestamp_local': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'passed', 'scope': scope, 'records': records, 'initial_drain': first, 'final_drain': final,
            'original_installation_unchanged': True, 'provider_calls': 0,
            'limits': ['Public owner APIs only; no migrations or direct SQL fixture seeding',
                       'Authored synthetic hypothesis, not LLM extraction or scientific acceptance',
                       'Actual retained local Data/Research/Knowledge processes; restart retains exact records']})
        print('Public owner records and exact restart replay passed', flush=True)
    finally:
        if controller is not None:
            controller.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('output', 'source-manifest', 'fixture'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    verify(args.output.absolute(), args.source_manifest.absolute(), args.fixture.absolute())
