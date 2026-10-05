"""Bounded effect histories; no state flag substitutes for an owner observation."""

import hashlib
import json
from dataclasses import dataclass

from ..campaign_context.records import canonical
from ..context.policy import require
from ..context.snapshot import _constant, _object
from .observation import CompilerObservation, verify_request

TERMINAL = frozenset({'saved', 'compiled', 'structural_invalid', 'rejected', 'candidate'})
BLOCKED = frozenset({'input_unavailable', 'relevant_input_changed', 'eligibility_rejected', 'eligibility_expired',
                     'owner_access_denied', 'owner_unavailable', 'owner_protocol', 'identity_conflict', 'dependency_unavailable'})


@dataclass(frozen=True)
class CompilerProgress:
    position: int
    state: str
    dispatches: int = 0
    observation: CompilerObservation | None = None
    reason: str | None = None

    @property
    def terminal(self):
        return self.state in TERMINAL


@dataclass(frozen=True)
class CompilerEvent:
    canonical: bytes

    @classmethod
    def record(cls, effect, position, action, data=None):
        require(type(position) is int and 1 <= position <= 64, 'compiler_event_limit')
        raw = canonical({'format': 'planning-compiler-event.v1', 'effect_id': effect.effect_id,
            'effect_sha256': effect.sha256, 'position': position, 'action': action, 'data': data})
        require(len(raw) <= 2101248, 'compiler_event_size')
        return cls(raw)

    def apply(self, previous, selection, effect, request, position):
        verify_request(selection, effect, request)
        require(type(self.canonical) is bytes and 0 < len(self.canonical) <= 2101248, 'compiler_event_size')
        value = json.loads(self.canonical.decode('utf-8'), object_pairs_hook=_object, parse_constant=_constant)
        require(type(value) is dict and set(value) == {'format', 'effect_id', 'effect_sha256', 'position', 'action', 'data'},
                'compiler_event_shape')
        require(type(value['position']) is int and value['position'] == position and
                self.record(effect, position, value['action'], value['data']).canonical == self.canonical,
                'compiler_event_binding')
        action, data = value['action'], value['data']
        if previous is None:
            require(position == 1 and action == 'prepared' and data is None, 'compiler_event_initial')
            result = CompilerProgress(position, 'prepared')
        else:
            require(previous.position == position - 1 and not previous.terminal, 'compiler_event_order_or_terminal')
            if action == 'dispatch':
                require(data is None, 'compiler_event_dispatch')
                result = CompilerProgress(position, 'dispatching', previous.dispatches + 1, previous.observation)
            elif action == 'uncertain':
                require(previous.state == 'dispatching' and data is None, 'compiler_event_uncertain')
                result = CompilerProgress(position, 'uncertain', previous.dispatches, previous.observation)
            elif action == 'blocked':
                require(type(data) is str and data in BLOCKED, 'compiler_event_blocked')
                result = CompilerProgress(position, 'blocked', previous.dispatches, previous.observation, data)
            else:
                require(action == 'observed' and type(data) is dict, 'compiler_event_action')
                observation = CompilerObservation.restore(canonical(data), selection, effect, request)
                result = CompilerProgress(position, observation.status, previous.dispatches, observation)
        require(position < 64 or result.terminal, 'compiler_event_terminal_slot_reserved')
        return result

    @property
    def sha256(self):
        return hashlib.sha256(self.canonical).hexdigest()
