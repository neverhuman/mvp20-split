"""Authenticated collected source, complete evidence and consumable initial-pool fitness."""
import pytest
from amphora_contracts_population import FitnessManifest,MembershipManifest,ObservationManifest,population_record_schema,membership_manifest_schema
from amphora_evolution_search.population.membership import GenerationMembership
from amphora_evolution_search.population.retained import PopulationArtifact,RetainedObservations,RetainedFitness
from amphora_evolution_search.population_workers.assembly import PrimaryAssembly
from amphora_evolution_search.population_workers.method_plan import payload_schema
from amphora_evolution_search.population_workers.payloads import FittedPrimaryGeneration

from .assembly_fixture import assembly_fixture


@pytest.mark.parametrize("status",["succeeded","failed","skipped","blocked"])
def test_assembly_publishes_complete_initial_pool_and_explicit_unavailability(worker_artifacts,status):
    e=worker_artifacts;c=assembly_fixture(e,status)
    assembly=PrimaryAssembly.load(c.source,c.session,c.runtime,c.binding)
    result=assembly.publish(c.session)
    fitted=result.decode(FittedPrimaryGeneration,payload_schema(FittedPrimaryGeneration,"population-worker.fitted"),e.client.identity.scope)
    def read(ref):return PopulationArtifact(ref,e.client.contents[ref.artifact_id])
    manifest=read(fitted.fitness).decode(FitnessManifest,population_record_schema("population.fitness-manifest"),e.client.identity.scope)
    pool_record=read(fitted.pool).decode(MembershipManifest,membership_manifest_schema(),e.client.identity.scope)
    pool=GenerationMembership.verified(c.prepared.declarations.membership.original,read(fitted.pool).content,
        tuple(read(page.artifact).content for page in pool_record.pages))
    verified=RetainedFitness.verify(pool,fitted.pool,read(fitted.fitness),tuple(read(page.artifact).content for page in manifest.pages),
        (RetainedObservations(read(assembly.record.observations),assembly.fitness.evidence),))
    assert len(verified.selection.decide().selected)==(4 if status=="succeeded" else 3)
    assert pool.role=="selection_pool" and pool.members==c.prepared.declarations.membership.members
    assert manifest.member_count==4 and manifest.pool==fitted.pool
    assert len(assembly.fitness.records())==4
    assert sum(item.record.outcome.status=="evaluated" for item in assembly.fitness.records())==(4 if status=="succeeded" else 3)
    assert fitted.collected==c.source.reference and fitted.resolution==assembly.record.resolution


def test_uploaded_but_unaccepted_collection_cannot_produce_fitness(worker_artifacts):
    c=assembly_fixture(worker_artifacts);c.page["nodes"][0]["status"]="failed"
    with pytest.raises(ValueError,match="collection_not_accepted"):
        PrimaryAssembly.load(c.source,c.session,c.runtime,c.binding)


def test_data_actor_and_accepted_collector_must_agree(worker_artifacts):
    c=assembly_fixture(worker_artifacts)
    original=c.session.client.derivation
    def different_actor(reference):
        result=original(reference)
        return result.model_copy(update={"origin":result.origin.model_copy(update={"actor_id":"other"})})
    c.session.client.derivation=different_actor
    with pytest.raises(ValueError,match="collection_actor"):
        PrimaryAssembly.load(c.source,c.session,c.runtime,c.binding)


def test_changed_collection_result_rejects_before_publication(worker_artifacts):
    c=assembly_fixture(worker_artifacts)
    c.proof["completion"]["result"]["outcome"]["outputs"][0]["artifact"]["artifact_id"]="other"
    with pytest.raises(ValueError,match="collection_not_accepted"):
        PrimaryAssembly.load(c.source,c.session,c.runtime,c.binding)
