"""Purpose-specific prepared-state reuse proof against authenticated Research/Data."""
import hashlib
import json
import urllib.error

from amphora_contracts_research import EligibilityInputProfile, synthetic_scientific_report_schema, synthetic_scientific_report_schema_document

from .feedback import derived, digest


def data_profile(directory):
    (directory / 'eligibility-report.json').write_bytes(synthetic_scientific_report_schema_document('eligibility'))
    return {'media_type': 'application/json', **synthetic_scientific_report_schema('eligibility').model_dump(mode='json'),
            'schema_path': 'eligibility-report.json'}


def profiles(records, conditions):
    plan = records['experiment-definition']
    adapter = {'schema_id': 'fixture.prepared-state-report', 'version': '1',
               'sha256': hashlib.sha256(b'amphora.synthetic-prepared-state-report.v1').hexdigest()}
    result = []
    for index, item in enumerate(plan['samples']):
        sample = item['sample']
        context = {'subject': {'candidate': sample['candidate'], 'material_state': sample['material_state'],
            'sample': sample['reference']}, 'domain': 'materials', 'purpose': 'synthetic_prepared_state_use', 'conditions': conditions}
        requirements = [{'criterion_id': 'reported_response', 'kind': 'measurement', 'method': plan['protocol']['method'],
                         'required': True, 'excluded_flags': []}]
        policy = {'wire_version': '1', 'authority': 'synthetic', 'reference': {'schema_id': 'fixture.prepared-state-policy',
            'version': '1', 'sha256': digest({'context': context, 'requirements': requirements})},
            'context': context, 'requirements': requirements}
        profile = {'wire_version': '1', 'kind': 'eligibility', 'profile_id': 'prepared-state-' + str(index + 1),
            'version': '1', 'policy': policy, 'adapter': adapter, 'publishers': ['fixture']}
        result.append(EligibilityInputProfile.model_validate_json(json.dumps(profile)).model_dump(mode='json'))
    return result


def prove(scenario, baseline):
    data, research, scope = scenario.data, scenario.research, scenario.scope
    configured = baseline['eligibility_profiles']
    assert len(configured) == 2
    assert configured[0]['policy']['context']['subject']['candidate'] == configured[1]['policy']['context']['subject']['candidate']
    assert configured[0]['policy']['context']['subject']['material_state'] != configured[1]['policy']['context']['subject']['material_state']
    reports = []
    for index, key in enumerate(('observation-revision', 'second_observation')):
        observation = baseline['specimens'][key]
        assert research.request('/v1/observations/read', observation['reference']) == observation
        schema = baseline['feedback_schemas']['fixture.observation-report']
        raw = derived(data, scope, observation, schema, [observation['source']], {
            'transformation_id': 'fixture.observation_snapshot', 'version': '1', 'sha256': schema['sha256']})
        profile = configured[index]
        context, adapter = profile['policy']['context'], profile['adapter']
        report = {'wire_version': '1', 'authority': 'synthetic', 'issuer': 'fixture', 'adapter': adapter, 'raw_report': raw,
            'claims': [{'criterion_id': 'reported_response', 'context': context,
                'origin': {'source': observation['source'], 'method': observation['binding']['measurement']['method'],
                    'kind': 'measurement', 'authority': 'synthetic', 'observation': observation['reference']},
                'disposition': 'supported', 'flags': observation['quality']['flags']}]}
        inputs = list({item['artifact_id']: item for item in (raw, context['conditions'], observation['source'])}.values())
        reports.append(derived(data, scope, report, synthetic_scientific_report_schema('eligibility').model_dump(mode='json'), inputs,
            {'transformation_id': adapter['schema_id'], 'version': adapter['version'], 'sha256': adapter['sha256']}))
    def request(index, report, identity):
        profile = configured[index]
        return {'wire_version': '1', 'decision_id': identity, 'profile': {'scope': scope, 'kind': 'eligibility',
            'profile_id': profile['profile_id'], 'version': profile['version'], 'sha256': digest(profile)}, 'reports': [report]}
    first_query = request(0, reports[0], 'reuse-original')
    first = research.request('/v1/scientific-assessments', first_query)
    assert first['outcome']['status'] == 'assessed'
    assert first['outcome']['decision']['assessment']['disposition'] == 'eligible'
    assert research.request('/v1/scientific-assessments', first_query) == first
    try:
        research.request('/v1/scientific-assessments', request(1, reports[0], 'reuse-original'))
    except urllib.error.HTTPError as error:
        assert error.code == 409
        conflict = json.load(error)
    else:
        raise AssertionError('Changed profile reused an existing decision identity')
    wrong_query = request(1, reports[0], 'reuse-wrong-state')
    wrong = research.request('/v1/scientific-assessments', wrong_query)
    assessment = wrong['outcome']['decision']['assessment']
    assert assessment['disposition'] == 'unknown'
    assert assessment['reviews'][0]['reasons'] == ['applicability_mismatch']
    assert assessment['criteria'][0]['reason'] == 'missing_eligible_evidence'
    second_query = request(1, reports[1], 'reuse-correct-state')
    second = research.request('/v1/scientific-assessments', second_query)
    accepted = second['outcome']['decision']['assessment']
    assert accepted['disposition'] == 'eligible'
    assert accepted['reviews'][0]['claim']['flags'] == ['temperature_review']
    assert accepted['focus'] == ['reported_response']
    for query, status in ((first_query, first), (wrong_query, wrong), (second_query, second)):
        assert research.request('/v1/scientific-assessments/read', query) == status
        assert research.request('/v1/scientific-decisions/read', status['outcome']['decision']['reference']) == status['outcome']['decision']
    assert first['outcome']['decision']['reference'] != second['outcome']['decision']['reference']
    return {'same_identity_wrong_context': {'http_status': 409, 'response': conflict},
            'original': first, 'wrong_state': wrong, 'correct_state': second, 'reports': reports,
            'authority': 'synthetic_purpose_specific_eligibility', 'cache_implementation_claim': False}
