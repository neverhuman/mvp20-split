"""Stable effect slot plus immutable content/configuration binding."""

import hashlib
import json
from dataclasses import dataclass

from amphora_contracts_core import Identifier
from amphora_contracts_planning import ExtractionTraceRef
from pydantic import TypeAdapter

from ..context.policy import require
from ..context.snapshot import _constant, _object
from ..publication.records import encode


@dataclass(frozen=True)
class ResultIdentity:
    canonical: bytes

    @classmethod
    def bind(cls, principal, trace, kind, local_id, publisher_id, artifact):
        principal.require("record_attempts", trace.scope)
        principal.require("read_attempts", trace.scope)
        return cls._encode(principal.actor_id, trace, kind, local_id, publisher_id, artifact)

    @classmethod
    def _encode(cls, actor_id, trace, kind, local_id, publisher_id, artifact):
        trace = ExtractionTraceRef.model_validate_json(trace.model_dump_json(warnings=False))
        require(kind in {"feedback", "answer"}, "result_kind")
        require(kind != "feedback" or local_id == "diagnostics", "result_feedback_slot")
        for value in (actor_id, local_id, publisher_id):
            TypeAdapter(Identifier).validate_python(value, strict=True)
        artifact.bind_slot(trace, kind, local_id)
        value = {"format": "planning-result-publication.v1", "actor_id": actor_id,
            "trace": trace.model_dump(mode="json"), "kind": kind, "local_id": local_id,
            "publisher_id": publisher_id, "payload_sha256": artifact.fingerprint}
        return cls(encode(value))

    @classmethod
    def restore(cls, raw, principal, artifact):
        require(type(raw) is bytes and 0 < len(raw) <= 16384, "result_identity_size")
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_object, parse_constant=_constant)
        require(type(value) is dict and set(value) == {"format", "actor_id", "trace", "kind", "local_id",
                "publisher_id", "payload_sha256"} and value["format"] == "planning-result-publication.v1",
                "result_identity_format")
        trace = ExtractionTraceRef.model_validate_json(json.dumps(value["trace"]))
        require(value["actor_id"] == principal.actor_id, "result_actor_binding")
        principal.require("read_attempts", trace.scope)
        identity = cls._encode(principal.actor_id, trace, value["kind"], value["local_id"], value["publisher_id"], artifact)
        require(identity.canonical == raw, "result_identity_binding")
        return identity

    def document(self):
        return json.loads(self.canonical)

    @property
    def publication_id(self):
        value = self.document()
        # Reconfiguration or changed payload must conflict in the same slot,
        # not silently create another externally visible effect.
        return "r-" + hashlib.sha256(encode({key: value[key] for key in
            ("format", "actor_id", "trace", "kind", "local_id")})).hexdigest()

    @property
    def sha256(self):
        return hashlib.sha256(self.canonical).hexdigest()

    @property
    def actor_id(self):
        return self.document()["actor_id"]

    def trace(self):
        return ExtractionTraceRef.model_validate_json(json.dumps(self.document()["trace"]))
