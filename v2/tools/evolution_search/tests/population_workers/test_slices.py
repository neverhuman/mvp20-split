"""Reference-backed slicing validates the whole frozen cohort before batching."""

from types import SimpleNamespace

import pytest
from amphora_contracts_population_steps import (
    PopulationMemberSlice, PopulationSliceRequest, SeedPopulationRequest, population_step_schema,
)
from amphora_contracts_population import population_specification_schema
from amphora_evolution_search.population import OriginalPopulation, canonical
from amphora_evolution_search.population_workers.artifacts import PopulationArtifacts
from amphora_evolution_search.population_workers.seed import SeedPreparation
from amphora_evolution_search.population_workers.slices import SeedSlices

from .conftest import Attempt


def prepared(e, population=16):
    import hashlib
    original = OriginalPopulation(e.original.record.model_copy(update={"budget": e.original.record.budget.model_copy(
        update={"population_size": population, "dispatch_slice": 32})}))
    raw = canonical(original.record)
    e.source = e.source.model_copy(update={"sha256": hashlib.sha256(raw).hexdigest(), "size_bytes": len(raw)})
    e.client.contents[e.source.artifact_id] = raw
    return SeedPreparation.load(SeedPopulationRequest(schema_version="1", specification=e.source), e.session).publish(e.session)


def test_batch_sizes_preserve_identical_candidate_context_bytes(worker_artifacts):
    e = worker_artifacts
    root = prepared(e)
    loaded = SeedSlices.load(root.reference, e.session)
    fingerprints = []
    for limit in (1, 8, 32):
        contexts, start = [], 0
        while True:
            attempt = Attempt()
            attempt.invocation.attempt_id = f"slice-{limit}-{start}"
            session = PopulationArtifacts(e.client, attempt, e.session.implementation)
            request = PopulationSliceRequest(schema_version="1", prepared=root.reference, start_index=start, limit=limit)
            result = loaded.publish(request, session).decode(PopulationMemberSlice,
                population_step_schema("population-step.member-slice"), e.original.record.scope)
            contexts.extend(e.client.contents[ref.artifact_id] for ref in result.members)
            assert result.next_index == start + len(result.members)
            if result.complete:
                break
            assert result.next_index > start
            start = result.next_index
        fingerprints.append(contexts)
    assert len(fingerprints[0]) == 16
    assert fingerprints[0] == fingerprints[1] == fingerprints[2]


def test_terminal_empty_slice_is_truthful_and_bound_to_source(worker_artifacts):
    e = worker_artifacts
    root = prepared(e)
    loaded = SeedSlices.load(root.reference, e.session)
    request = PopulationSliceRequest(schema_version="1", prepared=root.reference, start_index=16, limit=32)
    result = loaded.publish(request, e.session).decode(PopulationMemberSlice,
        population_step_schema("population-step.member-slice"), e.original.record.scope)
    assert result.members == () and result.complete and result.next_index == 16
    with pytest.raises(ValueError, match="dispatch_start"):
        loaded.publish(request.model_copy(update={"start_index": 17}), e.session)


def test_cross_run_preparation_is_rejected(worker_artifacts):
    e = worker_artifacts
    root = prepared(e)
    e.attempt.invocation.run_id = "different-run"
    before = len(e.client.calls)
    with pytest.raises(ValueError, match="slice_seed_run"):
        SeedSlices.load(root.reference, e.session)
    assert len(e.client.calls) == before


def test_admitted_input_carrier_is_declared_automatically(worker_artifacts):
    e = worker_artifacts
    root = prepared(e)
    e.attempt.invocation.inputs = (SimpleNamespace(artifact=root.reference),)
    from amphora_evolution_search.population import NumericBirth
    from amphora_contracts_population import candidate_birth_schema
    artifact = e.session.publish(NumericBirth.seed(e.original, 0).record,
        candidate_birth_schema(), (e.source,), "explicit-carrier")
    assert {ref.artifact_id for ref in e.client.parents[artifact.reference.artifact_id]} == {
        root.reference.artifact_id, e.source.artifact_id}
