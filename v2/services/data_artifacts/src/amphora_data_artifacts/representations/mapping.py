"""Explicit wire/domain translations; DTO shape grants no provenance or access authority."""

import json

from amphora_contracts_core import Scope
from amphora_contracts_representations import EncodingProfile, EncodingProfileRef, RepresentationVector
from pydantic import ValidationError

from .payloads import EncodedRepresentation
from .profiles import EncoderIdentity, InputContract, InputPipeline, RepresentationProfile, VectorSpace
from .validation import RepresentationError, record, require
from .vectors import Float32Vector


def _validated(value, model):
    require(type(value) is model, "representation_wire_type")
    try:
        return model.model_validate(value.model_dump(warnings=False), strict=True)
    except ValidationError as error:
        raise RepresentationError("representation_wire_shape") from error


def profile_to_wire(profile):
    require(type(profile) is RepresentationProfile, "representation_profile_required")
    body = profile.descriptor()
    del body["format"]
    return EncodingProfile.model_validate_json(json.dumps({"wire_version": "1", **body}))


def profile_from_wire(value):
    value = _validated(value, EncodingProfile)
    encoder = value.encoder
    inputs = value.inputs
    pipeline = value.pipeline
    space = value.space
    return RepresentationProfile(
        value.profile_id,
        value.version,
        EncoderIdentity(
            encoder.provider, encoder.model, encoder.revision, encoder.implementation, encoder.runtime
        ),
        InputContract(
            inputs.modality,
            inputs.task,
            inputs.role,
            inputs.template,
            inputs.instructions,
            inputs.context_schema,
        ),
        InputPipeline(
            pipeline.tokenizer,
            pipeline.preprocessing,
            pipeline.chunking,
            pipeline.truncation,
            pipeline.pooling,
        ),
        VectorSpace(space.dimensions, space.dtype, space.normalization, space.metric),
        value.applicability,
        value.limitations,
        value.determinism,
    )


def profile_reference(scope, profile):
    record(scope, Scope)
    require(type(profile) is RepresentationProfile, "representation_profile_required")
    return EncodingProfileRef(
        scope=scope, profile_id=profile.profile_id, version=profile.version, sha256=profile.reference.sha256
    )


def vector_to_wire(scope, encoded):
    require(type(encoded) is EncodedRepresentation, "representation_encoded_required")
    return RepresentationVector(
        wire_version="1",
        profile=profile_reference(scope, encoded.profile),
        input_sha256=encoded.input_sha256,
        context_sha256=encoded.context_sha256,
        dimensions=encoded.vector.space.dimensions,
        dtype=encoded.vector.space.dtype,
        payload_hex=encoded.vector.payload.hex(),
        payload_sha256=encoded.vector.sha256,
    )


def vector_from_wire(scope, profile, value):
    value = _validated(value, RepresentationVector)
    require(value.profile == profile_reference(scope, profile), "representation_profile_reference")
    require(
        (value.dimensions, value.dtype) == (profile.space.dimensions, profile.space.dtype),
        "representation_vector_profile",
    )
    vector = Float32Vector(profile.space, bytes.fromhex(value.payload_hex))
    require(vector.sha256 == value.payload_sha256, "representation_vector_digest")
    return EncodedRepresentation(profile, value.input_sha256, value.context_sha256, vector)
