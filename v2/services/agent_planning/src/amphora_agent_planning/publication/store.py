"""Owned publication intent and DB-clock lease; no peer calls under locks."""

import json
import uuid
from dataclasses import dataclass
from datetime import datetime

from amphora_contracts_core import Identifier
from pydantic import TypeAdapter
from sqlalchemy import text

from ..context.policy import require
from ..persistence.extraction import ExtractionJournal
from .identity import PublicationIdentity
from .payload import content_schema

KEY = "tenant_id=:tenant AND project_id=:project AND publication_id=:publication"
LEASE = KEY + " AND holder=:holder AND fence=:fence AND expires_at>clock_timestamp()"


@dataclass(frozen=True)
class PublicationLease:
    identity: PublicationIdentity
    holder: str
    fence: int
    expires_at: datetime


class PublicationStore:
    def __init__(self, engine, publisher_id):
        TypeAdapter(Identifier).validate_python(publisher_id, strict=True)
        self.engine, self.publisher_id = engine, publisher_id
        self.extractions = ExtractionJournal(engine)
        self.schema = content_schema()  # Package bytes read before any SQL transaction.

    @staticmethod
    def key(principal, publication_id):
        TypeAdapter(Identifier).validate_python(publication_id, strict=True)
        return {"tenant": principal.scope.tenant_id, "project": principal.scope.project_id,
                "publication": publication_id}

    @staticmethod
    def lock(connection, key):
        token = json.dumps(["planning.trace_publication.v1", key["tenant"], key["project"], key["publication"]])
        connection.execute(text("SELECT pg_advisory_xact_lock(hashtextextended(:token,0))"), {"token": token})

    def identity(self, connection, principal, key):
        row = connection.execute(text("SELECT * FROM planning.trace_publications WHERE " + KEY), key).mappings().first()
        if row is None:
            return None
        identity = PublicationIdentity.restore(bytes(row["canonical_bytes"]), principal)
        document, trace = identity.document(), identity.trace()
        require(identity.sha256 == row["identity_sha256"] and document["publication_id"] == key["publication"] and
                identity.actor_id == row["actor_id"] and trace.trace_id == row["trace_id"] and
                trace.sha256 == row["trace_sha256"], "stored_publication_identity")
        require(document["publisher_id"] == row["publisher_id"] == self.publisher_id and
                row["schema_sha256"] == self.schema.sha256, "publication_configuration_conflict")
        return identity

    def register(self, principal, publication_id, trace):
        identity = PublicationIdentity.bind(principal, publication_id, trace, self.publisher_id)
        key = self.key(principal, publication_id)
        with self.engine.begin() as connection:
            self.lock(connection, key)
            existing = self.identity(connection, principal, key)
            if existing is not None:
                require(existing.canonical == identity.canonical, "publication_identity_conflict")
                return existing
            require(self.extractions._trace(connection, principal, identity.trace()) is not None,
                    "publication_trace_unknown")
            connection.execute(text("INSERT INTO planning.trace_publications "
                "(tenant_id,project_id,publication_id,actor_id,trace_id,trace_sha256,publisher_id,schema_sha256,"
                "identity_sha256,canonical_bytes) VALUES (:tenant,:project,:publication,:actor,:trace,:trace_digest,"
                ":publisher,:schema,:digest,:content)"), {**key, "actor": principal.actor_id,
                "trace": trace.trace_id, "trace_digest": trace.sha256, "publisher": self.publisher_id,
                "schema": self.schema.sha256, "digest": identity.sha256, "content": identity.canonical})
            connection.execute(text("INSERT INTO planning.trace_publication_control "
                "(tenant_id,project_id,publication_id) VALUES (:tenant,:project,:publication)"), key)
        return identity

    @staticmethod
    def seconds(value):
        require(type(value) is int and 1 <= value <= 300, "publication_lease_seconds")

    def acquire(self, principal, publication_id, seconds=30):
        principal.require("record_attempts", principal.scope)
        self.seconds(seconds)
        key = self.key(principal, publication_id)
        with self.engine.begin() as connection:
            self.lock(connection, key)
            identity = self.identity(connection, principal, key)
            require(identity is not None, "publication_unknown")
            holder = uuid.uuid4().hex
            row = connection.execute(text("UPDATE planning.trace_publication_control SET holder=:holder,"
                "fence=fence+1,expires_at=clock_timestamp()+(:seconds * interval '1 second') WHERE " + KEY +
                " AND (expires_at IS NULL OR expires_at<=clock_timestamp()) AND fence<9007199254740991 "
                "RETURNING fence,expires_at"), {**key, "holder": holder, "seconds": seconds}).mappings().first()
            require(row is not None, "publication_lease_unavailable")
            return PublicationLease(identity, holder, row["fence"], row["expires_at"])

    def lease_key(self, connection, principal, lease):
        principal.require("record_attempts", lease.identity.trace().scope)
        key = self.key(principal, lease.identity.document()["publication_id"])
        actual = self.identity(connection, principal, key)
        require(actual is not None and actual.canonical == lease.identity.canonical, "publication_identity_conflict")
        return {**key, "holder": lease.holder, "fence": lease.fence}

    def guard(self, principal, lease):
        with self.engine.connect() as connection:
            key = self.lease_key(connection, principal, lease)
            require(connection.execute(text("SELECT 1 FROM planning.trace_publication_control WHERE " + LEASE), key)
                    .first() is not None, "publication_lease_lost")

    def renew(self, principal, lease, seconds=30):
        self.seconds(seconds)
        with self.engine.begin() as connection:
            key = self.lease_key(connection, principal, lease)
            self.lock(connection, key)
            expires = connection.execute(text("UPDATE planning.trace_publication_control SET "
                "expires_at=clock_timestamp()+(:seconds * interval '1 second') WHERE " + LEASE + " RETURNING expires_at"),
                {**key, "seconds": seconds}).scalar_one_or_none()
            require(expires is not None, "publication_lease_lost")
            return PublicationLease(lease.identity, lease.holder, lease.fence, expires)

    def release(self, principal, lease):
        with self.engine.begin() as connection:
            key = self.lease_key(connection, principal, lease)
            self.lock(connection, key)
            result = connection.execute(text("UPDATE planning.trace_publication_control SET holder=NULL,expires_at=NULL "
                                             "WHERE " + LEASE), key)
            require(result.rowcount == 1, "publication_lease_lost")
