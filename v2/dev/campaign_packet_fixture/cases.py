"""Original request and exact Research selections for one synthetic campaign."""

import copy
import hashlib
import json

from amphora_agent_planning.campaign_packet_profiles import fixture_tokenizer_reference
from amphora_agent_planning.context import RequestSnapshot
from amphora_contracts_core import Scope

from planning_knowledge_fixture import rescope


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()


def original(root, scope, artifacts, data):
    value = json.loads((root / 'services/agent_planning/tests/campaign_context/fixtures/request.json').read_bytes())
    rescope(value, scope)
    context = value['context']
    for name in ('objective', 'prompt', 'policy'):
        context[name] = artifacts[name]
    context['model']['configuration'] = artifacts['configuration']
    context['model']['tokenizer'] = fixture_tokenizer_reference().model_dump(mode='json')
    context['model']['context_window_tokens'] = 201024
    context['limits'].update(max_input_tokens=200000, max_output_tokens=1024, total_tokens=201024)
    context['entries'] = [{'artifact': data['artifact'], 'role': 'source', 'required': True}]
    context['omissions'] = []
    return value


def research(case, prepared, *, future=None):
    value = copy.deepcopy(case)
    request = value['request']
    scope = request['reference']['scope']
    bound = RequestSnapshot.from_bytes(canonical(request), actor_id='fixture', scope=Scope.model_validate_json(json.dumps(scope)))
    question = prepared['question'] if future is None else future['question']
    value['selection'] = {'schema_version': '1', 'engagement': request['reference'], 'request_sha256': bound.sha256,
        'questions': [question['reference']], 'needs': [] if future else [prepared['need']['reference']],
        'assessments': [] if future else [{'request': prepared['completed']['request'],
            'status_sha256': hashlib.sha256(canonical(prepared['completed'])).hexdigest()},
            {'request': prepared['pending'], 'status_sha256': '0' * 64}]}
    observation = prepared['observation'] if future is None else future['observation']['reference']
    value['queries'] = {'specimens': {'wire_version': '1', 'experiment': prepared['experiment'], 'limit': 1},
        'properties': {'wire_version': '1', 'experiment': prepared['experiment'], 'observations': [observation, prepared['series']], 'limit': 1},
        'observation_series': {'wire_version': '1', 'observation': prepared['series'], 'limit': 1}}
    return value


def research_config(scope, prepared):
    peer = {'endpoint': 'http://127.0.0.1:1', 'token_env': 'CTX_TOKEN'}
    return {'database_url_env': 'CAMPAIGN_RESEARCH_DB', 'principals': [
        {'token_env': 'CTX_TOKEN', 'actor_id': 'fixture', 'scope': scope,
         'actions': ['read_declarations', 'read_assessment', 'read_scientific_record']},
        {'token_env': 'CTX_DENIED', 'actor_id': 'fixture', 'scope': scope, 'actions': ['resolve_identity']}],
        'assessment': {'profiles': [prepared['profile']], 'data': peer,
            'publication': {'actor_id': 'publisher', 'issuer_id': 'fixture', 'token_env': 'CTX_TOKEN'}},
        'science': {'lab_profiles': [], 'eligibility_profiles': [], 'synthesis_profiles': [], 'data': peer,
            'publication': {'actor_id': 'publisher', 'token_env': 'CTX_TOKEN'}, 'consumer_publishers': []}}
