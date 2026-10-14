import pytest


@pytest.mark.parametrize("failed_method", [False, True])
def test_four_generations_are_independent_of_batch_size_and_completion_order(population_oracle, failed_method):
    baseline = population_oracle(1, False, failed_method)
    for batch in (8, 32):
        assert population_oracle(batch, True, failed_method) == baseline
    assert len(baseline) == 4 and baseline[-1][-1] == "generation_budget"
