"""Stable owner effect slots; payload and configuration cannot create a second slot."""

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
class HandoffSelection:
    canonical: bytes

    @classmethod
    def bind(cls, principal, trace, interpretation_id, kind, local_id, owner_id):
        principal.require("read_attempts", trace.scope)
        principal.require("record_attempts", trace.scope)
        return cls._encode(principal.actor_id, trace, interpretation_id, kind, local_id, owner_id)

    @classmethod
    def _encode(cls, actor, trace, interpretation_id, kind, local_id, owner_id):
        trace = ExtractionTraceRef.model_validate_json(trace.model_dump_json(warnings=False))
        for value in (actor, interpretation_id, local_id, owner_id):
            TypeAdapter(Identifier).validate_python(value, strict=True)
        require(kind in {"question", "need", "graph"}, "handoff_kind")
        require(kind != "graph" or local_id == "graph", "handoff_graph_slot")
        return cls(encode({"format": "planning-owner-selection.v1", "actor_id": actor,
            "trace": trace.model_dump(mode="json"), "interpretation_id": interpretation_id,
            "kind": kind, "local_id": local_id, "owner_id": owner_id}))

    @classmethod
    def restore(cls, raw, principal):
        require(type(raw) is bytes and 0 < len(raw) <= 16384, "handoff_selection_size")
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_object, parse_constant=_constant)
        require(type(value) is dict and set(value) == {"format", "actor_id", "trace", "interpretation_id", "kind", "local_id", "owner_id"}
            and value["format"] == "planning-owner-selection.v1", "handoff_selection_format")
        trace = ExtractionTraceRef.model_validate_json(json.dumps(value["trace"]))
        principal.require("read_attempts", trace.scope)
        require(value["actor_id"] == principal.actor_id, "handoff_actor_binding")
        result = cls._encode(principal.actor_id, trace, value["interpretation_id"], value["kind"], value["local_id"], value["owner_id"])
        require(result.canonical == raw, "handoff_selection_canonical")
        return result

    def document(self):
        return json.loads(self.canonical)

    def trace(self):
        return ExtractionTraceRef.model_validate_json(json.dumps(self.document()["trace"]))

    @property
    def effect_id(self):
        value = self.document()
        slot = {key: value[key] for key in ("actor_id", "trace", "kind", "local_id")}
        slot["format"] = "planning-owner-effect.v1"
        return "h-" + hashlib.sha256(encode(slot)).hexdigest()

    @property
    def sha256(self):
        return hashlib.sha256(self.canonical).hexdigest()
