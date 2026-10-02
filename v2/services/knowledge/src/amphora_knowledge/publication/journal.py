"""Immutable reviewed payload and bounded attempt journal; no external I/O."""

import hashlib
from dataclasses import dataclass

from sqlalchemy import text

from ..authoring.canonical import KnowledgeError
from .attempt import PublicationAttempt
from .identity import PublisherIdentity
from .payload import PublicationRequestDocument, ReasoningArtifact
from .records import AttemptEvent, PayloadRecord, checked_bytes
from .store import PUBLICATION_SCOPE


@dataclass(frozen=True)
class PublicationProgress:
    payload: PayloadRecord
    publisher: PublisherIdentity
    position: int
    attempt: PublicationAttempt


class PublicationJournal:
    def __init__(self, store):
        self.store = store

    @staticmethod
    def _require_open(connection, document):
        terminal = connection.execute(text("SELECT 1 FROM knowledge.publication_terminals WHERE " + PUBLICATION_SCOPE),
                                      document.key).scalar_one_or_none()
        if terminal is not None:
            raise KnowledgeError("publication_already_terminal")

    def _load(self, connection, document):
        intent = self.store._intent(connection, document)
        if intent is None:
            raise KnowledgeError("publication_intent_missing")
        row = connection.execute(text("SELECT * FROM knowledge.publication_payloads WHERE " + PUBLICATION_SCOPE),
                                 document.key).mappings().one_or_none()
        if row is None:
            return None
        source = self.store.source(connection, document)
        payload = PayloadRecord.restore(document, source.status, checked_bytes(row))
        if (payload.artifact.content.sha256 != intent["result_sha256"]
                or payload.artifact.content.schema_ref.sha256 != intent["schema_sha256"]):
            raise KnowledgeError("publication_storage_mismatch")
        publisher = PublisherIdentity(intent["publisher_actor"], intent["issuer_id"])
        rows = connection.execute(text("SELECT * FROM knowledge.publication_events WHERE " + PUBLICATION_SCOPE +
            " ORDER BY position LIMIT 49"), document.key).mappings().all()
        if not rows or len(rows) > 48:
            raise KnowledgeError("publication_storage_mismatch")
        attempt, used_ids = None, set()
        for position, row in enumerate(rows, 1):
            if row["position"] != position:
                raise KnowledgeError("publication_storage_mismatch")
            event = AttemptEvent(row["action"], checked_bytes(row))
            attempt = event.apply(attempt, payload.artifact)
            if row["ordinal"] != attempt.identity.ordinal:
                raise KnowledgeError("publication_storage_mismatch")
            if event.action == "prepared":
                keys = {attempt.identity.begin_id, attempt.identity.finalize_id}
                if keys & used_ids:
                    raise KnowledgeError("publication_storage_mismatch")
                used_ids.update(keys)
        return PublicationProgress(payload, publisher, len(rows), attempt)

    @staticmethod
    def _append(connection, lease, position, attempt, event):
        connection.execute(text("INSERT INTO knowledge.publication_events "
            "(tenant_id,project_id,graph_id,publication_id,position,ordinal,action,canonical_bytes,sha256,fence,holder) "
            "VALUES (:tenant,:project,:graph,:publication,:position,:ordinal,:action,:body,:sha,:fence,:holder)"),
            lease.key | {"position": position, "ordinal": attempt.identity.ordinal, "action": event.action,
                         "body": event.body, "sha": hashlib.sha256(event.body).hexdigest()})

    def prepare(self, lease, observation):
        with self.store.fenced(lease) as connection:
            self._require_open(connection, lease.document)
            previous = self._load(connection, lease.document)
            if previous is not None:
                return previous
            source = self.store.source(connection, lease.document)
            payload = PayloadRecord(ReasoningArtifact.reviewed(lease.document, source.status, observation))
            body = payload.body
            connection.execute(text("INSERT INTO knowledge.publication_payloads "
                "(tenant_id,project_id,graph_id,publication_id,canonical_bytes,sha256) "
                "VALUES (:tenant,:project,:graph,:publication,:body,:sha)"),
                lease.document.key | {"body": body, "sha": hashlib.sha256(body).hexdigest()})
            attempt = PublicationAttempt.first()
            self._append(connection, lease, 1, attempt, AttemptEvent.prepared(attempt))
            return self._load(connection, lease.document)

    def read(self, principal, request):
        document = PublicationRequestDocument.authorized(principal, request)
        with self.store.engine.connect() as connection:
            return self._load(connection, document)

    def advance(self, lease, position, action, receipt=None):
        with self.store.fenced(lease) as connection:
            self._require_open(connection, lease.document)
            progress = self._load(connection, lease.document)
            if progress is None:
                raise KnowledgeError("publication_payload_missing")
            if type(position) is not int or progress.position != position:
                raise KnowledgeError("publication_position_conflict")
            if action == "replacement" and receipt is None:
                event = AttemptEvent.prepared(progress.attempt.replacement())
            else:
                event = AttemptEvent.transition(action, receipt)
            attempt = event.apply(progress.attempt, progress.payload.artifact)
            self._append(connection, lease, position + 1, attempt, event)
            return PublicationProgress(progress.payload, progress.publisher, position + 1, attempt)
