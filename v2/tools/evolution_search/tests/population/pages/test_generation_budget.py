import hashlib

import pytest
from amphora_contracts_core import ArtifactRef
from amphora_contracts_population import membership_page_schema
from amphora_evolution_search.population import PopulationArtifact, canonical
from amphora_evolution_search.population.closure import GenerationPageClosure


def artifact(cohort, index=0):
    raw = canonical(cohort.pages()[0])
    return PopulationArtifact(ArtifactRef(artifact_id="page-" + str(index), scope=cohort.identity.scope,
        schema_ref=membership_page_schema(), sha256=hashlib.sha256(raw).hexdigest(), size_bytes=len(raw), media_type="application/json"), raw)


def test_generation_budget_applies_to_combined_reference_list(born_cohort):
    # This is the aggregate budget boundary, not a claim of full manifest reachability.
    # Every reference is distinct; the page verifier also checks content/hash/scope.
    pages = tuple(artifact(born_cohort, i) for i in range(512))
    result = GenerationPageClosure.verify(born_cohort.identity, pages)
    assert result.size_bytes == sum(len(p.content) for p in pages)
    assert len(result.pages) == 512
    with pytest.raises(ValueError, match="generation_closure_pages"):
        GenerationPageClosure.verify(born_cohort.identity, (*pages, artifact(born_cohort, 512)))


def test_generation_budget_rejects_alias_corruption_and_foreign_identity(born_cohort):
    page = artifact(born_cohort)
    with pytest.raises(ValueError, match="generation_closure_duplicate"):
        GenerationPageClosure.verify(born_cohort.identity, (page, page))
    with pytest.raises(ValueError, match="population_artifact_digest"):
        GenerationPageClosure.verify(born_cohort.identity, (PopulationArtifact(page.reference, page.content + b" "),))
    with pytest.raises(ValueError, match="generation_closure_page_bytes"):
        GenerationPageClosure.verify(born_cohort.identity, (PopulationArtifact(page.reference, b" " * 131073),))
    with pytest.raises(ValueError, match="generation_closure_identity"):
        GenerationPageClosure.verify(born_cohort.identity.model_copy(update={"run_id": "foreign"}), (page,))
