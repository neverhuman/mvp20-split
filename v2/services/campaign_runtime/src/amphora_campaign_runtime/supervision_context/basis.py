"""Immutable reviewed facts and remaining potential-call allowances."""

from dataclasses import dataclass

from amphora_contracts_supervision import CheckpointAllowance, SupervisionRef

from ..supervision_checkpoints.values import ValueCheckpointSeed, read_seed
from ..supervision_preparation import CallReservations, ReviewedRecipe
from ..supervision_scope.observations import require


@dataclass(frozen=True)
class ContextBasis:
    seed: ValueCheckpointSeed
    recipe: ReviewedRecipe
    reservations: CallReservations
    deadline_unix_ms: int

    def __post_init__(self):
        seed = read_seed(self.seed.canonical, self.seed.policy)
        require(isinstance(seed, ValueCheckpointSeed), 'context_scalar_seed_required')
        recipe = ReviewedRecipe(self.recipe.canonical)
        recipe.require_policy(seed.policy)
        require(type(self.reservations) is CallReservations, 'context_reservation_history')
        require(type(self.deadline_unix_ms) is int and 1 <= self.deadline_unix_ms <= 9007199254740991,
                'context_deadline')
        object.__setattr__(self, 'seed', seed)
        object.__setattr__(self, 'recipe', recipe)
        self.remaining()

    @property
    def rule(self):
        return next(item for item in self.seed.policy.document().checkpoints
                    if item.checkpoint_id == self.seed.document().checkpoint_id)

    @property
    def reference(self):
        cut = self.seed.footprint().cut
        return SupervisionRef(scope=cut.scope, run_id=cut.run_id, decision_id=self.seed.decision_id)

    def remaining(self):
        charges = self.reservations.charges
        slot = tuple(item for item in charges if item.decision_id == self.seed.decision_id)
        ceilings = self.seed.policy.document().ceilings
        return CheckpointAllowance(slot_requests=self.rule.max_requests - len(slot),
            slot_model_calls=self.rule.max_model_calls - sum(item.max_attempts for item in slot),
            campaign_requests=ceilings.max_requests - len(charges),
            campaign_model_calls=ceilings.max_model_calls - sum(item.max_attempts for item in charges))
