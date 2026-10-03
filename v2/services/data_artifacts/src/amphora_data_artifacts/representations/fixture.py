"""Reviewed synthetic byte histogram; not a scientifically useful embedding model."""

import hashlib
import math
import sys

from amphora_contracts_core import SchemaRef

from .identity import EncodingInput
from .profiles import EncoderIdentity, InputContract, InputPipeline, RepresentationProfile, VectorSpace
from .validation import require
from .vectors import Float32Vector


def _reference(name, descriptor, version="1"):
    return SchemaRef(
        schema_id=name, version=version, sha256=hashlib.sha256(descriptor.encode("utf-8")).hexdigest()
    )


def fixture_profile(normalization="none", *, version="1"):
    require(version == "1" or (version == "2" and normalization == "l2"), "representation_fixture_version")
    identity = _reference("fixture.identity", "preserve exact bytes; no hidden transform")
    encoder = EncoderIdentity(
        "fixture",
        "utf8-byte-histogram",
        "1",
        _reference(
            "fixture.histogram",
            "UTF8; byte modulo16 counts; optional L2 by sqrt(sum(count squared)); finite binary32 little endian; positive zero",
        ),
        _reference("fixture.runtime", sys.implementation.name + "|" + sys.version + "|" + sys.platform),
    )
    inputs = InputContract("text", "fixture.retrieval", "shared", identity, "", None)
    pipeline = InputPipeline(
        identity,
        identity,
        identity,
        identity,
        _reference("fixture.pooling", "count bytes by residue modulo16"),
    )
    return RepresentationProfile(
        "fixture.utf8-histogram",
        version,
        encoder,
        inputs,
        pipeline,
        VectorSpace(16, "float32-le", normalization, "dot"),
        ("synthetic protocol and ranking fixtures",),
        (
            "No semantic or scientific similarity claim",
            "Runtime-pinned arithmetic; no cross-provider reproducibility claim",
        ),
        "runtime_pinned",
    )


class FixtureEncoder:
    @staticmethod
    def available(profile):
        if type(profile) is not RepresentationProfile or profile.version not in {"1", "2"}:
            return False
        if profile.version == "2" and profile.space.normalization != "l2":
            return False
        return profile == fixture_profile(profile.space.normalization, version=profile.version)

    def encode(self, profile, source):
        require(
            type(profile) is RepresentationProfile and type(source) is EncodingInput,
            "representation_encoder_input",
        )
        require(self.available(profile) and source.context_sha256 is None, "representation_encoder_unavailable")
        counts = [0] * 16
        for value in source.content:
            counts[value % 16] += 1
        if profile.space.normalization == "l2":
            length = math.sqrt(sum(value * value for value in counts))
            values = tuple(value / length for value in counts)
        else:
            values = tuple(counts)
        return Float32Vector.from_values(profile.space, values)
