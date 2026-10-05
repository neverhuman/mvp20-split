"""Consumed processing inputs and selected semantic dependencies have distinct scopes."""

from dataclasses import dataclass

from amphora_contracts_core import ArtifactRef

from ..budget import BudgetPolicy
from ..campaign_context import ResearchSelection
from ..campaign_context.records import canonical
from ..campaign_decisions import CampaignDecisionReview
from ..context.policy import require
from ..registry_access import ObservedRelease


@dataclass(frozen=True)
class RefreshPlan:
    review: CampaignDecisionReview
    budget: BudgetPolicy
    artifacts: tuple[ArtifactRef, ...]
    research: ResearchSelection | None
    releases: tuple[ObservedRelease, ...]

    @classmethod
    def bind(cls, review, budget):
        verified = CampaignDecisionReview.bind(review.composition.evidence.proposal, review.declaration, budget)
        require(verified == review, 'refresh_review_binding')
        preparation = review.composition.evidence.proposal.inputs.preparation
        artifacts = tuple(ArtifactRef.model_validate_json(canonical(row['identity']))
                          for row in preparation.packet.context()['slices']
                          if row['lane'] == 'artifact' and row['payload']['status'] == 'available')
        require(len(artifacts) <= 132 and len(set(artifacts)) == len(artifacts), 'refresh_artifact_limit')
        research = review.composition.evidence.research
        releases = {use.release.record.document().lock: use.release.record for use in review.composition.uses}
        require(len(releases) <= 64, 'refresh_release_limit')
        return cls(review, budget, artifacts, None if research is None else research.context.selection,
                   tuple(releases[key] for key in sorted(releases, key=lambda key: canonical(key.model_dump(mode='json')))))

    @property
    def request(self):
        return self.review.composition.evidence.proposal.attempt.request

    def verify(self):
        require(self.bind(self.review, self.budget) == self, 'refresh_plan_binding')
        return self
