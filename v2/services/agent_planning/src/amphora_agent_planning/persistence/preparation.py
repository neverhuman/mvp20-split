"""Persist bounded input fingerprints before call issuance; never a rights lease."""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import text

from ..context.policy import require
from ..repair.manifest import PreparationManifest
from . import family_state
from .extraction import ExtractionJournal
from .journal import KEY, PlanningJournal
from .repair import RepairJournal


@dataclass(frozen=True)
class StoredPreparation:
    manifest: PreparationManifest
    registered_at: datetime


class PreparationJournal:
    def __init__(self, engine):
        self.engine = engine
        self.journal = PlanningJournal(engine)
        self.families = RepairJournal(engine)
        self.extractions = ExtractionJournal(engine)

    def _bound(self, connection, principal, manifest):
        document = manifest.document()
        key = self.journal._key(document.engagement)
        membership = self.families._member(connection, key, principal)
        require(membership is not None and membership.root.task.document().engagement == document.root, "repair_preparation_membership")
        member = family_state.member(connection, key)
        require(member["parent_trace_id"] == document.parent.trace_id and member["parent_sha256"] == document.parent.sha256,
                "repair_preparation_parent")
        task = self.extractions._task(connection, principal, document.task_id)
        require(task is not None and task.snapshot.document().engagement == document.engagement and
                task.snapshot.sha256 == document.task_sha256 and task.snapshot.request.sha256 == document.request_sha256,
                "repair_preparation_request")

    def _read(self, connection, principal, key):
        row = connection.execute(text("SELECT * FROM planning.repair_preparations WHERE " + KEY), key).mappings().first()
        if row is None:
            return None
        manifest = PreparationManifest.from_bytes(bytes(row["canonical_bytes"]))
        document = manifest.document()
        require(manifest.canonical == bytes(row["canonical_bytes"]) and manifest.sha256 == row["manifest_sha256"],
                "stored_repair_preparation")
        require(self.journal._key(document.engagement) == {name: key[name] for name in ("tenant", "project", "engagement")} and
                (document.root.engagement_id, document.task_id, document.task_sha256, document.request_sha256,
                 document.parent.trace_id, document.parent.sha256, document.packet.sha256) ==
                (row["root_engagement_id"], row["task_id"], row["task_sha256"], row["request_sha256"],
                 row["parent_trace_id"], row["parent_sha256"], row["packet_sha256"]), "stored_repair_preparation")
        self._bound(connection, principal, manifest)
        return StoredPreparation(manifest, row["registered_at"])

    def register(self, principal, prepared):
        principal.require("record_attempts", prepared.plan.task.document().scope)
        # All rendering/history revalidation is outside the transaction; no peer I/O here.
        manifest = PreparationManifest.bind(prepared)
        document = manifest.document()
        key = self.journal._key(document.engagement)
        with self.engine.begin() as connection:
            family_state.lock_request(connection, key)
            self._bound(connection, principal, manifest)
            existing = self._read(connection, principal, key)
            if existing is not None:
                require(existing.manifest.canonical == manifest.canonical, "repair_preparation_conflict")
                return existing
            consumed = connection.execute(text("SELECT EXISTS (SELECT 1 FROM planning.dispatches WHERE " + KEY +
                " UNION ALL SELECT 1 FROM planning.observations WHERE " + KEY + ")"), key).scalar_one()
            require(not consumed, "repair_preparation_after_call")
            connection.execute(text("INSERT INTO planning.repair_preparations "
                "(tenant_id,project_id,engagement_id,root_engagement_id,task_id,task_sha256,request_sha256,"
                "parent_trace_id,parent_sha256,manifest_sha256,packet_sha256,canonical_bytes) "
                "VALUES (:tenant,:project,:engagement,:root,:task,:task_digest,:request,:parent,:parent_digest,:digest,:packet,:content)"),
                {**key, "root": document.root.engagement_id, "task": document.task_id, "task_digest": document.task_sha256,
                 "request": document.request_sha256, "parent": document.parent.trace_id, "parent_digest": document.parent.sha256,
                 "digest": manifest.sha256, "packet": document.packet.sha256, "content": manifest.canonical})
            return self._read(connection, principal, key)

    def read(self, principal, reference):
        principal.require("read_attempts", reference.scope)
        with self.engine.connect() as connection:
            return self._read(connection, principal, self.journal._key(reference))

    def issued(self, principal, binding):
        reference = binding.reference()
        principal.require("read_attempts", reference.engagement.scope)
        key = {**self.journal._key(reference.engagement), "ordinal": reference.ordinal}
        with self.engine.connect() as connection:
            request = self.journal._request(connection, key, principal)
            require(request is not None and request.sha256 == reference.request_sha256, "request_conflict")
            return connection.execute(text("SELECT 1 FROM planning.dispatches WHERE " + KEY + " AND ordinal=:ordinal"), key).first() is not None
