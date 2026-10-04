"""Reviewed compiler pins; no local compilation, catalog discovery or admission."""

import hashlib
import json
from dataclasses import dataclass

from amphora_contracts_graph_runtime import DefinitionUniverse

from ..context import RequestSnapshot
from ..context.policy import require


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")


@dataclass(frozen=True)
class ReviewedUniverse:
    canonical: bytes
    request: RequestSnapshot

    @classmethod
    def bind(cls, supplied, request, expected=None):
        original = request.document()
        request = RequestSnapshot.bind(original, actor_id=original.actor_id, scope=original.reference.scope)
        require(original.purpose in {"campaign_proposal", "supervision"}, "runtime_metadata_purpose")
        require(type(supplied) is DefinitionUniverse, "runtime_metadata_type")
        value = DefinitionUniverse.model_validate(supplied.model_dump(mode="python", warnings=False))
        require(value.scope == original.reference.scope, "runtime_metadata_scope")
        require(len({lock.tool for lock in value.reviewed_tools}) == len(value.reviewed_tools), "runtime_metadata_duplicate_tool")
        require(len(set(value.schemas)) == len(value.schemas), "runtime_metadata_duplicate_schema")
        for lock in value.reviewed_tools:
            for ports in (lock.input_schemas, lock.output_schemas):
                require(len({port.port for port in ports}) == len(ports), "runtime_metadata_duplicate_port")
        profile = {"profile": "amphora-authoring-universe-v1", "compiler": "amphora-deterministic-compiler-v3",
            "scope": value.scope.model_dump(mode="json"),
            "tools": sorted((lock.model_dump(mode="json") for lock in value.reviewed_tools), key=canonical),
            "schemas": sorted((ref.model_dump(mode="json") for ref in value.schemas), key=canonical)}
        digest = hashlib.sha256(canonical(profile)).hexdigest()
        require(value.universe_sha256 == digest and (expected is None or expected == digest), "runtime_metadata_universe")
        raw = canonical(value.model_dump(mode="json"))
        require(len(raw) <= 4194304, "runtime_metadata_size")
        return cls(raw, request)

    def document(self):
        return DefinitionUniverse.model_validate_json(self.canonical)

    @property
    def sha256(self):
        return self.document().universe_sha256
