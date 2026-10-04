"""Immutable owned effect selection before fresh processing or uploads."""

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
class ResultSelection:
    canonical: bytes

    @classmethod
    def bind(cls, principal, trace, interpretation_id, kind, local_id, publisher_id):
        principal.require("record_attempts", trace.scope)
        principal.require("read_attempts", trace.scope)
        return cls._encode(principal.actor_id, trace, interpretation_id, kind, local_id, publisher_id)

    @classmethod
    def _encode(cls, actor, trace, interpretation_id, kind, local_id, publisher_id):
        trace = ExtractionTraceRef.model_validate_json(trace.model_dump_json(warnings=False))
        for value in (actor, interpretation_id, local_id, publisher_id):
            TypeAdapter(Identifier).validate_python(value, strict=True)
        require(kind in {"feedback", "answer"}, "result_kind")
        require(kind != "feedback" or local_id == "diagnostics", "result_feedback_slot")
        return cls(encode({"format": "planning-result-selection.v1", "actor_id": actor,
            "trace": trace.model_dump(mode="json"), "interpretation_id": interpretation_id,
            "kind": kind, "local_id": local_id, "publisher_id": publisher_id}))

    @classmethod
    def restore(cls, raw, principal):
        require(type(raw) is bytes and 0 < len(raw) <= 16384, "result_selection_size")
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_object, parse_constant=_constant)
        require(type(value) is dict and set(value) == {"format", "actor_id", "trace", "interpretation_id",
                "kind", "local_id", "publisher_id"} and value["format"] == "planning-result-selection.v1",
                "result_selection_format")
        trace = ExtractionTraceRef.model_validate_json(json.dumps(value["trace"]))
        principal.require("read_attempts", trace.scope)
        require(value["actor_id"] == principal.actor_id, "result_actor_binding")
        result = cls._encode(principal.actor_id, trace, value["interpretation_id"], value["kind"],
                             value["local_id"], value["publisher_id"])
        require(result.canonical == raw, "result_selection_canonical")
        return result

    def document(self):
        return json.loads(self.canonical)

    def trace(self):
        return ExtractionTraceRef.model_validate_json(json.dumps(self.document()["trace"]))

    @property
    def publication_id(self):
        value = self.document()
        slot = {key: value[key] for key in ("actor_id", "trace", "kind", "local_id")}
        slot["format"] = "planning-result-publication.v1"
        return "r-" + hashlib.sha256(encode(slot)).hexdigest()

    @property
    def sha256(self):
        return hashlib.sha256(self.canonical).hexdigest()
