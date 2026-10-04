"""Byte-owned request snapshot; caller DTOs and provider text are never authority."""

import hashlib
import json
from dataclasses import dataclass

from amphora_contracts_core import Scope
from amphora_contracts_planning import EngagementRequest, ProviderAttemptRef
from pydantic import ValidationError

from .policy import ContextPolicy, require

MAX_REQUEST_BYTES = 262144


def _object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate_json_key")
        result[key] = value
    return result


def _constant(_value):
    raise ValueError("nonfinite_json")


@dataclass(frozen=True)
class RequestSnapshot:
    canonical: bytes

    @classmethod
    def from_bytes(cls, raw: bytes, *, actor_id: str, scope: Scope) -> "RequestSnapshot":
        require(type(raw) is bytes and 0 < len(raw) <= MAX_REQUEST_BYTES, "request_size")
        try:
            document = json.loads(raw.decode("utf-8"), object_pairs_hook=_object, parse_constant=_constant)
            # JSON-mode validation admits JSON arrays for immutable wire tuples, not coercion of scalars.
            request = EngagementRequest.model_validate_json(json.dumps(document, allow_nan=False))
        except (UnicodeDecodeError, json.JSONDecodeError, ValidationError, RecursionError) as exc:
            raise ValueError("invalid_request") from exc
        ContextPolicy.validate(request, actor_id, scope)
        canonical = json.dumps(request.model_dump(mode="json"), sort_keys=True,
                               separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
        require(len(canonical) <= MAX_REQUEST_BYTES, "request_size")
        return cls(canonical)

    @classmethod
    def bind(cls, request: EngagementRequest, *, actor_id: str, scope: Scope) -> "RequestSnapshot":
        return cls.from_bytes(request.model_dump_json(warnings=False).encode("utf-8"), actor_id=actor_id, scope=scope)

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.canonical).hexdigest()

    def document(self) -> EngagementRequest:
        return EngagementRequest.model_validate_json(self.canonical)


@dataclass(frozen=True)
class AttemptBinding:
    request: RequestSnapshot
    ordinal: int

    def __post_init__(self):
        limit = self.request.document().context.limits.max_attempts
        require(type(self.ordinal) is int and 1 <= self.ordinal <= limit, "attempt_limit")

    def reference(self) -> ProviderAttemptRef:
        return ProviderAttemptRef(engagement=self.request.document().reference,
                                  request_sha256=self.request.sha256, ordinal=self.ordinal)

    def validate(self, supplied: ProviderAttemptRef) -> None:
        require(supplied == self.reference(), "attempt_binding_mismatch")
