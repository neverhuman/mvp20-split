import pytest

from amphora_contracts_population import (
    AvailableFitness, EvaluationKey, EvaluatedMethod, ExecutionPointer, FitnessRecord,
    MethodObservation, MethodOutput, ObjectiveAssessment,
)
from amphora_contracts_search import ObjectiveValue
from amphora_evolution_search.population import BoundEvaluation, FitnessEvidence, FrozenEvaluations


@pytest.fixture
def assessment_factory(born_cohort):
    cohort = born_cohort
    keys, observations = [], []
    for member in cohort.members:
        for method in cohort.original.record.method_graph.methods:
            key = BoundEvaluation(cohort, EvaluationKey(schema_version="1", profile="population-evaluation-key-v1",
                generation=cohort.identity, candidate_id=member.candidate_id, occurrence_id="primary",
                method_id=method.method_id, tool=method.tool, material=member.representation,
                inputs=(member.representation,), conditions=method.conditions,
                objective_policy_sha256=cohort.original.record.assembly.policy.sha256))
            keys.append(key)
            producer = ExecutionPointer(run_id=cohort.identity.run_id, activation_id="a-" + key.digest,
                invocation_id="i-" + key.digest, attempt_id="attempt-" + key.digest, completion_id="c-" + key.digest)
            observations.append(MethodObservation(schema_version="1", profile="population-method-observation-v1",
                key=key.record, evaluation_sha256=key.digest, outcome=EvaluatedMethod(status="evaluated", producer=producer,
                outputs=(MethodOutput(port="result", artifact=member.representation),))))
    evidence = FitnessEvidence(FrozenEvaluations(cohort, tuple(keys)), tuple(observations))
    def record(index=0, value=1.0, confidence=None, violation=0.0):
        candidate = cohort.members[index].candidate_id
        original = cohort.original.record
        objective = original.assembly.objectives[0].objective
        sources = tuple(key.digest for key in keys if key.record.candidate_id == candidate)
        return FitnessRecord(schema_version="1", profile="population-fitness-v1", generation=cohort.identity,
            candidate_id=candidate, assembly=original.assembly.tool, policy=original.assembly.policy,
            evaluation_set_sha256=evidence.evaluations.digest, outcome=AvailableFitness(status="evaluated",
            objectives=(ObjectiveAssessment(value=ObjectiveValue(objective_id=objective.objective_id, unit=objective.unit,
                value=value), evaluations=sources, quality="synthetic", confidence=confidence),), constraint_violation=violation))
    return evidence, record
