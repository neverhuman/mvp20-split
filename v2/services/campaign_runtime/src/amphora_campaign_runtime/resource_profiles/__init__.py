"""Immutable invocation capacity selected explicitly at admission."""

from dataclasses import dataclass

from amphora_contracts_campaign_resources import CampaignInvocationResources
from pydantic import ValidationError

from ..lifecycle.model import TransitionError


@dataclass(frozen=True, slots=True)
class InvocationCapacity:
    maximum: int | None

    @classmethod
    def from_snapshot(cls, snapshot):
        if "resources" not in snapshot:
            return cls(None)
        try:
            resources = CampaignInvocationResources.model_validate(snapshot["resources"])
        except ValidationError as error:
            raise TransitionError("unsupported_resource_profile") from error
        return cls(resources.max_active_attempts)

    def available(self, budget):
        return self.maximum is None or budget.reserved < self.maximum
