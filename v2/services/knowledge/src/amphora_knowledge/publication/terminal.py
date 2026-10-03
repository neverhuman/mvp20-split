"""One immutable transaction pairs a verified derived artifact and logical receipt."""

import hashlib

from amphora_contracts_artifacts import FinalizedReceipt, PublicationObservation
from amphora_contracts_knowledge import (
    ReasoningPublicationFailed,
    ReasoningPublicationPending,
    ReasoningPublicationPublished,
    ReasoningPublicationStatus,
)
from sqlalchemy import text

from ..authoring.canonical import KnowledgeError, canonical
from ..reasoning.profile import raw
from .payload import PublicationRequestDocument
from .policy import LogicalReceiptPolicy
from .records import checked_bytes
from .store import PUBLICATION_SCOPE


class PublicationTerminals:
    def __init__(self, journal):
        self.journal, self.store = journal, journal.store
        self.policy = LogicalReceiptPolicy()

    @staticmethod
    def _status(document, outcome):
        return ReasoningPublicationStatus(wire_version="1", request=document.request, actor_id=document.actor_id, outcome=outcome)

    @staticmethod
    def _rejection(progress, code, rejection):
        if progress is None or progress.attempt.stage != "finalizing":
            if rejection is not None:
                raise KnowledgeError("publication_rejection_unexpected")
            return
        if rejection is None:
            raise KnowledgeError("publication_finalization_unresolved")
        proof = PublicationObservation.model_validate(raw(rejection))
        command = progress.attempt.finalize_command(progress.publisher)
        if (proof.identity != command.identity or proof.request_sha256 != command.sha256
                or proof.outcome.status != "rejected" or proof.outcome.reason_code != code):
            raise KnowledgeError("publication_rejection_mismatch")

    def _read(self, connection, document):
        if self.store._intent(connection, document) is None:
            raise KnowledgeError("publication_intent_missing")
        row = connection.execute(text("SELECT * FROM knowledge.publication_terminals WHERE " + PUBLICATION_SCOPE),
                                 document.key).mappings().one_or_none()
        if row is None:
            return None
        body = checked_bytes(row)
        status = ReasoningPublicationStatus.model_validate_json(body)
        progress = self.journal._load(connection, document)
        if (status.request != document.request or status.actor_id != document.actor_id or canonical(status) != body
                or status.outcome.status != row["outcome"] or row["policy"] != self.policy.version
                or row["position"] != (None if progress is None else progress.position)):
            raise KnowledgeError("publication_storage_mismatch")
        if status.outcome.status == "published":
            if progress is None or row["rejection_bytes"] is not None:
                raise KnowledgeError("publication_storage_mismatch")
            derivation = status.outcome.derivation
            finalized = progress.attempt.finalized(progress.payload.artifact, progress.publisher,
                FinalizedReceipt(upload_id=derivation.upload_id, artifact=derivation.artifact), derivation)
            if self.policy.issue(document, progress, finalized) != status.outcome.receipt:
                raise KnowledgeError("publication_storage_mismatch")
        elif status.outcome.status == "failed":
            rejection = (None if row["rejection_bytes"] is None else
                         PublicationObservation.model_validate_json(bytes(row["rejection_bytes"])))
            self._rejection(progress, status.outcome.code, rejection)
            if status.outcome.external_effects != ("none" if progress is None else "possible"):
                raise KnowledgeError("publication_storage_mismatch")
        else:
            raise KnowledgeError("publication_storage_mismatch")
        return status

    def read(self, principal, request):
        document = PublicationRequestDocument.authorized(principal, request)
        with self.store.engine.connect() as connection:
            return self._read(connection, document) or self._status(document, ReasoningPublicationPending())

    def read_for_correction(self, principal, request):
        document = PublicationRequestDocument.for_correction(principal, request)
        with self.store.engine.connect() as connection:
            return self._read(connection, document) or self._status(document, ReasoningPublicationPending())

    def _save(self, connection, lease, progress, outcome, rejection=None):
        status = self._status(lease.document, outcome)
        body = canonical(status)
        if len(body) > 524288:
            raise KnowledgeError("publication_terminal_size_limit")
        connection.execute(text("INSERT INTO knowledge.publication_terminals "
            "(tenant_id,project_id,graph_id,publication_id,position,outcome,policy,canonical_bytes,sha256,rejection_bytes) "
            "VALUES (:tenant,:project,:graph,:publication,:position,:outcome,:policy,:body,:sha,:rejection)"),
            lease.document.key | {"position": None if progress is None else progress.position, "outcome": outcome.status,
                "policy": self.policy.version, "body": body, "sha": hashlib.sha256(body).hexdigest(),
                "rejection": None if rejection is None else canonical(rejection)})
        return status

    def finish(self, lease, position, receipt, derivation):
        with self.store.fenced(lease) as connection:
            previous = self._read(connection, lease.document)
            if previous is not None:
                return previous
            progress = self.journal._load(connection, lease.document)
            if progress is None:
                raise KnowledgeError("publication_payload_missing")
            if type(position) is not int or position != progress.position:
                raise KnowledgeError("publication_position_conflict")
            finalized = progress.attempt.finalized(progress.payload.artifact, progress.publisher, receipt, derivation)
            logical = self.policy.issue(lease.document, progress, finalized)
            return self._save(connection, lease, progress,
                ReasoningPublicationPublished(derivation=finalized.result, receipt=logical))

    def fail(self, lease, position, code, *, rejection=None):
        with self.store.fenced(lease) as connection:
            previous = self._read(connection, lease.document)
            if previous is not None:
                return previous
            progress = self.journal._load(connection, lease.document)
            if ((progress is None and position is not None) or
                    (progress is not None and (type(position) is not int or position != progress.position))):
                raise KnowledgeError("publication_position_conflict")
            if rejection is not None:
                rejection = PublicationObservation.model_validate(raw(rejection))
            self._rejection(progress, code, rejection)
            return self._save(connection, lease, progress, ReasoningPublicationFailed(code=code,
                external_effects="none" if progress is None else "possible"), rejection)
