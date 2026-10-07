"""Reconstruction acceptance: public CLI descriptors and independent numeric oracles."""

import ast
import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
from importlib.metadata import version
from pathlib import Path

import pytest
from amphora_contracts_search import search_checkpoint_schema
from amphora_tool_protocol import ToolInputRejected

spec = importlib.util.spec_from_file_location("reconstructed_numeric_adapter", Path(__file__).with_name("rebuilt_adapter.py"))
A = importlib.util.module_from_spec(spec)
spec.loader.exec_module(A)
IMAGE = "a" * 64


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


@pytest.fixture(scope="module")
def descriptors():
    return {operation: subprocess.run([sys.executable, "-I", "-m", "amphora_evolution_search", "describe",
        "--operation", operation, "--image-sha256", IMAGE], capture_output=True, check=True, timeout=30).stdout
        for operation in A.INPUTS}


@pytest.fixture
def specification():
    path = Path(__file__).absolute().parents[3] / "tools/evolution_search/tests/specification/synthetic_specification.json"
    record = json.loads(path.read_bytes())
    record["implementations"] = [{"name": "numeric-search", "version": version("amphora-evolution-search"), "sha256": IMAGE}]
    return record


def adapter(operation, descriptors):
    result = A.ReconstructedAdapter(operation, descriptors[operation])
    result.descriptor(IMAGE)
    return result


def context(raw):
    record = json.loads(raw)
    artifact = {"scope": record["specification"]["scope"], "artifact_id": "cp-" + hashlib.sha256(raw).hexdigest()[:16],
                "sha256": hashlib.sha256(raw).hexdigest(), "size_bytes": len(raw), "media_type": "application/json",
                "schema_ref": search_checkpoint_schema().model_dump(mode="json")}
    return {"original_specification": record["specification"], "checkpoint": record, "checkpoint_artifact": artifact}


def test_rebuilt_adapter_preserves_four_operation_results(descriptors, specification):
    seed = adapter("seed", descriptors).execute(encoded(specification))
    state = json.loads(seed)
    # Independent published SHA256-counter first-draw vector.
    assert state["attempts"][0]["genes"] == [5377210515782559 / 9007199254740992]
    assert state["rng"]["counter"] == 1 and state["progress"]["evaluations_issued"] == 1
    ctx = context(seed)
    batch = json.loads(adapter("requests", descriptors).execute(encoded(ctx)))
    request = batch["requests"][0]
    request_hash = hashlib.sha256(encoded(request)).hexdigest()
    assert state["pending"][0]["request_sha256"] == request_hash
    observation = {"schema_version": "1", "scope": request["scope"], "evaluation_id": request["evaluation_id"],
        "candidate_id": request["candidate"]["candidate_id"], "request_sha256": request_hash,
        "outcome": {"status": "evaluated", "evaluator": request["evaluator"]["tool"],
            "objectives": [{"objective_id": "cost", "unit": "dimensionless", "value": 0.5}], "constraint_violation": 0.0,
            "constraints_sha256": request["evaluator"]["constraints"]["sha256"], "quality": "synthetic", "evidence": [request["evaluator"]["constraints"]]}}
    selected = adapter("collect", descriptors).execute(encoded(dict(ctx, results=[observation])))
    ranked = json.loads(selected)
    assert ranked["population"] == [request["candidate"]["candidate_id"]]
    assert ranked["selection"]["ranks"] == [{"candidate_id": ranked["population"][0], "front": 0, "boundary": False, "distance": 0.0, "feasible": True}]
    varied = json.loads(adapter("vary", descriptors).execute(encoded(context(selected))))
    assert varied["generation"] == 1 and varied["previous"] == context(selected)["checkpoint_artifact"]
    assert ranked["observations"] == [observation] and not seed.endswith(b"\n")


@pytest.mark.parametrize("case", ["unbound", "image", "version", "size", "json", "type", "restore"])
def test_rebuilt_failures_are_closed_and_do_not_echo_inputs(descriptors, specification, case):
    worker = adapter("seed", descriptors)
    if case == "unbound": worker.bound = False
    if case == "image": specification["implementations"][0]["sha256"] = "b" * 64
    if case == "version": specification["implementations"][0]["version"] = "0.0.0"
    raw = encoded(specification)
    if case == "size": raw = b"sensitive" * 40000
    if case == "json": raw = b"sensitive"
    if case == "type": raw = "sensitive"
    if case == "restore":
        ctx = context(worker.execute(raw));ctx["checkpoint"]["rng"]["counter"] = 999
        worker = adapter("requests", descriptors);raw = encoded(ctx)
    with pytest.raises(ToolInputRejected, match="^invalid_numeric_search_step$"):
        worker.execute(raw)


def test_descriptor_cannot_change_operation_release_or_image(descriptors):
    with pytest.raises(ValueError, match="rebuild_operation"): A.ReconstructedAdapter("unknown", descriptors["seed"])
    with pytest.raises(ValueError, match="rebuild_descriptor"): A.ReconstructedAdapter("vary", descriptors["seed"])
    worker = adapter("seed", descriptors)
    with pytest.raises(ValueError, match="rebuild_image"): worker.descriptor("b" * 64)
    raw = json.loads(descriptors["seed"]);raw["tool"]["binding"]["release"] = "999.0.0"
    with pytest.raises(ValueError, match="rebuild_descriptor"): A.ReconstructedAdapter("seed", encoded(raw))


def test_reconstruction_imports_no_private_adapter_or_owner_state():
    tree = ast.parse(Path(A.__file__).read_text())
    imports = [node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
    assert not any(name.startswith(("amphora_campaign_runtime", "amphora_data_artifacts", "amphora_evolution_search.")) for name in imports)
    assert "amphora_evolution_search" in imports and "amphora_tool_protocol" in imports


def test_standalone_reconstruction_emits_original_public_bytes(descriptors, specification, tmp_path):
    path = tmp_path / "descriptor.json";path.write_bytes(descriptors["seed"])
    command = [sys.executable, "-I", A.__file__, "compute", "--operation", "seed", "--descriptor", str(path), "--image-sha256", IMAGE]
    result = subprocess.run(command, input=encoded(specification), capture_output=True, timeout=30)
    assert result.returncode == 0 and result.stdout == adapter("seed", descriptors).execute(encoded(specification))
    rejected = subprocess.run(command, input=b"private-fixture", capture_output=True, timeout=30)
    assert rejected.returncode == 2 and rejected.stderr.strip() == b"invalid_numeric_input_or_configuration" and not rejected.stdout
