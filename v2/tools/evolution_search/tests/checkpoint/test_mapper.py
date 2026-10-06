import json

import pytest
from amphora_evolution_search import CheckpointSnapshot


def test_portable_pending_roundtrip(checkpoint_data, original_search, decode_record):
    saved = CheckpointSnapshot(original_search, decode_record(checkpoint_data))
    assert CheckpointSnapshot.decode(original_search, saved.encode()) == saved
    assert saved.record.rng.counter == 1
    assert len(saved.record.pending) == 1


def test_ready_and_independently_constructed_selection(evaluated_data, selected_data, original_search, decode_record):
    assert CheckpointSnapshot(original_search, decode_record(selected_data)).record.population


@pytest.mark.parametrize("path,value,code", [
    (("specification_sha256",), "f" * 64, "original_specification"),
    (("rng", "seed"), "f" * 64, "rng_original_seed"),
    (("rng", "counter"), 0, "future_draw"),
    (("rng", "counter"), 2, "rng_tail"),
    (("attempts", 0, "candidate_id"), "f" * 64, "attempt_identity"),
    (("attempts", 0, "reason_code"), "invented", "proposed_disposition"),
    (("pending",), [], "evaluation_membership"),
    (("pending", 0, "evaluation_id"), "different", "evaluation_identity"),
    (("pending", 0, "request_sha256"), "f" * 64, "evaluation_request_binding"),
    (("population",), ["f" * 64], "population_membership"),
    (("progress", "evaluations_terminal"), 1, "pending_progress"),
    (("progress", "evaluations_issued"), 5, "evaluation_progress"),
    (("progress", "generations_completed"), 1, "generation_progress"),
    (("progress", "unchanged_front_generations"), 1, "stagnation_progress"),
    (("phase",), "selected", "unfinished_evaluations"),
    (("stop_reason",), "evaluation_budget", "stop_phase"),
])
def test_intrinsic_inconsistency_rejects(checkpoint_data, original_search, decode_record, path, value, code):
    target = checkpoint_data
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    with pytest.raises(ValueError, match=code):
        CheckpointSnapshot(original_search, decode_record(checkpoint_data))


@pytest.mark.parametrize("path,value,code", [
    (("scope", "project_id"), "elsewhere", "observation_scope"),
    (("outcome", "evaluator", "release"), "0.2.0", "fitness_evaluator"),
    (("outcome", "constraints_sha256"), "f" * 64, "fitness_constraints"),
    (("outcome", "objectives", 0, "unit"), "kg", "fitness_objectives"),
    (("outcome", "objectives", 0, "objective_id"), "yield", "fitness_objectives"),
    (("outcome", "evidence", 0, "scope", "tenant_id"), "elsewhere", "fitness_evidence_scope"),
])
def test_fitness_binding_rejects(evaluated_data, original_search, decode_record, path, value, code):
    data = json.loads(json.dumps(evaluated_data))
    target = data["observations"][0]
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    with pytest.raises(ValueError, match=code):
        CheckpointSnapshot(original_search, decode_record(data))


@pytest.mark.parametrize("field,value", [("requested", 0), ("selected", []), ("membership_sha256", "f" * 64),
                                        ("disposition", "no_feasible_candidates")])
def test_selection_receipt_is_recomputed(selected_data, original_search, decode_record, field, value):
    selected_data["selection"][field] = value
    with pytest.raises(ValueError, match="selection_receipt"):
        CheckpointSnapshot(original_search, decode_record(selected_data))


def test_unknown_fitness_is_visible_but_cannot_be_ranked(selected_data, original_search, decode_record):
    selected_data["observations"][0]["outcome"] = {"status": "unknown", "reason_code": "no_measurement", "evidence": []}
    with pytest.raises(ValueError, match="unavailable_selection"):
        CheckpointSnapshot(original_search, decode_record(selected_data))
    selected_data.update(phase="stopped", stop_reason="unavailable_fitness", selection=None, population=[])
    assert CheckpointSnapshot(original_search, decode_record(selected_data)).record.stop_reason == "unavailable_fitness"


def test_no_false_budget_stop(selected_data, original_search, decode_record):
    selected_data.update(phase="stopped", stop_reason="evaluation_budget")
    with pytest.raises(ValueError, match="false_evaluation_stop"):
        CheckpointSnapshot(original_search, decode_record(selected_data))
