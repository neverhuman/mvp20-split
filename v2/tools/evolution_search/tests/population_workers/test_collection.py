"""Frozen coverage and actual numerical outputs through the public inspection reader."""
import copy

import pytest
from amphora_contracts_population import EvaluationResolutionManifest,population_record_schema
from amphora_evolution_search.population.retained import RetainedEvaluations
from amphora_evolution_search.population_workers.collection import PrimaryCollection
from amphora_evolution_search.population_workers.payloads import CollectedPrimaryGeneration
from amphora_evolution_search.population_workers.method_plan import payload_schema

from .collection_fixture import fixture


@pytest.mark.parametrize("status",["succeeded","failed","skipped","blocked"])
def test_whole_primary_collection_keeps_terminal_outcomes_and_retained_evidence(worker_artifacts,status):
    e=worker_artifacts;c=fixture(e,status)
    collected=PrimaryCollection.load(c.request,c.session,c.runtime)
    assert len(collected.keys)==len(collected.observations)==4
    assert sum(row.outcome.status=="evaluated" for row in collected.observations)==(4 if status=="succeeded" else 3)
    unavailable=tuple(row for row in collected.observations if row.outcome.status!="evaluated")
    if unavailable:assert unavailable[0].outcome.status==("failed" if status=="failed" else "inapplicable" if status=="skipped" else "unknown")
    result=collected.publish(c.request,c.session)
    record=result.decode(CollectedPrimaryGeneration,payload_schema(CollectedPrimaryGeneration,"population-worker.collected"),e.client.identity.scope)
    from amphora_evolution_search.population.retained import PopulationArtifact
    def read(ref):return PopulationArtifact(ref,e.client.contents[ref.artifact_id])
    evaluation=read(record.evaluations)
    from amphora_contracts_population import EvaluationManifest
    manifest=evaluation.decode(EvaluationManifest,population_record_schema("population.evaluation-manifest"),e.client.identity.scope)
    retained=RetainedEvaluations.verify(c.prepared.declarations.membership,c.prepared.record.cohort,evaluation,
        tuple(read(page.artifact).content for page in manifest.pages))
    resolution=read(record.resolution).decode(EvaluationResolutionManifest,population_record_schema("population.evaluation-resolution"),e.client.identity.scope)
    c.prepared.declarations.verify_resolution(record.declarations,record.evaluations,resolution,retained.frozen)
    assert retained.frozen.digest==c.prepared.declarations.resolve(collected.keys).digest


def test_omitted_candidate_never_becomes_silent_empty_or_zero_fitness(worker_artifacts):
    c=fixture(worker_artifacts)
    c.page["nodes"].pop();c.page["snapshot"]["node_count"]-=1
    # Remove the corresponding final three replies as the server would.
    c.transport.replies=c.transport.replies[:-3]
    with pytest.raises(ValueError,match="coverage"):PrimaryCollection.load(c.request,c.session,c.runtime)


def test_owner_plan_digest_must_match_supplied_compiled_execution(worker_artifacts):
    c=fixture(worker_artifacts);c.page["snapshot"]["cut"]["plan_sha256"]="0"*64
    with pytest.raises(ValueError,match="admitted_plan"):PrimaryCollection.load(c.request,c.session,c.runtime)


def test_reversed_runtime_enumeration_preserves_exact_observations(worker_artifacts):
    e=copy.deepcopy(worker_artifacts)
    first=fixture(worker_artifacts);second=fixture(e)
    second.page["nodes"].reverse()
    groups=[second.responses[i:i+3] for i in range(0,len(second.responses),3)]
    second.transport.replies=[second.page,*[reply for group in reversed(groups) for reply in group]]
    left=PrimaryCollection.load(first.request,first.session,first.runtime)
    right=PrimaryCollection.load(second.request,second.session,second.runtime)
    assert left.observations==right.observations


def test_data_lineage_from_other_candidate_rejects_even_with_runtime_success(worker_artifacts):
    c=fixture(worker_artifacts)
    # Corrupt the declared direct context for a successful output while retaining
    # the exact Runtime completion. Candidate identity must agree across owners.
    proof=c.responses[2]
    output=proof["completion"]["result"]["outcome"]["outputs"][0]["artifact"]
    upload_id=output["artifact_id"];client=c.session.client
    upload,declaration=client.uploads[upload_id]
    other=c.responses[4]["scope_inputs"][0]["artifact"]
    from amphora_contracts_core import ArtifactRef
    other=ArtifactRef.model_validate_json(__import__("json").dumps(other))
    from amphora_contracts_population_steps import population_step_schema
    parents=tuple(other if ref.schema_ref==population_step_schema("population-step.candidate-context") else ref for ref in declaration.inputs)
    client.uploads[upload_id]=(upload,declaration.model_copy(update={"inputs":parents}))
    with pytest.raises(ValueError,match="output_context"):PrimaryCollection.load(c.request,c.session,c.runtime)


def test_data_producer_actor_must_match_accepted_runtime_worker(worker_artifacts):
    from dataclasses import replace
    c=fixture(worker_artifacts)
    original=c.session.client.derivation
    def different_actor(reference):
        receipt=original(reference)
        return receipt.model_copy(update={"origin":receipt.origin.model_copy(update={"actor_id":"other-worker"})})
    c.session.client.derivation=different_actor
    with pytest.raises(ValueError,match="producer_actor"):PrimaryCollection.load(c.request,c.session,c.runtime)
