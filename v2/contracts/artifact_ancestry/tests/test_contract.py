"""Additive bounded metadata DTO; no authority-bearing fields."""
import json
import pytest
from amphora_contracts_artifact_ancestry import ArtifactAncestryFootprint


def payload():
    return dict(schema_version="1",profile="artifact-ancestry-footprint-v1",artifact=dict(
        artifact_id="root",scope=dict(tenant_id="tenant",project_id="project"),sha256="a"*64,
        size_bytes=4,media_type="application/json",schema_ref=dict(schema_id="fixture",version="1",sha256="b"*64)),
        artifact_count=1,content_bytes=4,members_sha256="c"*64)


def test_roundtrip_and_no_authority_fields():
    result=ArtifactAncestryFootprint.model_validate_json(json.dumps(payload()))
    assert result.model_dump(mode="json")==payload()


@pytest.mark.parametrize("change",[{"artifact_count":0},{"artifact_count":4097},{"artifact_count":True},
    {"content_bytes":-1},{"content_bytes":9007199254740992},{"content_bytes":True},
    {"members_sha256":"bad"},{"retention_grant":"invented"}])
def test_bad_counts_identity_and_added_authority_reject(change):
    value=payload();value.update(change)
    with pytest.raises(ValueError):ArtifactAncestryFootprint.model_validate_json(json.dumps(value))
