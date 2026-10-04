"""Map observed owner replies into the immutable declared-fixture manifest."""
import json

from ..protocol.manifest import ScenarioManifest


def observed_manifest(scope, result):
    specimen = result['specimens']
    experiment = specimen['experiment-definition']
    state = specimen['material-state-revision']
    views = []
    for key in ('knowledge_views', 'research_views'):
        catalog = result[key]['catalog']
        views.extend({'owner': catalog['owner'], **view} for view in catalog['views'])
    document = {'format': 'amphora.knowledge-feedback-fixture.v1', 'authority': 'declared_fixture_only',
        'scenario_id': 'actual-baseline', 'scope': scope,
        'question': {'question': result['question']['reference'], 'need': result['need']['reference'], 'method': result['need']['method']},
        'source': {'span': result['span'], 'trace': result['trace']},
        'graph': {'snapshot': result['head']['snapshot'], 'assertion': result['assertion']},
        'specimens': [{'key': 'specimen-one', 'candidate': state['candidate'], 'material': state['reference'],
            'sample': experiment['samples'][0]['sample']['reference'], 'experiment': experiment['reference'],
            'observation': specimen['observation-revision']['reference']}],
        'representation': {'profile': result['representation']['profile'], 'generation': result['representation']['generation']['generation']['reference']},
        'campaign': {'cut': result['runtime']['snapshot']['snapshot']['cut'],
            'receipt': result['publication']['outcome']['derivation']['artifact']}, 'views': views}
    manifest = ScenarioManifest.parse(json.dumps(document).encode())
    assert ScenarioManifest.parse(manifest.canonical_bytes).sha256 == manifest.sha256
    return {'document': json.loads(manifest.canonical_bytes), 'sha256': manifest.sha256}
