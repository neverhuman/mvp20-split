import hashlib

import pytest
from amphora_contracts_core import ArtifactRef
from amphora_contracts_population import EvaluationManifest, ObservationManifest, FitnessManifest, MembershipPageReference, membership_manifest_schema, population_record_schema
from amphora_evolution_search.population import GenerationMembership, PopulationArtifact, RecordPages, RetainedEvaluations, RetainedFitness, canonical
from amphora_evolution_search.population.evaluations import observation_cut


def test_complete_manifest_chain_reconstructs_same_global_selection(assessment_factory):
    evidence, factory = assessment_factory
    frozen = evidence.evaluations; cohort = frozen.membership
    def artifact(name, schema, record=None):
        raw = canonical(record) if record is not None else b"{}"
        reference = ArtifactRef(artifact_id=name, scope=cohort.identity.scope, schema_ref=schema,
            media_type="application/json", size_bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
        return PopulationArtifact(reference, raw)
    def pages(kind, records):
        series = RecordPages(cohort.identity, kind, records).pack()
        refs, payloads = [], []
        for i, page in enumerate(series):
            pinned = artifact(kind + "-" + str(i), population_record_schema(kind), page)
            refs.append(MembershipPageReference(ordinal=i, members=len(page.records), artifact=pinned.reference))
            payloads.append(pinned.content)
        return tuple(refs), tuple(payloads)
    membership = artifact("membership", membership_manifest_schema())
    key_records = tuple(key.record for key in sorted(frozen.keys, key=lambda key: key.digest))
    key_refs, key_bytes = pages("population.evaluation-key-page", key_records)
    key_manifest = EvaluationManifest(schema_version="1", profile="population-evaluation-manifest-v1",
        generation=cohort.identity, membership=membership.reference, evaluation_set_sha256=frozen.digest,
        evaluation_count=len(key_records), pages=key_refs)
    retained = RetainedEvaluations.verify(cohort, membership.reference,
        artifact("key-manifest", population_record_schema("population.evaluation-manifest"), key_manifest), key_bytes)
    assert retained.frozen.digest == frozen.digest
    observation_refs, observation_bytes = pages("population.method-observation-page", evidence.observations)
    observations = ObservationManifest(schema_version="1", profile="population-observation-manifest-v1",
        generation=cohort.identity, evaluations=retained.artifact.reference, evaluation_set_sha256=frozen.digest,
        observation_cut_sha256=observation_cut(evidence.observations), terminal_count=len(evidence.observations), pages=observation_refs)
    observed = retained.observations(artifact("observed", population_record_schema("population.observation-manifest"), observations), observation_bytes)
    assert observed.evidence == evidence
    pool = GenerationMembership(cohort.original, cohort.identity, "selection_pool", cohort.members)
    pool_ref = artifact("pool", membership_manifest_schema()).reference
    fitness_rows = tuple(factory(i) for i in range(2))
    fitness_refs, fitness_bytes = pages("population.fitness-page", fitness_rows)
    fitness = FitnessManifest(schema_version="1", profile="population-fitness-manifest-v1", generation=cohort.identity,
        pool=pool_ref, observations=(observed.artifact.reference,), member_count=2, pages=fitness_refs)
    verified = RetainedFitness.verify(pool, pool_ref, artifact("fitness", population_record_schema("population.fitness-manifest"), fitness),
        fitness_bytes, (observed,))
    assert len(verified.selection.decide().selected) == 2
    tampered = observations.model_copy(update={"observation_cut_sha256": "f" * 64})
    with pytest.raises(ValueError, match="observation_manifest_cut"):
        retained.observations(artifact("changed", population_record_schema("population.observation-manifest"), tampered), observation_bytes)
    with pytest.raises(ValueError, match="fitness_observation_sources"):
        RetainedFitness.verify(pool, pool_ref, artifact("fitness", population_record_schema("population.fitness-manifest"), fitness),
            fitness_bytes, ())
