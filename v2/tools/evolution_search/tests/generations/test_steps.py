import json
from hashlib import sha256
from pathlib import Path

import pytest
from amphora_contracts_core import ArtifactRef
from amphora_contracts_graph_runtime import MissingValue
from amphora_contracts_search import (
    EvaluatedFitness,
    EvaluationObservation,
    ObjectiveValue,
    SearchSpec,
    search_checkpoint_schema,
)
from amphora_evolution_search import (
    BoundCheckpoint,
    CheckpointSnapshot,
    GenerationReducer,
    InitialPopulation,
    OriginalSearch,
    SuccessorPopulation,
)


def original(*, population=2, generations=2, evaluations=20, unchanged=None, mutation=1.0, crossover=1.0):
    data = json.loads((Path(__file__).parents[1] / "specification/synthetic_specification.json").read_bytes())
    data["budget"].update(population_size=population, max_generations=generations,
                          max_evaluations=evaluations, unchanged_front_limit=unchanged)
    data["operators"].update(mutation_probability=mutation, crossover_probability=crossover)
    return OriginalSearch(SearchSpec.model_validate_json(json.dumps(data)))


def bind(snapshot):
    raw = snapshot.encode()
    reference = ArtifactRef(artifact_id="checkpoint-" + sha256(raw).hexdigest(), scope=snapshot.original.record.scope,
                            sha256=sha256(raw).hexdigest(), size_bytes=len(raw), media_type="application/json",
                            schema_ref=search_checkpoint_schema())
    return BoundCheckpoint(snapshot, reference)


def results(bound, *, violation=0.0):
    return tuple(EvaluationObservation(schema_version="1", scope=request.scope, evaluation_id=request.evaluation_id,
                                       candidate_id=request.candidate.candidate_id, request_sha256=pending.request_sha256,
                                       outcome=EvaluatedFitness(status="evaluated", evaluator=request.evaluator.tool,
                                                                objectives=(ObjectiveValue(objective_id="cost", unit="dimensionless",
                                                                                           value=sum(x * x for x in request.candidate.genes)),),
                                                                constraint_violation=violation,
                                                                constraints_sha256=request.evaluator.constraints.sha256,
                                                                quality="synthetic", evidence=(request.evaluator.constraints,)))
                 for request, pending in zip(bound.request_batch().requests, bound.snapshot.record.pending, strict=True))


def test_all_terminal_selection_is_independent_of_observation_arrival_order():
    initial = bind(InitialPopulation.generate(original()).checkpoint())
    forward = GenerationReducer(initial).collect(results(initial))
    backward = GenerationReducer(initial).collect(tuple(reversed(results(initial))))
    assert forward.encode() == backward.encode()
    expected = tuple(a.candidate_id for a in sorted(initial.snapshot.record.attempts, key=lambda a: a.genes[0]))
    assert forward.record.population == expected
    assert forward.record.previous == initial.reference


def test_successor_progress_pending_and_restore_preserve_exact_steps():
    spec = original()
    initial = bind(InitialPopulation.generate(spec).checkpoint())
    selected = GenerationReducer(initial).collect(results(initial))
    traces = []
    for generation in (1, 2):
        previous = bind(selected)
        offspring = SuccessorPopulation(previous).create()
        restored = CheckpointSnapshot.decode(spec, offspring.encode())
        assert offspring == restored
        assert offspring.record.previous == previous.reference
        assert offspring.record.generation == generation
        assert offspring.record.progress.generations_completed == generation - 1
        assert offspring.record.rng.counter == 2 + generation * 12
        bound = bind(offspring)
        selected = GenerationReducer(bound).collect(results(bound))
        traces.append(selected.encode())
        assert selected.record.progress.generations_completed == generation
    assert selected.record.phase == "stopped" and selected.record.stop_reason == "generation_budget"
    assert SuccessorPopulation(bind(selected)).create() == selected
    assert GenerationReducer(bind(selected)).collect(()) == selected
    assert len(set(traces)) == 2


def test_duplicate_generation_consumes_draws_without_evaluation_and_stagnates():
    spec = original(unchanged=1, mutation=0.0, crossover=0.0)
    initial = bind(InitialPopulation.generate(spec).checkpoint())
    selected = GenerationReducer(initial).collect(results(initial))
    successor = SuccessorPopulation(bind(selected)).create()
    assert successor.record.phase == "ready_to_select"
    assert not successor.record.pending
    assert successor.record.progress.evaluations_issued == 2
    assert [a.disposition for a in successor.record.attempts[-2:]] == ["duplicate", "duplicate"]
    bound = bind(successor)
    assert bound.request_batch().requests == ()
    stopped = GenerationReducer(bound).collect(())
    assert stopped.record.stop_reason == "unchanged_front"
    assert stopped.record.progress.unchanged_front_generations == 1


@pytest.mark.parametrize("generations,evaluations,reason", [(0, 20, "generation_budget"), (2, 2, "evaluation_budget")])
def test_initial_selection_terminal_budgets(generations, evaluations, reason):
    initial = bind(InitialPopulation.generate(original(generations=generations, evaluations=evaluations)).checkpoint())
    stopped = GenerationReducer(initial).collect(results(initial))
    assert stopped.record.stop_reason == reason
    assert len(stopped.record.population) == 2


def test_budget_limited_offspring_retains_rejected_attempt():
    initial = bind(InitialPopulation.generate(original(evaluations=3)).checkpoint())
    selected = GenerationReducer(initial).collect(results(initial))
    successor = SuccessorPopulation(bind(selected)).create()
    assert len(successor.record.pending) == 1
    assert successor.record.attempts[-1].disposition == "rejected"
    assert successor.record.attempts[-1].reason_code == "evaluation_budget"
    bound = bind(successor)
    assert GenerationReducer(bound).collect(results(bound)).record.stop_reason == "evaluation_budget"


def test_infeasible_and_missing_fitness_remain_explicit():
    initial = bind(InitialPopulation.generate(original()).checkpoint())
    infeasible = GenerationReducer(initial).collect(results(initial, violation=1.0))
    assert infeasible.record.stop_reason == "no_feasible_candidates" and not infeasible.record.population
    missing = MissingValue(kind="missing", member_id="0", reason_code="tool_failed")
    stopped = GenerationReducer(initial).collect((missing, results(initial)[1]))
    assert stopped.record.stop_reason == "unavailable_fitness"
    assert {o.outcome.status for o in stopped.record.observations} == {"evaluated", "failed"}
    assert not stopped.record.pending


def test_partial_duplicate_or_mispositioned_results_reject():
    initial = bind(InitialPopulation.generate(original()).checkpoint())
    outcomes = results(initial)
    with pytest.raises(ValueError, match="terminal_result_count"):
        GenerationReducer(initial).collect(outcomes[:1])
    with pytest.raises(ValueError, match="duplicate_observation"):
        GenerationReducer(initial).collect((outcomes[0], outcomes[0]))
    with pytest.raises(ValueError, match="missing_result_position"):
        GenerationReducer(initial).collect((MissingValue(kind="missing", member_id="1", reason_code="tool_failed"), outcomes[1]))


def test_unselected_generation_cannot_vary_and_selected_cannot_recollect():
    initial = bind(InitialPopulation.generate(original()).checkpoint())
    with pytest.raises(ValueError, match="variation_source_phase"):
        SuccessorPopulation(initial).create()
    selected = bind(GenerationReducer(initial).collect(results(initial)))
    with pytest.raises(ValueError, match="reduction_source_phase"):
        GenerationReducer(selected).collect(())
