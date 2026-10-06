"""Fresh owner/tool processes retain old proofs and qualify new actual producers."""
import copy
import json


def replace(e, research, research_config, prepared, reports, requests, accepted, http):
    replacements = e.config['replacements']
    old = e.runtime
    old.close()
    e.runtime = http.Service(replacements['runtime'], old.module, old.config, old.env, old.directory, old.port)
    e.resources.append(e.runtime)
    e.runtime.ready(e.tokens['admin'])
    assert e.compile(replacements['runtime']) == e.plans
    port = research.port
    research.close()
    e.config.update(replacements)
    research = e.research_host(research_config, port)
    for kind in ('numeric', 'polymer', 'sequence', 'digest'):
        descriptor = json.loads(e.cli(kind, 'describe', '--image-sha256', e.images.digest(kind)))
        assert descriptor == e.descriptors[kind]
        e.images.verify(kind, descriptor, {kind: e.config['packages'][kind + '-replacement']})
    for report in reports:
        for name in ('source_producer', 'target_producer', 'evaluation_producer'):
            proof = report[name]
            # Selection comes from the fixture, not assumptions about internal completion fields.
            selected = prepared[report['kind']][name]
            observed = http.decoded(e.runtime.endpoint, '/v1/runs/' + selected['run_id'] + '/completions/' + selected['completion_id'] + '/producer', e.tokens['research'])
            assert observed == proof
    decisions = {}
    for kind, record in prepared.items():
        request = requests[kind]
        assert http.decoded(research.endpoint, '/v1/evaluation-reuse', e.tokens['admin'], request) == accepted[kind]
        assert http.decoded(research.endpoint, '/v1/evaluation-reuse/read', e.tokens['admin'], {'scope': e.scope, 'reuse_id': request['reuse_id']}) == accepted[kind]
        source, _, _, _ = e.run_tool(kind, record['candidates']['source']['representation'])
        target, _, _, _ = e.run_tool(kind, record['candidates']['target']['representation'])
        evaluation, _, artifact, _ = e.run_tool('digest', record['identities']['source'])
        for field in ('sha256', 'size_bytes', 'media_type', 'schema_ref'):
            assert artifact[field] == record['evaluation'][field]
        fresh = copy.deepcopy(request)
        fresh['reuse_id'] += '-replacement'
        fresh['source']['canonicalization'] = source
        fresh['target']['canonicalization'] = target
        fresh['evaluation'] = evaluation
        value = http.decoded(research.endpoint, '/v1/evaluation-reuse', e.tokens['admin'], fresh)
        assert value['status'] == 'permitted' and value['reusable_artifact'] == artifact
        assert http.decoded(research.endpoint, '/v1/evaluation-reuse', e.tokens['admin'], fresh) == value
        decisions[kind] = value['reference']
    return research, {'retained_producer_proofs': 9, 'retained_reuse_decisions': 3,
        'replacement_invocations': 9, 'replacement_decisions': decisions, 'wheel_closures_equal': True,
        'packages': {name: e.config['packages'][name + '-replacement'] for name in replacements}}
