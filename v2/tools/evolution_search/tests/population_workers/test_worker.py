"""Tool-owned worker dispatch and exact descriptors; scripted clients only."""

import hashlib
from types import SimpleNamespace

import pytest
from amphora_contracts_core import ArtifactRef
from amphora_contracts_population_steps import SeedPopulationRequest
from amphora_evolution_search.population import OriginalPopulation, canonical
from amphora_evolution_search.population_workers.capabilities import PopulationCapability
from amphora_evolution_search.population_workers.worker import PopulationWorker


@pytest.mark.parametrize("operation", ["seed", "slice"])
def test_capability_schemas_match_public_pins_and_legacy_is_separate(operation):
    capability = PopulationCapability(operation)
    descriptor = capability.descriptor("d" * 64)
    assert descriptor.tool.binding.capability_id == "numeric.population-" + operation
    assert descriptor.authority_ceiling == "synthetic_only" and descriptor.egress.mode == "deny"
    for direction in ("input", "output"):
        assert hashlib.sha256(capability.schema_bytes(direction)).hexdigest() == capability.schema_ref(direction).sha256
    with pytest.raises(ValueError):
        PopulationCapability("collect")


def worker_input(e):
    capability = PopulationCapability("seed")
    worker = PopulationWorker(SimpleNamespace(identity=e.client.identity), e.client, capability, "d" * 64)
    original = OriginalPopulation(e.original.record.model_copy(update={"implementations": (worker.implementation,)}))
    raw = canonical(original.record)
    source = e.source.model_copy(update={"sha256": hashlib.sha256(raw).hexdigest(), "size_bytes": len(raw)})
    e.client.contents[source.artifact_id] = raw
    request = canonical(SeedPopulationRequest(schema_version="1", specification=source))
    reference = ArtifactRef(artifact_id="admitted-input", scope=e.client.identity.scope,
        sha256=hashlib.sha256(request).hexdigest(), size_bytes=len(request), media_type="application/json",
        schema_ref=capability.schema_ref("input"))
    e.client.contents[reference.artifact_id] = request
    e.attempt.invocation.inputs = (SimpleNamespace(port="parameters", artifact=reference),)
    e.attempt.invocation.checkpoint = None
    return worker, reference


def test_worker_executes_seed_and_retains_admitted_carrier(worker_artifacts):
    e = worker_artifacts
    worker, source = worker_input(e)
    outcome = worker.execute(e.attempt)
    assert outcome["status"] == "succeeded"
    output = ArtifactRef.model_validate(outcome["outputs"][0]["artifact"])
    assert output.schema_ref == worker.capability.schema_ref("output")
    assert source in e.client.parents[output.artifact_id]


def test_worker_rejects_input_port_before_publication(worker_artifacts):
    e = worker_artifacts
    worker, _ = worker_input(e)
    e.attempt.invocation.inputs[0].port = "wrong"
    assert worker.execute(e.attempt) == {"status": "failed",
        "reason_code": "population_input_binding_mismatch", "retryable": False}
    assert e.client.calls == []


def test_worker_never_masks_lost_authority_as_invalid_input(worker_artifacts):
    e = worker_artifacts
    worker, _ = worker_input(e)
    e.attempt.live = False
    from amphora_tool_protocol import ProtocolError
    with pytest.raises(ProtocolError, match="authority_lost"):
        worker.execute(e.attempt)
    assert e.client.calls == []
