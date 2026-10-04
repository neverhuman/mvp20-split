"""Stable actor/trace/publisher intent; existence is checked by the owner journal."""

import hashlib
import json
from dataclasses import dataclass

from amphora_contracts_core import Identifier
from amphora_contracts_planning import ExtractionTraceRef
from pydantic import TypeAdapter


@dataclass(frozen=True)
class PublicationIdentity:
    canonical: bytes

    @classmethod
    def bind(cls, principal, publication_id, trace, publisher_id):
        principal.require("record_attempts", trace.scope)
        trace = ExtractionTraceRef.model_validate_json(trace.model_dump_json(warnings=False))
        for identifier in (publication_id, publisher_id):
            TypeAdapter(Identifier).validate_python(identifier, strict=True)
        value = {"format": "planning-trace-publication.v1", "publication_id": publication_id,
                 "actor_id": principal.actor_id, "trace": trace.model_dump(mode="json"),
                 "publisher_id": publisher_id}
        return cls(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8"))

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
