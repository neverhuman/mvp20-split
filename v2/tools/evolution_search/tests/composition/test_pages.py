"""Byte bounds can require more pages than the64-row count floor."""
import pytest
import json
from amphora_contracts_core import ArtifactRef,Scope,SchemaRef
from amphora_evolution_search.composition.pages import PageEnvelope,PageFootprint
from amphora_contracts_population import (BirthPage,MembershipPage,EvaluationSlotPage,
    EvaluationKeyPage,MethodObservationPage,FitnessPage,SelectionPage)


def test_byte_bound_splits_before_row_limit():
    bound=PageEnvelope(8192,1000).bound(64)
    assert bound.pages==5
    assert bound.bytes==64*8192+5000+59


def test_row_bound_and_empty_records():
    envelope=PageEnvelope(10,100)
    assert envelope.bound(65)==PageFootprint(2,913)
    assert envelope.bound(0)==PageFootprint()


def test_exact_page_byte_limit():
    envelope=PageEnvelope(8192,114687)
    assert envelope.bound(2)==PageFootprint(1,131072)
    assert envelope.bound(3).pages==2


def test_total_generation_closure_not_each_family_only():
    envelope=PageEnvelope(10,100)
    family=envelope.bound(64*256)
    assert family.include(family).pages==512
    with pytest.raises(ValueError,match="page_count"):
        family.include(family).include(envelope.bound(1))


@pytest.mark.parametrize("row,header",[(True,10),(8193,10),(1,True),(1,1),(8192,131072)])
def test_invalid_or_unfittable_envelope(row,header):
    with pytest.raises(ValueError):PageEnvelope(row,header)


def test_page_and_checked_count_overflows():
    with pytest.raises(ValueError):PageEnvelope(10,100).bound(True)
    with pytest.raises(ValueError,match="page_count"):PageEnvelope(10,100).bound(64*512+1)
    with pytest.raises(ValueError,match="overflow"):PageEnvelope(10,100).bound(9007199254740992)


@pytest.mark.parametrize("model",[BirthPage,MembershipPage,EvaluationSlotPage,EvaluationKeyPage,
    MethodObservationPage,FitnessPage,SelectionPage])
def test_public_page_header_profile_is_derived(model):
    envelope=PageEnvelope.population(model)
    assert envelope.row_bytes==8192
    assert 1000<envelope.header_bytes<10000
    assert envelope.bound(64).pages>1


def test_unknown_page_profile_rejects():
    with pytest.raises(ValueError,match="page_profile"):PageEnvelope.population(dict)


def test_header_bound_covers_large_public_metadata_and_escaped_media():
    scope=Scope(tenant_id="t"*128,project_id="p"*128)
    predecessor=ArtifactRef(artifact_id="a"*128,scope=scope,sha256="f"*64,
        media_type="\x00"*126+"/a",schema_ref=SchemaRef(schema_id="s"*128,version="1",sha256="f"*64),
        size_bytes=9007199254740991)
    header=dict(schema_version="1",profile="population-membership-v1",
        generation=dict(scope=scope.model_dump(mode="json"),run_id="r"*128,
            specification_sha256="f"*64,generation=100,predecessor=predecessor.model_dump(mode="json")),
        role="selection_pool",ordinal=511,members=[])
    raw=json.dumps(header,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
    assert len(raw)<=PageEnvelope.population(MembershipPage).header_bytes
