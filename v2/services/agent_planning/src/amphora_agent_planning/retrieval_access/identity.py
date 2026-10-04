"""Existing Data wire fingerprints; no access, ranking or backend authority."""

import hashlib
import json

from amphora_contracts_representations import RepresentationBinding

from ..context.policy import require


def canonical(value, limit=4194304):
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    require(0 < len(raw) <= limit, "retrieval_context_size")
    return raw


def fingerprint(value, limit=4194304):
    return hashlib.sha256(canonical(value, limit)).hexdigest()


def binding_key(ref):
    return ref.binding_id, ref.sha256


def policy(value, scope):
    if value.bindings is None:
        return value
    require(all(ref.scope == scope for ref in value.bindings), "retrieval_context_scope")
    require(len({ref.binding_id for ref in value.bindings}) == len(value.bindings), "retrieval_context_duplicate_binding")
    return value.model_copy(update={"bindings": tuple(sorted(value.bindings, key=binding_key))})


def binding(value, scope):
    value = RepresentationBinding.model_validate(value.model_dump(mode="python", warnings=False))
    require(value.reference.scope == value.profile.scope == value.source.source.scope ==
            value.source.source.raw.scope == value.vector.scope == scope, "retrieval_context_scope")
    require(0 <= value.source.start < value.source.end <= value.source.source.raw.size_bytes,
            "retrieval_context_span")
    descriptor = {"format": "data.representation-binding.v1", "binding_id": value.reference.binding_id,
        "scope": scope.model_dump(mode="json"), "profile": value.profile.model_dump(mode="json"),
        "source": value.source.model_dump(mode="json"), "vector": value.vector.model_dump(mode="json")}
    require(value.reference.sha256 == fingerprint(descriptor, 65536), "retrieval_context_binding_digest")
    return value
