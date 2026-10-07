"""Local configuration boundary: declared compatibility is not host readiness."""

import copy
import json

import pytest

from amphora_deployment import DeploymentProfile, ProfileError




def parse(record):
    return DeploymentProfile.from_bytes(json.dumps(record).encode())


def test_roundtrip_immutable_compatibility_and_secret_references(record):
    profile = parse(record)
    assert DeploymentProfile.from_bytes(profile.canonical_bytes()) == profile
    assert profile.credential_names() == ("DEMO_AUTH",)
    assert profile.artifacts[0].supports(profile.target)
    record["target"]["architecture"] = "aarch64"
    assert not parse(record).artifacts[0].supports(parse(record).target)
    assert profile.storage.durability == "unverified"  # Parsing never promotes readiness.


@pytest.mark.parametrize("owner,key,value,reason", [
    (None, "schema_version", "2", "profile_version"),
    (None, "profile_id", "../escape", "profile_id"),
    ("target", "min_cpu_count", True, "target_cpu"),
    ("target", "min_memory_bytes", 0, "target_memory"),
    ("target", "operating_system", "other", "target_system"),
    ("target", "architecture", "amd64", "target_architecture"),
    ("target", "python", "3.13", "target_python"),
    ("target", "accelerator", "anything", "target_accelerator"),
    ("storage", "artifact_root", "relative", "storage_absolute_path"),
    ("storage", "artifact_root", "/tmp/../data", "storage_absolute_path"),
    ("storage", "min_free_bytes", -1, "storage_space"),
    ("access", "bind_host", "hostname.invalid", "access_bind_address"),
    ("access", "auth_secret_env", "literal-secret-value", "access_secret_reference"),
    ("access", "tls", "yes", "access_shape"),
    ("provider", "budget_usd_micros", True, "provider_budget"),
    ("provider", "budget_usd_micros", 1, "provider_disabled_fields"),
    ("provider", "data_policy", "all_data", "provider_data_policy"),
])
def test_named_rejections(record, owner, key, value, reason):
    (record if owner is None else record[owner])[key] = value
    with pytest.raises(ProfileError, match="^" + reason + "$"):
        parse(record)


def test_duplicate_unknown_fields_and_bounds(record):
    for raw, reason in [(b'{"x":1,"x":2}', "profile_duplicate_key"),
                        (b"{", "profile_json"), (b"\xff", "profile_json"),
                        (b"[" * 2000 + b"]" * 2000, "profile_(json|fields)"), (b"x" * 65537, "profile_bytes")]:
        with pytest.raises(ProfileError, match=reason):
            DeploymentProfile.from_bytes(raw)
    record["unexpected"] = "hidden authority"
    with pytest.raises(ProfileError, match="profile_fields"):
        parse(record)
    del record["unexpected"]
    record["artifacts"].append(copy.deepcopy(record["artifacts"][0]))
    with pytest.raises(ProfileError, match="profile_duplicate_artifact"):
        parse(record)


def test_remote_credentials_are_references_and_endpoint_cannot_hide_secrets(record):
    record["provider"] = {"mode": "remote", "endpoint": "https://example.invalid/v1", "model": "fixture-model",
        "credential_env": "MODEL_KEY", "budget_usd_micros": 100000, "data_policy": "synthetic_only"}
    assert parse(record).credential_names() == ("DEMO_AUTH", "MODEL_KEY")
    for endpoint in ("http://example.invalid", "https://user:secret@example.invalid", "https://example.invalid?key=secret", "https://example.invalid:invalid", "https://exam\nple.invalid"):
        record["provider"]["endpoint"] = endpoint
        with pytest.raises(ProfileError, match="^provider_endpoint$") as error:
            parse(record)
        assert "secret" not in str(error.value)


def test_windows_target_path_is_parsed_independently_of_test_host(record):
    record["target"]["operating_system"] = "windows"
    record["storage"]["artifact_root"] = "C:/amphora/artifacts"
    assert parse(record).storage.artifact_root == "C:/amphora/artifacts"
    record["storage"]["artifact_root"] = "C:relative"
    with pytest.raises(ProfileError, match="storage_absolute_path"):
        parse(record)
