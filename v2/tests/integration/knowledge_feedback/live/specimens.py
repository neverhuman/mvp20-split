"""Explicit synthetic scientific fixture, installed only inside Research's process."""
import json
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
 ledger.publish(state.reference.scope,plan.samples[0].sample)
 ExperimentStore(engine).publish(state.reference.scope,'fixture',plan)
 ObservationStore(engine).publish(state.reference.scope,'fixture',observation)
finally: engine.dispose()
''', dict(environment, FIXTURE_PATH=str(path)))
    return records


def read_views(research, records):
    experiment = records['experiment-definition']['reference']
    observation = records['observation-revision']['reference']
    specimens = research.request('/v1/research-explore/specimens', {'wire_version': '1', 'experiment': experiment, 'limit': 16})
    properties = research.request('/v1/research-explore/properties', {'wire_version': '1', 'experiment': experiment,
        'observations': [observation], 'limit': 16})
    assert len(specimens['rows']) == len(properties['rows']) == 1
    assert properties['rows'][0]['value'] == records['observation-revision']['value']
    return {'specimens': specimens, 'properties': properties,
        'catalog': research.request('/v1/research-explore/catalog', experiment)}
