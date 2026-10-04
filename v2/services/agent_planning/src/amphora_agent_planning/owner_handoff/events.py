"""Bounded attributable events; final capacity is reserved for terminal evidence."""

import hashlib
import json
from dataclasses import dataclass

from ..context.policy import require
from ..context.snapshot import _constant, _object
from ..publication.records import encode
from .receipt import OwnerOutcome

TERMINAL = frozenset({"acknowledged", "rejected", "conflict"})
BLOCKED = frozenset({"source_access_denied", "source_unavailable", "dependency_unavailable",
    "owner_access_denied", "owner_unavailable", "owner_protocol", "request_rejected", "identity_conflict"})


@dataclass(frozen=True)
class HandoffProgress:
    state: str
    dispatches: int = 0
    outcome: OwnerOutcome | None = None
    reason: str | None = None

    @property
    def terminal(self):
        return self.state in TERMINAL


@dataclass(frozen=True)
class HandoffEvent:
    canonical: bytes

    @classmethod
    def record(cls, request, position, action, data=None):
        require(type(position) is int and 1 <= position <= 64, "handoff_event_limit")
        raw = encode({"format": "planning-owner-event.v1", "effect_id": request.selection.effect_id,
            "request_sha256": request.sha256, "position": position, "action": action, "data": data})
        require(len(raw) <= 2098176, "handoff_event_size")
        return cls(raw)

    @property
    def sha256(self):
        return hashlib.sha256(self.canonical).hexdigest()

    def apply(self, previous, request, position):
        require(type(self.canonical) is bytes and 0 < len(self.canonical) <= 2098176, "handoff_event_size")
        value = json.loads(self.canonical.decode("utf-8"), object_pairs_hook=_object, parse_constant=_constant)
        require(type(value) is dict and set(value) == {"format", "effect_id", "request_sha256", "position", "action", "data"},
                "stored_handoff_event")
        require(type(value["position"]) is int and value["position"] == position and
                self.record(request, position, value["action"], value["data"]).canonical == self.canonical,
                "stored_handoff_event")
        action, data = value["action"], value["data"]
        if previous is None:
            require(position == 1 and action == "prepared" and data is None, "handoff_initial_event")
            result = HandoffProgress("prepared")
        else:
            require(not previous.terminal, "handoff_terminal")
            if action == "dispatch":
                require(data is None, "handoff_dispatch_shape")
                result = HandoffProgress("dispatching", previous.dispatches + 1, previous.outcome)
            elif action == "uncertain":
                require(data is None and previous.state == "dispatching", "handoff_uncertain_transition")
                result = HandoffProgress("uncertain", previous.dispatches, previous.outcome)
            elif action == "blocked":
                require(type(data) is str and data in BLOCKED, "handoff_blocked_reason")
                result = HandoffProgress("blocked", previous.dispatches, previous.outcome, data)
            else:
                require(action == "observed" and type(data) is dict, "handoff_event_action")
                outcome = OwnerOutcome.restore(request, encode(data))
                result = HandoffProgress(outcome.state, previous.dispatches, outcome)
        require(position < 64 or result.terminal, "handoff_terminal_slot_reserved")
        return result
