"""Five actual peer owners to durable Planning packet, rights and future corrections."""

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
from campaign_packet_fixture import cases, sources
from planning_knowledge_fixture import ROOT, rescope
from postgres_fixture import owned_state
from verify_planning_campaign_context import graph


def verify(args):
    assert os.environ.get('AMPHORA_TEST_POSTGRES') == os.environ.get('AMPHORA_TEST_QDRANT') == '1'
    output = args.output.absolute()
    output.mkdir(parents=True, exist_ok=False)
    installation = args.planning_installation.absolute()
    proof = json.loads((installation / 'manifest.json').read_bytes())
    assert proof['status'] == 'passed' and proof['planning'] == '0.49.0' and proof['installations'] == 2
    pythons = {name: getattr(args, name + '_python').absolute() for name in ('registry', 'runtime', 'data', 'knowledge', 'research')}
    versions = {'registry': ('amphora-capability-registry', '0.1.0'), 'runtime': ('amphora-campaign-runtime', '0.20.2'),
        'data': ('amphora-data-artifacts', '0.29.0'), 'knowledge': ('amphora-knowledge', '0.18.0'), 'research': ('amphora-research', '0.34.0')}
    version_script = configuration.write(output / 'expected-versions.json', versions)
    check = output / 'check_version.py'
    check.write_text('import json,sys\nfrom importlib.metadata import version\nv=json.load(open(sys.argv[1]))[sys.argv[2]]\n'
        'assert version(v[0])==v[1]\nprint(json.dumps({"package":v[0],"version":v[1]}))\n', encoding='utf-8')
    env = environment()
    for name, python in pythons.items():
        run(python, check, [version_script, name], env, output)
    state, backend = owned_state(), qdrant_fixture.owned_state()
    host, port = state['endpoint'].split(':')
    for key, role in (('CTX_REGISTRY_DB', 'registry_service'), ('CTX_RUNTIME_DB', 'runtime_service'),
                      ('CTX_DATA_DB', 'artifact_service'), ('PLANNING_KNOWLEDGE_DATABASE', 'knowledge_service'),
                      ('CAMPAIGN_RESEARCH_DB', 'research_service'), ('CTX_PLANNING_DB', 'planning_service')):
        env[key] = URL.create('postgresql+psycopg', username=role, password=state['password'], host=host,
            port=int(port), database=state['database']).render_as_string(hide_password=False)
    env.update(CTX_TOKEN=secrets.token_hex(32), CTX_DENIED=secrets.token_hex(32), CTX_FOREIGN=secrets.token_hex(32), CTX_QDRANT=backend['api_key'])
    scope = {'tenant_id': 'campaign-packet', 'project_id': uuid.uuid4().hex}
    knowledge_fixture = json.loads((ROOT / 'services/knowledge/tests/fixtures/initial.json').read_bytes())
    rescope(knowledge_fixture, scope)
    knowledge_path = configuration.write(output / 'knowledge-input.json', knowledge_fixture)
    knowledge_seed = ROOT / 'dev/planning_knowledge_seed.py'
    first = run(pythons['knowledge'], knowledge_seed, ['prepare', knowledge_path], env, output)
    research_fixture = {'views': json.loads((ROOT / 'contracts/research_views/tests/fixtures/views.json').read_bytes()),
                        'records': json.loads((ROOT / 'services/agent_planning/tests/campaign_context/fixtures/records.json').read_bytes())}
    rescope(research_fixture, scope)
    research_path = configuration.write(output / 'research-input.json', research_fixture)
    research_seed = ROOT / 'dev/planning_campaign_research_seed.py'
    research = run(pythons['research'], research_seed, ['prepare', research_path], env, output)
    configs = {'registry': configuration.registry(ROOT, output, scope)}
    configs['runtime'], lock, descriptor = configuration.runtime(ROOT, output, scope)
    configs['data'], profile = configuration.data(ROOT, output, scope, backend)
    config = json.loads(configs['data'].read_bytes())
    config['profiles'].append(sources.text_profile())
    configuration.write(configs['data'], config)
    configs['knowledge'] = configuration.knowledge(output, scope, first)
    configs['research'] = configuration.write(output / 'research.json', cases.research_config(scope, research))
    modules = {'registry': 'amphora_capability_registry', 'runtime': 'amphora_campaign_runtime', 'data': 'amphora_data_artifacts',
               'knowledge': 'amphora_knowledge', 'research': 'amphora_research'}
    owners, processes, results = {}, {}, {}

    def start(name):
        owners[name] = Owner(pythons[name], modules[name], configs[name], env, env['CTX_TOKEN'], output)
        processes.setdefault(name, []).append(owners[name].process.pid)

    def probe(label, case, *, replacement=False, research_denied=False):
        path = configuration.write(output / (label + '.json'), case)
        python = installation / ('replacement' if replacement else 'initial') / 'Scripts/python.exe'
        worker_env = dict(environment(), CTX_PLANNING_DB=env['CTX_PLANNING_DB'], CTX_READ_TOKEN=env['CTX_TOKEN'],
            CTX_ENDPOINTS=json.dumps({name: owner.endpoint for name, owner in owners.items()}))
        if research_denied:
            worker_env['CTX_RESEARCH_TOKEN'] = env['CTX_DENIED']
        results[label] = run(python, ROOT / 'services/agent_planning/tests/acceptance/campaign_packet_probe.py', [path], worker_env, output)
        return results[label]

    def same(left, right):
        assert {key: value for key, value in left.items() if key != 'pid'} == {key: value for key, value in right.items() if key != 'pid'}

    try:
        for name in modules:
            start(name)
        registered = owners['registry'].call('POST', '/v1/registry/register', data.command(scope, 'registry.register', 'register',
            {'scope': scope, 'descriptor': descriptor, 'expected_lock': lock}))
        assert registered['reason_code'] == 'registered'
        prepared = data.prepare(owners['data'], scope, profile)
        roots = sources.roots(owners['data'], scope)
        universe = owners['runtime'].call('GET', '/v1/definition-universe')
        case = cases.research({'scope': scope, 'request': cases.original(ROOT, scope, roots, prepared), 'lock': lock,
            'universe': universe, 'query': prepared['query'], 'result_sha256': prepared['result']['sha256'], 'graph': graph(first)}, research)
        original = probe('original', case)
        assert original['preparation_failure'] is None and not original['artifact_failures'] and not original['missing_required']
        assert sorted(original['root_hashes']) == sorted(ref['sha256'] for ref in roots.values())
        assert original['registry_count'] == 1 and original['runtime_schemas'] == len(universe['schemas']) and not original['runtime_failures']
        assert original['graph_failure'] is None and not original['graph_retracted'] and original['retrieval_failure'] is None
        assert original['research_records'] == 3 and original['research_gaps'] == ['pending'] and original['assessment_dispositions'] == ['unknown']
        assert original['view_failures'] == [None, None, None] and original['packet_bytes'] == original['input_tokens'] <= 200000
        assert original['output_reserve'] == 1024 and original['omissions'] == 0 and original['consumed'] > 0
        assert set(original['included_lanes']) == {'artifact', 'registry_scan', 'registry_inventory', 'registry_exact', 'runtime',
            'runtime_schema', 'graph', 'research', 'research_view', 'retrieval'}
        partial_case = copy.deepcopy(case)
        partial_case['request']['reference']['engagement_id'] = 'partial'
        partial_case['request']['context']['entries'].append({'artifact': dict(prepared['artifact'], artifact_id='absent'), 'role': 'source', 'required': False})
        partial_case['graph']['base']['snapshot']['sha256'] = 'f' * 64
        partial_case = cases.research(partial_case, research)
        partial = probe('partial', partial_case)
        assert partial['preparation_failure'] is None and partial['artifact_failures'] == ['source_reference_unavailable']
        assert partial['graph_failure'] == 'knowledge_reference_unavailable' and partial['research_records'] == 3
        denied_case = copy.deepcopy(case)
        denied_case['request']['reference']['engagement_id'] = 'research-denied'
        denied = probe('research-denied', cases.research(denied_case, research), research_denied=True)
        assert denied['preparation_failure'] is None and denied['research_records'] == 0 and denied['research_gaps']
        assert denied['view_failures'] == ['research_access_denied'] * 3 and denied['registry_count'] == 1
        second = run(pythons['knowledge'], knowledge_seed, ['advance', knowledge_path], env, output)
        revised = run(pythons['research'], research_seed, ['advance', research_path], env, output)
        same(original, probe('original-after-correction', case))
        future_case = copy.deepcopy(case)
        future_case['request']['reference']['engagement_id'] = 'future'
        future_case['graph'] = graph(second)
        future = probe('future', cases.research(future_case, research, future=revised))
        assert future['preparation_failure'] is None and future['graph_retracted'] and future['research_records'] == 1
        assert future['properties_value'] == {'kind': 'missing', 'reason': 'report_corrected'} and future['packet_sha256'] != original['packet_sha256']
        for name in modules:
            owners[name].close()
            start(name)
        same(original, probe('owners-restarted', case, replacement=True))
        rights = prepared['rights']
        readonly = dict(rights, reference=dict(rights['reference'], revision=2), supersedes=rights['reference'], allowed_uses=['read'])
        owners['data'].call('POST', '/v1/acquisition/rights', readonly)
        inspect_case = dict(case, mode='inspect')
        blocked = probe('processing-denied', inspect_case)
        assert blocked['preparation_failure'] == 'required_artifact_unavailable' and blocked['stored'] == original['stored']
        assert blocked['missing_required'] == [prepared['artifact']['artifact_id']]
        for owner in owners.values():
            owner.close()
        history = probe('historical-offline', dict(case, mode='history'), replacement=True)
        assert history['stored'] == original['stored']
        for name in modules:
            start(name)
        same(blocked, probe('denial-after-restart', inspect_case, replacement=True))
        owners['data'].call('POST', '/v1/acquisition/rights', dict(rights, reference=dict(rights['reference'], revision=3), supersedes=readonly['reference']))
        same(original, probe('processing-restored', case, replacement=True))
    finally:
        for owner in owners.values():
            owner.close()
    assert len({result['pid'] for result in results.values()}) == len(results)
    manifest = {'status': 'passed', 'verified_at': datetime.now(ZoneInfo('America/Chicago')).strftime('%Y-%m-%d %H:%M:%S'),
        'planning': '0.49.0', 'migration': 'planning0012', 'scope': scope, 'peer_versions': versions,
        'owner_processes': processes, 'seed_processes': [first['pid'], second['pid'], research['pid'], revised['pid']], 'results': results,
        'limits': ['Actual public peer reads and Data/Registry setup; isolated synthetic Research/Knowledge fixture seeding',
            'Exact required roots, fixture tokenizer and owned journal; no live model, scientific validity or Runtime activation',
            'Retained PostgreSQL/Qdrant; no migrations/reset/history rewrite; historical replay is not fresh processing permission',
            'Two Planning installations of the same implementation, not a rewritten implementation']}
    configuration.write(output / 'manifest.json', manifest)
    print(json.dumps({'status': 'passed', 'planning_workers': len(results), 'peer_hosts': sum(map(len, processes.values()))}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--planning-installation', type=Path, required=True)
    for name in ('registry', 'runtime', 'data', 'knowledge', 'research'):
        parser.add_argument('--' + name + '-python', type=Path, required=True)
    verify(parser.parse_args())
