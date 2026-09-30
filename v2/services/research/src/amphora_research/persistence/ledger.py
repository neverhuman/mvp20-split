"""Owner-local atomic revisions; public authentication remains an adapter concern."""

import hashlib
import json
from dataclasses import dataclass

from amphora_contracts_core import Scope
from amphora_contracts_research import CandidateRevision, EvidenceNeed, ResearchQuestion, SampleIdentity
from sqlalchemy import Engine, text

from ..identity.questions import QuestionDefinition, ResearchIdentityError
from ..identity.samples import CandidateDefinition, SampleDefinition

Record = CandidateRevision | SampleIdentity | ResearchQuestion | EvidenceNeed
MODELS = {"candidate": CandidateRevision, "sample": SampleIdentity,
          "question": ResearchQuestion, "need": EvidenceNeed}
KEYS = {"candidate": "candidate_id", "sample": "sample_id", "question": "question_id", "need": "need_id"}


@dataclass(frozen=True)
class IdentityDocument:
    record: Record
    kind: str
    identity_id: str
    canonical_bytes: bytes

    @classmethod
    def from_record(cls, scope: Scope, record: Record) -> "IdentityDocument":
        if record.reference.scope != scope:
            raise ResearchIdentityError("record_scope_mismatch")
        kind = next((key for key, model in MODELS.items() if type(record) is model), None)
        if kind is None:
            raise ResearchIdentityError("unknown_record_kind")
        if kind == "candidate":
            CandidateDefinition(record)
        elif kind == "sample":
            SampleDefinition(record)
            if record.material_state is not None:
                raise ResearchIdentityError("material_state_owner_not_implemented")
        elif kind == "question":
            QuestionDefinition(record)
        canonical = json.dumps(record.model_dump(mode="json"), sort_keys=True,
                               separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()
        if len(canonical) > 262144:
            raise ResearchIdentityError("record_limit")
        return cls(record, kind, getattr(record.reference, KEYS[kind]), canonical)

    def key(self) -> dict:
        return {"tenant": self.record.reference.scope.tenant_id, "project": self.record.reference.scope.project_id,
                "kind": self.kind, "id": self.identity_id, "revision": self.record.reference.revision}


class IdentityLedger:
    def __init__(self, engine: Engine):
        self.engine = engine

    def publish(self, scope: Scope, record: Record) -> Record:
        document = IdentityDocument.from_record(scope, record)
        key = document.key()
        # Stable scoped identity lock, not Python's randomized hash. Collisions only serialize extra work.
        lock_bytes = json.dumps([key[k] for k in ("tenant", "project", "kind", "id")], separators=(",", ":")).encode()
        lock = int.from_bytes(hashlib.sha256(lock_bytes).digest()[:8], "big", signed=True)
        with self.engine.begin() as connection:
            connection.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": lock})
            existing = self._read(connection, key)
            if existing is not None:
                if bytes(existing) != document.canonical_bytes:
                    raise ResearchIdentityError("immutable_revision_conflict")
                return record
            head = connection.execute(text("SELECT revision FROM research.identity_heads WHERE "
                "tenant_id=:tenant AND project_id=:project AND kind=:kind AND identity_id=:id"), key).scalar_one_or_none()
            if record.reference.revision != (head or 0) + 1:
                raise ResearchIdentityError("revision_head_conflict")
            target = self._target(connection, document)
            connection.execute(text("INSERT INTO research.identity_records "
                "(tenant_id,project_id,kind,identity_id,revision,prior_revision,canonical_bytes) "
                "VALUES (:tenant,:project,:kind,:id,:revision,:prior,:body)"),
                key | {"prior": head, "body": document.canonical_bytes})
            if target is not None:
                connection.execute(text("INSERT INTO research.identity_links "
                    "(tenant_id,project_id,kind,identity_id,revision,target_kind,target_id,target_revision) "
                    "VALUES (:tenant,:project,:kind,:id,:revision,:target_kind,:target_id,:target_revision)"), key | target)
            connection.execute(text("INSERT INTO research.identity_heads "
                "(tenant_id,project_id,kind,identity_id,revision) VALUES (:tenant,:project,:kind,:id,:revision) "
                "ON CONFLICT (tenant_id,project_id,kind,identity_id) DO UPDATE SET revision=EXCLUDED.revision"), key)
        return record

    @staticmethod
    def _read(connection, key):
        return connection.execute(text("SELECT canonical_bytes FROM research.identity_records WHERE "
            "tenant_id=:tenant AND project_id=:project AND kind=:kind AND identity_id=:id AND revision=:revision"),
            key).scalar_one_or_none()

    def _target(self, connection, document):
        record = document.record
        if document.kind == "sample":
            target_kind, ref = "candidate", record.candidate
        elif document.kind == "need":
            target_kind, ref = "question", record.question
        else:
            return None
        if ref.scope != record.reference.scope:
            raise ResearchIdentityError("reference_scope_mismatch")
        target_id = getattr(ref, KEYS[target_kind])
        raw = self._read(connection, document.key() | {"kind": target_kind, "id": target_id, "revision": ref.revision})
        if raw is None:
            raise ResearchIdentityError("unknown_" + target_kind)
        if document.kind == "need":
            QuestionDefinition(ResearchQuestion.model_validate_json(bytes(raw))).bind_need(record)
        return {"target_kind": target_kind, "target_id": target_id, "target_revision": ref.revision}

    def read(self, scope: Scope, kind: str, identity_id: str, revision: int) -> Record | None:
        if kind not in MODELS:
            raise ResearchIdentityError("unknown_record_kind")
        with self.engine.connect() as connection:
            raw = self._read(connection, {"tenant": scope.tenant_id, "project": scope.project_id,
                                         "kind": kind, "id": identity_id, "revision": revision})
        return None if raw is None else MODELS[kind].model_validate_json(bytes(raw))
