"""Exact expiring eligibility observations, never capacity reservations."""

from dataclasses import dataclass
from datetime import datetime, timedelta

from amphora_contracts_tools import RegistryReceipt

from ..context.policy import require
from ..registry_access import ObservedRelease
from .request import EligibilityRequest


@dataclass(frozen=True)
class EligibilityObservation:
    request: EligibilityRequest
    receipt: RegistryReceipt
    status: str

    @classmethod
    def bind(cls, request, receipt):
        request.verify()
        receipt = RegistryReceipt.model_validate_json(receipt.model_dump_json())
        if receipt.status == 'rejected':
            # Negative observations remain negative, even if ancillary fields are
            # present; no positive eligibility is inferred from them.
            return cls(request, receipt, 'rejected')
        require(receipt.reason_code == 'candidate' and receipt.release is not None and receipt.decision is not None
                and receipt.deployment is None and receipt.heartbeat is None, 'eligibility_response_shape')
        selected = request.selected.document()
        observed = ObservedRelease.bind(receipt.release, selected.scope, selected.lock).document()
        require(observed.descriptor == selected.descriptor and observed.status == 'active', 'eligibility_release_status')
        decision = receipt.decision
        result = decision.observations
        require(result.scope == selected.scope and result.release == selected.lock, 'eligibility_observation_identity')
        require(result.policy_sha256 == request.configuration.document().policy_sha256, 'eligibility_policy')
        require(result.structural.status == 'valid' and result.scientific.status == 'eligible' and
                result.capacity.status == 'available' and decision.admission.status == 'allowed' and
                decision.status == 'candidate', 'eligibility_positive_statuses')
        require(decision.capacity_valid_until is not None and decision.capacity_valid_until > decision.assessed_at,
                'eligibility_expiry_window')
        return cls(request, receipt, 'candidate')

    def require_fresh(self, now):
        require(self.bind(self.request, self.receipt) == self, 'eligibility_observation_binding')
        require(isinstance(now, datetime) and now.tzinfo is not None and now.utcoffset() is not None,
                'eligibility_clock')
        require(self.status == 'candidate', 'eligibility_rejected')
        decision = self.receipt.decision
        maximum = self.request.configuration.document().maximum_age_seconds
        require(decision.assessed_at <= now < decision.capacity_valid_until and
                now - decision.assessed_at <= timedelta(seconds=maximum), 'eligibility_expired')
        return self
