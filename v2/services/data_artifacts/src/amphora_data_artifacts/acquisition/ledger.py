"""Owner-private immutable acquisition history; no scientific-use permission."""

from amphora_contracts_core import ArtifactRef
from amphora_contracts_evidence import ConversionTrace, SourceRevision
from sqlalchemy import text

from ..persistence.evidence_records import SCOPE, _canonical, _lock
from ..source_rights.ledger import SourceRights
from ..source_rights.model import RightsError
from .provenance import ProvenanceError, SourceDocument, TraceDocument


def _catalog(connection, principal, reference):
    if reference.scope != principal.scope:
        raise ProvenanceError("artifact_scope_mismatch")
    row = connection.execute(text("SELECT * FROM artifacts.catalog WHERE " + SCOPE + " AND artifact_id=:artifact"),
        principal.bindings | {"artifact": reference.artifact_id}).mappings().one_or_none()
    if row is None:
        raise ProvenanceError("artifact_not_finalized")
    actual = ArtifactRef(artifact_id=row["artifact_id"], scope=principal.scope, sha256=row["content_sha256"],
        media_type=row["media_type"], schema_ref=row["schema_ref"], size_bytes=row["size_bytes"])
    if actual != reference:
        raise ProvenanceError("catalog_reference_mismatch")


class AcquisitionLedger:
    def __init__(self, engine):
        self.engine = engine
        self.rights = SourceRights(engine)

    def register(self, principal, revision: SourceRevision, source: SourceDocument) -> SourceRevision:
        principal.require("acquire")
        if revision.reference.scope != principal.scope or revision.rights.scope != principal.scope:
            raise ProvenanceError("source_scope_mismatch")
        if revision.reference != source.reference:
            raise ProvenanceError("source_reference_mismatch")
        prior = revision.supersedes
        ref = revision.reference
        if prior is not None and (prior.scope != ref.scope or prior.source_id != ref.source_id
                                  or prior.revision_id == ref.revision_id):
            raise ProvenanceError("invalid_source_predecessor")
        body = _canonical(revision)
        key = principal.bindings | {"source": ref.source_id, "revision": ref.revision_id,
            "issuer": revision.delivery.issuer_id, "delivery": revision.delivery.delivery_id}
        with self.engine.begin() as connection:
            rights = self.rights.authorize(connection, principal, (ref.raw.artifact_id,), (revision.rights,), "process")
            _lock(connection, principal.scope, [("source", ref.source_id),
                  ("delivery", revision.delivery.issuer_id, revision.delivery.delivery_id)])
            delivered = connection.execute(text("SELECT canonical_bytes FROM artifacts.source_revisions WHERE "
                + SCOPE + " AND issuer_id=:issuer AND delivery_id=:delivery"), key).scalar_one_or_none()
            if delivered is not None:
                if bytes(delivered) != body:
                    raise ProvenanceError("delivery_conflict")
                return revision
            existing = self._source(connection, key)
            if existing is not None:
                raise ProvenanceError("source_revision_conflict")
            if dict(rights.heads)[revision.rights.rights_id] != revision.rights.revision:
                raise RightsError("rights_revision_stale")
            head = connection.execute(text("SELECT revision_id FROM artifacts.source_heads WHERE " + SCOPE
                + " AND source_id=:source"), key).scalar_one_or_none()
            if head != (None if prior is None else prior.revision_id):
                raise ProvenanceError("source_head_conflict")
            if prior is not None:
                previous = self._source(connection, key | {"revision": prior.revision_id})
                if previous is None or SourceRevision.model_validate_json(bytes(previous)).reference != prior:
                    raise ProvenanceError("source_predecessor_mismatch")
            _catalog(connection, principal, ref.raw)
            connection.execute(text("INSERT INTO artifacts.source_revisions "
                "(tenant_id,project_id,source_id,revision_id,issuer_id,delivery_id,raw_artifact_id,raw_sha256,"
                "prior_revision_id,canonical_bytes) VALUES "
                "(:tenant,:project,:source,:revision,:issuer,:delivery,:raw,:digest,:prior,:body)"),
                key | {"raw": ref.raw.artifact_id, "digest": ref.raw.sha256, "prior": head, "body": body})
            connection.execute(text("INSERT INTO artifacts.source_heads (tenant_id,project_id,source_id,revision_id) "
                "VALUES (:tenant,:project,:source,:revision) ON CONFLICT (tenant_id,project_id,source_id) "
                "DO UPDATE SET revision_id=EXCLUDED.revision_id"), key)
        return revision

    @staticmethod
    def _source(connection, key):
        return connection.execute(text("SELECT canonical_bytes FROM artifacts.source_revisions WHERE " + SCOPE
            + " AND source_id=:source AND revision_id=:revision"), key).scalar_one_or_none()

    def history(self, principal, source_id, revision_id):
        principal.require("source_history")
        with self.engine.connect() as connection:
            raw = self._source(connection, principal.bindings | {"source": source_id, "revision": revision_id})
        return None if raw is None else SourceRevision.model_validate_json(bytes(raw))

    def retain_trace(self, principal, trace: ConversionTrace, source: SourceDocument, output: bytes, *, rights_snapshot=None):
        principal.require("acquire")
        if trace.scope != principal.scope:
            raise ProvenanceError("trace_scope_mismatch")
        verified = TraceDocument.verify(trace, source, output)
        if len(verified.canonical_bytes) > 262144:
            raise ProvenanceError("record_limit")
        ref = verified.reference()
        key = principal.bindings | {"trace": trace.trace_id, "source": trace.source.source_id,
                                    "revision": trace.source.revision_id}
        with self.engine.begin() as connection:
            self.rights.lock(connection, principal)
            if rights_snapshot is not None:
                self.rights.fence(connection, principal, rights_snapshot)
            _lock(connection, principal.scope, [("trace", trace.trace_id)])
            existing = connection.execute(text("SELECT canonical_bytes FROM artifacts.conversion_traces WHERE "
                + SCOPE + " AND trace_id=:trace"), key).scalar_one_or_none()
            if existing is not None:
                if bytes(existing) != verified.canonical_bytes:
                    raise ProvenanceError("trace_identity_conflict")
                return ref
            raw = self._source(connection, key)
            if raw is None or SourceRevision.model_validate_json(bytes(raw)).reference != source.reference:
                raise ProvenanceError("unknown_source_revision")
            revision = SourceRevision.model_validate_json(bytes(raw))
            self.rights.authorize(connection, principal, (source.reference.raw.artifact_id, trace.output.artifact_id),
                                  (revision.rights,), "process")
            _catalog(connection, principal, trace.output)
            connection.execute(text("INSERT INTO artifacts.conversion_traces "
                "(tenant_id,project_id,trace_id,source_id,source_revision_id,output_artifact_id,output_sha256,"
                "trace_sha256,canonical_bytes) VALUES "
                "(:tenant,:project,:trace,:source,:revision,:output,:digest,:trace_digest,:body)"),
                key | {"output": trace.output.artifact_id, "digest": trace.output.sha256,
                       "trace_digest": ref.sha256, "body": verified.canonical_bytes})
        return ref

    def trace_history(self, principal, trace_id):
        principal.require("source_history")
        with self.engine.connect() as connection:
            raw = connection.execute(text("SELECT canonical_bytes FROM artifacts.conversion_traces WHERE "
                + SCOPE + " AND trace_id=:trace"), principal.bindings | {"trace": trace_id}).scalar_one_or_none()
        return None if raw is None else ConversionTrace.model_validate_json(bytes(raw))
