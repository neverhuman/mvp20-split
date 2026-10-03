"""Retained computed output groups its complete interpretation with exact vector bytes."""

from dataclasses import dataclass

from .identity import EncodingInput
from .profiles import RepresentationProfile
from .validation import digest, require
from .vectors import Float32Vector


@dataclass(frozen=True, slots=True)
class EncodedRepresentation:
    profile: RepresentationProfile
    input_sha256: str
    context_sha256: str | None
    vector: Float32Vector

    def __post_init__(self):
        require(type(self.profile) is RepresentationProfile, "representation_profile_required")
        require(type(self.vector) is Float32Vector, "representation_vector_required")
        require(self.vector.space == self.profile.space, "representation_vector_profile")
        digest(self.input_sha256)
        if self.context_sha256 is not None:
            digest(self.context_sha256)
        require(
            (self.profile.inputs.context_schema is None) == (self.context_sha256 is None),
            "representation_context_required",
        )

    @classmethod
    def prepare(cls, profile, source, vector):
        require(type(source) is EncodingInput, "representation_encoder_input")
        return cls(profile, source.sha256, source.context_sha256, vector)
