"""Configuration/preflight decisions, separate from permission to provision."""

import hashlib
import ipaddress
from dataclasses import asdict, dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class PreflightDecision:
    blockers: tuple[str, ...]
    limitations: tuple[str, ...]

    @property
    def status(self):
        return "blocked" if self.blockers else "preflight_passed"

    def to_record(self):
        return {"status": self.status, **asdict(self), "authorizes_installation": False}


def assess(profile, observed, environment, *, now=None):
    blockers = []
    def check(condition, reason):
        if not condition:
            blockers.append(reason)
    check(observed.profile_sha256 == hashlib.sha256(profile.canonical_bytes()).hexdigest(), "profile_observation_mismatch")
    try:
        timestamp = datetime.fromisoformat(observed.observed_at)
        age = ((now or datetime.now(timezone.utc)) - timestamp).total_seconds()
        check(-30 <= age <= 300, "observation_expired")
    except (ValueError, TypeError):
        check(False, "observation_timestamp")
    target = profile.target
    check(observed.hostname.lower() == target.host_id.lower(), "target_identity_mismatch")
    for name in ("operating_system", "architecture", "python"):
        check(getattr(observed, name) == getattr(target, name), "host_" + name)
    for actual, minimum, reason in ((observed.cpu_count, target.min_cpu_count, "host_cpu"),
                                    (observed.memory_bytes, target.min_memory_bytes, "host_memory"),
                                    (observed.free_bytes, profile.storage.min_free_bytes, "storage_space")):
        check(type(actual) is int and actual >= minimum, reason)
    check(observed.artifact_directory_exists is True, "storage_directory")
    check(profile.storage.durability != "unverified" and profile.storage.verification_ref is not None, "storage_policy_unverified")
    if target.accelerator == "nvidia":
        check(observed.accelerator.status == "observed" and type(observed.accelerator.device_count) is int
              and observed.accelerator.device_count > 0, "accelerator_unavailable")
    check(all(artifact.supports(target) for artifact in profile.artifacts), "artifact_target_incompatible")
    address = ipaddress.ip_address(profile.access.bind_host)
    if profile.access.mode == "loopback":
        check(address.is_loopback, "loopback_bind_required")
    else:
        networks = ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16", "fc00::/7")
        check(any(address in ipaddress.ip_network(network) for network in networks), "private_lan_bind_required")
        check(profile.access.tls, "private_lan_tls_required")
    for name in profile.credential_names():
        # Report the missing reference, never a value, prefix, hash or length.
        value = environment.get(name)
        check(type(value) is str and bool(value.strip()), "missing_environment:" + name)
    if profile.provider.mode == "remote":
        check(profile.provider.budget_usd_micros > 0, "provider_allowance_required")
        check(profile.provider.data_policy == "synthetic_only", "provider_egress_denied")
    return PreflightDecision(tuple(blockers), (
        "configuration_and_read_only_observations_only", "operator_storage_evidence_not_independently_validated",
        "filesystem_durability_and_network_exposure_require_target_acceptance", "no_model_request_or_spending_authorized"))
