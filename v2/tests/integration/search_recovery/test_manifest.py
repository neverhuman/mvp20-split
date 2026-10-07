"""Independent byte/identity and same-profile restore oracles."""

import copy
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest
from amphora_contracts_search import SearchSpec, search_checkpoint_schema
from amphora_evolution_search import CheckpointSnapshot, InitialPopulation, OriginalSearch

spec = importlib.util.spec_from_file_location("search_recovery_manifest", Path(__file__).with_name("manifest.py"))
M = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = M
spec.loader.exec_module(M)


@pytest.fixture
def original():
    path = Path(__file__).absolute().parents[3] / "tools/evolution_search/tests/specification/synthetic_specification.json"
    return OriginalSearch(SearchSpec.model_validate_json(path.read_bytes()))


def evidence(record, identity="baseline", *, raw=None):
    payload = M.canonical(record) if raw is None else raw
    artifact = {"scope": record["specification"]["scope"], "artifact_id": identity, "sha256": hashlib.sha256(payload).hexdigest(),
                "size_bytes": len(payload), "media_type": "application/json", "schema_ref": search_checkpoint_schema().model_dump(mode="json")}
    return artifact, payload


def snapshot(record, identity="baseline"):
    return M.CheckpointEvidence.from_bytes(*evidence(record, identity))


def test_same_profile_restore_preserves_every_byte_pending_identity_and_next_draw(original):
    original_bytes = InitialPopulation.generate(original).checkpoint().encode()
    restored = CheckpointSnapshot.decode(original, original_bytes)
    assert restored.encode() == original_bytes
    assert restored.record.pending and restored.record.rng == InitialPopulation.generate(original).checkpoint().record.rng
    left = snapshot(json.loads(original_bytes))
    right = snapshot(json.loads(original_bytes), "replacement")
    proof = M.CheckpointTrace([left]).equivalent(M.CheckpointTrace([right]))
    assert proof["equivalent"] and proof["authority"] == "synthetic_engineering_evidence_only"
    assert original.resume_random(restored.record.rng).draw() == original.resume_random(left.checkpoint.rng).draw()


@pytest.mark.parametrize("change,reason", [("hash", "checkpoint_content"), ("schema", "checkpoint_schema"),
    ("version", "checkpoint_profile"), ("shape", "checkpoint_shape"), ("scope", "checkpoint_scope"),
    ("spec", "checkpoint_specification_digest"), ("spacing", "checkpoint_canonical_bytes"), ("json", "checkpoint_json")])
def test_recovery_manifest_never_accepts_reidentified_or_unsupported_bytes(original, change, reason):
    record = InitialPopulation.generate(original).checkpoint().record.model_dump(mode="json")
    if change == "version": record["schema_version"] = "2"
    if change == "shape": record["rng"]["counter"] = -1
    if change == "spec": record["specification_sha256"] = "f" * 64
    raw = json.dumps(record).encode() if change == "spacing" else b"{" if change == "json" else None
    artifact, payload = evidence(record, raw=raw)
    if change == "hash": artifact["sha256"] = "e" * 64
    if change == "schema": artifact["schema_ref"]["sha256"] = "d" * 64
    if change == "scope": artifact["scope"] = {"tenant_id": "foreign", "project_id": "foreign"}
    with pytest.raises(M.RecoveryMismatch, match=reason):
        M.CheckpointEvidence.from_bytes(artifact, payload)


@pytest.mark.parametrize("field", ["seed", "evaluator", "operators", "implementations"])
def test_changed_original_never_resumes_or_silently_reseeds(original, field):
    payload = InitialPopulation.generate(original).checkpoint().encode()
    changed = original.record.model_dump(mode="json")
    if field == "seed": changed[field] = "f" * 64
    if field == "evaluator": changed[field]["tool"]["release"] = "999.0.0"
    if field == "operators": changed[field]["mutation_fraction"] = 0.25
    if field == "implementations": changed[field][0]["version"] = "999.0.0"
    new = OriginalSearch(SearchSpec.model_validate_json(json.dumps(changed)))
    with pytest.raises(ValueError, match="original_specification"):
        CheckpointSnapshot.decode(new, payload)
    assert CheckpointSnapshot.decode(original, payload).encode() == payload


def test_trace_rejects_missing_prefix_changed_rng_or_chain(original):
    record = InitialPopulation.generate(original).checkpoint().record.model_dump(mode="json")
    first = snapshot(record)
    with pytest.raises(M.RecoveryMismatch, match="trace_empty"): M.CheckpointTrace([])
    second_record = copy.deepcopy(record)
    second_record["previous"] = first.artifact.model_dump(mode="json")
    second = snapshot(second_record, "second")
    trace = M.CheckpointTrace([first, second])
    with pytest.raises(M.RecoveryMismatch, match="trace_length"): trace.equivalent(M.CheckpointTrace([first]))
    with pytest.raises(M.RecoveryMismatch, match="trace_origin"): M.CheckpointTrace([second])
    with pytest.raises(M.RecoveryMismatch, match="checkpoint_chain"): M.CheckpointTrace([first, first])
    second_record["rng"]["counter"] += 1
    with pytest.raises(M.RecoveryMismatch, match="checkpoint_replay_changed:1"):
        trace.equivalent(M.CheckpointTrace([first, snapshot(second_record, "changed")]))


@pytest.mark.parametrize("change,reason", [("revision", "checkpoint_revision_mixed"), ("rng", "checkpoint_progress_reversed")])
def test_trace_rejects_revision_mix_and_reversed_progress(original, change, reason):
    record = InitialPopulation.generate(original).checkpoint().record.model_dump(mode="json")
    first = snapshot(record)
    later = copy.deepcopy(record)
    later["previous"] = first.artifact.model_dump(mode="json")
    if change == "revision":
        later["specification"]["evaluator"]["tool"]["release"] = "999.0.0"
        later["specification_sha256"] = hashlib.sha256(M.canonical(later["specification"])).hexdigest()
    else:
        later["rng"]["counter"] = 0
    with pytest.raises(M.RecoveryMismatch, match=reason):
        M.CheckpointTrace([first, snapshot(later, "later")])


def test_invalid_artifact_shape_is_named_without_echoing_data(original):
    record = InitialPopulation.generate(original).checkpoint().record.model_dump(mode="json")
    artifact, payload = evidence(record)
    artifact["schema_ref"]["version"] = "unsupported"
    with pytest.raises(M.RecoveryMismatch, match="^checkpoint_artifact_shape$"):
        M.CheckpointEvidence.from_bytes(artifact, payload)
