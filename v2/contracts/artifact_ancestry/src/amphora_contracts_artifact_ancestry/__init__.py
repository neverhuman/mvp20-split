"""Read-only catalog ancestry totals; no retention or processing authority."""
from typing import Annotated,Literal
from pydantic import Field
from amphora_contracts_core import ArtifactRef,Digest,WireModel


class ArtifactAncestryFootprint(WireModel):
    schema_version: Literal["1"]
    profile: Literal["artifact-ancestry-footprint-v1"]
    artifact: ArtifactRef
    artifact_count: Annotated[int,Field(ge=1,le=4096)]
    content_bytes: Annotated[int,Field(ge=0,le=9007199254740991)]
    members_sha256: Digest


__all__=["ArtifactAncestryFootprint"]
