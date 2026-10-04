"""Immutable extraction history; derive provenance from this owner's journal."""

from dataclasses import dataclass
from datetime import datetime

from amphora_contracts_planning import ExtractionTraceRef, ProviderAttemptRef
from sqlalchemy import text

from ..context.policy import require
from ..extraction.snapshot import ExtractionSnapshot
from ..extraction.trace import TraceProjection
from .journal import KEY, PlanningJournal

SCOPE_KEY = "tenant_id=:tenant AND project_id=:project"


@dataclass(frozen=True)
class StoredTask:
    snapshot: ExtractionSnapshot
    registered_at: datetime


@dataclass(frozen=True)
class StoredTrace:
    projection: TraceProjection
    recorded_at: datetime


class ExtractionJournal:
    def __init__(self, engine):
        self.engine = engine
        self.journal = PlanningJournal(engine)

    @staticmethod
    def _scope(principal):
        return {"tenant": principal.scope.tenant_id, "project": principal.scope.project_id}

    def _task(self, connection, principal, task_id):
        key = {**self._scope(principal), "task": task_id}
        row = connection.execute(text("SELECT * FROM planning.extraction_tasks WHERE " + SCOPE_KEY +
                                      " AND task_id=:task"), key).mappings().first()
        if row is None:
            return None
        request = self.journal._request(connection, {**key, "engagement": row["engagement_id"]}, principal)
        require(request is not None and request.sha256 == row["request_sha256"], "stored_extraction_request")
        snapshot = ExtractionSnapshot.from_bytes(bytes(row["canonical_bytes"]), request)
        require(snapshot.sha256 == row["task_sha256"] and snapshot.document().task_id == task_id,
                "stored_extraction_task")
        return StoredTask(snapshot, row["registered_at"])

    def register(self, principal, task):
        principal.require("record_requests", task.document().scope)
        task = ExtractionSnapshot.from_bytes(task.canonical, task.request)
        document = task.document()
        key = self.journal._key(document.engagement)
        with self.engine.begin() as connection:
            self.journal._lock(connection, key)
            request = self.journal._request(connection, key, principal)
            require(request is not None and request.sha256 == document.request_sha256, "extraction_request_unknown")
            connection.execute(text("INSERT INTO planning.extraction_tasks "
                "(tenant_id,project_id,task_id,engagement_id,request_sha256,task_sha256,canonical_bytes) "
                "VALUES (:tenant,:project,:task,:engagement,:request,:digest,:content) ON CONFLICT DO NOTHING"),
                {**key, "task": document.task_id, "request": document.request_sha256,
                 "digest": task.sha256, "content": task.canonical})
            result = self._task(connection, principal, document.task_id)
            require(result is not None and result.snapshot.canonical == task.canonical, "extraction_task_conflict")
            return result

    def read_task(self, principal, task_id):
        principal.require("read_attempts", principal.scope)
        with self.engine.connect() as connection:
            return self._task(connection, principal, task_id)

    def _trace(self, connection, principal, reference, seen=()):
        require(reference.scope == principal.scope, "extraction_trace_scope")
        require(reference.trace_id not in seen and len(seen) <= 16, "stored_extraction_lineage")
        key = {**self._scope(principal), "trace": reference.trace_id}
        row = connection.execute(text("SELECT * FROM planning.extraction_traces WHERE " + SCOPE_KEY +
                                      " AND trace_id=:trace"), key).mappings().first()
        if row is None:
            return None
        projection = TraceProjection(bytes(row["canonical_bytes"]))
        require(projection.sha256 == row["trace_sha256"] == reference.sha256, "extraction_trace_digest")
        document = projection.document()
        require(document.scope == principal.scope and document.trace_id == reference.trace_id and
                document.task_id == row["task_id"] and document.attempt.ordinal == row["ordinal"] and
                document.attempt.engagement.engagement_id == row["engagement_id"], "stored_extraction_trace")
        prior = None
        require((document.prior is None) == (row["prior_trace_id"] is None), "stored_extraction_parent")
        if document.prior is not None:
            require(document.prior.trace_id == row["prior_trace_id"] and
                    document.prior.sha256 == row["prior_sha256"], "stored_extraction_parent")
            prior = self._trace(connection, principal, document.prior, (*seen, reference.trace_id))
            require(prior is not None, "extraction_parent_unknown")
        task = self._task(connection, principal, document.task_id)
        require(task is not None, "extraction_task_unknown")
        attempt_key = {**key, "engagement": row["engagement_id"], "ordinal": row["ordinal"]}
        attempt = self.journal._attempt(connection, attempt_key, task.snapshot.request)
        require(attempt is not None, "extraction_attempt_unknown")
        rebuilt = TraceProjection.derive(document.trace_id, task.snapshot, attempt.observation,
                                         None if prior is None else prior.projection)
        require(rebuilt.canonical == projection.canonical, "stored_extraction_projection")
        return StoredTrace(projection, row["recorded_at"])

    def read_trace(self, principal, reference):
        principal.require("read_attempts", reference.scope)
        reference = ExtractionTraceRef.model_validate_json(reference.model_dump_json(warnings=False))
        with self.engine.connect() as connection:
            return self._trace(connection, principal, reference)

    def record(self, principal, task_id, attempt_ref, trace_id, prior=None):
        principal.require("record_attempts", attempt_ref.engagement.scope)
        # Pydantic serialization can normalize a constructed bool ordinal to 1.
        require(type(attempt_ref.ordinal) is int, "extraction_attempt_ordinal")
        attempt_ref = ProviderAttemptRef.model_validate_json(attempt_ref.model_dump_json(warnings=False))
        if prior is not None:
            prior = ExtractionTraceRef.model_validate_json(prior.model_dump_json(warnings=False))
        key = {**self.journal._key(attempt_ref.engagement), "ordinal": attempt_ref.ordinal}
        with self.engine.begin() as connection:
            self.journal._lock(connection, key)
            task = self._task(connection, principal, task_id)
            require(task is not None, "extraction_task_unknown")
            require(task.snapshot.document().engagement == attempt_ref.engagement and
                    task.snapshot.request.sha256 == attempt_ref.request_sha256, "extraction_attempt_binding")
            attempt = self.journal._attempt(connection, key, task.snapshot.request)
            require(attempt is not None, "extraction_attempt_unknown")
            parent = None if prior is None else self._trace(connection, principal, prior)
            require(prior is None or parent is not None, "extraction_parent_unknown")
            projection = TraceProjection.derive(trace_id, task.snapshot, attempt.observation,
                                                 None if parent is None else parent.projection)
            connection.execute(text("INSERT INTO planning.extraction_traces "
                "(tenant_id,project_id,trace_id,task_id,engagement_id,ordinal,trace_sha256,canonical_bytes,"
                "prior_trace_id,prior_sha256) VALUES (:tenant,:project,:trace,:task,:engagement,:ordinal,:digest,"
                ":content,:prior,:prior_digest) ON CONFLICT DO NOTHING"),
                {**key, "trace": trace_id, "task": task_id, "digest": projection.sha256,
                 "content": projection.canonical, "prior": None if prior is None else prior.trace_id,
                 "prior_digest": None if prior is None else prior.sha256})
            row = connection.execute(text("SELECT trace_id,trace_sha256 FROM planning.extraction_traces WHERE " +
                                          KEY + " AND ordinal=:ordinal"), key).mappings().first()
            require(row is not None and row["trace_id"] == trace_id and row["trace_sha256"] == projection.sha256,
                    "extraction_trace_conflict")
            return self._trace(connection, principal, projection.reference())
