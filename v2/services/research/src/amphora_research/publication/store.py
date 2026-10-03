"""Research publication journal and DB-clock fencing; never holds SQL across peer I/O."""

import json
import uuid
from dataclasses import dataclass

from sqlalchemy import text

from ..assessment.policy import AssessmentError, _identifier
from ..assessment.store import AssessmentStore, canonical
from .artifact import AssessmentArtifact, SyntheticReceiptPolicy
from .attempt import PublicationProgress

WHERE = "tenant_id=:tenant AND project_id=:project AND assessment_id=:id"


@dataclass(frozen=True)
class PublicationLease:
    initial: PublicationProgress
    holder: str
    fence: int

    @property
    def key(self):
        return self.initial.artifact.stored.intent.key


class PublicationStore:
    def __init__(self, engine):
        self.engine = engine

    def begin(self, scope, assessment_id, actor_id, publisher, issuer):
        _identifier(publisher)
        _identifier(issuer)
        stored = AssessmentStore(self.engine).read(scope, assessment_id, actor_id)
        if stored is None:
            raise AssessmentError("publication_assessment_missing")
        artifact = AssessmentArtifact.from_stored(stored)
        initial = PublicationProgress(artifact, publisher, issuer)
        header = canonical({"format": "research.publication.v1", "publisher": publisher, "issuer": issuer,
                            "policy": SyntheticReceiptPolicy.version, "content": artifact.content.model_dump(mode="json"),
                            "declaration": artifact.declaration.model_dump(mode="json")}, 2097152)
        key = stored.intent.key
        with self.engine.begin() as connection:
            AssessmentStore._lock(connection, key)
            prior = connection.execute(text("SELECT canonical_bytes FROM research.publication_headers WHERE " + WHERE), key).scalar_one_or_none()
            if prior is None:
                connection.execute(text("INSERT INTO research.publication_headers VALUES (:tenant,:project,:id,:body)"), key | {"body": header})
                connection.execute(text("INSERT INTO research.publication_leases (tenant_id,project_id,assessment_id) "
                                        "VALUES (:tenant,:project,:id)"), key)
            elif bytes(prior) != header:
                raise AssessmentError("publication_identity_conflict")
        return initial

    @staticmethod
    def _seconds(seconds):
        if type(seconds) is not int or not 1 <= seconds <= 300:
            raise AssessmentError("publication_lease_duration")

    def acquire(self, initial, seconds=60):
        self._seconds(seconds)
        key = initial.artifact.stored.intent.key
        with self.engine.begin() as connection:
            row = connection.execute(text("SELECT fence, expires_at>clock_timestamp() AS busy FROM research.publication_leases "
                                          "WHERE " + WHERE + " FOR UPDATE"), key).mappings().one()
            if row["busy"]:
                return None
            holder, fence = str(uuid.uuid4()), row["fence"] + 1
            connection.execute(text("UPDATE research.publication_leases SET holder=CAST(:holder AS uuid),fence=:fence,"
                "expires_at=clock_timestamp()+:seconds*interval '1 second' WHERE " + WHERE),
                key | {"holder": holder, "fence": fence, "seconds": seconds})
        return PublicationLease(initial, holder, fence)

    @staticmethod
    def _guard(connection, lease):
        valid = connection.execute(text("SELECT holder=CAST(:holder AS uuid) AND fence=:fence "
            "AND expires_at>clock_timestamp() AS valid FROM research.publication_leases WHERE " + WHERE + " FOR UPDATE"),
            lease.key | {"holder": lease.holder, "fence": lease.fence}).scalar_one()
        if not valid:
            raise AssessmentError("publication_lease_lost")

    def renew(self, lease, seconds=60):
        self._seconds(seconds)
        with self.engine.begin() as connection:
            self._guard(connection, lease)
            connection.execute(text("UPDATE research.publication_leases SET expires_at=clock_timestamp()+:seconds*interval '1 second' "
                                    "WHERE " + WHERE), lease.key | {"seconds": seconds})

    def release(self, lease):
        with self.engine.begin() as connection:
            self._guard(connection, lease)
            connection.execute(text("UPDATE research.publication_leases SET expires_at=NULL,holder=NULL WHERE " + WHERE), lease.key)

    @staticmethod
    def _read(connection, initial):
        rows = connection.execute(text("SELECT position,canonical_bytes FROM research.publication_events WHERE " + WHERE + " ORDER BY position"),
                                  initial.artifact.stored.intent.key).all()
        progress = initial
        for position, content in rows:
            if position != progress.position + 1:
                raise AssessmentError("publication_history_gap")
            event = json.loads(bytes(content))
            progress = progress.advance(event["action"], event["data"])
        return progress

    def read(self, initial):
        with self.engine.connect() as connection:
            return self._read(connection, initial)

    def advance(self, lease, position, action, data=None):
        with self.engine.begin() as connection:
            self._guard(connection, lease)
            current = self._read(connection, lease.initial)
            if current.position != position:
                raise AssessmentError("publication_position_conflict")
            updated = current.advance(action, data)
            content = canonical({"action": action, "data": data}, 2097152)
            connection.execute(text("INSERT INTO research.publication_events VALUES (:tenant,:project,:id,:position,:body,DEFAULT)"),
                               lease.key | {"position": updated.position, "body": content})
        return updated
