"""Deterministic owner selection policy; no registration, dispatch or promotion."""

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime

from amphora_contracts_core import Scope
from amphora_contracts_tools import EligibilityDecision, EligibilityResult

from .assessments import Assessment, SyntheticScientificPolicy, aware
from .identity import ReleaseDocument
from .requirements import ResourceAllowance, compatibility_rejections
from .validation import DescriptorValidator, ValidationReport


@dataclass(frozen=True, slots=True)
class PermissionPolicy:
    allowed_egress_hosts: tuple[str, ...] = ()

    def __post_init__(self):
        if (not isinstance(self.allowed_egress_hosts, tuple) or len(self.allowed_egress_hosts) > 64
            or len(set(self.allowed_egress_hosts)) != len(self.allowed_egress_hosts)
            or any(not isinstance(host, str) or len(host) > 253 or not re.fullmatch(r"[a-z0-9]+(?:[.-][a-z0-9]+)*", host)
                   for host in self.allowed_egress_hosts)):
            raise ValueError("Explicit bounded egress host allowlist required")

    def rejections(self, descriptor):
        reasons = []
        if descriptor.tool.side_effects != "pure":
            reasons.append("effect_class_unsupported")
        if descriptor.egress.mode == "allowlist" and not set(descriptor.egress.hosts) <= set(self.allowed_egress_hosts):
            reasons.append("egress_forbidden")
        return tuple(reasons)


@dataclass(frozen=True, slots=True)
class EvaluationPolicy:
    scope: Scope
    resources: ResourceAllowance
    permissions: PermissionPolicy

    @property
    def digest(self):
        value = {"profile": "amphora-tool-selection-v1", "scientific_profile": SyntheticScientificPolicy.profile,
                 "scope": self.scope.model_dump(mode="json"), "resources": asdict(self.resources),
                 "permissions": {"allowed_egress_hosts": sorted(self.permissions.allowed_egress_hosts), "effects": ["pure"]}}
        return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()


@dataclass(frozen=True, slots=True)
class AssessmentSet:
    structural: ValidationReport
    scientific: Assessment
    capacity: Assessment
    admission: Assessment

    @property
    def candidate(self):
        return (self.structural.valid and self.scientific.status == "eligible"
                and self.capacity.status == "available" and self.admission.status == "allowed")


@dataclass(frozen=True, slots=True)
class ObservationWindow:
    assessed_at: datetime
    capacity_valid_until: datetime | None


@dataclass(frozen=True, slots=True)
class SelectionEvaluation:
    scope: Scope
    release: ReleaseDocument
    policy_digest: str
    assessments: AssessmentSet
    window: ObservationWindow

    def to_wire(self):
        values = self.assessments
        observed = EligibilityResult(scope=self.scope, release=self.release.to_lock(), policy_sha256=self.policy_digest,
            structural=values.structural.to_wire(), scientific=values.scientific.scientific_wire(), capacity=values.capacity.capacity_wire())
        return EligibilityDecision(observations=observed, admission=values.admission.admission_wire(),
            status="candidate" if values.candidate else "rejected", assessed_at=self.window.assessed_at,
            capacity_valid_until=self.window.capacity_valid_until)


class EligibilityEvaluator:
    def evaluate(self, descriptor, need, policy, capacity, *, now):
        aware(now)
        if need.scope != policy.scope:
            raise ValueError("policy_scope_mismatch")
        release = ReleaseDocument.from_descriptor(descriptor)
        structural = DescriptorValidator().validate(descriptor)
        scientific = SyntheticScientificPolicy().assess(descriptor, need, structural)
        observed = Assessment("unknown", ("capacity_unobserved",)) if capacity is None else capacity.assess(
            need.scope, release.digest, now, descriptor.resources.max_parallel_invocations)
        reasons = compatibility_rejections(descriptor, need) + policy.permissions.rejections(descriptor) + policy.resources.rejections(descriptor.resources)
        if not structural.valid:
            reasons = ("descriptor_invalid", *reasons)
        reasons = tuple(dict.fromkeys(reasons))
        admission = Assessment("denied", reasons) if reasons else Assessment("allowed", ("policy_compatible",))
        expires = capacity.expires_at if capacity is not None and observed.status != "unknown" else None
        return SelectionEvaluation(need.scope, release, policy.digest, AssessmentSet(structural, scientific, observed, admission),
                                   ObservationWindow(now, expires))
