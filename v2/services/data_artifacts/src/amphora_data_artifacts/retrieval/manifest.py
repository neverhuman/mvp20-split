"""Ordered corpus snapshots; public references alone never establish source authority."""

import uuid
from dataclasses import dataclass

from amphora_contracts_core import Scope
from amphora_contracts_representations import RepresentationBinding

from ..representations.bindings.receipts import validate_binding_projection
from ..representations.mapping import profile_reference
from ..representations.profiles import RepresentationProfile
from .validation import canonical, fingerprint, record, require


def point_id(binding):
    body = {"format": "data.index-point.v1", "binding": binding.reference.model_dump(mode="json")}
    return str(uuid.UUID(hex=fingerprint(body)[:32]))


@dataclass(frozen=True, slots=True)
class CorpusManifest:
    scope: Scope
    profile: RepresentationProfile
    bindings: tuple[RepresentationBinding, ...]

    def __post_init__(self):
        record(self.scope, Scope)
        require(type(self.profile) is RepresentationProfile, "retrieval_profile_required")
        self.profile.require_compatible(self.profile)
        require(type(self.bindings) is tuple and 1 <= len(self.bindings) <= 256, "retrieval_corpus_bound")
        seen = set()
        points = set()
        for binding in self.bindings:
            binding = validate_binding_projection(self.scope, binding)
            require(binding.profile == self.profile_reference, "retrieval_binding_profile")
            require(binding.reference.binding_id not in seen, "retrieval_duplicate_binding")
            seen.add(binding.reference.binding_id)
            key = point_id(binding)
            require(key not in points, "retrieval_point_collision")
            points.add(key)
        canonical(self.descriptor())

    @property
    def profile_reference(self):
        return profile_reference(self.scope, self.profile)

    def descriptor(self):
        return {
            "format": "data.corpus-manifest.v1",
            "scope": self.scope.model_dump(mode="json"),
            "profile": self.profile_reference.model_dump(mode="json"),
            "bindings": [binding.model_dump(mode="json") for binding in self.bindings],
        }

    @property
    def watermark(self):
        return fingerprint(self.descriptor())

    @property
    def point_ids(self):
        return tuple(point_id(binding) for binding in self.bindings)
