"""Focused delivery policy and immutable claimed work."""

from dataclasses import dataclass

from amphora_contracts_runtime import RuntimeNotification


@dataclass(frozen=True, slots=True)
class DeliveryPolicy:
    max_attempts: int = 8
    lease_seconds: int = 30

    def __post_init__(self):
        if (type(self.max_attempts) is not int or not 1 <= self.max_attempts <= 100 or
            type(self.lease_seconds) is not int or not 1 <= self.lease_seconds <= 300):
            raise ValueError("Invalid bounded delivery policy")

    def backoff(self, attempts):
        return min(60, 2 ** min(attempts, 6))


@dataclass(frozen=True, slots=True)
class DeliveryClaim:
    journal: str
    scope: object
    operation_id: str
    event_id: str
    target: str
    payload: dict
    object_id: str
    revision: int
    event_kind: str
    token: str
    generation: int
    attempt: int

    def notification(self):
        return RuntimeNotification.model_validate({"scope": self.scope, "operation_id": self.operation_id,
            "event_id": self.event_id, "event_kind": self.event_kind, "reference": {
                "kind": "run" if self.journal == "outbox" else "worker_policy",
                "object_id": self.object_id, "revision": self.revision}})
