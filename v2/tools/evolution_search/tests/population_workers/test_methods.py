"""Numerical method fixtures bind to the frozen candidate/method, not dispatch order."""

import hashlib
import math
from types import SimpleNamespace

import pytest
from amphora_contracts_core import ArtifactRef
from amphora_contracts_population_steps import (
    PopulationMemberSlice, PopulationSliceRequest, SeedPopulationRequest, population_step_schema,
)
from amphora_contracts_search import ObjectiveValue
from amphora_evolution_search.population import OriginalPopulation, canonical
from amphora_evolution_search.population_workers.artifacts import PopulationArtifacts
from amphora_evolution_search.population_workers.capabilities import PopulationCapability
from amphora_evolution_search.population_workers.seed import SeedPreparation
from amphora_evolution_search.population_workers.slices import SeedSlices
from amphora_evolution_search.population_workers.worker import PopulationWorker


def method_context(e, operation="evaluate-squares", *, unit="dimensionless", output_mismatch=False):
    capability = PopulationCapability(operation)
    worker = PopulationWorker(SimpleNamespace(identity=e.client.identity), e.client, capability, "f" * 64)
    methods = []
    for index, method in enumerate(e.original.record.method_graph.methods):
        profile = PopulationCapability("evaluate-squares" if index == 0 else "evaluate-negative-sum")
        methods.append(method.model_copy(update={"tool": profile.descriptor("f" * 64).tool.binding,
            "input_schema": profile.schema_ref("input"), "output_schema": profile.schema_ref("output")}))
    if output_mismatch:
        index = 0 if operation == "evaluate-squares" else 1
        methods[index] = methods[index].model_copy(update={"output_schema": methods[index].output_schema.model_copy(update={"sha256": "e" * 64})})
    objectives = tuple(binding.model_copy(update={"objective": binding.objective.model_copy(update={"unit": unit})})
                       for binding in e.original.record.assembly.objectives)
    original = OriginalPopulation(e.original.record.model_copy(update={"implementations": (worker.implementation,),
        "method_graph": e.original.record.method_graph.model_copy(update={"methods": tuple(methods)}),
        "assembly": e.original.record.assembly.model_copy(update={"objectives": objectives}),
        "budget": e.original.record.budget.model_copy(update={"population_size": 4, "dispatch_slice": 4})}))
    raw = canonical(original.record)
    source = e.source.model_copy(update={"sha256": hashlib.sha256(raw).hexdigest(), "size_bytes": len(raw)})
    e.client.contents[source.artifact_id] = raw
    session = PopulationArtifacts(e.client, e.attempt, worker.implementation)
    root = SeedPreparation.load(SeedPopulationRequest(schema_version="1", specification=source), session).publish(session)
    loaded = SeedSlices.load(root.reference, session)
    sliced = loaded.publish(PopulationSliceRequest(schema_version="1", prepared=root.reference, start_index=0, limit=4), session)
    record = sliced.decode(PopulationMemberSlice, population_step_schema("population-step.member-slice"), e.original.record.scope)
    e.attempt.invocation.inputs = (SimpleNamespace(port="parameters", artifact=record.members[0]),)
    e.attempt.invocation.node_id = methods[0 if operation == "evaluate-squares" else 1].node_path[-1]
    return worker, loaded, record


@pytest.mark.parametrize("operation", ["evaluate-squares", "evaluate-negative-sum"])
def test_method_result_uses_exact_frozen_genes_and_retains_sources(worker_artifacts, operation):
    e = worker_artifacts
    worker, loaded, record = method_context(e, operation)
    outcome = worker.execute(e.attempt)
    assert outcome["status"] == "succeeded"
    reference = ArtifactRef.model_validate(outcome["outputs"][0]["artifact"])
    result = ObjectiveValue.model_validate_json(e.client.contents[reference.artifact_id])
    context = loaded.prepared.slice(0, 4).contexts[0]
    from amphora_contracts_population import CandidateBirth
    birth = CandidateBirth.model_validate_json(e.client.contents[context.member.birth.artifact_id])
    expected = math.fsum(g * g for g in birth.genes) if operation == "evaluate-squares" else -math.fsum(birth.genes)
    assert result.value == expected and result.objective_id == "cost" and result.unit == "dimensionless"
    parents = e.client.parents[reference.artifact_id]
    assert record.members[0] in parents and context.member.birth in parents
    assert context.specification in parents and context.declarations in parents
    assert e.client.uploads[reference.artifact_id][1].transformation.transformation_id == worker.tool.binding.capability_id


def test_method_rejects_wrong_node_occurrence_without_publishing(worker_artifacts):
    e = worker_artifacts
    worker, _, _ = method_context(e)
    e.attempt.invocation.node_id = "wrong-method"
    before = len(e.client.calls)
    assert worker.execute(e.attempt)["status"] == "failed"
    assert len(e.client.calls) == before


@pytest.mark.parametrize("options", [{"unit": "kelvin"}, {"output_mismatch": True}])
def test_method_rejects_incompatible_units_or_result_schema(worker_artifacts, options):
    e = worker_artifacts
    worker, _, _ = method_context(e, **options)
    before = len(e.client.calls)
    assert worker.execute(e.attempt)["status"] == "failed"
    assert len(e.client.calls) == before


def test_reference_backed_input_schemas_keep_existing_public_pins():
    for operation, input_name, output_name in (("seed", "population-step.seed", "population-step.prepared"),
            ("slice", "population-step.slice-request", "population-step.member-slice")):
        capability = PopulationCapability(operation)
        assert capability.schema_ref("input") == population_step_schema(input_name)
        assert capability.schema_ref("output") == population_step_schema(output_name)
