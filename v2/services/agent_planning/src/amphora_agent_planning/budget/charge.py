"""Version-one policy never refunds a reserved attempt on uncertain usage."""

import hashlib
from dataclasses import dataclass

from ..context.policy import require
from ..providers.wire import observation_document
from .policy import ReservationDemand


@dataclass(frozen=True)
class BudgetCharge:
    observation_sha256: str
    input_tokens: int
    output_tokens: int
    accounting_units: int
    overage: bool

    @classmethod
    def reconcile(cls, demand: ReservationDemand, canonical_observation: bytes):
        wire = observation_document(canonical_observation)
        require(wire.attempt == demand.attempt, "charge_attempt_mismatch")
        observed = (wire.usage.input_tokens, wire.usage.output_tokens, wire.usage.accounting_units)
        reserved = (demand.input_tokens, demand.output_tokens, demand.accounting_units)
        # Unknown/partial reports remain lower bounds; neither status nor certainty grants a refund.
        charged = tuple(max(floor, value if value is not None else 0)
                        for floor, value in zip(reserved, observed, strict=True))
        return cls(hashlib.sha256(canonical_observation).hexdigest(), *charged,
                   any(value > floor for value, floor in zip(charged, reserved, strict=True)))

    @property
    def tokens(self):
        return self.input_tokens + self.output_tokens
