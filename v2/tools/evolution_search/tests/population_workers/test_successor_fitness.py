"""Parent fitness retains its historical generation and evidence without rescoring."""
from types import SimpleNamespace

import pytest
from amphora_evolution_search.population.membership import GenerationMembership
from amphora_evolution_search.population_workers.assembly import PrimaryAssembly
from amphora_evolution_search.population_workers.slices import SeedSlices

from .test_successor_source import consumer_fixture


def parent_only_case(e):
    fixture = consumer_fixture(e)
    loaded = SeedSlices.load(fixture.prepared, fixture.c.session, fixture.runtime())
    cohort = loaded.cohort.membership
    empty = GenerationMembership(cohort.original, cohort.identity, "cohort", ())
    subject = SimpleNamespace(prepared=SimpleNamespace(declarations=SimpleNamespace(membership=empty)),
        fitness=SimpleNamespace(records=lambda: ()), successor=loaded.successor)
    return subject, loaded.successor


def test_empty_offspring_preserves_all_selected_parent_fitness(worker_artifacts):
    subject, source = parent_only_case(worker_artifacts)
    pool = PrimaryAssembly.selection_pool(subject)
    expected = {item.record.candidate_id: item for item in source.fitness.selection.fitness
        if item.record.candidate_id in source.selected.decision.selected}
    assert len(pool.pool.members) == len(expected) == 4
    assert all(member.source == "parent" for member in pool.pool.members)
    assert pool.pool.identity.generation == 1
    for item in pool.fitness:
        assert item.record == expected[item.record.candidate_id].record
        assert item.evidence is expected[item.record.candidate_id].evidence
        assert item.record.generation.generation == 0


def test_missing_parent_fitness_cannot_disappear_from_the_union(worker_artifacts):
    subject, source = parent_only_case(worker_artifacts)
    subject.successor = SimpleNamespace(selected=source.selected,
        fitness=SimpleNamespace(selection=SimpleNamespace(fitness=source.fitness.selection.fitness[:-1])))
    with pytest.raises(ValueError, match="selection_fitness_coverage"):
        PrimaryAssembly.selection_pool(subject)


@pytest.mark.parametrize("generation", [0, 1])
def test_collection_adapter_only_extracts_successor_slice_requests(worker_artifacts, generation):
    from amphora_contracts_core import ArtifactRef
    from amphora_contracts_population_steps import PopulationSliceRequest, PopulationMemberSlice, population_step_schema
    from amphora_evolution_search.population_workers.capabilities import PopulationCapability
    from amphora_evolution_search.population_workers.method_plan import payload_schema
    from amphora_evolution_search.population_workers.payloads import CollectPrimaryRequest, CollectSuccessorSliceRequest
    from amphora_evolution_search.population_workers.successor_source import unique_carrier
    from amphora_evolution_search.population_workers.worker import PopulationWorker

    e = worker_artifacts
    fixture = consumer_fixture(e)
    loaded = SeedSlices.load(fixture.prepared, fixture.c.session, fixture.runtime())
    sliced = loaded.publish(PopulationSliceRequest(schema_version="1", prepared=fixture.prepared,
        start_index=0, limit=4), fixture.c.session)
    if generation == 0:
        record = sliced.decode(PopulationMemberSlice, population_step_schema("population-step.member-slice"), e.client.identity.scope)
        record = record.model_copy(update={"generation": fixture.c.source.prepared.record.generation})
        sliced = fixture.c.session.publish(record, population_step_schema("population-step.member-slice"),
            (fixture.prepared,), "test/old-slice")
    source = unique_carrier(fixture.c.source.request.resolution, CollectPrimaryRequest,
        payload_schema(CollectPrimaryRequest, "population-worker.collect-request"), fixture.c.session)
    capability = PopulationCapability("prepare-successor-collection")
    request = CollectSuccessorSliceRequest(schema_version="1", sliced=sliced.reference,
        execution_plan=source.execution_plan, method_plan=source.method_plan, method_scope_path=("successor_evaluate",))
    carrier = fixture.c.session.publish(request, capability.schema_ref("input"), (sliced.reference,), "test/adapter-input")
    worker = PopulationWorker(fixture.runtime(), e.client, capability, "f"*64)
    e.attempt.invocation.inputs = (SimpleNamespace(port="parameters", artifact=carrier.reference),)
    e.attempt.invocation.tool = worker.tool.binding
    outcome = worker.execute(e.attempt)
    assert outcome["status"] == ("succeeded" if generation == 1 else "failed")
    if generation == 1:
        reference = ArtifactRef.model_validate(outcome["outputs"][0]["artifact"])
        output = fixture.c.session.read(reference).decode(CollectPrimaryRequest,
            capability.schema_ref("output"), e.client.identity.scope)
        assert output.prepared == fixture.prepared and output.method_scope_path == ("successor_evaluate",)
        assert carrier.reference in e.client.parents[reference.artifact_id]
