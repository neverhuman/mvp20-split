import json
import subprocess
import sys
from hashlib import sha256
from importlib.metadata import version
from pathlib import Path
from types import SimpleNamespace

import pytest
from amphora_contracts_core import ArtifactRef
from amphora_contracts_search import (
    EvaluationObservation,
    SearchCheckpoint,
    search_checkpoint_schema,
    search_spec_schema,
)
from amphora_contracts_search_steps import EvaluationRequestBatch, SearchStepContext
from amphora_evolution_search.adapter import NumericWorkerAdapter
from amphora_evolution_search.capabilities import NumericCapability
from amphora_tool_protocol import PureToolWorker, ToolInputRejected
from jsonschema import Draft202012Validator

IMAGE = "a" * 64  # Descriptor fixture identity; not a built image claim.


def specification():
    data = json.loads((Path(__file__).parents[1] / "specification/synthetic_specification.json").read_bytes())
    data["implementations"] = [{"name": "numeric-search", "version": version("amphora-evolution-search"), "sha256": IMAGE}]
    return data


def adapter(operation):
    worker = NumericWorkerAdapter(operation)
    worker.descriptor(IMAGE)
    return worker


def context(payload):
    checkpoint = SearchCheckpoint.model_validate_json(payload)
    reference = ArtifactRef(artifact_id="checkpoint-fixture", scope=checkpoint.specification.scope,
                            sha256=sha256(payload).hexdigest(), size_bytes=len(payload), media_type="application/json",
                            schema_ref=search_checkpoint_schema())
    return SearchStepContext(original_specification=checkpoint.specification, checkpoint=checkpoint,
                             checkpoint_artifact=reference)


@pytest.mark.parametrize("operation", ["seed", "requests", "collect", "vary"])
def test_descriptors_fit_actual_sdk_pure_worker_profile(operation):
    capability = NumericCapability(operation)
    descriptor = capability.descriptor(IMAGE)
    runtime = SimpleNamespace(identity="test-worker")
    artifacts = SimpleNamespace(identity="test-worker")
    PureToolWorker(runtime, artifacts, descriptor, adapter(operation).execute)
    assert descriptor.tool.binding.capability_id == "numeric.search-" + operation
    assert descriptor.tool.checkpoint_schema is None
    assert descriptor.authority_ceiling == "synthetic_only"
    assert "synthetic-tests" in descriptor.tool.applicability
    for direction in ("input", "output"):
        raw = capability.schema_bytes(direction)
        assert sha256(raw).hexdigest() == capability.schema_ref(direction).sha256
        Draft202012Validator.check_schema(json.loads(raw))
    if operation == "seed":
        assert capability.schema_ref("input") == search_spec_schema()
    if operation != "requests":
        assert capability.schema_ref("output") == search_checkpoint_schema()


def test_four_capabilities_use_same_bound_original_and_preserve_output_schemas():
    seed = adapter("seed").execute(json.dumps(specification()).encode())
    current = context(seed)
    expanded = adapter("requests").execute(current.model_dump_json().encode())
    batch = EvaluationRequestBatch.model_validate_json(expanded)
    request = batch.requests[0]
    observation = EvaluationObservation.model_validate_json(json.dumps({
        "schema_version": "1", "scope": request.scope.model_dump(mode="json"),
        "evaluation_id": request.evaluation_id, "candidate_id": request.candidate.candidate_id,
        "request_sha256": current.checkpoint.pending[0].request_sha256,
        "outcome": {"status": "evaluated", "evaluator": request.evaluator.tool.model_dump(mode="json"),
                    "objectives": [{"objective_id": "cost", "unit": "dimensionless", "value": 0.5}],
                    "constraint_violation": 0.0, "constraints_sha256": request.evaluator.constraints.sha256,
                    "quality": "synthetic", "evidence": [request.evaluator.constraints.model_dump(mode="json")]}}))
    collect = current.model_dump(mode="json")
    collect["results"] = [observation.model_dump(mode="json")]
    selected = adapter("collect").execute(json.dumps(collect).encode())
    successor = adapter("vary").execute(context(selected).model_dump_json().encode())
    checkpoint = SearchCheckpoint.model_validate_json(successor)
    assert checkpoint.generation == 1 and checkpoint.previous == context(selected).checkpoint_artifact
    Draft202012Validator(json.loads(NumericCapability("vary").schema_bytes("output"))).validate(json.loads(successor))


@pytest.mark.parametrize("case", ["unbound", "wrong_image", "wrong_version", "oversized", "invalid_json"])
def test_safe_rejection_before_any_protocol_effect(case):
    worker = adapter("seed")
    data = specification()
    if case == "unbound":
        worker = NumericWorkerAdapter("seed")
    elif case == "wrong_image":
        data["implementations"][0]["sha256"] = "b" * 64
    elif case == "wrong_version":
        data["implementations"][0]["version"] = "0.0.0"
    raw = json.dumps(data).encode()
    if case == "oversized":
        raw = b"sensitive-fixture" * 20000
    elif case == "invalid_json":
        raw = b"sensitive-fixture"
    with pytest.raises(ToolInputRejected, match="^invalid_numeric_search_step$"):
        worker.execute(raw)


def test_adapter_cannot_rebind_to_another_image():
    worker = adapter("seed")
    with pytest.raises(ValueError, match="worker_image_changed"):
        worker.descriptor("b" * 64)


def test_cli_emits_exact_canonical_checkpoint_bytes_and_safe_errors():
    command = [sys.executable, "-m", "amphora_evolution_search", "compute", "--operation", "seed", "--image-sha256", IMAGE]
    raw = json.dumps(specification()).encode()
    result = subprocess.run(command, input=raw, capture_output=True, timeout=30, check=False)
    assert result.returncode == 0 and not result.stderr
    assert result.stdout == adapter("seed").execute(raw)
    assert not result.stdout.endswith(b"\n")
    failure = subprocess.run(command, input=b"sensitive-fixture", capture_output=True, timeout=30, check=False)
    assert failure.returncode == 2 and not failure.stdout
    assert failure.stderr.strip() == b"invalid_numeric_input_or_configuration"


def test_cli_descriptor_and_schema_profiles():
    command = [sys.executable, "-m", "amphora_evolution_search"]
    described = subprocess.run([*command, "describe", "--operation", "collect", "--image-sha256", IMAGE],
                               capture_output=True, check=True, timeout=30)
    assert json.loads(described.stdout)["tool"]["binding"]["capability_id"] == "numeric.search-collect"
    schema = subprocess.run([*command, "schema", "--operation", "collect", "--direction", "input"],
                            capture_output=True, check=True, timeout=30)
    assert schema.stdout == NumericCapability("collect").schema_bytes("input")


def test_invalid_capability_or_schema_direction_rejects():
    with pytest.raises(ValueError, match="unsupported_numeric_operation"):
        NumericCapability("anything")
    with pytest.raises(ValueError, match="unknown_payload_direction"):
        NumericCapability("seed").schema_bytes("other")
