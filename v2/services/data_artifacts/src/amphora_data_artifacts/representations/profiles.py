"""Complete immutable profile semantics; equal dimensions grant no compatibility."""

from dataclasses import dataclass

from amphora_contracts_core import SchemaRef

from .validation import fingerprint, identifier, labels, record, require, text


@dataclass(frozen=True, slots=True)
class EncoderIdentity:
    provider: str
    model: str
    revision: str
    implementation: SchemaRef
    runtime: SchemaRef

    def __post_init__(self):
        for value in (self.provider, self.model, self.revision):
            identifier(value)
        record(self.implementation, SchemaRef)
        record(self.runtime, SchemaRef)

    def descriptor(self):
        return {
            "provider": self.provider,
            "model": self.model,
            "revision": self.revision,
            "implementation": self.implementation.model_dump(mode="json"),
            "runtime": self.runtime.model_dump(mode="json"),
        }


@dataclass(frozen=True, slots=True)
class InputContract:
    modality: str
    task: str
    role: str
    template: SchemaRef
    instructions: str
    context_schema: SchemaRef | None

    def __post_init__(self):
        identifier(self.modality)
        identifier(self.task)
        require(self.role in ("query", "document", "shared"), "representation_role")
        record(self.template, SchemaRef)
        text(self.instructions, 4096, empty=True)
        if self.context_schema is not None:
            record(self.context_schema, SchemaRef)

    def descriptor(self):
        return {
            "modality": self.modality,
            "task": self.task,
            "role": self.role,
            "template": self.template.model_dump(mode="json"),
            "instructions": self.instructions,
            "context_schema": None
            if self.context_schema is None
            else self.context_schema.model_dump(mode="json"),
        }


@dataclass(frozen=True, slots=True)
class InputPipeline:
    tokenizer: SchemaRef
    preprocessing: SchemaRef
    chunking: SchemaRef
    truncation: SchemaRef
    pooling: SchemaRef

    def __post_init__(self):
        for value in (self.tokenizer, self.preprocessing, self.chunking, self.truncation, self.pooling):
            record(value, SchemaRef)

    def descriptor(self):
        return {
            name: getattr(self, name).model_dump(mode="json")
            for name in ("tokenizer", "preprocessing", "chunking", "truncation", "pooling")
        }


@dataclass(frozen=True, slots=True)
class VectorSpace:
    dimensions: int
    dtype: str
    normalization: str
    metric: str

    def __post_init__(self):
        require(
            type(self.dimensions) is int and 1 <= self.dimensions <= 4096, "representation_dimension_bound"
        )
        require(self.dtype == "float32-le", "representation_dtype")
        require(self.normalization in ("none", "l2"), "representation_normalization")
        require(self.metric in ("dot", "cosine", "euclidean"), "representation_metric")

    def descriptor(self):
        return {
            "dimensions": self.dimensions,
            "dtype": self.dtype,
            "normalization": self.normalization,
            "metric": self.metric,
        }


@dataclass(frozen=True, slots=True)
class RepresentationProfile:
    profile_id: str
    version: str
    encoder: EncoderIdentity
    inputs: InputContract
    pipeline: InputPipeline
    space: VectorSpace
    applicability: tuple[str, ...]
    limitations: tuple[str, ...]
    determinism: str

    def __post_init__(self):
        identifier(self.profile_id)
        identifier(self.version)
        for value, model in (
            (self.encoder, EncoderIdentity),
            (self.inputs, InputContract),
            (self.pipeline, InputPipeline),
            (self.space, VectorSpace),
        ):
            require(type(value) is model, "representation_profile_component")
        labels(self.applicability)
        labels(self.limitations)
        require(self.determinism in ("runtime_pinned", "retained_output_only"), "representation_determinism")

    def descriptor(self):
        return {
            "format": "data.representation-profile.v1",
            "profile_id": self.profile_id,
            "version": self.version,
            "encoder": self.encoder.descriptor(),
            "inputs": self.inputs.descriptor(),
            "pipeline": self.pipeline.descriptor(),
            "space": self.space.descriptor(),
            "applicability": list(self.applicability),
            "limitations": list(self.limitations),
            "determinism": self.determinism,
        }

    @property
    def reference(self):
        return SchemaRef(
            schema_id="data.representation-profile", version="1", sha256=fingerprint(self.descriptor())
        )

    def require_compatible(self, other):
        require(type(other) is RepresentationProfile, "representation_profile_required")
        require(
            self.inputs.role == other.inputs.role == "shared" and self.reference == other.reference,
            "representation_pairing_unconfigured",
        )
