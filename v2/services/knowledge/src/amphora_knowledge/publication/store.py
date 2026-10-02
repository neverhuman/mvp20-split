"""Immutable publication selection and fenced short owner transactions."""

import hashlib
import uuid
from contextlib import contextmanager

from amphora_contracts_knowledge import ReasoningRequest, reasoning_artifact_schema
from sqlalchemy import text

from ..authoring.canonical import KnowledgeError, canonical
from ..persistence.ledger import lock_graph
from ..persistence.records import SCOPE
from ..reasoning.requests import RequestDocument
from ..reasoning.store import REQUEST_SCOPE, ReasoningStore
from .identity import PublicationLease, PublisherIdentity
from .payload import PublicationRequestDocument

PUBLICATION_SCOPE = SCOPE + " AND publication_id=:publication"


def _duration(seconds):
    if type(seconds) is not int or not 1 <= seconds <= 300:
        raise KnowledgeError("publication_lease_duration_invalid")
    return seconds


class PublicationStore:
    def __init__(self, engine):
        self.engine = engine

    @staticmethod
    def source(connection, document):
        """Restore owner history under publish authority, without minting grants."""
        key = {k: v for k, v in document.key.items() if k != "publication"}
        key["request"] = document.request.reasoning_request_id
        row = connection.execute(text("SELECT * FROM knowledge.reasoning_intents WHERE " + REQUEST_SCOPE), key).mappings().one_or_none()
        if row is None:
            raise KnowledgeError("publication_reasoning_missing")
        body = bytes(row["canonical_bytes"])
        request = ReasoningRequest.model_validate_json(body)
        source = RequestDocument(request, row["actor_id"], body, hashlib.sha256(body).hexdigest())
        if source.key != key or canonical(request) != body:
            raise KnowledgeError("reasoning_storage_mismatch")
        registered = ReasoningStore._existing(connection, source)
        document.result(registered.status)
        return registered

    @staticmethod
    def _intent(connection, document):
        row = connection.execute(text("SELECT * FROM knowledge.reasoning_publications WHERE " + PUBLICATION_SCOPE),
                                 document.key).mappings().one_or_none()
        if row is not None and (row["actor_id"] != document.actor_id or row["request_sha256"] != document.sha256
                               or bytes(row["canonical_bytes"]) != document.body):
            raise KnowledgeError("publication_identity_conflict")
        return row

    def begin(self, principal, request, publisher):
        document = PublicationRequestDocument.authorized(principal, request)
        publisher = PublisherIdentity(publisher.actor_id, publisher.issuer_id)
        schema = reasoning_artifact_schema()
        with self.engine.begin() as connection:
            lock_graph(connection, document.request.graph)
            row = self._intent(connection, document)
            source = self.source(connection, document)
            result_sha = hashlib.sha256(canonical(document.result(source.status))).hexdigest()
            if row is not None:
                if (row["publisher_actor"] != publisher.actor_id or row["issuer_id"] != publisher.issuer_id
                        or row["schema_sha256"] != schema.sha256 or row["result_sha256"] != result_sha):
                    raise KnowledgeError("publication_binding_conflict")
                return document
            connection.execute(text("INSERT INTO knowledge.reasoning_publications "
                "(tenant_id,project_id,graph_id,publication_id,actor_id,request_sha256,canonical_bytes,request_id,"
                "result_sha256,publisher_actor,issuer_id,schema_sha256) VALUES "
                "(:tenant,:project,:graph,:publication,:actor,:sha,:body,:request,:result,:publisher,:issuer,:schema)"),
                document.key | {"actor": document.actor_id, "sha": document.sha256, "body": document.body,
                    "request": document.request.reasoning_request_id, "result": result_sha,
                    "publisher": publisher.actor_id, "issuer": publisher.issuer_id, "schema": schema.sha256})
            connection.execute(text("INSERT INTO knowledge.publication_leases "
                "(tenant_id,project_id,graph_id,publication_id) VALUES (:tenant,:project,:graph,:publication)"), document.key)
        return document

    def acquire(self, principal, request, *, seconds=60):
        document = PublicationRequestDocument.authorized(principal, request)
        duration, holder = _duration(seconds), uuid.uuid4().hex
        with self.engine.begin() as connection:
            if self._intent(connection, document) is None:
                raise KnowledgeError("publication_intent_missing")
            row = connection.execute(text("UPDATE knowledge.publication_leases SET fence=fence+1, holder=:holder, "
                "expires_at=clock_timestamp()+make_interval(secs=>:seconds) WHERE " + PUBLICATION_SCOPE +
                " AND (expires_at IS NULL OR expires_at <= clock_timestamp()) RETURNING fence,expires_at"),
                document.key | {"holder": holder, "seconds": duration}).mappings().one_or_none()
            return None if row is None else PublicationLease(document, holder, row["fence"], row["expires_at"])

    @contextmanager
    def fenced(self, lease):
        """Compose a short state write; callers must never do peer I/O here."""
        with self.engine.begin() as connection:
            if self._intent(connection, lease.document) is None:
                raise KnowledgeError("publication_intent_missing")
            # Take the lock BEFORE comparing the database clock, including after
            # waiting on another transaction. A pre-lock timestamp is unsafe.
            connection.execute(text("SELECT fence FROM knowledge.publication_leases WHERE " + PUBLICATION_SCOPE +
                                    " FOR UPDATE"), lease.key).scalar_one()
            live = connection.execute(text("SELECT 1 FROM knowledge.publication_leases WHERE " + PUBLICATION_SCOPE +
                " AND holder=:holder AND fence=:fence AND expires_at > clock_timestamp()"), lease.key).scalar_one_or_none()
            if live is None:
                raise KnowledgeError("publication_lease_lost")
            yield connection

    def renew(self, lease, *, seconds=60):
        duration = _duration(seconds)
        with self.fenced(lease) as connection:
            expires = connection.execute(text("UPDATE knowledge.publication_leases SET "
                "expires_at=clock_timestamp()+make_interval(secs=>:seconds) WHERE " + PUBLICATION_SCOPE +
                " RETURNING expires_at"), lease.key | {"seconds": duration}).scalar_one()
        return PublicationLease(lease.document, lease.holder, lease.fence, expires)

    def release(self, lease):
        with self.fenced(lease) as connection:
            connection.execute(text("UPDATE knowledge.publication_leases SET holder=NULL,expires_at=NULL WHERE " +
                                    PUBLICATION_SCOPE), lease.key)
