"""Pin and freshness policy for public Registry observations."""

from dataclasses import dataclass
from datetime import timedelta

from ...coordinator.values import ensure
from ...lifecycle.model import TransitionError


class EligibilityUnavailable(TransitionError):
    """Unavailable observation rejects admission before any run or execution effect exists."""


@dataclass(frozen=True, slots=True)
class EligibilityObservation:
    command: object
    receipt: object
    maximum_age_seconds: int

    @classmethod
    def bind(cls, command, receipt, reviewed, maximum_age_seconds):
        if receipt.status == "rejected":
            ensure(False, "draft_tool_ineligible")
        release, decision = receipt.release, receipt.decision
        valid = (receipt.status == "accepted" and receipt.reason_code == "candidate" and release is not None
                 and decision is not None and receipt.deployment is None and receipt.heartbeat is None)
        if not valid:
            raise EligibilityUnavailable("draft_registry_response_invalid")
        scope = command.identity.scope
        observations = decision.observations
        if (release.scope != scope or release.lock != reviewed.lock or release.descriptor != reviewed.descriptor
                or release.status != "active" or observations.scope != scope or observations.release != reviewed.lock
                or observations.structural.status != "valid" or observations.scientific.status != "eligible"
                or observations.capacity.status != "available" or decision.admission.status != "allowed"
                or decision.status != "candidate" or decision.capacity_valid_until is None
                or decision.capacity_valid_until <= decision.assessed_at):
            raise EligibilityUnavailable("draft_registry_response_invalid")
        if reviewed.execution_profile is not None:
            if observations.scientific.reason_codes != ("supplied_structure_mapping_only",):
                raise EligibilityUnavailable("draft_registry_response_invalid")
        return cls(command, receipt, maximum_age_seconds)

    def require_fresh(self, now):
        decision = self.receipt.decision
        ensure(decision.assessed_at <= now < decision.capacity_valid_until
               and now - decision.assessed_at <= timedelta(seconds=self.maximum_age_seconds),
               "draft_tool_eligibility_expired")

    def record(self):
        return {"command_identity": self.command.identity.model_dump(mode="json"),
                "request_sha256": self.command.sha256, "receipt": self.receipt.model_dump(mode="json"),
                "maximum_age_seconds": self.maximum_age_seconds}
