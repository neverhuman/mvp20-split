"""Pinned worker costs count orchestration, retry output and materialization bytes."""
from pathlib import Path
from importlib.metadata import version

import pytest
from amphora_contracts_population import PopulationSpecification
from amphora_contracts_tools import ToolBinding
from amphora_evolution_search.composition.publications import NumericPublicationProfile,reference_groups,REVIEWED_RELEASE
from amphora_evolution_search.composition.work import ScopeWork,BindingBudgets


def profile():
    spec=PopulationSpecification.model_validate_json((Path(__file__).parents[1]/
        "population/specification/fixtures/specification.json").read_bytes())
    return NumericPublicationProfile(spec,"f"*64)


def binding(operation):
    return ToolBinding(capability_id="numeric.population-"+operation,
        release=version("amphora-evolution-search"),image_sha256="f"*64,contract_version="1")


def test_future_package_release_requires_explicit_cost_profile_review():
    assert REVIEWED_RELEASE==version("amphora-evolution-search")
    with pytest.raises(ValueError,match="release_pin"):
        profile().per_call(binding("seed").model_copy(update={"release":"0.25.0"}))


def test_reference_groups_match_multilevel_source_algorithm():
    assert [reference_groups(n) for n in (0,120,121,512,14400,14401)]==[0,0,2,5,120,123]


def test_retry_outputs_include_adapters_and_materialization_uses_declared_bytes():
    costs=profile()
    work=ScopeWork(4,1,((binding("evaluate-squares"),2),(binding("prepare-selection"),1)),3,
        BindingBudgets(materializations=1,declared_bytes=700000))
    result=costs.assess(work,3)
    assert (result.successful_artifacts,result.all_attempt_artifacts)==(4,10)
    assert result.all_attempt_content_bytes==9*262144+700000


@pytest.mark.parametrize("change",[{"release":"0.23.0"},{"image_sha256":"a"*64},{"contract_version":"2"}])
def test_exact_release_image_and_contract_pins(change):
    with pytest.raises(ValueError):
        profile().per_call(binding("seed").model_copy(update=change))


def test_unknown_tool_rejected_even_without_expanded_calls():
    work=ScopeWork(1,1,((binding("unknown"),0),),0,BindingBudgets())
    with pytest.raises(ValueError,match="unknown_publication_profile"):profile().assess(work,1)


def test_seed_cost_includes_births_pages_and_all_four_roots():
    costs=profile()
    count=costs.per_call(binding("seed"))
    assert count>costs.original.record.budget.population_size+4


@pytest.mark.parametrize("attempts",[True,0,101])
def test_attempt_bound(attempts):
    with pytest.raises(ValueError):profile().assess(ScopeWork(0,1,(),0,BindingBudgets()),attempts)
