import pytest
from amphora_evolution_search.population import OriginalPopulation
from amphora_evolution_search.population.planning import EvaluationCapacity, PrimaryBirthBatch


def configured(original, *, fixed=False):
    record = original.record.model_copy(update={"budget": original.record.budget.model_copy(update={"population_size": 4})})
    if fixed:
        record = record.model_copy(update={"variables": tuple(v.model_copy(update={"lower": 0.0, "upper": 0.0}) for v in record.variables)})
    return OriginalPopulation(record)


@pytest.mark.parametrize("evaluations,attempts,proposed,reason", [(0, 100, 0, "evaluation_budget"),
    (1, 100, 0, "evaluation_budget"), (3, 100, 1, "evaluation_budget"),
    (100, 0, 0, "attempt_budget"), (100, 3, 1, "attempt_budget"), (8, 8, 4, None)])
def test_entire_method_cost_allocated_before_candidate_publication(population_original, evaluations, attempts, proposed, reason):
    original = configured(population_original)
    result = PrimaryBirthBatch.seed(original, EvaluationCapacity(evaluations, attempts))
    assert len(result.births) == 4 and len(result.proposed) == proposed
    assert result.evaluations_reserved == proposed * len(original.record.method_graph.methods)
    assert result.rng.counter == 4 * len(original.record.variables)
    rejected = [b for b in result.births if b.record.disposition == "rejected"]
    assert all(b.record.reason_code == reason for b in rejected)
    assert len(rejected) == 4 - proposed
    assert result.disposition == ("evaluate" if proposed else reason)


def test_fixed_seed_duplicates_retain_all_births_without_fake_evaluations(population_original):
    original = configured(population_original, fixed=True)
    result = PrimaryBirthBatch.seed(original)
    assert len(result.proposed) == 1 and result.evaluations_reserved == 2
    first = result.proposed[0].record.candidate_id
    assert all(b.record.disposition == "duplicate" and b.record.duplicate_of == first for b in result.births[1:])
    assert [b.record.draws.start for b in result.births] == [0, 1, 2, 3]


def test_birth_identity_and_rng_do_not_depend_on_available_budget(population_original):
    original = configured(population_original)
    whole = PrimaryBirthBatch.seed(original)
    limited = PrimaryBirthBatch.seed(original, EvaluationCapacity(0, 0))
    assert whole.rng == limited.rng
    assert [b.record.candidate_id for b in whole.births] == [b.record.candidate_id for b in limited.births]


@pytest.mark.parametrize("value", [-1, True, 1.5, 808001])
def test_capacity_is_strict(value):
    with pytest.raises(ValueError):
        EvaluationCapacity(value, 0)
