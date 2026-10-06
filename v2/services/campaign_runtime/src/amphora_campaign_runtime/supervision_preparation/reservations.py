"""Potential-call accounting, distinct from Planning's actual cost ledger."""

from dataclasses import dataclass

from ..supervision_scope.observations import digest, require


@dataclass(frozen=True)
class RequestCharge:
    decision_id: str
    request_sha256: str
    max_attempts: int

    def __post_init__(self):
        digest(self.decision_id)
        digest(self.request_sha256)
        require(type(self.max_attempts) is int and 1 <= self.max_attempts <= 16, 'reservation_attempts')


@dataclass(frozen=True)
class CallReservations:
    """One run's immutable reservation history, supplied by its locked SQL owner."""

    charges: tuple[RequestCharge, ...] = ()

    def __post_init__(self):
        require(type(self.charges) is tuple and all(type(item) is RequestCharge for item in self.charges),
                'reservation_history')
        require(len({item.request_sha256 for item in self.charges}) == len(self.charges),
                'reservation_duplicate_request')

    def reserve(self, charge, *, rule, ceilings):
        require(type(charge) is RequestCharge, 'reservation_charge')
        previous = next((item for item in self.charges if item.request_sha256 == charge.request_sha256), None)
        if previous is not None:
            require(previous == charge, 'reservation_replay_conflict')
            return self
        slot = tuple(item for item in self.charges if item.decision_id == charge.decision_id)
        require(len(slot) < rule.max_requests, 'reservation_slot_requests')
        require(len(self.charges) < ceilings.max_requests, 'reservation_campaign_requests')
        require(sum(item.max_attempts for item in slot) + charge.max_attempts <= rule.max_model_calls,
                'reservation_slot_calls')
        require(sum(item.max_attempts for item in self.charges) + charge.max_attempts <= ceilings.max_model_calls,
                'reservation_campaign_calls')
        return CallReservations((*self.charges, charge))
