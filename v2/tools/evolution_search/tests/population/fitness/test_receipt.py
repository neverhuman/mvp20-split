import hashlib

import pytest
from amphora_contracts_core import ArtifactRef
from amphora_contracts_population import MembershipPageReference, membership_manifest_schema, population_record_schema
from amphora_evolution_search.population import GenerationMembership, PopulationSelection, RecordPages, canonical


def test_receipt_binds_exact_sources_pages_and_recomputed_decision(assessment_factory):
    evidence, factory = assessment_factory
    cohort = evidence.evaluations.membership
    pool = GenerationMembership(cohort.original, cohort.identity, "selection_pool", cohort.members)
    decision = PopulationSelection(pool, tuple(evidence.bind(factory(i)) for i in range(2))).decide()
    def reference(name, schema, raw=b"{}"):
        return ArtifactRef(artifact_id=name, scope=pool.identity.scope, sha256=hashlib.sha256(raw).hexdigest(),
            media_type="application/json", schema_ref=schema, size_bytes=len(raw))
    pool_ref = reference("pool", membership_manifest_schema())
    fitness_ref = reference("fitness", population_record_schema("population.fitness-manifest"))
    payloads = tuple(canonical(page) for page in decision.pages())
    pages = tuple(MembershipPageReference(ordinal=i, members=len(page.members),
        artifact=reference(f"rank-page-{i}", population_record_schema("population.selection-page"), raw))
        for i, (page, raw) in enumerate(zip(decision.pages(), payloads, strict=True)))
    receipt = decision.receipt(pool_ref, fitness_ref, pages)
    decision.verify_receipt(receipt, pool_ref, fitness_ref)
    assert RecordPages.verified(pool.identity, "population.selection-page", pages, payloads, 2).records == decision.members
    for change in ({"selected": ()}, {"stopped": True}, {"observation_cut_sha256": "f" * 64}):
        with pytest.raises(ValueError, match="selection_receipt_replay"):
            decision.verify_receipt(receipt.model_copy(update=change), pool_ref, fitness_ref)
    altered = pages[0].model_copy(update={"artifact": pages[0].artifact.model_copy(update={"sha256": "f" * 64})})
    with pytest.raises(ValueError, match="selection_page_digest"):
        decision.receipt(pool_ref, fitness_ref, (altered,))
    with pytest.raises(ValueError, match="record_page_digest"):
        RecordPages.verified(pool.identity, "population.selection-page", pages, (payloads[0] + b" ",), 2)


def test_fitness_pages_keep_canonical_candidate_order(assessment_factory):
    evidence, factory = assessment_factory
    identity = evidence.evaluations.membership.identity
    records = tuple(factory(i) for i in range(2))
    pages = RecordPages(identity, "population.fitness-page", records).pack()
    assert len(pages) == 1 and pages[0].records == records
    with pytest.raises(ValueError, match="record_order_or_duplicate"):
        RecordPages(identity, "population.fitness-page", tuple(reversed(records)))
