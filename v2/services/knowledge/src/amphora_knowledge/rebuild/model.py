"""Rebuild identities and verified materializations are owner domain objects."""

import hashlib
import json
import re
import uuid
from dataclasses import dataclass

from amphora_contracts_knowledge import DomainGraphRef, DomainHead

from ..authoring.canonical import KnowledgeError, canonical
from ..persistence.records import graph_key


@dataclass(frozen=True)
class RebuildRequest:
    graph: DomainGraphRef
    rebuild_id: str
    actor_id: str

    @classmethod
    def authorized(cls, principal, graph, rebuild_id):
        principal.require("rebuild_graph", graph.scope)
        if not isinstance(rebuild_id, str) or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}", rebuild_id) is None:
            raise KnowledgeError("invalid_rebuild_id")
        return cls(graph, rebuild_id, principal.actor_id)

    @property
    def key(self):
        return graph_key(self.graph) | {"rebuild": self.rebuild_id}

    @property
    def raw(self):
        return json.dumps({"graph": self.graph.model_dump(mode="json"), "rebuild_id": self.rebuild_id},
                          sort_keys=True, separators=(",", ":")).encode()

    @property
    def sha256(self):
        return hashlib.sha256(self.raw).hexdigest()

    def require_same(self, row):
        if row["actor_id"] != self.actor_id:
            raise KnowledgeError("rebuild_actor_conflict")
        if bytes(row["request_bytes"]) != self.raw or row["request_sha256"] != self.sha256:
            raise KnowledgeError("rebuild_identity_conflict")


@dataclass(frozen=True)
class RebuildStatus:
    request: RebuildRequest
    initial_head: DomainHead
    outcome: str = "pending"
    result_head: DomainHead | None = None
    attempts: int = 0
    code: str | None = None


@dataclass(frozen=True)
class Candidate:
    request: RebuildRequest
    candidate_id: str
    attempt: int
    head: DomainHead
    snapshot_bytes: bytes

    @classmethod
    def from_cursor(cls, request, attempt, cursor):
        if type(attempt) is not int or not 1 <= attempt <= 3:
            raise KnowledgeError("invalid_rebuild_attempt")
        if cursor.head is None or cursor.state.graph != request.graph:
            raise KnowledgeError("rebuild_graph_mismatch")
        snapshot = cursor.state.to_snapshot()
        if snapshot.reference != cursor.head.snapshot:
            raise KnowledgeError("rebuild_snapshot_mismatch")
        raw = canonical(snapshot)
        if len(raw) > 16777216:
            raise KnowledgeError("rebuild_snapshot_limit")
        return cls(request, uuid.uuid4().hex, attempt, cursor.head, raw)

    @property
    def bindings(self):
        head = self.head
        return self.request.key | {"candidate": self.candidate_id, "attempt": self.attempt,
            "revision": head.snapshot.revision, "snapshot_sha": head.snapshot.sha256,
            "change": head.change.change_id, "change_sha": head.change.sha256,
            "snapshot_bytes": self.snapshot_bytes}
