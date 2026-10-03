"""Complete profile identity and explicit pairing, independent of dimensional coincidence."""

from dataclasses import FrozenInstanceError, replace

import pytest
from amphora_contracts_core import SchemaRef
from amphora_data_artifacts.representations.fixture import fixture_profile
from amphora_data_artifacts.representations.profiles import InputContract, RepresentationProfile, VectorSpace
from amphora_data_artifacts.representations.validation import RepresentationError

REFERENCE = SchemaRef(schema_id="fixture.other", version="1", sha256="a" * 64)


@pytest.mark.parametrize(
    "group,field,value",
    [
        (None, "profile_id", "other"),
        (None, "version", "2"),
        (None, "applicability", ("other context",)),
        (None, "limitations", ("other limitation",)),
        (None, "determinism", "retained_output_only"),
        ("encoder", "provider", "other"),
        ("encoder", "model", "other"),
        ("encoder", "revision", "2"),
        ("encoder", "implementation", REFERENCE),
        ("encoder", "runtime", REFERENCE),
        ("inputs", "modality", "sequence"),
        ("inputs", "task", "different"),
        ("inputs", "role", "query"),
        ("inputs", "template", REFERENCE),
        ("inputs", "instructions", "different"),
        ("inputs", "context_schema", REFERENCE),
        ("pipeline", "tokenizer", REFERENCE),
        ("pipeline", "preprocessing", REFERENCE),
        ("pipeline", "chunking", REFERENCE),
        ("pipeline", "truncation", REFERENCE),
        ("pipeline", "pooling", REFERENCE),
        ("space", "dimensions", 32),
        ("space", "normalization", "l2"),
        ("space", "metric", "cosine"),
    ],
)
def test_every_profile_component_changes_identity_and_cannot_silently_pair(group, field, value):
    profile = fixture_profile()
    changed = replace(
        profile,
        **({field: value} if group is None else {group: replace(getattr(profile, group), **{field: value})}),
    )
    assert changed.reference != profile.reference
    with pytest.raises(RepresentationError, match="pairing_unconfigured"):
        profile.require_compatible(changed)


def test_exact_shared_pair_and_immutable_descriptor():
    profile = fixture_profile()
    profile.require_compatible(fixture_profile())
    descriptor = profile.descriptor()
    descriptor["space"]["normalization"] = "l2"
    assert profile.reference == fixture_profile().reference
    with pytest.raises(FrozenInstanceError):
        profile.version = "changed"
    for role in ("query", "document"):
        asymmetric = replace(profile, inputs=replace(profile.inputs, role=role))
        with pytest.raises(RepresentationError, match="pairing_unconfigured"):
            asymmetric.require_compatible(asymmetric)
    with pytest.raises(RepresentationError, match="profile_required"):
        profile.require_compatible(profile.reference)


@pytest.mark.parametrize(
    "field,value,reason",
    [
        ("profile_id", "", "identifier"),
        ("version", True, "identifier"),
        ("encoder", None, "profile_component"),
        ("inputs", None, "profile_component"),
        ("pipeline", None, "profile_component"),
        ("space", None, "profile_component"),
        ("applicability", [], "label_bound"),
        ("applicability", (), "label_bound"),
        ("limitations", ("x",) * 17, "label_bound"),
        ("limitations", ("x", "x"), "duplicate_label"),
        ("limitations", ("",), "text_bound"),
        ("limitations", ("x" * 257,), "text_bound"),
        ("limitations", ("\ud800",), "text_utf8"),
        ("determinism", "guaranteed", "determinism"),
    ],
)
def test_invalid_profile_is_not_a_cache_key(field, value, reason):
    with pytest.raises(RepresentationError, match=reason):
        replace(fixture_profile(), **{field: value})


@pytest.mark.parametrize(
    "field,value,reason",
    [
        ("dimensions", 0, "dimension_bound"),
        ("dimensions", 4097, "dimension_bound"),
        ("dimensions", True, "dimension_bound"),
        ("dimensions", 16.0, "dimension_bound"),
        ("dtype", "float64", "dtype"),
        ("normalization", "implicit", "normalization"),
        ("metric", "unknown", "metric"),
    ],
)
def test_invalid_vector_space(field, value, reason):
    with pytest.raises(RepresentationError, match=reason):
        replace(fixture_profile().space, **{field: value})


def test_nested_schema_references_are_revalidated_and_input_text_is_bounded():
    profile = fixture_profile()
    forged = REFERENCE.model_copy(update={"sha256": "not-a-digest"})
    with pytest.raises(RepresentationError, match="reference_shape"):
        replace(profile.encoder, implementation=forged)
    with pytest.raises(RepresentationError, match="reference_type"):
        replace(profile.pipeline, tokenizer={})
    with pytest.raises(RepresentationError, match="role"):
        replace(profile.inputs, role="implicit")
    with pytest.raises(RepresentationError, match="text_bound"):
        replace(profile.inputs, instructions="x" * 4097)
    with pytest.raises(RepresentationError, match="text_utf8"):
        replace(profile.inputs, instructions="\ud800")
    assert replace(profile.inputs, instructions="x" * 4096).instructions == "x" * 4096
    assert VectorSpace(4096, "float32-le", "none", "euclidean").dimensions == 4096
    assert type(replace(profile.inputs, context_schema=REFERENCE)) is InputContract
    assert type(profile) is RepresentationProfile
