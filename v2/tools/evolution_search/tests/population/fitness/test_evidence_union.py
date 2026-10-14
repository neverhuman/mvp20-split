import pytest
from amphora_evolution_search.population import FitnessEvidence, GenerationMembership, PopulationSelection
from amphora_evolution_search.population.evaluations import observation_cut


def test_shared_evidence_is_charged_and_hashed_once_per_set(assessment_factory):
    evidence, factory = assessment_factory
    cohort = evidence.evaluations.membership
    selection = PopulationSelection(GenerationMembership(cohort.original, cohort.identity, "selection_pool", cohort.members),
                                    tuple(evidence.bind(factory(i)) for i in range(2)))
    assert len(selection.observations()) == len(evidence.observations) == 4
    assert selection.decide().observation_cut_sha256 == observation_cut(evidence.observations)
    assert evidence.cut_sha256 == observation_cut(evidence.observations)
    with pytest.raises(TypeError):
        evidence.by_candidate[cohort.members[0].candidate_id] = {}
    with pytest.raises(TypeError):
        cohort.by_id[cohort.members[0].candidate_id] = cohort.members[0]


def test_same_keys_with_conflicting_producer_receipt_cannot_be_deduplicated(assessment_factory):
    evidence, factory = assessment_factory
    observation = evidence.observations[0]
    altered = observation.model_copy(update={"outcome": observation.outcome.model_copy(update={
        "producer": observation.outcome.producer.model_copy(update={"completion_id": "different"})})})
    conflicting = FitnessEvidence(evidence.evaluations, (altered, *evidence.observations[1:]))
    cohort = evidence.evaluations.membership
    with pytest.raises(ValueError, match="selection_observation_conflict"):
        PopulationSelection(GenerationMembership(cohort.original, cohort.identity, "selection_pool", cohort.members),
                            (evidence.bind(factory(0)), conflicting.bind(factory(1))))
