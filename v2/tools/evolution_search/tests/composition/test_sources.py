"""Complete owner observations replace guesses about opaque external ancestry."""
import json
from types import SimpleNamespace
import pytest
from amphora_contracts_artifact_ancestry import ArtifactAncestryFootprint
from amphora_contracts_core import ArtifactRef
from amphora_tool_protocol import ProtocolError
from amphora_evolution_search.composition.sources import SourceFootprints
from amphora_evolution_search.composition.publications import PublicationBudget


def reference():
    return ArtifactRef(artifact_id="source",scope=dict(tenant_id="tenant",project_id="project"),
        size_bytes=10,sha256="a"*64,media_type="application/json",
        schema_ref=dict(schema_id="fixture",version="1",sha256="b"*64))


def observation(count=4):
    return ArtifactAncestryFootprint(schema_version="1",profile="artifact-ancestry-footprint-v1",
        artifact=reference(),artifact_count=count,content_bytes=100,members_sha256="c"*64)


class Client:
    def __init__(self):
        self.identity=SimpleNamespace(scope=reference().scope)
        self.transport=self;self.calls=[];self.record=observation();self.status=200
    def request(self,method,path):
        self.calls.append((method,path))
        return SimpleNamespace(status=self.status,body=self.record.model_dump_json().encode())


def test_scoped_read_deduplicates_source_roots_and_counts_full_ancestry():
    client=Client();sources=SourceFootprints.load(client,(reference(),reference()))
    result=sources.assess(PublicationBudget(5,9,900))
    assert client.calls==[("GET","/v1/artifacts/source/ancestry-footprint")]
    assert result.retained_artifacts_upper==9 and result.content_bytes_upper==1000
    assert len(result.observations_sha256)==64


def test_shared_ancestors_across_different_roots_are_conservatively_charged():
    first=observation()
    second=first.model_copy(update={"artifact":reference().model_copy(update={"artifact_id":"source2"})})
    result=SourceFootprints((first,second)).assess(PublicationBudget(0,0,0))
    assert result.retained_artifacts_upper==8 and result.content_bytes_upper==200


def test_exact_retained_identity_boundary_includes_future_root():
    sources=SourceFootprints((observation(4095),))
    assert sources.assess(PublicationBudget(1,1,20)).retained_artifacts_upper==4096
    with pytest.raises(ValueError,match="retained_limit"):sources.assess(PublicationBudget(2,2,20))


def test_digest_change_requires_reassessment():
    client=Client();sources=SourceFootprints.load(client,(reference(),));sources.unchanged(client)
    client.record=client.record.model_copy(update={"members_sha256":"d"*64})
    with pytest.raises(ProtocolError,match="ancestry_changed"):sources.unchanged(client)


@pytest.mark.parametrize("status",[403,404,409,503])
def test_unavailable_is_never_inferred_as_leaf(status):
    client=Client();client.status=status
    with pytest.raises(ProtocolError,match="ancestry_unavailable"):SourceFootprints.load(client,(reference(),))


def test_scope_and_conflicting_references_reject_before_any_io():
    client=Client()
    foreign=reference().model_copy(update={"scope":reference().scope.model_copy(update={"project_id":"other"})})
    with pytest.raises(ValueError,match="source_scope"):SourceFootprints.load(client,(foreign,))
    with pytest.raises(ValueError,match="reference_conflict"):
        SourceFootprints.load(client,(reference(),reference().model_copy(update={"sha256":"f"*64})))
    assert client.calls==[]


def test_owner_metadata_must_match_and_cover_root_bytes():
    client=Client();client.record=client.record.model_copy(update={"artifact":reference().model_copy(update={"sha256":"f"*64})})
    with pytest.raises(ProtocolError,match="ancestry_mismatch"):SourceFootprints.load(client,(reference(),))
    client.record=observation().model_copy(update={"content_bytes":0})
    with pytest.raises(ProtocolError,match="ancestry_invalid"):SourceFootprints.load(client,(reference(),))


@pytest.mark.parametrize("arguments",[(-1,1,1),(1,0,1),(True,1,1),(1,1,-1)])
def test_invalid_publication_counts_cannot_hide_source_costs(arguments):
    with pytest.raises(ValueError):PublicationBudget(*arguments)
