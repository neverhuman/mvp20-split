import json
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest
from amphora_contracts_search import SearchSpec
from amphora_evolution_search import (
    CheckpointSnapshot,
    InitialPopulation,
    OriginalSearch,
)


def specification(*, size=3, evaluations=4, fixed=False):
    data = json.loads((Path(__file__).parents[1] / "specification/synthetic_specification.json").read_text())
    data["budget"]["population_size"] = size
    data["budget"]["max_evaluations"] = evaluations
    if fixed:
        data["variables"][0].update(lower=2.0, upper=2.0)
    return OriginalSearch(SearchSpec.model_validate_json(json.dumps(data)))


def test_initial_coordinates_match_independent_dotnet_oracle():
    population = InitialPopulation.generate(specification())
    expected = (5377210515782559, 4601183230486650, 1940936019154208)
    assert tuple(a.genes[0] for a in population.attempts) == tuple(n / 9007199254740992 for n in expected)
    assert [(a.draws.start, a.draws.end) for a in population.attempts] == [(0, 1), (1, 2), (2, 3)]
    checkpoint = population.checkpoint()
    assert checkpoint.record.progress.evaluations_issued == 3
    assert len(checkpoint.record.pending) == len(population.requests) == 3
    assert CheckpointSnapshot.decode(population.original, checkpoint.encode()) == checkpoint


def test_fixed_box_retains_duplicates_without_extra_evaluations():
    population = InitialPopulation.generate(specification(fixed=True))
    assert [a.disposition for a in population.attempts] == ["proposed", "duplicate", "duplicate"]
    assert all(a.duplicate_of == population.attempts[0].candidate_id for a in population.attempts[1:])
    assert population.random.counter == 3
    assert len(population.requests) == 1
    assert len(population.checkpoint().record.attempts) == 3


@pytest.mark.parametrize("evaluations", [0, 1, 2])
def test_budget_caps_requests_and_retains_every_attempt(evaluations):
    population = InitialPopulation.generate(specification(evaluations=evaluations))
    assert len(population.requests) == evaluations
    assert [a.disposition for a in population.attempts] == ["proposed"] * evaluations + ["rejected"] * (3 - evaluations)
    assert all(a.reason_code == "evaluation_budget" for a in population.attempts[evaluations:])
    snapshot = population.checkpoint()
    assert snapshot.record.progress.evaluations_issued == evaluations
    assert snapshot.record.stop_reason == ("evaluation_budget" if evaluations == 0 else None)


def test_initial_population_cannot_hide_or_change_requests():
    population = InitialPopulation.generate(specification())
    with pytest.raises(ValueError, match="initial_request_set"):
        replace(population, requests=population.requests[:-1])
    altered = population.requests[0].model_copy(update={"evaluation_id": "wrong"})
    with pytest.raises(ValueError, match="initial_request_set"):
        replace(population, requests=(altered, *population.requests[1:]))


def test_generation_zero_budget_still_allows_initial_population():
    original = specification()
    budget = original.record.budget.model_copy(update={"max_generations": 0})
    initial_only = OriginalSearch(original.record.model_copy(update={"budget": budget}))
    assert InitialPopulation.generate(initial_only).checkpoint().record.generation == 0


def test_independent_processes_replay_exact_canonical_bytes(tmp_path):
    path = tmp_path / "original.json"
    original = specification(size=128, evaluations=128)
    path.write_text(original.record.model_dump_json(), encoding="utf-8")
    script = """import sys
from pathlib import Path
from amphora_contracts_search import SearchSpec
from amphora_evolution_search import OriginalSearch, InitialPopulation
original = OriginalSearch(SearchSpec.model_validate_json(Path(sys.argv[1]).read_bytes()))
sys.stdout.buffer.write(InitialPopulation.generate(original).checkpoint().encode())
"""
    first = subprocess.run([sys.executable, "-c", script, str(path)], check=True, capture_output=True, timeout=45)
    second = subprocess.run([sys.executable, "-c", script, str(path)], check=True, capture_output=True, timeout=45)
    assert first.stdout == second.stdout
    assert not first.stderr and not second.stderr
    assert len(CheckpointSnapshot.decode(original, first.stdout).record.attempts) == 128
