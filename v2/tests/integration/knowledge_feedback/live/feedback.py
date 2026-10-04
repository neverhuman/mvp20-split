"""Synthetic iteration through public owner APIs; fixture installation stays owner-local."""
import copy
import hashlib
import json
import uuid

from amphora_contracts_research import (
    EvidenceAssessment, EvidenceAssessmentProfile, ObservationRevision,
    synthetic_evidence_schema, synthetic_evidence_schema_document,
)

from .process import owned_setup


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()


def digest(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def data_profiles(directory):
    profiles = []
    for name, schema_id, model in [('assessment', 'research.evidence-assessment.payload', EvidenceAssessment),
                                   ('observation-report', 'fixture.observation-report', ObservationRevision)]:
        schema = model.model_json_schema(mode='validation')
        schema['$schema'] = 'https://json-schema.org/draft/2020-12/schema'
        body = encoded(schema) + b'\n'
        (directory / (name + '.json')).write_bytes(body)
        profiles.append({'media_type': 'application/json', 'schema_id': schema_id, 'version': '1',
                         'sha256': hashlib.sha256(body).hexdigest(), 'schema_path': name + '.json'})
    (directory / 'evidence.json').write_bytes(synthetic_evidence_schema_document())
    profiles.append({'media_type': 'application/json', **synthetic_evidence_schema().model_dump(mode='json'),
                     'schema_path': 'evidence.json'})
    return profiles


def research_profiles(question, need, claim, context):
    target = {key: claim[key] for key in ('subject', 'predicate', 'object', 'polarity')}
    base = {'wire_version': '1', 'profile_id': 'feedback-assessment', 'authority': 'synthetic',
            'purpose': 'fixture_support', 'question': question, 'subject': context,
            'targets': [{'criterion_id': 'declared', 'target_sha256': digest(target)}],
            'answer_publishers': ['fixture'],
            'requirements': [{'need': need, 'categories': ['observation'], 'issuers': ['fixture']}]}
    return [EvidenceAssessmentProfile.model_validate_json(json.dumps(base | {'version': version})).model_dump(mode='json')
            for version in ('v1', 'v2')]


def derived(data, scope, value, schema, inputs, method):
    content = encoded(value)
    descriptor = {'sha256': hashlib.sha256(content).hexdigest(), 'size_bytes': len(content),
                  'media_type': 'application/json', 'schema_ref': schema}
    def command(family, payload):
        return {'identity': {'command_family': family, 'command_id': uuid.uuid4().hex,
            'actor_id': 'fixture', 'scope': scope}, 'payload': payload}
    upload = data.request('/v1/derived-uploads', command('artifacts.begin_derived_upload', {
        'content': descriptor, 'declaration': {'schema_version': '1', 'transformation': method, 'inputs': inputs}}))['upload']
    data.request('/v1/uploads/' + upload['upload_id'] + '/content', content=content, method='PUT')
    artifact = data.request('/v1/artifacts/finalize', command('artifacts.finalize', {'upload_id': upload['upload_id'], 'content': descriptor}))['artifact']
    proof = data.request('/v1/artifacts/' + artifact['artifact_id'] + '/derivation')
    assert proof['declaration']['inputs'] == inputs
    assert data.request('/v1/artifacts/' + artifact['artifact_id'] + '/content', binary=True) == content
    return artifact


def install_correction(scenario, observation):
    # The bounded fixture owns this synthetic measurement; no actual instrument is claimed.
    path = scenario.directory / 'corrected-observation.json'
    path.write_text(json.dumps(observation), encoding='utf-8')
    owned_setup(scenario.interpreters['research'], '''
import json,os
from pathlib import Path
from sqlalchemy import create_engine
from amphora_contracts_research import ObservationRevision
from amphora_research.observations.store import ObservationStore
value=ObservationRevision.model_validate_json(Path(os.environ['FIXTURE_PATH']).read_text(encoding='utf-8'))
engine=create_engine(os.environ['OWNER_DATABASE'])
try: ObservationStore(engine).publish(value.reference.scope,'fixture',value)
finally: engine.dispose()
''', dict(scenario.environments['research'], FIXTURE_PATH=str(path)))


def progress(scenario, baseline, runtime):
    data, research, knowledge, scope = scenario.data, scenario.research, scenario.knowledge, scenario.scope
    question, need = baseline['question'], baseline['need']
    context = question['applicability']
    original_observation = baseline['specimens']['observation-revision']
    report_profile = next(p for p in data_profiles(scenario.directory) if p['schema_id'] == 'fixture.observation-report')
    report_schema = {k: report_profile[k] for k in ('schema_id', 'version', 'sha256')}
    method = {'transformation_id': need['method']['schema_id'], 'version': need['method']['version'], 'sha256': need['method']['sha256']}
    profiles = baseline['assessment_profiles']
    def report_snapshot(observation):
        observed = research.request('/v1/observations/read', observation['reference'])
        assert observed == observation
        assert observed['binding']['measurement'] == {'method': need['method'], 'context': need['required_context']}
        return derived(data, scope, observed, report_schema, [observation['source']],
                         {'transformation_id': 'fixture.observation_snapshot', 'version': '1', 'sha256': report_schema['sha256']})
    def assess(version, answer, observation, label, report=None):
        report = report or report_snapshot(observation)
        evidence = derived(data, scope, {'wire_version': '1', 'authority': 'synthetic', 'need': need['reference'],
            'criterion_id': 'declared', 'subject': answer, 'method': need['method'], 'context': need['required_context'],
            'category': 'observation', 'issuer': 'fixture', 'purpose': 'fixture_support', 'disposition': 'supported'},
            synthetic_evidence_schema().model_dump(mode='json'), [answer, context, report], method)
        profile = profiles[version - 1]
        request = {'wire_version': '1', 'assessment_id': label, 'profile': {'scope': scope,
            'profile_id': profile['profile_id'], 'version': profile['version'], 'sha256': digest(profile)},
            'question': question['reference'], 'answers': [{'criterion_id': 'declared', 'artifact': answer}], 'receipts': [evidence]}
        status = research.request('/v1/assessments', request)
        assert status['outcome']['assessment']['sufficient'] is True
        assert status['outcome']['assessment']['scientifically_established'] is False
        selection = {'wire_version': '1', 'scope': scope, 'assessment_id': label}
        publication = research.request('/v1/assessment-publications', selection)
        assert publication['outcome']['receipt']['outcome']['status'] == 'accepted'
        assert research.request('/v1/assessments/read', request) == status
        return {'request': request, 'assessment': status, 'publication': publication, 'report': report, 'evidence': evidence}

    first = assess(1, baseline['publication']['outcome']['derivation']['artifact'], original_observation, 'original')
    gap_request = first['request'] | {'assessment_id': 'unmet', 'receipts': []}
    unmet = research.request('/v1/assessments', gap_request)
    assert unmet['outcome']['assessment']['sufficient'] is False
    chain = {'schema_version': '1', 'scope': scope, 'issuer_id': 'research-synthetic', 'chain_id': 'feedback'}
    root = research.request('/v1/assessment-receipts/correct', {'wire_version': '1', 'chain': chain,
        'change_id': 'initial', 'assessment_id': 'original', 'reason_code': 'initial_evidence', 'expected_head': None})
    first_run = runtime.consume(data, root['record']['receipt'], campaign_id='feedback-original', output_schema='assessment.json')
    corrected = copy.deepcopy(original_observation)
    corrected['reference']['revision'] += 1
    corrected['supersedes'] = original_observation['reference']
    corrected['quality']['flags'].append('review_next_campaign')
    install_correction(scenario, corrected)
    correction = research.request('/v1/observation-corrections/read', corrected['reference'])
    assert correction['before'] == original_observation and correction['after'] == corrected
    assert correction['policy'] == 'future_campaigns_only'
    corrected_report = report_snapshot(corrected)

    proposal = copy.deepcopy(baseline['proposal'])
    old_claim = proposal['operations'][2]['assertion']
    new_claim = copy.deepcopy(old_claim)
    new_claim['reference']['revision'] += 1
    new_claim['supersedes'] = old_claim['reference']
    new_claim['statement'] = 'Synthetic hypothesis remains useful; revisit the flagged measurement in the next campaign.'
    new_claim['grounding']['interpretation_artifacts'].append(corrected_report)
    proposal['grounding']['interpretation_artifacts'].append(corrected_report)
    proposal.update(change_id='feedback-next', base=baseline['head'], description='Carry the measurement review forward',
                    rationale='A synthetic reported result now has a quality flag; preserve history and explicitly revise future inputs.',
                    operations=[{'operation': 'correct_assertion', 'prior': old_claim['reference'], 'replacement': new_claim}])
    decision = knowledge.request('/v1/graph-proposals', proposal)
    assert decision['decision']['outcome'] == 'accepted'
    head = decision['decision']['head']
    reason = copy.deepcopy(baseline['reasoning']['request'])
    reason.update(request_id='reason-next', snapshot=head['snapshot'])
    knowledge.request('/v1/graph-reasoning', reason)
    answer = knowledge.request('/v1/reasoning-publications', {'wire_version': '1', 'graph': proposal['graph'],
        'publication_id': 'next', 'reasoning_request_id': 'reason-next'})
    second = assess(2, answer['outcome']['derivation']['artifact'], corrected, 'next', corrected_report)
    next_receipt = research.request('/v1/assessment-receipts/correct', {'wire_version': '1', 'chain': chain,
        'change_id': 'next', 'assessment_id': 'next', 'reason_code': 'quality_review', 'expected_head': root['reference']})
    assert next_receipt['record']['predecessor'] == root['reference']
    second_run = runtime.consume(data, next_receipt['record']['receipt'], campaign_id='feedback-next', output_schema='assessment.json')
    old_wait = first_run['opened']['expectation']
    assert runtime.owner.request('/v1/graph-runs/' + old_wait['run_id'] + '/waits/' + old_wait['activation_id']) == first_run['closed']
    assert research.request('/v1/observations/read', original_observation['reference']) == original_observation
    previous_selection = {'wire_version': '1', 'chain': chain, 'revision': root['reference']}
    next_selection = {'wire_version': '1', 'chain': chain, 'revision': next_receipt['reference']}
    assert research.request('/v1/assessment-receipts/select', previous_selection) == root
    assert research.request('/v1/assessment-receipts/select', next_selection) == next_receipt
    assert first_run['graph']['plan_sha256'] != second_run['graph']['plan_sha256']
    return {'unmet': unmet, 'first': first, 'second': second, 'observation_correction': correction,
        'proposal': knowledge.request('/v1/graphs/' + proposal['graph']['graph_id'] + '/proposals/feedback-next'),
        'change': knowledge.request('/v1/graph-changes/read', head['change']),
        'root': root, 'next': next_receipt, 'first_run': first_run, 'second_run': second_run,
        'pins': {'question': question['reference'], 'need': need['reference'], 'assessment': second['request'],
            'publication': second['publication']['request'], 'proposal': {'graph': proposal['graph'], 'change_id': 'feedback-next'},
            'corrections': {'owner': 'research', 'previous': previous_selection, 'next': next_selection}}}
