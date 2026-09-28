"""Independent policy observations and bounded capacity freshness."""

from dataclasses import dataclass
from datetime import datetime

from amphora_contracts_core import Scope
from amphora_contracts_tools import CapacityAssessment, PolicyAdmission, ScientificEligibility


@dataclass(frozen=True, slots=True)
class Assessment:
    status: str
    reasons: tuple[str, ...]

    def scientific_wire(self):
        return ScientificEligibility(status=self.status, reason_codes=self.reasons)

    def capacity_wire(self):
        return CapacityAssessment(status=self.status, reason_codes=self.reasons)

    def admission_wire(self):
        return PolicyAdmission(status=self.status, reason_codes=self.reasons)


def aware(value):
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("Explicit timezone-aware observation time required")


@dataclass(frozen=True, slots=True)
class CapacityObservation:
    scope: Scope
    descriptor_sha256: str
    healthy_replicas: int
    free_slots: int
    sampled_at: datetime
    expires_at: datetime

    def __post_init__(self):
        aware(self.sampled_at)
        aware(self.expires_at)
        if not 0 < (self.expires_at - self.sampled_at).total_seconds() <= 300:
            raise ValueError("Capacity observation lifetime must be bounded")
        if any(type(value) is not int or not 0 <= value <= 1048576 for value in (self.healthy_replicas, self.free_slots)):
            raise ValueError("Invalid capacity counters")
        if not self.healthy_replicas and self.free_slots:
            raise ValueError("No slots without a healthy replica")
        if len(self.descriptor_sha256) != 64 or any(c not in "0123456789abcdef" for c in self.descriptor_sha256):
            raise ValueError("Exact descriptor digest required")

    def assess(self, scope, descriptor_sha256, now, max_parallel):
        aware(now)
        if self.scope != scope or self.descriptor_sha256 != descriptor_sha256:
            return Assessment("unknown", ("capacity_binding_mismatch",))
        if now < self.sampled_at or now >= self.expires_at:
            return Assessment("unknown", ("capacity_observation_stale",))
        if self.free_slots > self.healthy_replicas * max_parallel:
            return Assessment("unknown", ("capacity_counts_inconsistent",))
        if self.healthy_replicas == 0:
            return Assessment("unavailable", ("no_healthy_replicas",))
        if self.free_slots == 0:
            return Assessment("unavailable", ("capacity_busy",))
        return Assessment("available", ("healthy_capacity",))


class SyntheticScientificPolicy:
    profile = "synthetic-only-v1"

    def assess(self, descriptor, need, report):
        if not report.valid:
            return Assessment("unreviewed", ("descriptor_invalid",))
        if need.context != "synthetic-tests":
            return Assessment("ineligible", ("synthetic_profile_only",))
        if need.context not in descriptor.tool.applicability:
            return Assessment("ineligible", ("context_not_supported",))
        if descriptor.authority_ceiling != "synthetic_only":
            return Assessment("unreviewed", ("scientific_evidence_unreviewed",))
        return Assessment("eligible", ("synthetic_fixture_only",))
