import json
from pathlib import Path

import pytest
from amphora_contracts_search import SearchSpec
from amphora_evolution_search import (
    BoxVariation,
    CounterRandom,
    OriginalSearch,
    ParentVector,
)


def original(*, crossover=1.0, mutation=0.0, fixed=False):
    data = json.loads((Path(__file__).parents[1] / "specification/synthetic_specification.json").read_bytes())
    data["budget"]["population_size"] = 2
    data["operators"].update(crossover_probability=crossover, mutation_probability=mutation, mutation_fraction=1.0)
    if fixed:
        data["variables"][0].update(lower=0.25, upper=0.25)
    return OriginalSearch(SearchSpec.model_validate_json(json.dumps(data)))


def test_convex_crossover_matches_independent_dotnet_draws():
    parents = (ParentVector("a" * 64, (0.25,)), ParentVector("b" * 64, (0.75,)))
    draw = BoxVariation(original()).draw(parents, CounterRandom("0" * 64, 1))
    # Counters1/2 choose right/left, counter3 crosses, counter4 supplies blend.
    blend = 2891449216599693 / 9007199254740992
    assert draw.genes == (blend * 0.75 + (1 - blend) * 0.25,)
    assert draw.parents == ("b" * 64, "a" * 64)
    assert draw.before.counter == 1 and draw.after.counter == 7


@pytest.mark.parametrize("crossover,mutation,expected", [(0.0, 0.0, 0.75), (0.0, 1.0, 0.0), (1.0, 1.0, 0.0)])
def test_fixed_schedule_and_mutation_clamping(crossover, mutation, expected):
    parents = (ParentVector("a" * 64, (0.25,)), ParentVector("b" * 64, (0.75,)))
    draw = BoxVariation(original(crossover=crossover, mutation=mutation)).draw(parents, CounterRandom("0" * 64))
    assert draw.genes == (expected,)
    assert draw.after.counter == 6
    assert draw.parents == ("b" * 64,)


def test_fixed_axis_consumes_all_draws_and_single_parent_stays_explicit():
    draw = BoxVariation(original(fixed=True, mutation=1.0)).draw((ParentVector("a" * 64, (0.25,)),), CounterRandom("0" * 64))
    assert draw.genes == (0.25,) and draw.parents == ("a" * 64,)
    assert draw.after.counter == 6


@pytest.mark.parametrize("parents,code", [
    ((), "variation_population"),
    ((ParentVector("bad", (0.2,)),), "variation_parent_identity"),
    ((ParentVector("a" * 64, (0.2,)),) * 2, "variation_duplicate_parent"),
    ((ParentVector("a" * 64, (2.0,)),), "variation_parent_bounds"),
    ((ParentVector("a" * 64, (float("nan"),)),), "variation_parent_bounds"),
])
def test_invalid_parent_pool_rejects(parents, code):
    with pytest.raises(ValueError, match=code):
        BoxVariation(original()).draw(parents, CounterRandom("0" * 64))


def test_wrong_seed_and_exhaustion_leave_input_state_unchanged():
    parents = (ParentVector("a" * 64, (0.25,)),)
    with pytest.raises(ValueError, match="variation_seed"):
        BoxVariation(original()).draw(parents, CounterRandom("f" * 64))
    almost_exhausted = CounterRandom("0" * 64, 9007199254740988)
    with pytest.raises(ValueError, match="rng_exhausted"):
        BoxVariation(original()).draw(parents, almost_exhausted)
    assert almost_exhausted.counter == 9007199254740988
