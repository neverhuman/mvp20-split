"""Public source-to-accepted-graph scenario; no private service imports."""
import copy
import hashlib
import json
import uuid
from pathlib import Path

from amphora_contracts_knowledge import reasoning_artifact_schema, reasoning_artifact_schema_document

from .process import Owner, owned_setup
from .specimens import install as install_specimens, read_views
from .feedback import data_profiles, research_profiles
from .reuse import data_profile as reuse_data_profile, profiles as reuse_profiles


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()


def publish(data, scope, content, schema, media='application/json'):
    descriptor = dict(sha256=hashlib.sha256(content).hexdigest(), size_bytes=len(content),
                      media_type=media, schema_ref=schema)
    def command(family, payload):
        return {'identity': {'command_family': family, 'command_id': uuid.uuid4().hex,
            'actor_id': 'fixture', 'scope': scope}, 'payload': payload}
    upload = data.request('/v1/uploads', command('artifacts.begin_upload', {'content': descriptor}))
    data.request('/v1/uploads/' + upload['upload_id'] + '/content', content=content, method='PUT')
    return data.request('/v1/artifacts/finalize', command('artifacts.finalize',
        {'upload_id': upload['upload_id'], 'content': descriptor}))['artifact']


class SourceGraphScenario:
    def __init__(self, directory, scope, interpreters, environments, runtime=None, retrieval=None):
        self.directory, self.scope = directory, scope
        self.interpreters, self.environments, self.owners = interpreters, environments, []
        self.runtime = runtime
        self.retrieval = retrieval

    def start(self, owner, config, token):
        path = self.directory / (owner + '.json')
        path.write_text(json.dumps(config), encoding='utf-8')
        process = Owner(self.interpreters[owner], 'amphora_' + owner, path, self.environments[owner], token)
        self.owners.append(process)
        return process

    def close(self):
        for owner in reversed(self.owners):
            owner.close()

    def run(self):
        scope = self.scope
        document = b'Synthetic claims are not scientifically accepted.'
        source_schema = {'schema_id': 'fixture.text', 'version': '1',
            'sha256': hashlib.sha256(b'{"type":"string"}').hexdigest()}
        (self.directory / 'bytes').mkdir()
        (self.directory / 'reasoning.json').write_bytes(reasoning_artifact_schema_document())
        data_config = {'database_url_env': 'OWNER_DATABASE',
            'storage_root': str(self.directory / 'bytes'), 'acquisition': True,
            'principals': [{'token_env': 'OWNER_TOKEN', 'actor_id': 'fixture', 'scope': scope,
                'actions': ['read', 'source_history', 'upload', 'finalize', 'acquire', 'manage_source_rights']},
                {'token_env': 'BROWSER_TOKEN', 'actor_id': 'browser', 'scope': scope, 'actions': ['read', 'source_history']}],
            'profiles': [{'media_type': 'text/plain', **source_schema},
                {'media_type': 'application/json', **reasoning_artifact_schema().model_dump(mode='json'),
                 'schema_path': 'reasoning.json'}]}
        feedback_profiles = data_profiles(self.directory)
        data_config['profiles'].extend(feedback_profiles)
        data_config['profiles'].append(reuse_data_profile(self.directory))
        if self.runtime is not None:
            self.runtime.configure_data(data_config, self.environments['data_artifacts'])
        if self.retrieval is not None:
            data_config.update(representations=True, retrieval=self.retrieval)
            data_config['principals'][0]['actions'].extend(['representation_manage', 'representation_read', 'representation_encode'])
        data = self.start('data_artifacts', data_config, self.environments['data_artifacts']['OWNER_TOKEN'])
        artifact = publish(data, scope, document, source_schema, 'text/plain')
        rights = {'wire_version': '1', 'reference': {'scope': scope, 'rights_id': 'fixture', 'revision': 1},
            'supersedes': None, 'status': 'granted', 'allowed_uses': ['read', 'process'],
            'expires_at': None, 'retention': 'retain_audit_payload'}
        data.request('/v1/acquisition/rights', rights)
        source = {'wire_version': '1', 'reference': {'scope': scope, 'source_id': 'document', 'revision_id': 'r1', 'raw': artifact},
            'delivery': {'issuer_id': 'fixture', 'delivery_id': 'one'},
            'method': {'connector_id': 'fixture', 'connector_version': '1', 'configuration_sha256': 'a'*64, 'format': 'utf8_document'},
            'rights': rights['reference'], 'supersedes': None, 'completeness': 'unknown'}
        prepared = data.request('/v1/acquisition/prepare', source)
        converted = publish(data, scope, prepared['content_json_utf8'].encode(), prepared['schema_ref'])
        trace = data.request('/v1/acquisition/retain', {'wire_version': '1', 'source': source, 'trace_id': 'conversion', 'output': converted})
        span = {'source': source['reference'], 'unit': 'byte', 'start': 0, 'end': len(document), 'sha256': hashlib.sha256(document).hexdigest()}
        fixture = json.loads(Path(__file__).with_name('graph.json').read_text(encoding='utf-8'))
        proposal = fixture['proposal']
        def patch(value):
            if isinstance(value, dict):
                if set(value) == {'tenant_id', 'project_id'}:
                    value.update(scope)
                elif 'artifact_id' in value:
                    value.clear(); value.update(copy.deepcopy(artifact))
                elif 'trace_id' in value:
                    value.clear(); value.update(copy.deepcopy(trace))
                elif value.get('unit') == 'byte':
                    value.clear(); value.update(copy.deepcopy(span))
                for child in value.values():
                    patch(child)
            elif isinstance(value, list):
                for child in value:
                    patch(child)
        patch(proposal)
        specimens = install_specimens(self.directory, scope, artifact, self.interpreters['research'], self.environments['research'])
        claim = proposal['operations'][2]['assertion']
        link = claim['research_links'][0]
        link['validation_method'] = specimens['experiment-definition']['protocol']['method']
        question = {'wire_version': '1', 'reference': link['question'], 'objective': 'Inspect a synthetic hypothesis',
            'applicability': artifact, 'criteria': [{'criterion_id': 'declared', 'description': 'Preserve uncertainty'}], 'supersedes': None}
        need = {'wire_version': '1', 'reference': link['need'], 'question': link['question'], 'criterion_ids': ['declared'],
            'method': specimens['experiment-definition']['protocol']['method'], 'required_context': artifact, 'supersedes': None}
        # Declarations have read-only HTTP routes: fixture installation remains inside Research.
        seed_environment = dict(self.environments['research'], FIXTURE_RECORDS=json.dumps([question, need]))
        owned_setup(self.interpreters['research'], '''
import json,os
from sqlalchemy import create_engine
from amphora_contracts_research import ResearchQuestion,EvidenceNeed
from amphora_research.persistence.ledger import IdentityLedger
engine=create_engine(os.environ['OWNER_DATABASE'])
try:
 ledger=IdentityLedger(engine)
 for model,raw in zip((ResearchQuestion,EvidenceNeed),json.loads(os.environ['FIXTURE_RECORDS'])):
  value=model.model_validate_json(json.dumps(raw)); ledger.publish(value.reference.scope,value)
finally: engine.dispose()
''', seed_environment)
        profiles = research_profiles(question, need, claim, artifact)
        eligibility_profiles = reuse_profiles(specimens, artifact)
        self.environments['research']['DATA_TOKEN'] = self.environments['data_artifacts']['OWNER_TOKEN']
        research = self.start('research', {'database_url_env': 'OWNER_DATABASE', 'principals': [
            {'token_env': 'OWNER_TOKEN', 'actor_id': 'reader', 'scope': scope, 'actions': ['read_declarations', 'assess_eligibility', 'read_scientific_assessment', 'read_scientific_record', 'assess', 'read_assessment', 'publish_assessment', 'read_assessment_publication', 'correct_assessment_receipt', 'select_assessment_receipt']},
            {'token_env': 'BROWSER_TOKEN', 'actor_id': 'browser', 'scope': scope, 'actions': ['read_scientific_record']}],
            'assessment': {'profiles': profiles, 'data': {'endpoint': data.endpoint, 'token_env': 'DATA_TOKEN'},
                'publication': {'actor_id': 'fixture', 'issuer_id': 'research-synthetic', 'token_env': 'DATA_TOKEN'}},
            'science': {'lab_profiles': [], 'eligibility_profiles': eligibility_profiles, 'synthesis_profiles': [],
                'data': {'endpoint': data.endpoint, 'token_env': 'DATA_TOKEN'},
                'publication': {'actor_id': 'fixture', 'token_env': 'DATA_TOKEN'}, 'consumer_publishers': []}},
            self.environments['research']['OWNER_TOKEN'])
        rules = {'wire_version': '1', 'graph': proposal['graph'], 'rule_set_id': 'fixture', 'version': 'v1',
            'authority': 'synthetic_logical_entailment', 'context': artifact,
            'limits': {'depth': 32, 'work': 100000, 'facts': 8192}, 'rules': []}
        policy = {'policy_id': 'synthetic-structural', 'version': '1', 'authority': 'structural_only',
            'max_entities': 4096, 'max_assertions': 8192, 'max_aliases': 4096, 'max_retractions': 8192}
        knowledge = self.start('knowledge', {'database_url_env': 'OWNER_DATABASE', 'principals': [
            {'token_env': 'OWNER_TOKEN', 'actor_id': 'author', 'scope': scope,
             'actions': ['read_graph', 'propose_graph', 'reason_graph', 'publish_reasoning', 'rebuild_graph']},
            {'token_env': 'BROWSER_TOKEN', 'actor_id': 'browser', 'scope': scope, 'actions': ['read_graph']}],
            'vocabulary': fixture['vocabulary'], 'policy': policy, 'reasoning': [rules],
            'publication': {'actor_id': 'fixture', 'issuer_id': 'knowledge-synthetic', 'token_env': 'DATA_TOKEN'},
            'data': {'endpoint': data.endpoint, 'token_env': 'DATA_TOKEN'},
            'research': {'endpoint': research.endpoint, 'token_env': 'RESEARCH_TOKEN'}}, self.environments['knowledge']['OWNER_TOKEN'])
        profile = knowledge.request('/v1/graph-profiles/read', proposal['graph'])
        proposal['vocabulary'], proposal['policy'] = profile['vocabulary_reference'], profile['policy']
        accepted = knowledge.request('/v1/graph-proposals', proposal)
        assert accepted['decision']['outcome'] == 'accepted'
        head = accepted['decision']['head']
        snapshot = knowledge.request('/v1/graph-snapshots/read', head['snapshot'])
        assert snapshot['content']['assertions'][0]['posture'] == 'hypothesis'
        reasoning = knowledge.request('/v1/graph-reasoning', {'wire_version': '1', 'request_id': 'reason-initial',
            'snapshot': head['snapshot'], 'rule_set': {'graph': proposal['graph'], 'rule_set_id': 'fixture', 'version': 'v1',
            'sha256': hashlib.sha256(canonical(rules)).hexdigest()}, 'context': artifact, 'subject': artifact,
            'purpose': 'fixture_support', 'targets': [{key: claim[key] for key in ('subject', 'predicate', 'object', 'polarity')}]})
        assert reasoning['decision']['outcome'] == 'evaluated'
        assert reasoning['decision']['result']['findings'][0]['supporting_assertions'] == [claim['reference']]
        published = knowledge.request('/v1/reasoning-publications', {'wire_version': '1', 'graph': proposal['graph'],
            'publication_id': 'initial', 'reasoning_request_id': 'reason-initial'})
        assert published['outcome']['status'] == 'published'
        assert data.request('/v1/artifacts/' + artifact['artifact_id'] + '/content', binary=True) == document
        assert research.request('/v1/questions/read', question['reference']) == question
        assert research.request('/v1/evidence-needs/read', need['reference']) == need
        self.data, self.research, self.knowledge = data, research, knowledge
        views = read_views(research, specimens)
        graph_views = {'catalog': knowledge.request('/v1/graph-explore/catalog', head['snapshot']),
            'entities': knowledge.request('/v1/graph-explore/entities', {'wire_version': '1', 'revision': head['snapshot'], 'limit': 50})}
        return {'source': source, 'span': span, 'trace': trace, 'question': question, 'need': need,
            'eligibility_profiles': eligibility_profiles,
            'feedback_schemas': {p['schema_id']: {k: p[k] for k in ('schema_id', 'version', 'sha256')} for p in feedback_profiles},
            'specimens': specimens, 'research_views': views, 'knowledge_views': graph_views,
            'proposal': proposal, 'assessment_profiles': profiles, 'head': head, 'assertion': claim['reference'], 'reasoning': reasoning, 'publication': published}
