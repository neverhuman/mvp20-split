import hashlib

import pytest
from amphora_contracts_core import ArtifactRef
from amphora_contracts_population import GenerationIdentity, MembershipPageReference, population_record_schema
from amphora_evolution_search.population import NumericBirth, RecordPages, canonical


def test_birth_pages_cover_large_cohort_and_verify_full_closure(population_original):
    original = population_original
    identity = GenerationIdentity(scope=original.record.scope, run_id="paged-birth", specification_sha256=original.digest,
                                  generation=0, predecessor=None)
    records = tuple(NumericBirth.seed(original, i).record for i in range(1000))
    series = RecordPages(identity, "population.birth-page", records)
    pages = series.pack()
    assert len(pages) == 16 and sum(len(page.records) for page in pages) == 1000
    payloads = tuple(canonical(page) for page in pages)
    refs = tuple(MembershipPageReference(ordinal=i, members=len(page.records), artifact=ArtifactRef(
        artifact_id=f"page-{i}", scope=identity.scope, sha256=hashlib.sha256(raw).hexdigest(), media_type="application/json",
        schema_ref=population_record_schema("population.birth-page"), size_bytes=len(raw)))
        for i, (page, raw) in enumerate(zip(pages, payloads, strict=True)))
    assert RecordPages.verified(identity, "population.birth-page", refs, payloads, 1000).records == records
    with pytest.raises(ValueError, match="record_page_coverage"):
        RecordPages.verified(identity, "population.birth-page", refs, payloads[:-1], 1000)
    with pytest.raises(ValueError, match="record_page_digest"):
        RecordPages.verified(identity, "population.birth-page", refs, tuple(reversed(payloads)), 1000)
    with pytest.raises(ValueError, match="record_page_identity"):
        RecordPages.verified(identity.model_copy(update={"run_id": "other"}), "population.birth-page", refs, payloads, 1000)


def test_birth_pages_reject_wrong_generation_or_order(population_original):
    original = population_original
    identity = GenerationIdentity(scope=original.record.scope, run_id="run", specification_sha256=original.digest,
                                  generation=0, predecessor=None)
    first, second = (NumericBirth.seed(original, i).record for i in (0, 1))
    with pytest.raises(ValueError, match="record_order_or_duplicate"):
        RecordPages(identity, "population.birth-page", (second, first))
    changed = second.model_copy(update={"specification_sha256": "f" * 64})
    with pytest.raises(ValueError, match="record_generation"):
        RecordPages(identity, "population.birth-page", (changed,))
