import json

import pytest
from amphora_contracts_search import SearchSpec
from amphora_evolution_search import (
    CheckpointSnapshot,
    InitialPopulation,
    OriginalSearch,
)


@pytest.mark.parametrize("path,value", [
    (("schema_version",), "2"), (("rng", "algorithm"), "splitmix64"),
    (("rng", "counter"), True), (("rng", "counter"), -1),
    (("rng", "counter"), 9007199254740992), (("rng", "seed"), "bad"),
    (("specification", "operators", "variation"), "unreviewed-variation"),
    (("specification", "implementations", 0, "version"), "unreviewed"),
    (("attempts", 0, "genes", 0), float("nan")),
])
def test_corrupt_or_changed_wire_state_rejects(checkpoint_data, original_search, path, value):
    target = checkpoint_data
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    with pytest.raises(ValueError):
        CheckpointSnapshot.decode(original_search, json.dumps(checkpoint_data).encode())


@pytest.mark.parametrize("kind", ["pending", "observations", "both"])
def test_repeated_terminal_or_pending_identity_rejects(evaluated_data, original_search, decode_record, kind):
    observation = evaluated_data["observations"][0]
    pending = {key: observation[key] for key in ("candidate_id", "evaluation_id", "request_sha256")}
    if kind == "observations":
        evaluated_data["observations"] *= 2
    elif kind == "pending":
        evaluated_data.update(observations=[], pending=[pending, pending], phase="awaiting_evaluations")
    else:
        evaluated_data["pending"] = [pending]
    with pytest.raises(ValueError, match="duplicate_|pending_terminal_overlap"):
        CheckpointSnapshot(original_search, decode_record(evaluated_data))


def test_forged_rank_and_unselected_population_reject(selected_data, original_search, decode_record):
    selected_data["selection"]["ranks"][0]["front"] = 1
    with pytest.raises(ValueError, match="selection_receipt"):
        CheckpointSnapshot(original_search, decode_record(selected_data))
    selected_data.update(selection=None, phase="ready_to_select")
    with pytest.raises(ValueError, match="unselected_population"):
        CheckpointSnapshot(original_search, decode_record(selected_data))


@pytest.mark.parametrize("reason,code", [("generation_budget", "false_generation_stop"),
                                        ("unchanged_front", "false_stagnation_stop"),
                                        ("no_feasible_candidates", "false_no_feasible"),
                                        ("unavailable_fitness", "false_unavailable")])
def test_false_stop_reasons_reject(selected_data, original_search, decode_record, reason, code):
    selected_data.update(phase="stopped", stop_reason=reason)
    with pytest.raises(ValueError, match=code):
        CheckpointSnapshot(original_search, decode_record(selected_data))


def test_duplicate_target_must_be_retained(original_search, decode_record):
    data = original_search.record.model_dump(mode="json")
    data["budget"]["population_size"] = 3
    data["variables"][0].update(lower=2.0, upper=2.0)
    original = OriginalSearch(SearchSpec.model_validate_json(json.dumps(data)))
    state = InitialPopulation.generate(original).checkpoint().record.model_dump(mode="json")
    state["attempts"][1]["duplicate_of"] = "f" * 64
    with pytest.raises(ValueError, match="missing_duplicate"):
        CheckpointSnapshot(original, decode_record(state))


def test_missing_initial_attempt_rejects(original_search, decode_record):
    data = original_search.record.model_dump(mode="json")
    data["budget"]["population_size"] = 3
    original = OriginalSearch(SearchSpec.model_validate_json(json.dumps(data)))
    state = InitialPopulation.generate(original).checkpoint().record.model_dump(mode="json")
    state["attempts"].pop()
    state["pending"].pop()
    state["rng"]["counter"] = 2
    state["progress"]["evaluations_issued"] = 2
    with pytest.raises(ValueError, match="seed_population_size"):
        CheckpointSnapshot(original, decode_record(state))
