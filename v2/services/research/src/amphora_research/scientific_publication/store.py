"""Private scientific publication journal with DB-clock leases and immutable source verification."""
import hashlib
import json
import uuid
from dataclasses import dataclass

from sqlalchemy import text

from ..observations.intake_store import LabIntakeStore
from ..persistence.decision_document import IDENTIFIER
from ..persistence.decision_journal import DecisionJournal
from .artifact import ScientificArtifact, canonical, require
from .attempt import ScientificProgress

WHERE = "tenant_id=:tenant AND project_id=:project AND kind=:kind AND record_id=:id"


@dataclass(frozen=True, slots=True)
class ScientificLease:
    initial: ScientificProgress
    holder: str
    fence: int

    @property
    def key(self):
        return self.initial.artifact.key


class ScientificPublicationStore:
    def __init__(self, engine):
        self.engine = engine

    def _verify_source(self, artifact):
        require(type(artifact) is ScientificArtifact,"science_publication_artifact_required")
        if artifact.kind == "lab-intake":
            stored = LabIntakeStore(self.engine).read(artifact.scope,artifact.document.actor_id,artifact.record_id)
            require(stored is not None,"science_publication_source_missing")
            expected = ScientificArtifact.from_intake(stored)
        else:
            stored = DecisionJournal(self.engine).read(artifact.scope,artifact.document.reference)
            require(stored is not None,"science_publication_source_missing")
            expected = ScientificArtifact.from_decision(stored)
        require(expected == artifact,"science_publication_source_mismatch")

    @staticmethod
    def _header(initial):
        artifact = initial.artifact
        return canonical({"format":"research.scientific-publication.v1","publisher":initial.publisher,
            "kind":artifact.kind,"record_id":artifact.record_id,"actor":artifact.document.actor_id,
            "content":artifact.content.model_dump(mode="json"),"declaration":artifact.declaration.model_dump(mode="json")},2097152)

    def begin(self, artifact, publisher):
        IDENTIFIER.validate_python(publisher,strict=True)
        self._verify_source(artifact)
        initial = ScientificProgress(artifact,publisher)
        header = self._header(initial)
        key = artifact.key
        with self.engine.begin() as connection:
            # Distinct namespace from decision and sufficiency-publication locks.
            lock = int.from_bytes(hashlib.sha256(canonical(["research.scientific-publication",key])).digest()[:8],"big",signed=True)
            connection.execute(text("SELECT pg_advisory_xact_lock(:key)"),{"key":lock})
            previous = connection.execute(text("SELECT canonical_bytes FROM research.science_publication_headers WHERE "+WHERE),key).scalar_one_or_none()
            if previous is None:
                connection.execute(text("INSERT INTO research.science_publication_headers VALUES (:tenant,:project,:kind,:id,:body)"),key|{"body":header})
                connection.execute(text("INSERT INTO research.science_publication_leases (tenant_id,project_id,kind,record_id) "
                                        "VALUES (:tenant,:project,:kind,:id)"),key)
            else:
                require(bytes(previous) == header,"science_publication_identity_conflict")
        return initial

    @staticmethod
    def _seconds(seconds):
        require(type(seconds) is int and 1 <= seconds <= 300,"science_publication_lease_duration")

    def acquire(self, initial, seconds=60):
        self._seconds(seconds)
        with self.engine.begin() as connection:
            row = connection.execute(text("SELECT fence,expires_at>clock_timestamp() AS busy FROM research.science_publication_leases "
                "WHERE "+WHERE+" FOR UPDATE"),initial.artifact.key).mappings().one()
            if row["busy"]:
                return None
            holder,fence = str(uuid.uuid4()),row["fence"]+1
            connection.execute(text("UPDATE research.science_publication_leases SET holder=CAST(:holder AS uuid),fence=:fence,"
                "expires_at=clock_timestamp()+:seconds*interval '1 second' WHERE "+WHERE),
                initial.artifact.key|{"holder":holder,"fence":fence,"seconds":seconds})
        return ScientificLease(initial,holder,fence)

    @staticmethod
    def _guard(connection, lease):
        valid = connection.execute(text("SELECT holder=CAST(:holder AS uuid) AND fence=:fence AND expires_at>clock_timestamp() "
            "FROM research.science_publication_leases WHERE "+WHERE+" FOR UPDATE"),lease.key|{"holder":lease.holder,"fence":lease.fence}).scalar_one()
        require(valid,"science_publication_lease_lost")

    def renew(self, lease, seconds=60):
        self._seconds(seconds)
        with self.engine.begin() as connection:
            self._guard(connection,lease)
            connection.execute(text("UPDATE research.science_publication_leases SET expires_at=clock_timestamp()+:seconds*interval '1 second' WHERE "+WHERE),
                lease.key|{"seconds":seconds})

    def release(self, lease):
        with self.engine.begin() as connection:
            self._guard(connection,lease)
            connection.execute(text("UPDATE research.science_publication_leases SET holder=NULL,expires_at=NULL WHERE "+WHERE),lease.key)

    def _read(self, connection, initial):
        header = connection.execute(text("SELECT canonical_bytes FROM research.science_publication_headers WHERE "+WHERE),initial.artifact.key).scalar_one_or_none()
        require(header is not None and bytes(header) == self._header(initial),"science_publication_identity_conflict")
        rows = connection.execute(text("SELECT position,canonical_bytes FROM research.science_publication_events WHERE "+WHERE+" ORDER BY position"),initial.artifact.key).all()
        progress = initial
        for position,content in rows:
            require(position == progress.position+1,"science_publication_history_gap")
            event = json.loads(bytes(content))
            progress = progress.advance(event["action"],event["data"])
        return progress

    def read(self, initial):
        with self.engine.connect() as connection:
            return self._read(connection,initial)

    def lookup(self, artifact):
        """Read original publisher/history without creating intent, leases or peer effects."""
        self._verify_source(artifact)
        with self.engine.connect() as connection:
            raw = connection.execute(text("SELECT canonical_bytes FROM research.science_publication_headers WHERE "+WHERE),
                artifact.key).scalar_one_or_none()
            if raw is None:
                return None
            header = json.loads(bytes(raw))
            IDENTIFIER.validate_python(header["publisher"],strict=True)
            return self._read(connection,ScientificProgress(artifact,header["publisher"]))

    def advance(self, lease, position, action, data=None):
        with self.engine.begin() as connection:
            self._guard(connection,lease)
            current = self._read(connection,lease.initial)
            require(position == current.position,"science_publication_position_conflict")
            updated = current.advance(action,data)
            body = canonical({"action":action,"data":data},2097152)
            connection.execute(text("INSERT INTO research.science_publication_events "
                "(tenant_id,project_id,kind,record_id,position,canonical_bytes) VALUES (:tenant,:project,:kind,:id,:position,:body)"),
                lease.key|{"position":updated.position,"body":body})
        return updated
