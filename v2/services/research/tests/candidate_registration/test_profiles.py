import hashlib
import json
from pathlib import Path

import pytest
from amphora_contracts_core import ArtifactRef, SchemaRef, Scope
from amphora_research.candidate_registration.profiles import (
    CandidateProfile,
    CandidateProfiles,
    CandidateRegistrationError,
    schema_reference,
)


def fixture():
    data = json.loads(Path(__file__).with_name("sequence.json").read_bytes())
    profile = CandidateProfile(
        schema_reference("candidate-space.sequence"),
        "sequence",
        SchemaRef.model_validate(data["profile"]),
    )
    return data, profile


def reference(data, profile):
    raw = json.dumps(data).encode()
    ref = ArtifactRef(
        artifact_id="source",
        scope=Scope.model_validate(data["scope"]),
        sha256=hashlib.sha256(raw).hexdigest(),
        size_bytes=len(raw),
        schema_ref=profile.schema,
        media_type="application/json",
    )
    return ref, raw


def test_exact_encoding_and_multiple_reviewed_profiles():
    data, profile = fixture()
    ref, raw = reference(data, profile)
    wrong = CandidateProfile(
        profile.schema,
        "sequence",
        profile.semantic_profile.model_copy(update={"sha256": "f" * 64}),
    )
    assert CandidateProfiles([wrong, profile]).validate(ref, raw).sequence == "ACGT"
    with pytest.raises(CandidateRegistrationError, match="binding"):
        CandidateProfiles([wrong]).validate(ref, raw)


@pytest.mark.parametrize("kind", ["numeric", "polymer", "sequence", "change"])
def test_owned_schema_matches_public_bytes(kind):
    ref = schema_reference("candidate-space." + kind)
    root = Path(__file__).absolute().parents[4]
    raw = (
        root / "contracts/schemas/v1" / (ref.schema_id + ".validation.json")
    ).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == ref.sha256


def test_configuration_rejects_unknown_forged_and_duplicate_profiles():
    _, profile = fixture()
    with pytest.raises(CandidateRegistrationError, match="unsupported"):
        schema_reference("unknown")
    with pytest.raises(CandidateRegistrationError, match="invalid"):
        CandidateProfile(
            profile.schema.model_copy(update={"sha256": "f" * 64}),
            "sequence",
            profile.semantic_profile,
        )
    with pytest.raises(CandidateRegistrationError, match="kind_mismatch"):
        CandidateProfile(profile.schema, "polymer", profile.semantic_profile)
    for values in ([], [profile, profile]):
        with pytest.raises(CandidateRegistrationError, match="profiles_invalid"):
            CandidateProfiles(values)


@pytest.mark.parametrize(
    "body",
    [b'{"a":1,"a":2}', b'{"a":NaN}', b"{}", b"\xff", b"x" * 262145],
    ids=["duplicate", "nonfinite", "shape", "encoding", "capacity"],
)
def test_bad_encoding_does_not_become_candidate(body):
    data, profile = fixture()
    with pytest.raises(CandidateRegistrationError):
        profile.decode(body, Scope.model_validate(data["scope"]))


def test_integrity_scope_kind_schema_and_capacity_are_not_trusted():
    data, profile = fixture()
    ref, raw = reference(data, profile)
    profiles = CandidateProfiles([profile])
    with pytest.raises(CandidateRegistrationError, match="integrity"):
        profiles.validate(ref, raw + b" ")
    for change in (
        {"size_bytes": 262145},
        {"media_type": "text/plain"},
        {"schema_ref": ref.schema_ref.model_copy(update={"sha256": "f" * 64})},
    ):
        with pytest.raises(CandidateRegistrationError):
            profiles.admit(ref.model_copy(update=change))
    with pytest.raises(CandidateRegistrationError, match="binding"):
        profile.decode(raw, ref.scope.model_copy(update={"project_id": "foreign"}))


def test_proposal_wrapper_keeps_declared_provenance_without_execution_claim():
    data, original = fixture()
    profile = CandidateProfile(
        schema_reference("candidate-space.change"),
        "sequence",
        original.semantic_profile,
    )
    proposal = {
        "wire_version": "1",
        "source_sha256": "b" * 64,
        "operator": original.semantic_profile.model_dump(),
        "move": {"kind": "substitute_base", "position": 0, "base": "A"},
        "result": data,
    }
    result = profile.decode(
        json.dumps(proposal).encode(), Scope.model_validate(data["scope"])
    )
    assert result.sequence == "ACGT" and result.authority == "synthetic"


def test_matching_metadata_does_not_excuse_invalid_body():
    data, profile = fixture()
    ref, _ = reference(data, profile)
    raw = b"{}"
    ref = ref.model_copy(update={"sha256": hashlib.sha256(raw).hexdigest(), "size_bytes": len(raw)})
    with pytest.raises(CandidateRegistrationError, match="representation_invalid"):
        CandidateProfiles([profile]).validate(ref, raw)


def test_host_rejects_nonlist_profiles_before_sql():
    from amphora_research.candidate_registration.host import configured
    from amphora_research.transport.host import _keys
    config = {"data": {"endpoint": "http://127.0.0.1:1", "token_env": "TOKEN"}, "profiles": {}}
    with pytest.raises(CandidateRegistrationError, match="profiles_invalid"):
        configured(None, config, _keys, lambda name: "a" * 32)
