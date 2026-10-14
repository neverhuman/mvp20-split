import pytest
from amphora_contracts_population import UnavailableMethod, UnavailablePopulationFitness
from amphora_evolution_search.population import FitnessEvidence, GenerationMembership, PopulationSelection


@pytest.mark.parametrize("population_original", ["optional"], indirect=True)
def test_failed_optional_annotation_does_not_exclude_useful_candidate(assessment_factory):
    evidence, factory = assessment_factory
    observations = tuple(row.model_copy(update={"outcome": UnavailableMethod(status="failed", reason_code="annotation_unavailable",
        producer=None, evidence=())}) if row.key.method_id == "annotation" else row for row in evidence.observations)
    amended = FitnessEvidence(evidence.evaluations, observations)
    cohort = evidence.evaluations.membership
    pool = GenerationMembership(cohort.original, cohort.identity, "selection_pool", cohort.members)
    decision = PopulationSelection(pool, tuple(amended.bind(factory(i, confidence=0.0)) for i in range(2))).decide()
    assert len(decision.selected) == 2 and not decision.stopped
    assert all(row.status == "ranked" for row in decision.members)


@pytest.mark.parametrize("population_original", ["one_parent"], indirect=True)
def test_explicit_one_parent_policy_continues_reduced_population(assessment_factory):
    evidence, factory = assessment_factory
    cohort = evidence.evaluations.membership
    pool = GenerationMembership(cohort.original, cohort.identity, "selection_pool", cohort.members)
    missing = factory(1).model_copy(update={"outcome": UnavailablePopulationFitness(status="unavailable", reason_code="assembly_failed")})
    decision = PopulationSelection(pool, (evidence.bind(factory(0)), evidence.bind(missing))).decide()
    assert decision.disposition == "insufficient_survivors" and not decision.stopped
    assert len(decision.selected) == 1
