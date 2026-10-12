"""Publish synthetic roots/criteria with exact existing scientific and graph context."""
import copy
import hashlib
import json
import uuid
from pathlib import Path

from amphora_agent_planning.campaign_decisions import DecisionDeclaration
from amphora_agent_planning.campaign_packet_profiles import fixture_tokenizer_reference, reviewed_instructions
from amphora_contracts_planning import campaign_draft_schema
from verify_local_owner_records import Scenario
from .preparation import write

ROOT = Path(__file__).parents[2]


class OriginScenario(Scenario):
    def publish(self, content, schema, media_type='application/json'):
        descriptor = {'sha256': hashlib.sha256(content).hexdigest(), 'size_bytes': len(content),
                      'media_type': media_type, 'schema_ref': schema}
        def command(family, payload):
            return {'identity': {'scope': self.scope, 'actor_id': 'admin',
                'command_family': family, 'command_id': uuid.uuid4().hex}, 'payload': payload}
        upload = self.call('artifact', '/v1/uploads', command('artifacts.begin_upload', {'content': descriptor}))
        self.call('artifact', '/v1/uploads/' + upload['upload_id'] + '/content', content, method='PUT')
        return self.call('artifact', '/v1/artifacts/finalize', command('artifacts.finalize',
            {'upload_id': upload['upload_id'], 'content': descriptor}))['artifact']


def prepare_case(controller, tokens, output, graph_records):
    initial = json.loads((output / 'origin-prepared.json').read_bytes())
    scope = initial['scope']
    scenario = OriginScenario(controller, tokens, scope, output)
    config = json.loads((output / 'artifact.json').read_bytes())
    profile = next(row for row in config['profiles'] if row['media_type'] == 'text/plain')
    schema = {key: profile[key] for key in ('schema_id', 'version', 'sha256')}
    tag = uuid.uuid4().hex
    rights = {'wire_version': '1', 'reference': {'scope': scope, 'rights_id': 'origin-' + tag, 'revision': 1},
        'supersedes': None, 'status': 'granted', 'allowed_uses': ['read', 'process'], 'expires_at': None,
        'retention': 'retain_audit_payload'}
    scenario.call('artifact', '/v1/acquisition/rights', rights)

    def source(ref, label, format):
        scenario.call('artifact', '/v1/acquisition/prepare', {'wire_version': '1',
            'reference': {'scope': scope, 'source_id': 'origin-' + tag + '-' + label, 'revision_id': 'r1', 'raw': ref},
            'delivery': {'issuer_id': 'origin-fixture', 'delivery_id': tag + '-' + label},
            'method': {'connector_id': 'synthetic-engineering', 'connector_version': '1',
                'configuration_sha256': hashlib.sha256(b'{}').hexdigest(), 'format': format},
            'rights': rights['reference'], 'supersedes': None, 'completeness': 'unknown'})

    def publish(body, label):
        ref = scenario.publish(body, schema, 'text/plain')
        source(ref, label, 'utf8_document')
        return ref

    roots = {name: publish(body, name) for name, body in (
        ('objective', b'Compare the supplied synthetic polymer parameter sets with parallel Hansen solvency and Arrhenius viscosity screens. Preserve missing synthesis and laboratory evidence.'),
        ('policy', b'Internal synthetic software demonstration. No measured science, calibrated accuracy, synthesis feasibility or overall winner is established.'),
        ('configuration', b'Deterministic engineering proposal fixture; no live LLM or paid provider invocation.'),
        ('prompt', reviewed_instructions()))}
    graph = copy.deepcopy(json.loads((output / 'draft-save-command.json').read_bytes())['payload']['definition'])
    refs = {}
    for node in graph['body']['nodes']:
        for binding in node['inputs' if node['kind'] == 'invoke' else 'outputs']:
            ref = binding['source'].get('artifact')
            if ref: refs[ref['artifact_id']] = ref
    for index, ref in enumerate(refs.values()):
        # Retain these JSON bytes as an explicit UTF-8 source document. No lab
        # conversion or inferred molecular interpretation is claimed.
        source(ref, 'input-' + str(index), 'utf8_document')
    records = json.loads(graph_records.read_bytes())
    assert records['scope'] == scope
    snapshot = records['snapshot']
    graph_ref = snapshot['reference']['graph']
    profile = scenario.call('knowledge', '/v1/graph-profiles/read', graph_ref)
    graph_context = {'graph': graph_ref, 'base': records['accepted']['decision']['head'],
        'vocabulary': profile['vocabulary_reference'], 'policy': profile['policy'],
        'entities': [row['reference'] for row in snapshot['content']['entities']],
        'assertions': [row['reference'] for row in snapshot['content']['assertions']]}
    question = copy.deepcopy(json.loads((ROOT / 'services/agent_planning/tests/campaign_context/fixtures/records.json').read_bytes())['question'])
    question.update(reference={'scope': scope, 'question_id': 'polymer-origin-' + tag, 'revision': 1},
        objective='What do the parallel solvency and temperature-adjusted viscosity screens show for the supplied synthetic polymer parameter sets?',
        applicability=roots['policy'], supersedes=None)
    question['criteria'] = [dict(question['criteria'][0], criterion_id='solvency', description='Report Hansen distance and inside/outside the declared compatibility sphere; experimental compatibility remains unknown.'),
        dict(question['criteria'][0], criterion_id='viscosity', description='Report viscosity at the specified target temperature; process suitability and laboratory confirmation remain unknown.')]
    question = scenario.call('research', '/v1/questions', question)
    raw = json.loads((ROOT / 'services/agent_planning/tests/campaign_context/fixtures/request.json').read_bytes())
    raw.update(reference={'scope': scope, 'engagement_id': 'origin-' + tag}, actor_id='compiler-demo',
        purpose='campaign_proposal', runtime_cut=None)
    context = raw['context']
    context.update(scope=scope, objective=roots['objective'], prompt=roots['prompt'], policy=roots['policy'],
        entries=[{'artifact': ref, 'role': 'source', 'required': True} for ref in refs.values()], omissions=[],
        output_schema=campaign_draft_schema().model_dump(mode='json'), allowed_actions=['abstain', 'propose_campaign', 'request_evidence'])
    context['model'].update(provider_id='deterministic', model_id='adversarial-fixture', model_revision='1',
        configuration=roots['configuration'], tokenizer=fixture_tokenizer_reference().model_dump(mode='json'), context_window_tokens=240000)
    context['limits'].update(max_input_tokens=220000, max_output_tokens=20000, total_tokens=240000,
        max_attempts=1, total_accounting_units=2)
    pins = [{'kind': kind, 'identity': roots[key]['artifact_id'], 'revision': '1', 'sha256': roots[key]['sha256']}
            for kind, key in [('source', 'objective'), ('policy', 'policy')]]
    graph['context'] = [*graph['context'], *pins]
    declaration = DecisionDeclaration.from_bytes(json.dumps({'format': 'planning-campaign-decision.v2',
        'engagement': raw['reference'], 'objective': roots['objective'], 'policy': roots['policy'], 'runtime_cut': None,
        'allowed_actions': ['propose_campaign'], 'eligibility_context': 'synthetic-tests',
        'future': {'campaign_id': graph['campaign_id'], 'revision': graph['revision'], 'context': graph['context'],
            'max_nodes': 8, 'max_scopes': 1, 'max_depth': 0, 'max_iterations': 1, 'max_tool_timeout': 60,
            'side_effects': ['pure']}, 'adjustments': []}).encode())
    ref = publish(declaration.canonical, 'decision')
    context['entries'].append({'artifact': ref, 'role': 'constraint', 'required': True})
    raw['decision_scope'] = declaration.sha256
    proposal = json.loads((ROOT / 'services/agent_planning/tests/campaign_output/fixtures/future.json').read_bytes())
    proposal.update(decision_scope=declaration.sha256, rationale='Deterministic engineering proposal: run the supplied solvency and viscosity screens concurrently for each declared parameter set, then retain all outputs and review context. Research criteria and the selected Knowledge hypotheses frame the comparison; synthesis and laboratory validity remain unresolved.')
    proposal['candidate'].update(title='Planning provenance: synthetic polymer screens', definition=graph, expected_evidence=[])
    proposal['unresolved'] = []
    registry = json.loads((output / 'registry.json').read_bytes())
    policy = {'profile': 'amphora-tool-selection-v1', 'scientific_profile': 'synthetic-only-v1', 'scope': scope,
        'resources': registry['resources'], 'permissions': {'allowed_egress_hosts': [], 'effects': ['pure']}}
    case = {'scope': scope, 'request': raw, 'proposal': proposal, 'declaration': json.loads(declaration.canonical),
        'graph': graph_context, 'questions': [question['reference']], 'needs': [],
        'endpoints': {name: controller.routes.endpoint(name) for name in ('artifact', 'registry', 'runtime', 'research', 'knowledge')},
        'eligibility_policy_sha256': hashlib.sha256(json.dumps(policy, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()).hexdigest()}
    return write(output / 'compiler-case.json', case)
