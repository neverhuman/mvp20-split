"""Declaration-specific immutable events over unchanged upload transitions."""
from dataclasses import dataclass
import hashlib
import json

from ..campaign_context.records import canonical
from ..context.policy import require
from ..context.snapshot import _object, _constant
from ..publication.attempt import PublicationAttempt
from ..publication.records import advance


@dataclass(frozen=True)
class DeclarationEvent:
    canonical: bytes

    @classmethod
    def record(cls, position, attempt, action, data):
        require(type(position) is int and 1 <= position <= 64, 'curation_declaration_event_limit')
        raw = canonical({'profile': 'planning-curation-declaration-event.v1', 'position': position,
                         'ordinal': attempt.identity.ordinal, 'action': action, 'data': data})
        require(len(raw) <= 262144, 'curation_declaration_event_size')
        return cls(raw)

    @property
    def sha256(self):
        return hashlib.sha256(self.canonical).hexdigest()

    def apply(self, previous, origin, artifact, position):
        require(type(self.canonical) is bytes and 0 < len(self.canonical) <= 262144, 'curation_declaration_event_size')
        value = json.loads(self.canonical.decode('utf-8'), object_pairs_hook=_object, parse_constant=_constant)
        require(type(value) is dict and set(value) == {'profile', 'position', 'ordinal', 'action', 'data'}
                and value['profile'] == 'planning-curation-declaration-event.v1'
                and type(value['position']) is int and value['position'] == position
                and type(value['ordinal']) is int and canonical(value) == self.canonical,
                'curation_declaration_event_binding')
        if previous is None:
            require(position == 1 and value['action'] == 'prepared' and value['data'] is None,
                    'curation_declaration_initial_event')
            result = PublicationAttempt.first(origin)
        else:
            result = advance(previous, value['action'], value['data'], origin, artifact)
        require(value['ordinal'] == result.identity.ordinal, 'curation_declaration_event_ordinal')
        return result
