import pytest
from amphora_contracts_population import population_record_schema
from amphora_evolution_search.population import GenerationMembership, PopulationSelection
from amphora_evolution_search.population.fronts import FitnessFront
from amphora_evolution_search.ranking import CandidateScore


def test_front_compares_vectors_not_new_candidate_names_and_preserves_directions():
    original = FitnessFront.from_scores(("minimize", "maximize"), (CandidateScore("a" * 64, (1.0, 2.0), 0.0),))
    renamed = FitnessFront.from_scores(("minimize", "maximize"), (
        CandidateScore("b" * 64, (1.0, 2.0), 0.0), CandidateScore("c" * 64, (2.0, 1.0), 0.0),
        CandidateScore("d" * 64, (0.0, 3.0), 1.0)))
    assert renamed == original and renamed.unchanged_count(original, 3) == 4
    improved = FitnessFront.from_scores(("minimize", "maximize"), (CandidateScore("b" * 64, (0.0, 2.0), 0.0),))
    assert improved.unchanged_count(original, 3) == 0
    with pytest.raises(ValueError, match="front_prior_count"):
        improved.unchanged_count(original, 100)


def test_parent_only_duplicate_generation_counts_unchanged_front(assessment_factory):
    evidence, factory = assessment_factory
    cohort = evidence.evaluations.membership
    initial = PopulationSelection(GenerationMembership(cohort.original, cohort.identity, "selection_pool", cohort.members),
                                  tuple(evidence.bind(factory(i)) for i in range(2)))
    assert initial.front_progress(0) == 0
    predecessor = cohort.members[0].birth.model_copy(update={"artifact_id": "checkpoint", "schema_ref": population_record_schema("population.checkpoint")})
    identity = cohort.identity.model_copy(update={"generation": 1, "predecessor": predecessor})
    parents = tuple(m.model_copy(update={"source": "parent"}) for m in cohort.members)
    successor = PopulationSelection(GenerationMembership(cohort.original, identity, "selection_pool", parents), initial.fitness)
    assert successor.front_progress(0) == 1
    with pytest.raises(ValueError, match="front_generation_count"):
        successor.front_progress(1)
