"""Combine owned origin and fresh prerequisites; outgoing effects remain journal-gated."""

from dataclasses import dataclass
from datetime import UTC, datetime

from ..campaign_authoring import AuthoringPlan
from ..campaign_eligibility import EligibilityBatch, EligibilityObservation
from ..campaign_refresh import RefreshPlan, RefreshResult
from ..context.policy import require
from .origin import StoredCampaignOrigin


@dataclass(frozen=True)
class CompilerPreparation:
    authoring: AuthoringPlan
    origin: StoredCampaignOrigin
    refresh: RefreshResult
    eligibility: EligibilityBatch
    observations: tuple[EligibilityObservation, ...]
    status: str


class CompilerPreparer:
    def __init__(self, origin, refresh):
        self.origin, self.refresh = origin, refresh

    def prepare(self, principal, authoring, eligibility, observations, *, clock=None):
        checked = AuthoringPlan.bind(authoring.review, authoring.budget, owner_id=authoring.owner_id, actor_id=authoring.actor_id)
        require(checked == authoring, 'compiler_preparation_authoring')
        eligibility.verify()
        require(eligibility.review == authoring.review and eligibility.budget == authoring.budget,
                'compiler_preparation_eligibility')
        require(type(observations) is tuple and len(observations) == len(eligibility.requests),
                'compiler_preparation_coverage')
        by_command = {}
        for observation in observations:
            verified = EligibilityObservation.bind(observation.request, observation.receipt)
            require(verified == observation, 'compiler_preparation_observation')
            command = observation.request.command.canonical_bytes
            require(command not in by_command, 'compiler_preparation_duplicate')
            by_command[command] = observation
        ordered = tuple(by_command.get(request.command.canonical_bytes) for request in eligibility.requests)
        require(all(item is not None and item.request == request for item, request in zip(ordered, eligibility.requests, strict=True)),
                'compiler_preparation_request')
        origin = self.origin.read(principal, authoring.review, authoring.budget)
        origin.verify()
        require(origin.review == authoring.review and origin.budget == authoring.budget, 'compiler_preparation_origin')
        plan = RefreshPlan.bind(authoring.review, authoring.budget)
        result = self.refresh.collect(plan)
        require(result.plan == plan, 'compiler_preparation_refresh')
        now = datetime.now(UTC) if clock is None else clock()
        require(isinstance(now, datetime) and now.tzinfo is not None and now.utcoffset() is not None,
                'compiler_preparation_clock')
        if result.failures:
            status = 'input_unavailable'
        elif result.changes:
            status = 'relevant_input_changed'
        elif any(item.status == 'rejected' for item in ordered):
            status = 'eligibility_rejected'
        else:
            status = 'ready_to_journal'
            for item in ordered:
                try:
                    item.require_fresh(now)
                except ValueError as error:
                    if str(error) != 'eligibility_expired':
                        raise
                    status = 'eligibility_expired'
                    break
        return CompilerPreparation(authoring, origin, result, eligibility, ordered, status)
