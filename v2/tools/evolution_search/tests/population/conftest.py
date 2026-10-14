import hashlib
from pathlib import Path

import pytest
from amphora_contracts_core import ArtifactRef
from amphora_contracts_population import CandidateMember, GenerationIdentity, PopulationSpecification, candidate_birth_schema
from amphora_evolution_search.population import GenerationMembership, NumericBirth, OriginalPopulation, canonical


@pytest.fixture
def population_original():
    return OriginalPopulation(PopulationSpecification.model_validate_json(
        (Path(__file__).parent / "specification/fixtures/specification.json").read_bytes()))


@pytest.fixture
def born_cohort(population_original):
    original = population_original
    identity = GenerationIdentity(scope=original.record.scope, run_id="test-run", specification_sha256=original.digest,
                                  generation=0, predecessor=None)
    members = []
    for ordinal in range(2):
        birth = NumericBirth.seed(original, ordinal)
        reference = ArtifactRef(artifact_id=f"birth-{ordinal}", scope=identity.scope,
            sha256=hashlib.sha256(canonical(birth.record)).hexdigest(), media_type="application/json",
            schema_ref=candidate_birth_schema(), size_bytes=len(canonical(birth.record)))
        representation = reference.model_copy(update={"artifact_id": f"vector-{ordinal}", "schema_ref": original.record.representation})
        members.append(CandidateMember(candidate_id=birth.record.candidate_id, birth=reference,
                                       representation=representation, source="seed"))
    return GenerationMembership(original, identity, "cohort", tuple(sorted(members, key=lambda m: m.candidate_id)))

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
        sources = tuple(key.digest for key in keys if key.record.candidate_id == candidate
                        and key.record.method_id in original.assembly.objectives[0].method_ids)
        return FitnessRecord(schema_version="1", profile="population-fitness-v1", generation=cohort.identity,
            candidate_id=candidate, assembly=original.assembly.tool, policy=original.assembly.policy,
            evaluation_set_sha256=evidence.evaluations.digest, outcome=AvailableFitness(status="evaluated",
            objectives=(ObjectiveAssessment(value=ObjectiveValue(objective_id=objective.objective_id, unit=objective.unit,
                value=value), evaluations=sources, quality="synthetic", confidence=confidence),), constraint_violation=violation))
    return evidence, record
