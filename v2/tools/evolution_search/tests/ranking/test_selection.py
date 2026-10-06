import math
from dataclasses import replace

import pytest
from amphora_evolution_search import CandidateScore, ObjectiveSpace


def point(name, *values, violation=0.0, eligible=True):
    return CandidateScore(name, tuple(float(v) for v in values), violation, eligible)


def test_independent_fronts_constraints_and_crowding_oracle():
    scores = (point("a", 0, 3), point("b", 1, 2), point("c", 2, 1), point("d", 3, 0),
              point("e", 4, 4), point("f", 0, 0, violation=1.0), point("g", -9, -9, violation=2.0))
    policy = ObjectiveSpace(("minimize", "minimize"))
    result = policy.select(scores, 3)
    assert result.selected == ("a", "d", "b")
    assert {r.candidate_id: r.front for r in result.ranks} == {"a": 0, "b": 0, "c": 0, "d": 0, "e": 1, "f": 2, "g": 3}
    assert result == policy.select(tuple(reversed(scores)), 3)
    assert result.disposition == "selected"


def test_objective_direction_and_equal_infeasible_ties():
    policy = ObjectiveSpace(("maximize", "minimize"))
    result = policy.select((point("a", 2, 1), point("b", 1, 2)), 1)
    assert result.selected == ("a",)
    result = policy.select((point("a", 2, 1, violation=1.0), point("b", 1, 2, violation=1.0)), 2)
    assert result.selected == () and result.disposition == "no_feasible_candidates"
    assert [r.front for r in result.ranks] == [0, 0]


def test_constant_axes_and_identical_values_have_only_identifier_tie_breaks():
    result = ObjectiveSpace(("minimize",)).select((point("c", 1), point("a", 1), point("b", 1)), 2)
    assert result.selected == ("a", "b")
    assert all(not row.boundary and row.distance == 0 for row in result.ranks)


@pytest.mark.parametrize("magnitude", [1e308, 5e-324])
def test_crowding_stays_finite_across_extreme_ranges(magnitude):
    scores = (point("a", -magnitude, magnitude), point("b", 0, 0), point("c", magnitude, -magnitude))
    result = ObjectiveSpace(("minimize", "minimize")).select(scores, 3)
    middle = next(r for r in result.ranks if r.candidate_id == "b")
    assert middle.distance == 2.0 and all(math.isfinite(r.distance) for r in result.ranks)


def test_partial_feasibility_and_zero_request_remain_explicit():
    scores = (point("a", 3), point("b", 0, violation=1.0))
    policy = ObjectiveSpace(("minimize",))
    result = policy.select(scores, 2)
    assert result.selected == ("a",) and result.disposition == "insufficient_feasible_candidates"
    assert policy.select(scores, 0).disposition == "zero_requested"


@pytest.mark.parametrize("case,code", [("unknown", "fitness_not_eligible"), ("duplicate", "duplicate_candidate"),
                                     ("dimension", "objective_dimension"), ("count_bool", "selection_count"),
                                     ("empty", "population_bound"), ("large", "population_bound")])
def test_invalid_selection_has_no_silent_fallback(case, code):
    scores, count = (point("a", 0),), 1
    if case == "unknown": scores = (replace(scores[0], eligible=False),)
    if case == "duplicate": scores = scores * 2
    if case == "dimension": scores = (point("a", 0, 0),)
    if case == "count_bool": count = True
    if case == "empty": scores = ()
    if case == "large": scores = tuple(point(str(i), i) for i in range(257))
    with pytest.raises(ValueError, match=code):
        ObjectiveSpace(("minimize",)).select(scores, count)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf"), True, 1])
def test_nonfinite_or_untyped_objective_values_rejected(value):
    with pytest.raises(ValueError, match="objective_nonfinite"):
        CandidateScore("a", (value,), 0.0)


def test_closed_direction_and_nonnegative_violation():
    with pytest.raises(ValueError, match="objective_direction"):
        ObjectiveSpace(("best",))
    with pytest.raises(ValueError, match="constraint_violation"):
        point("a", 0, violation=-1.0)
