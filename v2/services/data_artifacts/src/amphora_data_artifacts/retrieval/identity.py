"""Generation plans and attempt-private backend namespaces, with no backend effects."""

from dataclasses import dataclass

from amphora_contracts_core import SchemaRef, Scope

from .manifest import CorpusManifest
from .validation import digest, fingerprint, identifier, record, require


@dataclass(frozen=True, slots=True)
class GenerationReference:
    scope: Scope
    corpus_id: str
    generation_id: str
    sha256: str

    def __post_init__(self):
        record(self.scope, Scope)
        identifier(self.corpus_id)
        identifier(self.generation_id)
        digest(self.sha256)

    def descriptor(self):
        return {
            "scope": self.scope.model_dump(mode="json"),
            "corpus_id": self.corpus_id,
            "generation_id": self.generation_id,
            "sha256": self.sha256,
        }


@dataclass(frozen=True, slots=True)
class GenerationPlan:
    corpus_id: str
    generation_id: str
    actor_id: str
    manifest: CorpusManifest
    expected_head: GenerationReference | None
    backend_profile: SchemaRef

    def __post_init__(self):
        for value in (self.corpus_id, self.generation_id, self.actor_id):
            identifier(value)
        require(type(self.manifest) is CorpusManifest, "retrieval_manifest_required")
        record(self.backend_profile, SchemaRef)
        if self.expected_head is not None:
            require(type(self.expected_head) is GenerationReference, "retrieval_head_required")
            require(
                self.expected_head.scope == self.manifest.scope
                and self.expected_head.corpus_id == self.corpus_id,
                "retrieval_head_scope",
            )
            require(self.expected_head.generation_id != self.generation_id, "retrieval_self_head")

    def descriptor(self):
        return {
            "format": "data.index-generation.v1",
            "scope": self.manifest.scope.model_dump(mode="json"),
            "corpus_id": self.corpus_id,
            "generation_id": self.generation_id,
            "actor_id": self.actor_id,
            "manifest_sha256": self.manifest.watermark,
            "expected_head": None if self.expected_head is None else self.expected_head.descriptor(),
            "backend_profile": self.backend_profile.model_dump(mode="json"),
        }

    @property
    def reference(self):
        return GenerationReference(
            self.manifest.scope, self.corpus_id, self.generation_id, fingerprint(self.descriptor())
        )


@dataclass(frozen=True, slots=True)
class BuildAttempt:
    generation: GenerationReference
    token: str
    fence: int

    def __post_init__(self):
        require(type(self.generation) is GenerationReference, "retrieval_generation_required")
        identifier(self.token)
        require(type(self.fence) is int and 1 <= self.fence <= 9007199254740991, "retrieval_fence_bound")

    @property
    def namespace(self):
        body = {
            "format": "data.index-namespace.v1",
            "generation": self.generation.descriptor(),
            "token": self.token,
            "fence": self.fence,
        }
        return "amphora_" + fingerprint(body)
