"""Stable actor/trace/publisher intent; existence is checked by the owner journal."""

import hashlib
import json
from dataclasses import dataclass

from amphora_contracts_core import Identifier
from amphora_contracts_planning import ExtractionTraceRef
from pydantic import TypeAdapter

from ..context.policy import require
from ..context.snapshot import _constant, _object


@dataclass(frozen=True)
class PublicationIdentity:
    canonical: bytes

    @classmethod
    def bind(cls, principal, publication_id, trace, publisher_id):
        principal.require("record_attempts", trace.scope)
        return cls._encode(principal.actor_id, publication_id, trace, publisher_id)

    @classmethod
    def _encode(cls, actor_id, publication_id, trace, publisher_id):
        trace = ExtractionTraceRef.model_validate_json(trace.model_dump_json(warnings=False))
        for identifier in (actor_id, publication_id, publisher_id):
            TypeAdapter(Identifier).validate_python(identifier, strict=True)
        value = {"format": "planning-trace-publication.v1", "publication_id": publication_id,
                 "actor_id": actor_id, "trace": trace.model_dump(mode="json"),
                 "publisher_id": publisher_id}
        return cls(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8"))

    @classmethod
    def restore(cls, raw, principal):
        require(type(raw) is bytes and 0 < len(raw) <= 16384, "publication_identity_size")
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_object, parse_constant=_constant)
        require(type(value) is dict and set(value) == {"format", "publication_id", "actor_id", "trace", "publisher_id"}
                and value["format"] == "planning-trace-publication.v1", "publication_identity_format")
        trace = ExtractionTraceRef.model_validate_json(json.dumps(value["trace"]))
        require(value["actor_id"] == principal.actor_id and trace.scope == principal.scope, "publication_actor_binding")
        identity = cls._encode(value["actor_id"], value["publication_id"], trace, value["publisher_id"])
        require(identity.canonical == raw, "publication_identity_canonical")
        return identity

    def document(self):
        return json.loads(self.canonical)

    @property
    def sha256(self):
        return hashlib.sha256(self.canonical).hexdigest()

    @property
    def actor_id(self):
        return self.document()["actor_id"]

    def trace(self):
        return ExtractionTraceRef.model_validate_json(json.dumps(self.document()["trace"]))

    @property
    def scope(self):
        return self.trace().scope
