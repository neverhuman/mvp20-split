"""Read-only external ancestry observations bound prospective campaign content."""
from dataclasses import dataclass
import hashlib
import json

from amphora_contracts_artifact_ancestry import ArtifactAncestryFootprint
from amphora_contracts_core import ArtifactRef
from amphora_tool_protocol import ProtocolError

from ..ranking import require
from .publications import PublicationBudget
from .work import add


@dataclass(frozen=True)
class SourceResourceBound:
    observations_sha256: str
    retained_artifacts_upper: int
    content_bytes_upper: int


@dataclass(frozen=True)
class SourceFootprints:
    observations: tuple[ArtifactAncestryFootprint,...]

    def __post_init__(self):
        require(type(self.observations) is tuple and len(self.observations)<=128
            and all(isinstance(item,ArtifactAncestryFootprint) for item in self.observations),
            "composition_source_observations")
        checked=tuple(ArtifactAncestryFootprint.model_validate_json(item.model_dump_json()) for item in self.observations)
        identities=tuple(item.artifact.artifact_id for item in checked)
        require(identities==tuple(sorted(set(identities))),"composition_source_identity")
        require(not checked or all(item.artifact.scope==checked[0].artifact.scope for item in checked),
            "composition_source_scope")
        require(all(item.content_bytes>=item.artifact.size_bytes for item in checked),
            "composition_source_root_bytes")
        object.__setattr__(self,"observations",checked)

    @classmethod
    def load(cls,client,references):
        require(type(references) is tuple and len(references)<=128
            and all(isinstance(item,ArtifactRef) for item in references),"composition_source_references")
        unique={}
        for ref in references:
            ref=ArtifactRef.model_validate_json(ref.model_dump_json())
            require(ref.scope==client.identity.scope,"composition_source_scope")
            require(unique.setdefault(ref.artifact_id,ref)==ref,"composition_source_reference_conflict")
        require(len(unique)<=128,"composition_source_roots")
        observed=[]
        for identity,reference in sorted(unique.items()):
            reply=client.transport.request("GET",f"/v1/artifacts/{identity}/ancestry-footprint")
            if reply.status!=200:raise ProtocolError("composition_source_ancestry_unavailable")
            try:record=ArtifactAncestryFootprint.model_validate_json(reply.body)
            except ValueError:raise ProtocolError("composition_source_ancestry_invalid") from None
            if record.artifact!=reference:raise ProtocolError("composition_source_ancestry_mismatch")
            observed.append(record)
        try:return cls(tuple(observed))
        except ValueError:raise ProtocolError("composition_source_ancestry_invalid") from None

    def unchanged(self,client):
        current=type(self).load(client,tuple(item.artifact for item in self.observations))
        if current!=self:raise ProtocolError("composition_source_ancestry_changed")

    def assess(self,publications):
        require(type(publications) is PublicationBudget,"composition_publication_budget")
        count=publications.successful_artifacts;size=publications.all_attempt_content_bytes
        for observed in self.observations:
            count=add(count,observed.artifact_count)
            size=add(size,observed.content_bytes)
        # Every root is already included. Shared source ancestors may be charged
        # more than once; this is deliberately an upper bound, never truncation.
        require(count<=4096,"composition_source_retained_limit")
        raw=json.dumps([item.model_dump(mode="json") for item in self.observations],
            sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False).encode()
        digest=hashlib.sha256(b"amphora.population/source-footprints-v1\0"+raw).hexdigest()
        return SourceResourceBound(digest,count,size)
