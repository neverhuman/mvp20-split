"""Planning-owned byte values; factories, not caller JSON, define inclusion policy."""

import hashlib
import json
from dataclasses import dataclass

from ..campaign_context.records import canonical
from ..context.policy import require


@dataclass(frozen=True)
class ContextSlice:
    lane: str
    identity: bytes
    payload: bytes
    required: bool
    observations: bytes

    @classmethod
    def _capture(cls, lane, identity, payload, required, observations=()):
        return cls(lane, canonical(identity), canonical(payload), required, canonical(observations))

    @property
    def key(self):
        return self.lane, self.identity

    @property
    def sha256(self):
        return hashlib.sha256(self.payload).hexdigest()

    def document(self):
        return {'lane': self.lane, 'identity': json.loads(self.identity), 'required': self.required,
                'payload': json.loads(self.payload), 'observations': json.loads(self.observations)}


def ordered(slices):
    require(len(slices) <= 900 and len({row.key for row in slices}) == len(slices), 'campaign_slice_count_or_duplicate')
    require(sum(len(row.payload) + len(row.identity) + len(row.observations) for row in slices) <= 134217728,
            'campaign_slice_total')
    # Stable within class: manifest and explicit owner selection order remain priority.
    return tuple(sorted(slices, key=lambda row: not row.required))
