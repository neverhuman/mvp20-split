"""A new evaluator revision gets new candidates/evaluations; old rank bytes stay exact."""

import copy
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest
from amphora_contracts_search import EvaluationObservation, SearchSpec, search_checkpoint_schema, search_spec_schema
from amphora_contracts_search_steps import SearchStepContext
from amphora_evolution_search import BoundCheckpoint, CheckpointSnapshot, GenerationReducer, InitialPopulation, OriginalSearch

spec = importlib.util.spec_from_file_location("search_correction", Path(__file__).with_name("correction.py"))
C = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = C
spec.loader.exec_module(C)
M = C.M


def artifact(payload, scope, schema, identity):
    return {"artifact_id": identity, "scope": scope, "sha256": hashlib.sha256(payload).hexdigest(), "size_bytes": len(payload),
            "schema_ref": schema.model_dump(mode="json"), "media_type": "application/json"}


def bound(snapshot):
    raw = snapshot.encode()
    ref = artifact(raw, snapshot.record.specification.scope.model_dump(mode="json"), search_checkpoint_schema(), "seed")
    return BoundCheckpoint.from_context(SearchStepContext.model_validate_json(M.canonical({
        "original_specification": snapshot.record.specification.model_dump(mode="json"), "checkpoint": json.loads(raw), "checkpoint_artifact": ref})))


@pytest.fixture
def correction():
    path = Path(__file__).absolute().parents[3] / "tools/evolution_search/tests/specification/synthetic_specification.json"
    original = OriginalSearch(SearchSpec.model_validate_json(path.read_bytes()))
    state = bound(InitialPopulation.generate(original).checkpoint())
    request = state.request_batch().requests[0]
    observation = EvaluationObservation.model_validate_json(M.canonical({"schema_version": "1", "scope": request.scope.model_dump(mode="json"),
        "candidate_id": request.candidate.candidate_id, "evaluation_id": request.evaluation_id,
        "request_sha256": state.snapshot.record.pending[0].request_sha256,
        "outcome": {"status": "evaluated", "evaluator": request.evaluator.tool.model_dump(mode="json"),
                    "objectives": [{"objective_id": "cost", "unit": "dimensionless", "value": 1.0}],
                    "constraint_violation": 0.0, "constraints_sha256": request.evaluator.constraints.sha256,
                    "quality": "synthetic", "evidence": [request.evaluator.constraints.model_dump(mode="json")]}}))
    selected = GenerationReducer(state).collect((observation,))
    raw = selected.encode()
    previous = M.CheckpointEvidence.from_bytes(artifact(raw, original.record.scope.model_dump(mode="json"), search_checkpoint_schema(), "selected"), raw)
    new = original.record.model_dump(mode="json")
    new["search_id"] = "explicit-correction-revision"
    new["evaluator"]["tool"]["release"] = "0.2.0"
    return previous, new, observation


def prepare(previous, new, **kwargs):
    payload = M.canonical(new)
    ref = artifact(payload, new["scope"], search_spec_schema(), "new-specification")
    ref.update(kwargs)
    return C.CorrectionRevision.prepare(previous, ref, payload)


def test_correction_starts_explicit_revision_without_reusing_fitness(correction):
    previous, new, observation = correction
    original_bytes = M.canonical(previous.checkpoint.model_dump(mode="json"))
    decision = prepare(previous, new)
    record = decision.record()
    assert record["mode"] == "new_search_from_declared_seed" and record["resume"] is False
    assert record["fitness_reuse"] == "forbidden_evaluator_revision_changed"
    fresh = InitialPopulation.generate(OriginalSearch(decision.specification)).checkpoint()
    assert fresh.record.generation == 0 and fresh.record.observations == () and fresh.record.selection is None
    assert fresh.record.attempts[0].genes == previous.checkpoint.attempts[0].genes
    assert fresh.record.attempts[0].candidate_id != previous.checkpoint.attempts[0].candidate_id
    with pytest.raises(ValueError, match="original_specification"):
        CheckpointSnapshot.decode(OriginalSearch(decision.specification), original_bytes)
    with pytest.raises(ValueError):
        GenerationReducer(bound(fresh)).collect((observation,))
    assert M.canonical(previous.checkpoint.model_dump(mode="json")) == original_bytes
    assert record["prior"]["selection_sha256"] == hashlib.sha256(M.canonical(previous.checkpoint.selection.model_dump(mode="json"))).hexdigest()


@pytest.mark.parametrize("case,reason", [("id", "revision_identity"), ("tool", "evaluator_unchanged"),
    ("capability", "evaluator_contract"), ("scope", "correction_scope"), ("seed", "unrelated_specification_change"),
    ("objective", "unrelated_specification_change"), ("budget", "unrelated_specification_change"), ("bytes", "specification_bytes"),
    ("schema", "specification_schema")])
def test_correction_evidence_rejects_unpinned_or_unrelated_change(correction, case, reason):
    previous, new, _ = correction
    if case == "id": new["search_id"] = previous.checkpoint.specification.search_id
    if case == "tool": new["evaluator"]["tool"] = previous.checkpoint.specification.evaluator.tool.model_dump(mode="json")
    if case == "capability": new["evaluator"]["tool"]["capability_id"] = "other"
    if case == "scope": new["scope"] = {"tenant_id": "other", "project_id": "other"}
    if case == "seed": new["seed"] = "f" * 64
    if case == "objective": new["objectives"][0]["direction"] = "maximize"
    if case == "budget": new["budget"]["max_evaluations"] += 1
    changes = {"sha256": "f" * 64} if case == "bytes" else {"schema_ref": search_checkpoint_schema().model_dump(mode="json")} if case == "schema" else {}
    with pytest.raises(M.RecoveryMismatch, match=reason): prepare(previous, new, **changes)


def test_missing_original_rank_is_not_rewritten_as_a_correction(correction):
    previous, new, _ = correction
    initial = InitialPopulation.generate(OriginalSearch(previous.checkpoint.specification)).checkpoint()
    raw = initial.encode()
    unranked = M.CheckpointEvidence.from_bytes(artifact(raw, new["scope"], search_checkpoint_schema(), "unranked"), raw)
    with pytest.raises(M.RecoveryMismatch, match="original_rank_missing"): prepare(unranked, new)


def test_noncanonical_specification_does_not_alias_correction_identity(correction):
    previous, new, _ = correction
    raw = json.dumps(new, indent=2).encode()
    ref = artifact(raw, new["scope"], search_spec_schema(), "formatted")
    with pytest.raises(M.RecoveryMismatch, match="specification_canonical"):
        C.CorrectionRevision.prepare(previous, ref, raw)
