"""Explicit synthetic scientific fixture, installed only inside Research's process."""
import json
import copy
from pathlib import Path

from .process import owned_setup


def install(directory, scope, artifact, python, environment):
    records = json.loads(Path(__file__).with_name('specimen.json').read_text(encoding='utf-8'))
    def patch(value):
        if isinstance(value, dict):
            if set(value) == {'tenant_id', 'project_id'}:
                return dict(scope)
            if 'artifact_id' in value:
                return artifact
            return {key: patch(child) for key, child in value.items()}
        return [patch(child) for child in value] if isinstance(value, list) else value
    records = patch(records)
    state = records['material-state-revision']
    state['preparation'] = [{'event_id': 'annealing', 'context': {
        'method': {'schema_id': 'fixture.preparation', 'version': '1', 'sha256': 'a'*64},
        'conditions': [{'name': 'temperature', 'quantity': {'value': '80.0', 'unit': 'degC'}}],
        'duration': {'value': '30', 'unit': 'min'}, 'atmosphere': 'air'},
        'attribution': {'basis': 'observed', 'actor': 'fixture', 'equipment': ['synthetic-oven'], 'source': artifact}}]
    plan = records['experiment-definition']
    plan['samples'][0]['state'] = state
    hotter = copy.deepcopy(state)
    hotter['reference']['material_state_id'] = 'state-hot'
    hotter['preparation'][0]['context']['conditions'][0]['quantity']['value'] = '120.0'
    hotter['preparation'][0]['context']['duration']['value'] = '60'
    sample = copy.deepcopy(plan['samples'][0]['sample'])
    sample['reference']['sample_id'] = 'sample-hot'
    sample['material_state'] = hotter['reference']
    plan['samples'].append({'sample': sample, 'state': hotter})
    expectation = copy.deepcopy(plan['expectations'][0])
    expectation.update(expectation_id='expectation-hot', sample=sample['reference'])
    expectation['replicate']['replicate_id'] = 'replicate-hot'
    plan['expectations'].append(expectation)
    observation = copy.deepcopy(records['observation-revision'])
    observation['reference']['observation_id'] = 'observation-hot'
    observation['binding']['target'].update(expectation_id='expectation-hot', replicate_id='replicate-hot')
    observation['binding']['specimen'] = {'sample': sample['reference'], 'material_state': hotter['reference']}
    unit = observation['value']['quantity']['unit']
    observation['value'] = {'kind': 'numeric', 'quantity': {'value': '9.000', 'unit': unit}, 'uncertainty': None}
    observation['quality']['flags'].append('temperature_review')
    records.update(second_state=hotter, second_observation=observation)
    path = directory / 'specimen-fixture.json'
    path.write_text(json.dumps(records), encoding='utf-8')
    owned_setup(python, '''
import json,os
from pathlib import Path
from sqlalchemy import create_engine
from amphora_contracts_research import CandidateRevision,MaterialStateRevision,ExperimentDefinition,ObservationRevision
from amphora_research.persistence.ledger import IdentityLedger
from amphora_research.material_state.store import MaterialStateStore
from amphora_research.experiments.store import ExperimentStore
from amphora_research.observations.store import ObservationStore
records=json.loads(Path(os.environ['FIXTURE_PATH']).read_text(encoding='utf-8'))
state=MaterialStateRevision.model_validate_json(json.dumps(records['material-state-revision']))
plan=ExperimentDefinition.model_validate_json(json.dumps(records['experiment-definition']))
observation=ObservationRevision.model_validate_json(json.dumps(records['observation-revision']))
engine=create_engine(os.environ['OWNER_DATABASE'])
try:
 ledger=IdentityLedger(engine)
 candidate=CandidateRevision(wire_version='1',reference=state.candidate,representation=plan.samples[0].sample.identity_evidence,supersedes=None)
 ledger.publish(state.reference.scope,candidate)
 MaterialStateStore(engine).publish(state.reference.scope,'fixture',state)
 second=MaterialStateRevision.model_validate_json(json.dumps(records['second_state']))
 MaterialStateStore(engine).publish(state.reference.scope,'fixture',second)
 for item in plan.samples: ledger.publish(state.reference.scope,item.sample)
 ExperimentStore(engine).publish(state.reference.scope,'fixture',plan)
 ObservationStore(engine).publish(state.reference.scope,'fixture',observation)
 second_observation=ObservationRevision.model_validate_json(json.dumps(records['second_observation']))
 ObservationStore(engine).publish(state.reference.scope,'fixture',second_observation)
finally: engine.dispose()
''', dict(environment, FIXTURE_PATH=str(path)))
    return records


def read_views(research, records):
    experiment = records['experiment-definition']['reference']
    observation = records['observation-revision']['reference']
    specimens = research.request('/v1/research-explore/specimens', {'wire_version': '1', 'experiment': experiment, 'limit': 16})
    properties = research.request('/v1/research-explore/properties', {'wire_version': '1', 'experiment': experiment,
        'observations': [observation], 'limit': 16})
    assert len(specimens['rows']) == 2 and len(properties['rows']) == 1
    assert properties['rows'][0]['value'] == records['observation-revision']['value']
    return {'specimens': specimens, 'properties': properties,
        'catalog': research.request('/v1/research-explore/catalog', experiment)}


def compare_views(research, records):
    experiment = records['experiment-definition']['reference']
    observations = [records[key]['reference'] for key in ('observation-revision', 'second_observation')]
    specimens = research.request('/v1/research-explore/specimens', {'wire_version': '1', 'experiment': experiment, 'limit': 16})
    properties = research.request('/v1/research-explore/properties', {'wire_version': '1', 'experiment': experiment,
        'observations': observations, 'limit': 16})
    assert len(specimens['rows']) == len(properties['rows']) == 2
    assert specimens['rows'][0]['sample']['candidate'] == specimens['rows'][1]['sample']['candidate']
    assert specimens['rows'][0]['sample']['material_state'] != specimens['rows'][1]['sample']['material_state']
    materials = [research.request('/v1/material-states/read', records[key]['reference'])
                 for key in ('material-state-revision', 'second_state')]
    assert [item['preparation'][0]['context']['conditions'][0]['quantity']['value'] for item in materials] == ['80.0', '120.0']
    assert [row['reference'] for row in properties['rows']] == observations
    assert properties['rows'][1]['value']['quantity']['value'] == '9.000'
    assert properties['rows'][1]['quality']['flags'] == ['temperature_review']
    return {'specimens': specimens, 'properties': properties, 'materials': materials}
