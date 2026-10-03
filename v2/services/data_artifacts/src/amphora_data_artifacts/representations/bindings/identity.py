"""Deterministic source/publisher binding identity, independent of request aliases."""

from dataclasses import dataclass

from amphora_contracts_core import Scope
from amphora_contracts_evidence import SourceSpan
from amphora_contracts_representations import EncodeSourceRequest, EncodingProfileRef

from ...acquisition.provenance import MAX_PROVENANCE_BYTES
from ..mapping import _validated
from ..validation import fingerprint, identifier, record, require


@dataclass(frozen=True, slots=True)
class SourceBindingIdentity:
    scope: Scope
    actor_id: str
    profile: EncodingProfileRef
    source: SourceSpan

    def __post_init__(self):
        record(self.scope, Scope)
        identifier(self.actor_id)
        profile = _validated(self.profile, EncodingProfileRef)
        source = _validated(self.source, SourceSpan)
        require(
            profile.scope == source.source.scope == source.source.raw.scope == self.scope,
            "representation_binding_scope",
        )
        require(
            0 <= source.start < source.end <= source.source.raw.size_bytes
            and source.end - source.start <= 65536,
            "representation_span_bound",
        )
        require(source.source.raw.size_bytes <= MAX_PROVENANCE_BYTES, "representation_source_bound")

    @classmethod
    def prepare(cls, principal, request):
        request = _validated(request, EncodeSourceRequest)
        return cls(principal.scope, principal.actor_id, request.profile, request.source)

    def descriptor(self):
        return {
            "format": "data.encoding-binding.v1",
            "scope": self.scope.model_dump(mode="json"),
            "actor_id": self.actor_id,
            "profile": self.profile.model_dump(mode="json"),
            "source": self.source.model_dump(mode="json"),
        }

    @property
    def sha256(self):
        return fingerprint(self.descriptor())

    @property
    def binding_id(self):
        return "binding." + self.sha256

    def command_id(self, stage):
        require(stage in ("begin", "finalize"), "representation_publication_stage")
        return "binding." + stage + "." + self.sha256
