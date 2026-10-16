"""Validation reads and SDK recovery are work even when method kernels are cheap."""
from importlib.metadata import version
import pytest

from amphora_evolution_search.composition.validation_io import SeedValidationIoProfile,REVIEWED_SDK_RELEASE
from amphora_evolution_search.composition.work import ScopeWork,BindingBudgets
from .test_publications import profile,binding


def costs():
    record=profile().original.record
    record=record.model_copy(update={"budget":record.budget.model_copy(update={"successor_generations":0})})
    return SeedValidationIoProfile(record,"f"*64)


def test_reviewed_sdk_does_not_float_with_future_installs():
    assert version("amphora-tool-protocol")==REVIEWED_SDK_RELEASE


def test_seed_read_and_recovery_envelope():
    budget=costs().per_attempt(binding("seed"))
    publications=profile().per_call(binding("seed"))
    assert budget.artifact_reads==2 and budget.content_read_bytes==524288
    assert budget.data_requests==4+11*publications
    assert budget.runtime_requests==34+18*publications
    assert budget.response_body_bytes==(budget.data_requests+budget.runtime_requests)*262145


def test_slice_revalidates_all_three_page_families():
    assert costs().per_attempt(binding("slice")).artifact_reads>costs().per_attempt(binding("evaluate-squares")).artifact_reads


def test_each_worker_attempt_charged_without_claiming_binding_io():
    work=ScopeWork(3,1,((binding("evaluate-squares"),2),),1,
        BindingBudgets(materializations=1,declared_bytes=200))
    single=costs().per_attempt(binding("evaluate-squares"))
    total=costs().assess(work,3)
    assert total.artifact_reads==6*single.artifact_reads
    assert total.runtime_requests==6*single.runtime_requests


def test_successors_require_separate_source_review():
    record=profile().original.record
    record=record.model_copy(update={"budget":record.budget.model_copy(update={"successor_generations":1})})
    with pytest.raises(ValueError,match="successor_profile"):SeedValidationIoProfile(record,"f"*64)


def test_unsupported_operation_rejects_even_when_expansion_is_zero():
    work=ScopeWork(1,1,((binding("select-primary"),0),),0,BindingBudgets())
    with pytest.raises(ValueError,match="unknown_validation_profile"):costs().assess(work,1)
