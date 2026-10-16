"""Complete synthetic seed ancestry using a scripted Artifact client, not Data."""

import pytest
from amphora_contracts_population import BirthManifest, MembershipManifest, population_record_schema, membership_manifest_schema
from amphora_contracts_population_steps import PreparedPopulationGeneration, SeedPopulationRequest, population_step_schema
from amphora_evolution_search.population_workers.seed import SeedPreparation


def test_thousand_birth_seed_retains_every_published_child(worker_artifacts):
    e = worker_artifacts
    request = SeedPopulationRequest(schema_version="1", specification=e.source)
    seed = SeedPreparation.load(request, e.session)
    root = seed.publish(e.session)
    prepared = root.decode(PreparedPopulationGeneration, population_step_schema("population-step.prepared"), e.original.record.scope)
    births = e.session.read(prepared.births).decode(BirthManifest,
        population_record_schema("population.birth-manifest"), e.original.record.scope)
    cohort = e.session.read(prepared.cohort).decode(MembershipManifest, membership_manifest_schema(), e.original.record.scope)
    assert births.birth_count == 1000 and cohort.member_count == len(seed.batch.proposed)
    assert prepared.generation.run_id == "admitted-run"
    seen, pending = set(), [root.reference.artifact_id]
    while pending:
        key = pending.pop()
        if key not in seen:
            seen.add(key)
            pending.extend(parent.artifact_id for parent in e.client.parents.get(key, ()))
    assert set(e.client.parents) <= seen
    assert len(seen) <= 4096
    assert all(len(parents) <= 128 for parents in e.client.parents.values())
    from amphora_evolution_search.composition.publications import NumericPublicationProfile
    from amphora_evolution_search.population_workers.capabilities import PopulationCapability
    image="f"*64
    costs=NumericPublicationProfile(e.original.record,image)
    binding=PopulationCapability("seed").descriptor(image).tool.binding
    assert len(e.client.parents)<=costs.per_call(binding)
    assert seed.publish(e.session) == root


def test_unsupported_representation_rejects_before_any_publication(worker_artifacts):
    e = worker_artifacts
    from amphora_contracts_core import SchemaRef
    from amphora_evolution_search.population import OriginalPopulation, canonical
    import hashlib
    original = OriginalPopulation(e.original.record.model_copy(update={"representation": SchemaRef(
        schema_id="unknown", version="1", sha256="f" * 64)}))
    raw = canonical(original.record)
    reference = e.source.model_copy(update={"sha256": hashlib.sha256(raw).hexdigest(), "size_bytes": len(raw)})
    e.client.contents[reference.artifact_id] = raw
    with pytest.raises(ValueError, match="representation_not_supported"):
        SeedPreparation.load(SeedPopulationRequest(schema_version="1", specification=reference), e.session)
    assert e.client.calls == []
