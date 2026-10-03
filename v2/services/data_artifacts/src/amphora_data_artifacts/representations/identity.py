"""Result-affecting work identity is distinct from any authorized source binding."""

import hashlib
from dataclasses import dataclass

from amphora_contracts_core import SchemaRef, Scope

from .profiles import RepresentationProfile
from .validation import RepresentationError, digest, fingerprint, record, require


@dataclass(frozen=True, slots=True)
class EncodingInput:
    content: bytes
    context_sha256: str | None = None

    def __post_init__(self):
        require(type(self.content) is bytes and 1 <= len(self.content) <= 65536, "representation_input_bound")
        try:
            self.content.decode("utf-8", errors="strict")
        except UnicodeDecodeError as error:
            raise RepresentationError("representation_input_utf8") from error
        if self.context_sha256 is not None:
            digest(self.context_sha256)

    @property
    def sha256(self):
        return hashlib.sha256(self.content).hexdigest()


@dataclass(frozen=True, slots=True)
class EncodingWorkIdentity:
    scope: Scope
    profile: SchemaRef
    input_sha256: str
    context_sha256: str | None

    def __post_init__(self):
        record(self.scope, Scope)
        record(self.profile, SchemaRef)
        require(
            (self.profile.schema_id, self.profile.version) == ("data.representation-profile", "1"),
            "representation_profile_reference",
        )
        digest(self.input_sha256)
        if self.context_sha256 is not None:
            digest(self.context_sha256)

    @classmethod
    def prepare(cls, scope, profile, source):
        require(
            type(profile) is RepresentationProfile and type(source) is EncodingInput,
            "representation_work_input",
        )
        require(
            (profile.inputs.context_schema is None) == (source.context_sha256 is None),
            "representation_context_required",
        )
        return cls(scope, profile.reference, source.sha256, source.context_sha256)

    @property
    def sha256(self):
        return fingerprint(
            {
                "format": "data.encoding-work.v1",
                "scope": self.scope.model_dump(mode="json"),
                "profile": self.profile.model_dump(mode="json"),
                "input_sha256": self.input_sha256,
                "context_sha256": self.context_sha256,
            }
        )
