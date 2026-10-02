"""Authenticated stable request identity and restored immutable evaluation state."""

import hashlib
from dataclasses import dataclass

from amphora_contracts_knowledge import DomainHead, ReasoningRequest, ReasoningStatus

from ..authoring.canonical import KnowledgeError, canonical
from ..persistence.records import graph_key
from .profile import RuleProfile, raw


@dataclass(frozen=True)
class RequestDocument:
    request: ReasoningRequest
    actor_id: str
    body: bytes
    sha256: str

    @classmethod
    def authorized(cls, principal, request):
        request = ReasoningRequest.model_validate(raw(request))
        principal.require("reason_graph", request.snapshot.graph.scope)
        body = canonical(request)
        if len(body) > 262144:
            raise KnowledgeError("reasoning_request_size_limit")
        return cls(request, principal.actor_id, body, hashlib.sha256(body).hexdigest())

    @property
    def key(self):
        return graph_key(self.request.snapshot.graph) | {"request": self.request.request_id}

    def require_same(self, row):
        if (row["actor_id"] != self.actor_id or row["request_sha256"] != self.sha256
                or bytes(row["canonical_bytes"]) != self.body):
            raise KnowledgeError("reasoning_request_conflict")

    def pending(self):
        return ReasoningStatus(wire_version="1", request=self.request, actor_id=self.actor_id, decision=None)


@dataclass(frozen=True)
class RegisteredEvaluation:
    document: RequestDocument
    profile: RuleProfile
    head: DomainHead
    status: ReasoningStatus
