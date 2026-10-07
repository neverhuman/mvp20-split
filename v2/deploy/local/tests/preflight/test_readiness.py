"""Fail closed for incompatible host/package/policy without leaking credentials."""

import hashlib
import json
from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from amphora_deployment import DeploymentProfile
from amphora_deployment.observations import AcceleratorObservation, HostObservation
from amphora_deployment.readiness import assess


@pytest.fixture
def context(record):
    record["storage"].update(durability="local_durable", verification_ref="operator-review-1")
    profile = DeploymentProfile.from_bytes(json.dumps(record).encode())
    now = datetime.now(timezone.utc)
    observation = HostObservation(hashlib.sha256(profile.canonical_bytes()).hexdigest(), now.isoformat(),
        profile.target.host_id, "linux", "x86_64", "3.12", 4, 8192, True, 8192, "unverified",
        AcceleratorObservation("not_required", None), ())
    return profile, observation, now


def test_matching_preflight_is_not_installation_or_durability_authority(context):
    profile, observation, now = context
    decision = assess(profile, observation, {"DEMO_AUTH": "private-value"}, now=now)
    assert decision.status == "preflight_passed"
    assert decision.to_record()["authorizes_installation"] is False
    assert "private-value" not in json.dumps(decision.to_record())


@pytest.mark.parametrize("changes,reason", [
    ({"profile_sha256": "0" * 64}, "profile_observation_mismatch"),
    ({"hostname": "other-host"}, "target_identity_mismatch"),
    ({"architecture": "aarch64"}, "host_architecture"),
    ({"operating_system": "windows"}, "host_operating_system"),
    ({"python": "3.13"}, "host_python"),
    ({"cpu_count": None}, "host_cpu"),
    ({"memory_bytes": 1}, "host_memory"),
    ({"free_bytes": 1}, "storage_space"),
    ({"artifact_directory_exists": False}, "storage_directory"),
    ({"observed_at": "invalid"}, "observation_timestamp"),
    ({"observed_at": "2026-01-01T00:00:00"}, "observation_timestamp"),
])
def test_missing_or_incompatible_observation(context, changes, reason):
    profile, observation, now = context
    assert reason in assess(profile, replace(observation, **changes), {"DEMO_AUTH": "test"}, now=now).blockers


def test_stale_future_and_missing_secrets(context):
    p, o, now = context
    for seconds in (-301, 31):
        changed = replace(o, observed_at=(now + timedelta(seconds=seconds)).isoformat())
        assert "observation_expired" in assess(p, changed, {}, now=now).blockers
    assert "missing_environment:DEMO_AUTH" in assess(p, o, {"DEMO_AUTH": "  "}, now=now).blockers


@pytest.mark.parametrize("address,tls,reason", [
    ("0.0.0.0", True, "private_lan_bind_required"),
    ("8.8.8.8", True, "private_lan_bind_required"),
    ("192.168.1.2", False, "private_lan_tls_required"),
])
def test_lan_policy(context, address, tls, reason):
    p, o, now = context
    p = replace(p, access=replace(p.access, mode="private_lan", bind_host=address, tls=tls))
    assert reason in assess(p, o, {}, now=now).blockers


def test_declared_artifact_storage_accelerator_and_provider(context):
    p, o, now = context
    p = replace(p, storage=replace(p.storage, durability="unverified"), target=replace(p.target, accelerator="nvidia"),
                artifacts=(replace(p.artifacts[0], architecture="aarch64"),),
                access=replace(p.access, bind_host="192.168.1.2"),
                provider=replace(p.provider, mode="remote", endpoint="https://example.invalid", model="test", credential_env="MODEL_KEY"))
    result = assess(p, o, {}, now=now)
    assert {"storage_policy_unverified", "artifact_target_incompatible", "accelerator_unavailable", "loopback_bind_required",
            "provider_allowance_required", "provider_egress_denied", "missing_environment:MODEL_KEY"} <= set(result.blockers)
