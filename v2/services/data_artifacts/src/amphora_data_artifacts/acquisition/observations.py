"""Durable lookup intent/result ownership; no locks span peer HTTP calls."""

from amphora_contracts_evidence import (
    ConversionTrace,
    ObserveSourceIdentity,
    SourceIdentityObservation,
    SourceIdentityStatus,
    SourceRevision,
)
from sqlalchemy import text

from ..persistence.evidence_records import SCOPE, _canonical, _lock
from ..source_rights.ledger import SourceRights
from .provenance import ProvenanceError


class IdentityObservations:
    def __init__(self, engine):
        self.engine = engine

    @staticmethod
    def _key(principal, request):
        principal.require("acquire")
        if request.trace.scope != principal.scope:
            raise ProvenanceError("observation_scope_mismatch")
        return principal.bindings | {"observation": request.observation_id}

    @staticmethod
    def _result(connection, key):
        raw = connection.execute(text("SELECT canonical_bytes FROM artifacts.identity_observation_results WHERE "
            + SCOPE + " AND observation_id=:observation"), key).scalar_one_or_none()
        return None if raw is None else SourceIdentityObservation.model_validate_json(bytes(raw))

    def begin(self, principal, request):
        key = self._key(principal, request)
        body = _canonical(request)
        with self.engine.begin() as connection:
            _lock(connection, principal.scope, [("identity_observation", request.observation_id)])
            previous = connection.execute(text("SELECT canonical_bytes FROM artifacts.identity_observation_intents WHERE "
                + SCOPE + " AND observation_id=:observation"), key).scalar_one_or_none()
            if previous is not None:
                if bytes(previous) != body:
                    raise ProvenanceError("observation_identity_conflict")
                return self._result(connection, key)
            digest = connection.execute(text("SELECT trace_sha256 FROM artifacts.conversion_traces WHERE "
                + SCOPE + " AND trace_id=:trace"), key | {"trace": request.trace.trace_id}).scalar_one_or_none()
            if digest != request.trace.sha256:
                raise ProvenanceError("observation_trace_mismatch")
            connection.execute(text("INSERT INTO artifacts.identity_observation_intents "
                "(tenant_id,project_id,observation_id,trace_id,trace_sha256,canonical_bytes) "
                "VALUES (:tenant,:project,:observation,:trace,:digest,:body)"),
                key | {"trace": request.trace.trace_id, "digest": digest, "body": body})
        return None

    def source(self, principal, request):
        key = self._key(principal, request)
        with self.engine.connect() as connection:
            row = connection.execute(text("SELECT t.canonical_bytes AS trace,s.canonical_bytes AS source "
                "FROM artifacts.conversion_traces t JOIN artifacts.source_revisions s ON "
                "(s.tenant_id,s.project_id,s.source_id,s.revision_id)="
                "(t.tenant_id,t.project_id,t.source_id,t.source_revision_id) "
                "WHERE t.tenant_id=:tenant AND t.project_id=:project AND t.trace_id=:trace AND t.trace_sha256=:digest"),
                key | {"trace": request.trace.trace_id, "digest": request.trace.sha256}).mappings().one_or_none()
        if row is None:
            raise ProvenanceError("observation_trace_mismatch")
        return ConversionTrace.model_validate_json(bytes(row["trace"])), SourceRevision.model_validate_json(bytes(row["source"]))

    def complete(self, principal, result, *, rights_snapshot):
        request = result.request
        key = self._key(principal, request)
        with self.engine.begin() as connection:
            rights = SourceRights(self.engine)
            rights.lock(connection, principal)
            _lock(connection, principal.scope, [("identity_observation", request.observation_id)])
            intent = connection.execute(text("SELECT canonical_bytes FROM artifacts.identity_observation_intents WHERE "
                + SCOPE + " AND observation_id=:observation"), key).scalar_one_or_none()
            if intent is None or bytes(intent) != _canonical(request):
                raise ProvenanceError("observation_intent_mismatch")
            existing = self._result(connection, key)
            if existing is not None:
                return existing
            rights.fence(connection, principal, rights_snapshot)
            body = _canonical(result)
            if len(body) > 16384:
                raise ProvenanceError("observation_result_limit")
            connection.execute(text("INSERT INTO artifacts.identity_observation_results "
                "(tenant_id,project_id,observation_id,canonical_bytes) VALUES (:tenant,:project,:observation,:body)"),
                key | {"body": body})
        return result

    def history(self, principal, observation_id):
        principal.require("source_history")
        key = principal.bindings | {"observation": observation_id}
        with self.engine.connect() as connection:
            intent = connection.execute(text("SELECT canonical_bytes FROM artifacts.identity_observation_intents WHERE "
                + SCOPE + " AND observation_id=:observation"), key).scalar_one_or_none()
            if intent is None:
                return None
            request = ObserveSourceIdentity.model_validate_json(bytes(intent))
            return SourceIdentityStatus(wire_version="1", request=request, result=self._result(connection, key))
