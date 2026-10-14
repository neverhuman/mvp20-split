import pytest
from amphora_evolution_search.population.planning import PrimaryBirthBatch


def test_successor_allocation_replays_retained_selected_parent_order(successor_case):
    source = successor_case["source"]
    batch = PrimaryBirthBatch.successor(source)
    assert batch.rng.to_record() == successor_case["proposal"].rng
    assert batch.evaluations_reserved == successor_case["proposal"].evaluations_reserved
    assert batch.generation == source.record.generation.generation + 1


@pytest.mark.parametrize("population_original", ["no_variation"], indirect=True)
def test_duplicate_only_generation_has_zero_fresh_evaluations_and_advances_rng(successor_case):
    source = successor_case["source"]
    batch = PrimaryBirthBatch.successor(source)
    assert batch.disposition == "duplicate_only" and not batch.proposed
    assert batch.evaluations_reserved == 0
    assert all(b.record.duplicate_of in source.decision.selected for b in batch.births)
    assert batch.rng.counter == source.record.rng.counter + 2 * (3 + 3 * len(batch.original.record.variables))


@pytest.mark.parametrize("population_original,reason", [("evaluation_tail", "evaluation_budget"),
                                                         ("attempt_tail", "attempt_budget")], indirect=["population_original"])
def test_budget_remainder_cannot_start_partial_required_method_set(successor_case, reason):
    assert successor_case["source"].stop_reason == reason
    with pytest.raises(ValueError, match="allocation_stopped_source"):
        PrimaryBirthBatch.successor(successor_case["source"])
