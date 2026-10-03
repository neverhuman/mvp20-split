"""Coverage and per-point use stay independent; preserve all explicit replicates in order."""
from dataclasses import dataclass

from ...experiments.model import Experiment
from ..identity import require
from ..records import Observation
from .policy import ObservationUsePolicy
from .review import ObservationUseReview


@dataclass(frozen=True, slots=True)
class ObservationUseBatch:
    policy: ObservationUsePolicy
    experiment: Experiment
    reviews: tuple[ObservationUseReview, ...]
    missing_expectations: tuple[str, ...]

    @property
    def usable(self):
        return tuple(review.observation.identity.reference for review in self.reviews if review.disposition == "usable")

    @property
    def focus(self):
        return tuple(review.observation.identity.reference for review in self.reviews if review.focus)

    @classmethod
    def assess(cls, policy, experiment, observations):
        require(type(policy) is ObservationUsePolicy and type(experiment) is Experiment,"observation_use_profile_required")
        require(type(observations) is tuple and len(observations) <= 1024,"observation_use_batch_bound")
        require(all(type(item) is Observation for item in observations),"observation_use_record_required")
        require(all(item.identity.reference.scope == experiment.identity.reference.scope for item in observations),"observation_use_scope_mismatch")
        require(len({item.identity.reference.observation_id for item in observations}) == len(observations),"duplicate_observation_use_identity")
        reviews = tuple(policy.review(item,experiment) for item in observations)
        returned = {item.observation.binding.target.expectation_id for item in reviews if not item.match.reasons}
        missing = tuple(item.expectation_id for item in experiment.expectations if item.expectation_id not in returned)
        return cls(policy,experiment,reviews,missing)
