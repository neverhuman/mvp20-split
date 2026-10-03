"""Research-only append history; head is the last committed immutable chain row."""
import hashlib
import json

from amphora_contracts_graph_runtime import ReceiptCorrection
from sqlalchemy import text

from ..assessment.policy import AssessmentError, _identifier
from ..assessment.store import canonical
from ..publication.store import PublicationStore
from .policy import CorrectionPolicy, CorrectionRevision, encoded

SCOPE = "tenant_id=:tenant AND project_id=:project AND issuer_id=:issuer"
CHAIN = SCOPE + " AND chain_id=:chain"


class CorrectionStore:
    def __init__(self, engine):
        self.engine = engine

    @staticmethod
    def _key(chain):
        return {"tenant":chain.scope.tenant_id, "project":chain.scope.project_id,
                "issuer":chain.issuer_id, "chain":chain.chain_id}

    @staticmethod
    def _lock(connection, identity):
        digest = hashlib.sha256(canonical(identity, 2097152)).digest()
        connection.execute(text("SELECT pg_advisory_xact_lock(:key)"),
                           {"key":int.from_bytes(digest[:8], "big", signed=True)})

    @staticmethod
    def _decode(raw):
        record = ReceiptCorrection.model_validate_json(bytes(raw))
        if encoded(record) != bytes(raw):
            raise AssessmentError("correction_record_corrupt")
        return CorrectionRevision(record)

    def select(self, request):
        key = self._key(request.chain)
        if request.revision is not None and request.revision.chain != request.chain:
            raise AssessmentError("correction_selection_mismatch")
        suffix = " ORDER BY ordinal DESC LIMIT 1"
        if request.revision is not None:
            suffix = " AND ordinal=:ordinal"
            key["ordinal"] = request.revision.ordinal
        with self.engine.connect() as connection:
            raw = connection.execute(text("SELECT record_bytes FROM research.receipt_corrections WHERE " + CHAIN + suffix), key).scalar_one_or_none()
        if raw is None:
            return None
        result = self._decode(raw)
        if result.record.chain != request.chain or (request.revision is not None and result.reference != request.revision):
            raise AssessmentError("correction_selection_conflict")
        return result

    def append(self, request, actor_id):
        _identifier(actor_id)
        if request.expected_head is not None and request.expected_head.chain != request.chain:
            raise AssessmentError("correction_predecessor_mismatch")
        key = self._key(request.chain) | {"change":request.change_id}
        intent = canonical({"request":request.model_dump(mode="json"), "actor_id":actor_id}, 2097152)
        # Published source and terminal history are immutable; load before taking a transaction lock.
        # Exact prior command replay needs no newly selected source.
        with self.engine.connect() as connection:
            replay = self._replay(connection, key, intent)
        if replay is not None:
            return replay
        source = PublicationStore(self.engine).lookup(request.chain.scope, request.assessment_id, actor_id)
        if source is None or source.stage != "published":
            raise AssessmentError("correction_publication_pending")
        with self.engine.begin() as connection:
            self._lock(connection, {"kind":"research.correction.change", **{k:v for k,v in key.items() if k != "chain"}})
            self._lock(connection, {"kind":"research.correction.chain", **{k:v for k,v in key.items() if k != "change"}})
            replay = self._replay(connection, key, intent)
            if replay is not None:
                return replay
            raw = connection.execute(text("SELECT record_bytes FROM research.receipt_corrections WHERE " + CHAIN +
                                          " ORDER BY ordinal DESC LIMIT 1"), key).scalar_one_or_none()
            previous = None if raw is None else self._decode(raw)
            actual = None if previous is None else previous.reference
            if actual != request.expected_head:
                raise AssessmentError("correction_head_conflict")
            result = CorrectionPolicy().issue(request.chain, source.receipt, change_id=request.change_id,
                actor_id=actor_id, reason_code=request.reason_code, predecessor=previous)
            body = encoded(result.record)
            if len(body) > 2097152:
                raise AssessmentError("correction_record_limit")
            connection.execute(text("INSERT INTO research.receipt_corrections "
                "(tenant_id,project_id,issuer_id,chain_id,ordinal,change_id,request_bytes,record_bytes) "
                "VALUES (:tenant,:project,:issuer,:chain,:ordinal,:change,:request,:record)"),
                key | {"ordinal":result.record.ordinal, "request":intent, "record":body})
            return result

    def _replay(self, connection, key, intent):
        row = connection.execute(text("SELECT request_bytes,record_bytes FROM research.receipt_corrections WHERE " +
                                      SCOPE + " AND change_id=:change"), key).mappings().one_or_none()
        if row is None:
            return None
        stored = bytes(row["request_bytes"])
        if json.loads(stored)["actor_id"] != json.loads(intent)["actor_id"]:
            raise AssessmentError("assessment_actor_mismatch")
        if stored != intent:
            raise AssessmentError("correction_identity_conflict")
        return self._decode(row["record_bytes"])
