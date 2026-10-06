"""Capture-specific event encoding using the unchanged pure upload transitions."""

import hashlib
import json
from dataclasses import dataclass

from ..context.policy import require
from ..context.snapshot import _constant, _object
from ..publication.attempt import PublicationAttempt
from ..publication.records import advance, encode


@dataclass(frozen=True)
class CaptureEvent:
    canonical: bytes

    @classmethod
    def record(cls, position, attempt, action, data):
        require(type(position) is int and 1 <= position <= 64, "publication_event_limit")
        value = {"format": "planning-capture-publication-event.v1", "position": position,
                 "ordinal": attempt.identity.ordinal, "action": action, "data": data}
        raw = encode(value)
        require(len(raw) <= 262144, "publication_event_size")
        return cls(raw)

    @property
    def sha256(self):
        return hashlib.sha256(self.canonical).hexdigest()

    def apply(self, previous, identity, artifact, position):
        require(type(self.canonical) is bytes and 0 < len(self.canonical) <= 262144, "publication_event_size")
        value = json.loads(self.canonical.decode("utf-8"), object_pairs_hook=_object, parse_constant=_constant)
        require(type(value) is dict and set(value) == {"format", "position", "ordinal", "action", "data"} and
                value["format"] == "planning-capture-publication-event.v1" and type(value["position"]) is int and
                value["position"] == position and type(value["ordinal"]) is int, "stored_publication_event")
        if previous is None:
            require(position == 1 and value["action"] == "prepared" and value["data"] is None,
                    "stored_publication_initial")
            result = PublicationAttempt.first(identity)
        else:
            result = advance(previous, value["action"], value["data"], identity, artifact)
        require(value["ordinal"] == result.identity.ordinal and encode(value) == self.canonical,
                "stored_publication_event")
        return result
