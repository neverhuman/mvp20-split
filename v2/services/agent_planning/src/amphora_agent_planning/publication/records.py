"""Reconstruct prepared payloads and replay a bounded immutable event stream."""

import hashlib
import json
from dataclasses import dataclass

from amphora_contracts_artifacts import (
    DerivationReceipt,
    DerivedUploadReceipt,
    FinalizedReceipt,
    UploadContentReceipt,
)

from ..context.policy import require
from ..context.snapshot import _constant, _object
from .attempt import PublicationAttempt
from .payload import TraceArtifact
from .review_record import ReviewRecord


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


@dataclass(frozen=True)
class PayloadRecord:
    artifact: TraceArtifact
    review: ReviewRecord

    @property
    def manifest(self):
        return encode({"format": "planning-trace-payload.v1", "content": self.artifact.content.model_dump(mode="json"),
                       "declaration": self.artifact.declaration.model_dump(mode="json")})

    @property
    def sha256(self):
        digest = hashlib.sha256(b"planning-trace-payload.v1")
        for raw in (self.artifact.body, self.review.canonical, self.manifest):
            digest.update(len(raw).to_bytes(8, "big"))
            digest.update(raw)
        return digest.hexdigest()

    @classmethod
    def from_row(cls, row, identity, projection, task, schema):
        review = ReviewRecord.from_bytes(bytes(row["review_bytes"]))
        artifact = TraceArtifact.restore(identity, projection, task, review, schema=schema)
        result = cls(artifact, review)
        require(artifact.body == bytes(row["trace_bytes"]) and result.manifest == bytes(row["manifest_bytes"]) and
                result.sha256 == row["payload_sha256"], "stored_publication_payload")
        return result


def advance(attempt, action, data, identity, artifact):
    require(type(action) is str, "publication_event_action")
    if action == "begun":
        return attempt.begun(identity, artifact, DerivedUploadReceipt.model_validate_json(json.dumps(data)))
    if action == "streamed":
        return attempt.streamed(UploadContentReceipt.model_validate_json(json.dumps(data)))
    if action == "finalized":
        require(type(data) is dict and set(data) == {"receipt", "derivation"}, "publication_event_data")
        return attempt.finalized(identity, artifact, FinalizedReceipt.model_validate_json(json.dumps(data["receipt"])),
                                 DerivationReceipt.model_validate_json(json.dumps(data["derivation"])))
    if action == "rejected":
        require(type(data) is dict and set(data) == {"reason"}, "publication_event_data")
        return attempt.rejected(data["reason"])
    require(data is None, "publication_event_data")
    methods = {"streaming": attempt.start_stream, "abandoned": attempt.abandon,
               "finalizing": attempt.start_finalize, "replacement": lambda: attempt.replacement(identity)}
    require(action in methods, "publication_event_action")
    return methods[action]()


@dataclass(frozen=True)
class PublicationEvent:
    canonical: bytes

    @classmethod
    def record(cls, position, attempt, action, data):
        require(type(position) is int and 1 <= position <= 64, "publication_event_limit")
        value = {"format": "planning-trace-publication-event.v1", "position": position,
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
                value["format"] == "planning-trace-publication-event.v1" and type(value["position"]) is int and
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
