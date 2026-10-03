"""Literal vector oracles; no semantic, permission, publication or cache-store claim."""

import hashlib
import math
import struct
from dataclasses import replace

import pytest
from amphora_contracts_core import SchemaRef, Scope
from amphora_data_artifacts.representations.fixture import FixtureEncoder, fixture_profile
from amphora_data_artifacts.representations.identity import EncodingInput, EncodingWorkIdentity
from amphora_data_artifacts.representations.validation import RepresentationError
from amphora_data_artifacts.representations.vectors import Float32Vector

SCOPE = Scope(tenant_id="fixture", project_id="representations")


def test_reviewed_v2_l2_profile_preserves_legacy_encoders_and_rejects_arbitrary_versions():
    encoder = FixtureEncoder()
    source = EncodingInput(b"AAAABBB")
    legacy = fixture_profile("l2")
    current = fixture_profile("l2", version="2")
    assert legacy.version == "1" and current.version == "2"
    assert legacy.reference != current.reference
    assert encoder.encode(legacy, source) == encoder.encode(current, source)
    assert encoder.available(fixture_profile())
    assert not encoder.available(replace(current, version="3"))
    assert not encoder.available(replace(fixture_profile(), version="2"))
    for normalization, version in (("none", "2"), ("l2", "3"), ("l2", True)):
        with pytest.raises(RepresentationError, match="fixture_version"):
            fixture_profile(normalization, version=version)


def test_literal_histogram_unicode_and_explicit_float32_normalization():
    encoder = FixtureEncoder()
    plain = encoder.encode(fixture_profile(), EncodingInput(b"ABBA"))
    expected = (0, 2, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    assert plain.values == expected and plain.payload == struct.pack("<16f", *expected)
    assert plain.sha256 == hashlib.sha256(struct.pack("<16f", *expected)).hexdigest()
    unicode = encoder.encode(fixture_profile(), EncodingInput("é".encode("utf-8")))
    assert unicode.values == (0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0)
    normalized = encoder.encode(fixture_profile("l2"), EncodingInput(b"AAAABBB"))
    assert normalized.payload == struct.pack("<16f", 0, 0.8, 0.6, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    assert math.isclose(sum(value * value for value in normalized.values), 1, rel_tol=1e-7)
    maximum = encoder.encode(fixture_profile(), EncodingInput(b"A" * 65536))
    assert maximum.values[1] == 65536


def test_work_identity_preserves_original_input_profile_context_and_scope():
    profile = fixture_profile()
    source = EncodingInput(b" ABBA\n")
    work = EncodingWorkIdentity.prepare(SCOPE, profile, source)
    assert source.content == b" ABBA\n" and source.sha256 == hashlib.sha256(b" ABBA\n").hexdigest()
    assert EncodingWorkIdentity.prepare(SCOPE, profile, EncodingInput(b" ABBA\n")) == work
    for scope, chosen, content in (
        (SCOPE, profile, EncodingInput(b"ABBA")),
        (SCOPE, fixture_profile("l2"), source),
        (SCOPE.model_copy(update={"project_id": "other"}), profile, source),
    ):
        assert EncodingWorkIdentity.prepare(scope, chosen, content).sha256 != work.sha256
    context = SchemaRef(schema_id="fixture.context", version="1", sha256="a" * 64)
    contextual = replace(profile, inputs=replace(profile.inputs, context_schema=context))
    first = EncodingWorkIdentity.prepare(SCOPE, contextual, EncodingInput(b"ABBA", "b" * 64))
    second = EncodingWorkIdentity.prepare(SCOPE, contextual, EncodingInput(b"ABBA", "c" * 64))
    assert first.sha256 != second.sha256
    for selected, input in ((profile, EncodingInput(b"ABBA", "b" * 64)), (contextual, source)):
        with pytest.raises(RepresentationError, match="context_required"):
            EncodingWorkIdentity.prepare(SCOPE, selected, input)


@pytest.mark.parametrize(
    "value,reason",
    [
        (b"", "input_bound"),
        (b"x" * 65537, "input_bound"),
        (bytearray(b"x"), "input_bound"),
        ("x", "input_bound"),
        (b"\xff", "input_utf8"),
        (b"\xc3", "input_utf8"),
    ],
    ids=["empty", "oversize", "mutable", "text", "invalid-utf8", "truncated-utf8"],
)
def test_no_truncation_or_replacement_character_fallback(value, reason):
    with pytest.raises(RepresentationError, match=reason):
        EncodingInput(value)


def test_identity_and_encoder_reject_unreviewed_profiles_and_forged_references():
    profile = fixture_profile()
    source = EncodingInput(b"ABBA")
    encoder = FixtureEncoder()
    for changed in (
        replace(profile, inputs=replace(profile.inputs, instructions="extra")),
        replace(profile, space=replace(profile.space, metric="cosine")),
    ):
        with pytest.raises(RepresentationError, match="encoder_unavailable"):
            encoder.encode(changed, source)
    with pytest.raises(RepresentationError, match="encoder_unavailable"):
        encoder.encode(profile, EncodingInput(b"ABBA", "a" * 64))
    with pytest.raises(RepresentationError, match="encoder_input"):
        encoder.encode(profile, b"ABBA")
    with pytest.raises(RepresentationError, match="work_input"):
        EncodingWorkIdentity.prepare(SCOPE, profile, b"ABBA")
    with pytest.raises(RepresentationError, match="digest"):
        EncodingInput(b"ABBA", "bad")
    work = EncodingWorkIdentity.prepare(SCOPE, profile, source)
    with pytest.raises(RepresentationError, match="reference_shape"):
        replace(work, scope=SCOPE.model_copy(update={"tenant_id": ""}))
    with pytest.raises(RepresentationError, match="profile_reference"):
        replace(work, profile=profile.reference.model_copy(update={"schema_id": "other"}))
    with pytest.raises(RepresentationError, match="digest"):
        replace(work, input_sha256="bad")
    with pytest.raises(RepresentationError, match="digest"):
        replace(work, context_sha256="bad")


@pytest.mark.parametrize(
    "value,reason",
    [
        (float("nan"), "nonfinite"),
        (float("inf"), "nonfinite"),
        (-float("inf"), "nonfinite"),
        (True, "number"),
        ("1", "number"),
        (1e39, "overflow"),
        (10**1000, "overflow"),
    ],
)
def test_invalid_vector_number_never_produces_reusable_payload(value, reason):
    with pytest.raises(RepresentationError, match=reason):
        Float32Vector.from_values(replace(fixture_profile().space, dimensions=1), (value,))


def test_canonical_binary32_bounds_zero_and_rounding_are_explicit():
    space = replace(fixture_profile().space, dimensions=1)
    assert Float32Vector.from_values(space, (-0.0,)).payload == b"\0" * 4
    assert Float32Vector.from_values(space, (-1e-100,)).payload == b"\0" * 4
    assert Float32Vector.from_values(space, (0.1,)).payload == bytes.fromhex("cdcccc3d")
    for raw, reason in (
        (b"\0" * 3, "length"),
        (b"\0" * 8, "length"),
        (struct.pack("<f", float("nan")), "nonfinite"),
        (struct.pack("<f", -0.0), "negative_zero"),
    ):
        with pytest.raises(RepresentationError, match=reason):
            Float32Vector(space, raw)
    with pytest.raises(RepresentationError, match="vector_length"):
        Float32Vector.from_values(space, [1])
    with pytest.raises(RepresentationError, match="vector_space"):
        Float32Vector.from_values(None, (1,))
    with pytest.raises(RepresentationError, match="vector_space"):
        Float32Vector(None, b"\0" * 4)
