"""Owner-local fixture graph; every test receives a unique retained PostgreSQL scope."""
import json

from amphora_contracts_research import CandidateRevision
from amphora_research.experiments import wire as experiment_wire
from amphora_research.material_state import wire as material_wire
from amphora_research.material_state.store import MaterialStateStore
from amphora_research.observations import wire as observation_wire

from ..experiments.fixtures import experiment
from ..observations.test_matching import observation


def in_scope(record, scope):
    def replace_scopes(value):
        if isinstance(value,dict):
            if set(value) == {"tenant_id","project_id"}:
                return scope.model_dump(mode="json")
            return {key:replace_scopes(item) for key,item in value.items()}
        if isinstance(value,list):
            return [replace_scopes(item) for item in value]
        return value
    return type(record).model_validate_json(json.dumps(replace_scopes(record.model_dump(mode="json"))))


def records(scope):
    plan = experiment()
    return (in_scope(material_wire.to_wire(plan.samples[0].state),scope),
            in_scope(experiment_wire.to_wire(plan),scope),in_scope(observation_wire.to_wire(observation(plan)),scope))


def publish_candidate(ledger, state):
    candidate = CandidateRevision(wire_version="1",reference=state.candidate,
        representation=records(state.reference.scope)[1].samples[0].sample.identity_evidence,supersedes=None)
    ledger.publish(state.reference.scope,candidate)
    return candidate


def publish_specimen(ledger, scope):
    state,plan,result = records(scope)
    publish_candidate(ledger,state)
    MaterialStateStore(ledger.engine).publish(scope,"fixture-publisher",state)
    ledger.publish(scope,plan.samples[0].sample)
    return state,plan,result
