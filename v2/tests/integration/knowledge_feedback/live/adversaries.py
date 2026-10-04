"""LAB-REF03: retained incompatible reports do not establish specimen equivalence."""
import copy

from amphora_contracts_research import synthetic_scientific_report_schema

from .feedback import derived, digest, install_observation


def prove(scenario, records):
    observation = copy.deepcopy(records['specimens']['observation-revision'])
    observation['reference']['observation_id'] = 'observation-incompatible'
    observation['binding']['specimen']['material_state'] = records['specimens']['second_state']['reference']
    observation['binding']['measurement']['method'] = {'schema_id': 'fixture.other-method', 'version': '1', 'sha256': 'f'*64}
    observation['value'] = {'kind': 'numeric', 'quantity': {'value': '12.340', 'unit': 'synthetic-other-unit'}, 'uncertainty': None}
    observation['quality'] = {'controls': 'failed', 'flags': ['specimen_context_review']}
    install_observation(scenario, observation)
    assert scenario.research.request('/v1/observations/read', observation['reference']) == observation
    query = {**records['comparison']['properties']['request'], 'observations': [
        records['specimens']['observation-revision']['reference'], observation['reference']]}
    page = scenario.research.request('/v1/research-explore/properties', query)
    row = page['rows'][1]
    assert row['binding'] == observation['binding'] and row['value'] == observation['value']
    assert row['quality'] == observation['quality']
    assert row['context_link'] == 'declared_expectation'  # Named target is not a consistency verdict.
    profile = records['eligibility_profiles'][0]
    context = copy.deepcopy(profile['policy']['context'])
    context['subject']['material_state'] = observation['binding']['specimen']['material_state']
    schema = records['feedback_schemas']['fixture.observation-report']
    raw = derived(scenario.data, scenario.scope, observation, schema, [observation['source']], {
        'transformation_id': 'fixture.observation_snapshot', 'version': '1', 'sha256': schema['sha256']})
    adapter = profile['adapter']
    report = {'wire_version': '1', 'authority': 'synthetic', 'issuer': 'fixture', 'adapter': adapter, 'raw_report': raw,
        'claims': [{'criterion_id': 'reported_response', 'context': context,
            'origin': {'source': observation['source'], 'method': observation['binding']['measurement']['method'],
                'kind': 'measurement', 'authority': 'synthetic', 'observation': observation['reference']},
            'disposition': 'supported', 'flags': observation['quality']['flags']}]}
    inputs = list({item['artifact_id']: item for item in (raw, context['conditions'], observation['source'])}.values())
    artifact = derived(scenario.data, scenario.scope, report, synthetic_scientific_report_schema('eligibility').model_dump(mode='json'), inputs,
        {'transformation_id': adapter['schema_id'], 'version': adapter['version'], 'sha256': adapter['sha256']})
    request = {'wire_version': '1', 'decision_id': 'incompatible-preparation', 'profile': {'scope': scenario.scope,
        'kind': 'eligibility', 'profile_id': profile['profile_id'], 'version': profile['version'], 'sha256': digest(profile)}, 'reports': [artifact]}
    status = scenario.research.request('/v1/scientific-assessments', request)
    assessment = status['outcome']['decision']['assessment']
    assert assessment['disposition'] == 'unknown'
    assert set(assessment['reviews'][0]['reasons']) >= {'applicability_mismatch', 'method_mismatch'}
    assert assessment['reviews'][0]['claim']['flags'] == ['specimen_context_review']
    for key in ('original', 'correct_state'):
        prior = records['reuse'][key]
        assert scenario.research.request('/v1/scientific-decisions/read', prior['outcome']['decision']['reference']) == prior['outcome']['decision']
    return {'observation': observation, 'properties': page, 'assessment': status,
            'specimen_windows': records['windows']['specimen_pages'], 'report': artifact,
            'authority': 'reported_evidence_only; explicit purpose-specific Research eligibility'}
