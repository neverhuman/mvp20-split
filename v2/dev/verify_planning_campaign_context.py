"""Actual combined owner client compatibility; no migration or provider call."""

import argparse
import copy
import json
import os
import secrets
import uuid
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from sqlalchemy import URL

import qdrant_fixture
from campaign_context_fixture import configuration, data
from campaign_context_fixture.support import Owner, environment, run
from planning_knowledge_fixture import ROOT, rescope
from postgres_fixture import owned_state


def graph(prepared):
    return {'graph': prepared['profile']['graph'], 'base': prepared['head'],
        'vocabulary': prepared['profile']['vocabulary_reference'], 'policy': prepared['profile']['policy'],
        'entities': [row['reference'] for row in prepared['snapshot']['content']['entities']],
        'assertions': [row['reference'] for row in prepared['snapshot']['content']['assertions']]}


def verify(args):
    assert os.environ.get('AMPHORA_TEST_POSTGRES') == os.environ.get('AMPHORA_TEST_QDRANT') == '1'
    output = args.output.absolute()
    output.mkdir(parents=True, exist_ok=False)
    installation = args.planning_installation.absolute()
    installed = json.loads((installation / 'manifest.json').read_bytes())
    assert installed['status'] == 'passed' and installed['planning'] == '0.39.0'
    interpreters = {name: getattr(args, name + '_python').absolute() for name in ('registry', 'runtime', 'data', 'knowledge')}
    state, backend = owned_state(), qdrant_fixture.owned_state()
    host, port = state['endpoint'].split(':')
    env = environment()
    for name, role in (('REGISTRY', 'registry_service'), ('RUNTIME', 'runtime_service'), ('DATA', 'artifact_service')):
        env['CTX_' + name + '_DB'] = URL.create('postgresql+psycopg', username=role, password=state['password'],
            host=host, port=int(port), database=state['database']).render_as_string(hide_password=False)
    env['PLANNING_KNOWLEDGE_DATABASE'] = URL.create('postgresql+psycopg', username='knowledge_service', password=state['password'],
        host=host, port=int(port), database=state['database']).render_as_string(hide_password=False)
    env.update(CTX_TOKEN=secrets.token_hex(32), CTX_DENIED=secrets.token_hex(32), CTX_FOREIGN=secrets.token_hex(32), CTX_QDRANT=backend['api_key'])
    scope = {'tenant_id': 'campaign-context', 'project_id': uuid.uuid4().hex}
    fixture = json.loads((ROOT / 'services/knowledge/tests/fixtures/initial.json').read_bytes())
    rescope(fixture, scope)
    fixture_path = configuration.write(output / 'knowledge-input.json', fixture)
    seed = ROOT / 'dev/planning_knowledge_seed.py'
    first = run(interpreters['knowledge'], seed, ['prepare', fixture_path], env, output)
    configs = {'registry': configuration.registry(ROOT, output, scope)}
    configs['runtime'], lock, descriptor = configuration.runtime(ROOT, output, scope)
    configs['data'], profile = configuration.data(ROOT, output, scope, backend)
    configs['knowledge'] = configuration.knowledge(output, scope, first)
    modules = {'registry': 'amphora_capability_registry', 'runtime': 'amphora_campaign_runtime',
        'data': 'amphora_data_artifacts', 'knowledge': 'amphora_knowledge'}
    owners, pids, results = {}, {}, {}

    def start(name):
        owner = Owner(interpreters[name], modules[name], configs[name], env, env['CTX_TOKEN'], output)
        owners[name] = owner
        pids.setdefault(name, []).append(owner.process.pid)

    probe = ROOT / 'services/agent_planning/tests/acceptance/campaign_context_probe.py'
    python = installation / 'environment/Scripts/python.exe'

    def read(label, case, credential='CTX_TOKEN'):
        path = configuration.write(output / (label + '.json'), case)
        result = run(python, probe, [path], dict(environment(), CTX_READ_TOKEN=env[credential],
            CTX_ENDPOINTS=json.dumps({name: owner.endpoint for name, owner in owners.items()})), output)
        results[label] = result
        return result

    def same(left, right):
        assert {k: v for k, v in left.items() if k != 'pid'} == {k: v for k, v in right.items() if k != 'pid'}

    try:
        for name in modules:
            start(name)
        registered = owners['registry'].call('POST', '/v1/registry/register', data.command(scope, 'registry.register', 'register',
            {'scope': scope, 'descriptor': descriptor, 'expected_lock': lock}))
        assert registered['reason_code'] == 'registered'
        prepared = data.prepare(owners['data'], scope, profile)
        universe = owners['runtime'].call('GET', '/v1/definition-universe')
        request = json.loads((ROOT / 'services/agent_planning/tests/campaign_context/fixtures/request.json').read_bytes())
        rescope(request, scope)
        case = {'scope': scope, 'request': request, 'lock': lock, 'universe': universe,
            'artifacts': [prepared['artifact']], 'query': prepared['query'], 'result_sha256': prepared['result']['sha256'], 'graph': graph(first)}
        original = read('original', case)
        assert original['registry']['failure'] is None and original['registry']['complete'] and original['registry']['count'] == 1
        assert 'exact' in original['registry'] and original['runtime']['universe'] == universe['universe_sha256']
        assert len(original['runtime']['schemas']) == len(universe['schemas']) and not original['runtime']['failures']
        assert original['artifacts']['bodies'] == [prepared['artifact']['sha256']] and not original['artifacts']['failures']
        assert original['retrieval']['record'] == prepared['result'] and original['retrieval']['failure'] is None
        assert original['knowledge']['failure'] is None and original['knowledge']['snapshot'] is not None
        partial_case = copy.deepcopy(case)
        partial_case['artifacts'].append(dict(prepared['artifact'], artifact_id='absent'))
        partial_case['graph']['base']['snapshot']['sha256'] = 'f' * 64
        partial = read('partial', partial_case)
        assert partial['artifacts']['bodies'] == original['artifacts']['bodies']
        assert partial['artifacts']['failures'] == ['source_reference_unavailable']
        assert partial['knowledge']['failure'] == 'knowledge_reference_unavailable'
        assert partial['registry'] == original['registry'] and partial['runtime'] == original['runtime']
        assert partial['retrieval'] == original['retrieval']
        denied = read('denied', case, 'CTX_DENIED')
        assert denied['registry']['failure'] == denied['runtime']['failure'] == denied['retrieval']['failure'] == 'metadata_denied'
        assert denied['artifacts']['failures'] == ['source_access_denied'] and denied['knowledge']['failure'] == 'knowledge_access_denied'
        foreign = read('foreign', case, 'CTX_FOREIGN')
        assert not foreign['artifacts']['bodies'] and foreign['retrieval']['record'] is None and foreign['knowledge']['snapshot'] is None
        assert foreign['registry']['count'] == 0 and 'failure' in foreign['runtime']
        second = run(interpreters['knowledge'], seed, ['advance', fixture_path], env, output)
        same(original, read('original-after-correction', case))
        future_case = copy.deepcopy(case)
        future_case['request']['reference']['engagement_id'] = 'future-campaign'
        future_case['graph'] = graph(second)
        future = read('future-campaign', future_case)
        assert future['knowledge']['snapshot'] != original['knowledge']['snapshot'] and future['knowledge']['retracted']
        assert future['knowledge']['failure'] is None
        for name in modules:
            owners[name].close()
            start(name)
        same(original, read('original-after-owner-restarts', case))
        rights = prepared['rights']
        readonly = dict(rights, reference=dict(rights['reference'], revision=2), supersedes=rights['reference'], allowed_uses=['read'])
        owners['data'].call('POST', '/v1/acquisition/rights', readonly)
        revoked = read('processing-denied', case)
        assert revoked['artifacts']['failures'] == ['source_access_denied'] and not revoked['artifacts']['bodies']
        assert revoked['knowledge'] == original['knowledge'] and revoked['registry'] == original['registry']
        owners['data'].close()
        start('data')
        same(revoked, read('processing-denied-after-restart', case))
        owners['data'].call('POST', '/v1/acquisition/rights', dict(rights, reference=dict(rights['reference'], revision=3), supersedes=readonly['reference']))
        same(original, read('processing-restored', case))
    finally:
        for owner in owners.values():
            owner.close()
    assert len({record['pid'] for record in results.values()}) == len(results)
    manifest = {'status': 'passed', 'verified_at': datetime.now(ZoneInfo('America/Chicago')).strftime('%Y-%m-%d %H:%M:%S'),
        'planning': '0.39.0', 'scope': scope, 'owner_processes': pids, 'knowledge_fixture_processes': [first['pid'], second['pid']],
        'results': results, 'research_evidence_reused': 'docs/Audits/Evidence/BP-07-Campaigns/Research_Owner_Reads.json',
        'limits': ['Synthetic public Data/Registry setup and Knowledge-local reference fixture; no scientific validity claim',
            'Actual retained PostgreSQL/Qdrant, installed service CLIs and Planning-only workers; no migrations or reset',
            'Research public clients/contracts unchanged since separate actual-owner checkpoint',
            'Request root Artifacts remain fixture pins; this gate does not assemble or tokenize a complete provider context']}
    configuration.write(output / 'manifest.json', manifest)
    print(json.dumps({'status': 'passed', 'workers': len(results), 'owners': sum(map(len, pids.values()))}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--planning-installation', type=Path, required=True)
    for name in ('registry', 'runtime', 'data', 'knowledge'):
        parser.add_argument('--' + name + '-python', type=Path, required=True)
    verify(parser.parse_args())
