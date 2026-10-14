import hashlib

import pytest
from amphora_contracts_core import ArtifactRef
from amphora_contracts_population import (
    BirthManifest, CandidateMember, EvaluationKey, GenerationIdentity, MembershipPageReference,
    PopulationCheckpoint, PopulationProgress, ProposedSuccessor, candidate_birth_schema,
    membership_manifest_schema, population_record_schema,
)
from amphora_evolution_search.population import (
    BoundEvaluation, FrozenEvaluations, GenerationMembership, NumericBirth, OriginalPopulation,
    PopulationArtifact, PopulationSelection, RecordPages, RetainedEvaluations, SelectedGeneration, canonical,
)
from amphora_evolution_search.randomness import CounterRandom
from amphora_evolution_search.variation import ParentVector


@pytest.fixture
def population_original(population_original):
    record = population_original.record
    return OriginalPopulation(record.model_copy(update={"budget": record.budget.model_copy(update={"population_size": 2})}))


@pytest.fixture
def successor_case(assessment_factory):
    evidence, assessment = assessment_factory
    cohort = evidence.evaluations.membership
    original = cohort.original
    def artifact(name, schema, record=None):
        raw = canonical(record) if record is not None else b"{}"
        return PopulationArtifact(ArtifactRef(artifact_id=name, scope=cohort.identity.scope,
            sha256=hashlib.sha256(raw).hexdigest(), media_type="application/json", schema_ref=schema, size_bytes=len(raw)), raw)
    def pages(kind, identity, records):
        packed = RecordPages(identity, kind, records).pack()
        refs, payloads = [], []
        for index, page in enumerate(packed):
            item = artifact(kind + str(index), population_record_schema(kind), page)
            rows = page.members if hasattr(page, "members") else page.records
            refs.append(MembershipPageReference(ordinal=index, members=len(rows), artifact=item.reference))
            payloads.append(item.content)
        return tuple(refs), tuple(payloads)
    pool = GenerationMembership(original, cohort.identity, "selection_pool", cohort.members)
    decision = PopulationSelection(pool, tuple(evidence.bind(assessment(i)) for i in range(2))).decide()
    pool_ref = artifact("old-pool", membership_manifest_schema()).reference
    fitness_ref = artifact("old-fitness", population_record_schema("population.fitness-manifest")).reference
    rank_refs, _ = pages("population.selection-page", cohort.identity, decision.members)
    selection = artifact("selection", population_record_schema("population.selection-receipt"), decision.receipt(pool_ref, fitness_ref, rank_refs))
    rng = CounterRandom(original.record.seed, 2 * len(original.record.variables))
    checkpoint_record = PopulationCheckpoint(schema_version="1", profile="population-checkpoint-v1", generation=cohort.identity,
        selection=selection.reference, rng=rng.to_record(), progress=PopulationProgress(evaluations_issued=4,
        evaluations_terminal=4, attempts_issued=4, activations_created=12, unchanged_front_generations=0))
    checkpoint = artifact("checkpoint", population_record_schema("population.checkpoint"), checkpoint_record)
    seeds = {NumericBirth.seed(original, i).record.candidate_id: NumericBirth.seed(original, i) for i in range(2)}
    members = {m.candidate_id: m for m in pool.members}
    parents = tuple(PopulationArtifact(members[key].birth, canonical(seeds[key].record)) for key in decision.selected)
    source = SelectedGeneration.verify(checkpoint, selection, decision, pool_ref, fitness_ref, parents)
    identity = GenerationIdentity(scope=cohort.identity.scope, run_id=cohort.identity.run_id, specification_sha256=original.digest,
        generation=1, predecessor=checkpoint.reference)
    vectors = tuple(ParentVector(b.record.candidate_id, b.record.genes) for b in source.parents)
    seen = {p.genes: p.candidate_id for p in vectors}
    births, offspring = [], []
    for ordinal in range(2):
        birth = NumericBirth.vary(original, 1, ordinal, vectors, rng)
        rng = CounterRandom(original.record.seed, birth.record.draws.end)
        if birth.record.genes in seen:
            birth = NumericBirth(original, birth.record.model_copy(update={"disposition": "duplicate", "reason_code": "duplicate_genes",
                                                                         "duplicate_of": seen[birth.record.genes]}))
        else:
            seen[birth.record.genes] = birth.record.candidate_id
            pinned = artifact("new-birth-" + str(ordinal), candidate_birth_schema(), birth.record)
            representation = pinned.reference.model_copy(update={"artifact_id": "new-vector-" + str(ordinal), "schema_ref": original.record.representation})
            offspring.append(CandidateMember(candidate_id=birth.record.candidate_id, birth=pinned.reference,
                                             representation=representation, source="offspring"))
        births.append(birth.record)
    offspring = tuple(sorted(offspring, key=lambda m: m.candidate_id))
    new_cohort = GenerationMembership(original, identity, "cohort", offspring)
    union = tuple(sorted((*offspring, *(members[key].model_copy(update={"source": "parent"}) for key in decision.selected)), key=lambda m: m.candidate_id))
    new_pool = GenerationMembership(original, identity, "selection_pool", union)
    keys = []
    for member in offspring:
        for method in original.record.method_graph.methods:
            keys.append(BoundEvaluation(new_cohort, EvaluationKey(schema_version="1", profile="population-evaluation-key-v1",
                generation=identity, candidate_id=member.candidate_id, occurrence_id="primary", method_id=method.method_id,
                tool=method.tool, material=member.representation, inputs=(member.representation,), conditions=method.conditions,
                objective_policy_sha256=original.record.assembly.policy.sha256)))
    evaluations = RetainedEvaluations(artifact("new-evaluations", population_record_schema("population.evaluation-manifest")),
                                      FrozenEvaluations(new_cohort, tuple(keys)))
    birth_refs, birth_bytes = pages("population.birth-page", identity, tuple(births))
    birth_manifest = artifact("new-births", population_record_schema("population.birth-manifest"), BirthManifest(
        schema_version="1", profile="population-birth-manifest-v1", generation=identity, birth_count=2, pages=birth_refs))
    cohort_ref = artifact("new-cohort", membership_manifest_schema()).reference
    new_pool_ref = artifact("new-pool", membership_manifest_schema()).reference
    proposal = ProposedSuccessor(schema_version="1", profile="population-proposed-successor-v1", generation=identity,
        selection=selection.reference, births=birth_manifest.reference, cohort=cohort_ref, pool=new_pool_ref,
        evaluations=evaluations.artifact.reference, rng=rng.to_record(), evaluations_reserved=len(keys),
        disposition="evaluate" if offspring else "duplicate_only")
    return dict(source=source, proposal=proposal, artifact=artifact, birth_manifest=birth_manifest, birth_payloads=birth_bytes,
        cohort=new_cohort, cohort_reference=cohort_ref, pool=new_pool, pool_reference=new_pool_ref, evaluations=evaluations,
        checkpoint=checkpoint_record, selection=selection, decision=decision, old_pool_ref=pool_ref, fitness_ref=fitness_ref, parents=parents)
