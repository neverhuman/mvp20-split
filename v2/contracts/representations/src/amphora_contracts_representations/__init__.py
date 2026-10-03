"""Public representation wire surface. No encoding, authorization or persistence."""

from .bindings import (
    EncodeSourceRequest,
    EncodingPending,
    EncodingPublished,
    EncodingStatus,
    RepresentationBinding,
    RepresentationBindingRef,
    RepresentationVector,
)
from .generations import (
    BuildIndexGeneration,
    IndexGeneration,
    IndexGenerationRef,
    IndexGenerationStatus,
    IndexManifest,
)
from .profiles import (
    EncoderDescriptor,
    EncodingInputDescriptor,
    EncodingPipelineDescriptor,
    EncodingProfile,
    EncodingProfileRef,
    VectorSpaceDescriptor,
)
from .retrieval import RetrievalMatch, RetrievalPolicy, RetrievalRecord, RetrieveRepresentations
from .schema import representation_vector_schema

__all__ = [
    "RetrieveRepresentations",
    "RetrievalMatch",
    "RetrievalPolicy",
    "RetrievalRecord",
    "BuildIndexGeneration",
    "IndexGeneration",
    "IndexGenerationRef",
    "IndexGenerationStatus",
    "IndexManifest",
    "EncodeSourceRequest",
    "EncodingPending",
    "EncodingPublished",
    "EncodingStatus",
    "RepresentationBinding",
    "RepresentationBindingRef",
    "RepresentationVector",
    "EncoderDescriptor",
    "EncodingInputDescriptor",
    "EncodingPipelineDescriptor",
    "EncodingProfile",
    "EncodingProfileRef",
    "VectorSpaceDescriptor",
    "representation_vector_schema",
]
