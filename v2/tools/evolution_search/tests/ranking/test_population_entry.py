import pytest

from amphora_evolution_search.ranking import CandidateScore, ObjectiveSpace


def test_old_entry_retains_256_guard_and_new_entry_has_closed_2000_bound():
    space = ObjectiveSpace(("minimize",))
    scores = tuple(CandidateScore(f"candidate-{i:04d}", (float(i),), 0.0) for i in range(257))
    with pytest.raises(ValueError, match="population_bound"): space.select(scores, 2)
    selected = space.select_population(scores, 2)
    assert selected.selected == ("candidate-0000", "candidate-0001")
    with pytest.raises(ValueError, match="population_bound"): space.select_population(scores * 8, 2)
    assert space.select(scores[:256], 2) == space.select_population(scores[:256], 2)


def test_2000_bound_returns_all_ranks_without_inventing_feasible_members():
    scores = tuple(CandidateScore(f"candidate-{i:04d}", (0.0,), 1.0) for i in range(2000))
    result = ObjectiveSpace(("minimize",)).select_population(scores, 1000)
    assert len(result.ranks) == 2000 and result.selected == ()


def test_2000_eligible_candidates_rank_globally_across_reversed_completion_order():
    scores = tuple(CandidateScore(f"candidate-{i:04d}", (float(i),), 0.0) for i in range(2000))
    space = ObjectiveSpace(("minimize",))
    result = space.select_population(tuple(reversed(scores)), 1000)
    assert result.selected == tuple(f"candidate-{i:04d}" for i in range(1000))
    assert {r.candidate_id: r.front for r in result.ranks} == {f"candidate-{i:04d}": i for i in range(2000)}
