"""Domain boundary verifies interpretation, not merely a DTO's structural validity."""

import hashlib
import struct
from dataclasses import replace

import pytest
from amphora_contracts_core import SchemaRef, Scope
from amphora_contracts_representations import EncodingProfile
from amphora_data_artifacts.representations.fixture import FixtureEncoder, fixture_profile
from amphora_data_artifacts.representations.identity import EncodingInput
from amphora_data_artifacts.representations.mapping import (
    profile_from_wire,
    profile_reference,
    profile_to_wire,
    vector_from_wire,
    vector_to_wire,
)
from amphora_data_artifacts.representations.payloads import EncodedRepresentation
from amphora_data_artifacts.representations.validation import RepresentationError
from amphora_data_artifacts.representations.vectors import Float32Vector

SCOPE = Scope(tenant_id="fixture", project_id="representations")


def encoded():
    profile = fixture_profile()
    source = EncodingInput(b"ABBA")
    return EncodedRepresentation.prepare(profile, source, FixtureEncoder().encode(profile, source))


def test_complete_profile_and_vector_roundtrip_preserves_exact_identities():
    value = encoded()
    wire = profile_to_wire(value.profile)
    assert profile_from_wire(wire) == value.profile
    assert (
        profile_from_wire(EncodingProfile.model_validate_json(wire.model_dump_json())).reference
        == value.profile.reference
    )
    document = vector_to_wire(SCOPE, value)
    assert document.payload_hex == struct.pack("<16f", 0, 2, 2, *([0] * 13)).hex()
    assert document.input_sha256 == hashlib.sha256(b"ABBA").hexdigest()
    assert vector_from_wire(SCOPE, value.profile, document) == value
    changed = replace(value.profile, inputs=replace(value.profile.inputs, instructions="different"))
    with pytest.raises(RepresentationError, match="profile_reference"):
        vector_from_wire(SCOPE, changed, document)
    with pytest.raises(RepresentationError, match="profile_reference"):
        vector_from_wire(SCOPE.model_copy(update={"project_id": "other"}), value.profile, document)
    assert profile_reference(SCOPE, changed).sha256 != document.profile.sha256


@pytest.mark.parametrize(
    "changes,reason",
    [
        ({"dimensions": 15}, "vector_profile"),
        ({"payload_sha256": "a" * 64}, "vector_digest"),
        ({"payload_hex": "00000000"}, "vector_length"),
        ({"payload_hex": ("0000807f" + "00000000" * 15)}, "vector_nonfinite"),
        ({"payload_hex": ("00000080" + "00000000" * 15)}, "vector_negative_zero"),
        ({"context_sha256": "b" * 64}, "context_required"),
        ({"input_sha256": "bad"}, "wire_shape"),
        ({"payload_hex": "invalid"}, "wire_shape"),
    ],
)
def test_retained_payload_tampering_rejected(changes, reason):
    value = encoded()
    document = vector_to_wire(SCOPE, value).model_copy(update=changes)
    with pytest.raises(RepresentationError, match=reason):
        vector_from_wire(SCOPE, value.profile, document)


def test_wire_validation_does_not_replace_domain_invariants_or_input_validation():
    value = encoded()
    wire = profile_to_wire(value.profile)
    duplicate = wire.model_copy(update={"limitations": ("same", "same")})
    with pytest.raises(RepresentationError, match="duplicate_label"):
        profile_from_wire(duplicate)
    with pytest.raises(RepresentationError, match="wire_shape"):
        profile_from_wire(wire.model_copy(update={"version": True}))
    with pytest.raises(RepresentationError, match="wire_type"):
        profile_from_wire(wire.model_dump())
    with pytest.raises(RepresentationError, match="profile_required"):
        profile_to_wire(wire)
    with pytest.raises(RepresentationError, match="encoded_required"):
        vector_to_wire(SCOPE, object())
    with pytest.raises(RepresentationError, match="encoder_input"):
        EncodedRepresentation.prepare(value.profile, b"ABBA", value.vector)
    with pytest.raises(RepresentationError, match="vector_required"):
        replace(value, vector=value.vector.values)
    other = Float32Vector.from_values(replace(value.profile.space, dimensions=1), (1,))
    with pytest.raises(RepresentationError, match="vector_profile"):
        replace(value, vector=other)
    with pytest.raises(RepresentationError, match="profile_required"):
        replace(value, profile=wire)
    with pytest.raises(RepresentationError, match="digest"):
        replace(value, context_sha256="bad")
    context = SchemaRef(schema_id="fixture.context", version="1", sha256="c" * 64)
    profile = replace(value.profile, inputs=replace(value.profile.inputs, context_schema=context))
    contextual = replace(value, profile=profile, context_sha256="d" * 64)
    assert vector_from_wire(SCOPE, profile, vector_to_wire(SCOPE, contextual)) == contextual
