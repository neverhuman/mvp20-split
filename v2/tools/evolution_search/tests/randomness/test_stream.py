import json

import pytest
from amphora_contracts_search import RngState
from amphora_evolution_search import CounterRandom


# Independently calculated by Windows .NET SHA256/UInt64, not this Python kernel.
@pytest.mark.parametrize("counter,numerator", [
    (0, 5377210515782559), (1, 4601183230486650), (2, 1940936019154208),
    (9007199254740990, 4317695533480164),
])
def test_independent_dotnet_golden(counter, numerator):
    rng = CounterRandom("0" * 64, counter)
    value, advanced = rng.draw()
    assert value == numerator / 9007199254740992
    assert rng.counter == counter
    assert advanced.counter == counter + 1
    assert 0 <= value < 1


def test_json_resume_has_identical_future_draws_without_global_state():
    rng = CounterRandom("a" * 64)
    for _ in range(31):
        _, rng = rng.draw()
    saved = RngState.model_validate_json(rng.to_record().model_dump_json())
    resumed = CounterRandom.from_record(saved, expected_seed="a" * 64)
    for _ in range(100):
        expected, rng = rng.draw()
        actual, resumed = resumed.draw()
        assert actual.hex() == expected.hex()
    assert resumed == rng


def test_seed_change_and_counter_exhaustion_fail_without_advancing():
    final = CounterRandom("0" * 64, 9007199254740991)
    with pytest.raises(ValueError, match="rng_exhausted"):
        final.draw()
    assert final.counter == 9007199254740991
    with pytest.raises(ValueError, match="rng_original_seed"):
        CounterRandom.from_record(final.to_record(), expected_seed="1" * 64)


@pytest.mark.parametrize("seed,counter", [("A" * 64, 0), ("x" * 64, 0), ("0" * 63, 0),
                                          (0, 0), ("0" * 64, True), ("0" * 64, -1),
                                          ("0" * 64, 1.0), ("0" * 64, 9007199254740992)])
def test_invalid_stream(seed, counter):
    with pytest.raises(ValueError):
        CounterRandom(seed, counter)


def test_unsupported_algorithm_and_unvalidated_record_reject():
    data = CounterRandom("0" * 64).to_record().model_dump(mode="json")
    data["algorithm"] = "python-random"
    with pytest.raises(ValueError):
        RngState.model_validate_json(json.dumps(data))
    with pytest.raises(ValueError):
        CounterRandom.from_record(RngState.model_construct(**data), expected_seed="0" * 64)
