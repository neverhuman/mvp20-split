"""Append-only owner projection with scoped identity, exact replay and historical reads."""
import hashlib

from amphora_contracts_fitness import FitnessProjection
from sqlalchemy import text

from ..transport.access import AccessDenied
from .document import bounded
from .policy import require
from .reuse import canonical, digest

WHERE = "tenant_id=:tenant AND project_id=:project AND fitness_id=:id"


def key(scope, fitness_id):
    return {"tenant":scope.tenant_id,"project":scope.project_id,"id":fitness_id}


class FitnessStore:
    def __init__(self, engine):
        self.engine = engine

    @staticmethod
    def _read(connection, identity, actor):
        row = connection.execute(text("SELECT actor_id,sha256,canonical_bytes FROM research.fitness_projections WHERE "+WHERE),identity).first()
        if row is None:
            return None
        if row.actor_id != actor:
            raise AccessDenied("access_denied")
        result = FitnessProjection.model_validate_json(bytes(row.canonical_bytes))
        require(result.actor_id == actor and key(result.reference.scope,result.reference.fitness_id) == identity,
                "fitness_stored_identity_mismatch")
        expected = digest({"format":"research.fitness.v1", "scope":result.reference.scope.model_dump(mode="json"),
            "fitness_id":result.reference.fitness_id, "projection":result.model_dump(mode="json",exclude={"reference"})})
        require(result.reference.sha256 == row.sha256 == expected and bounded(result.model_dump(mode="json")) == bytes(row.canonical_bytes),
                "fitness_stored_document_mismatch")
        return result

    def publish(self, document):
        record = document.record
        identity = key(record.reference.scope,record.reference.fitness_id)
        lock = int.from_bytes(hashlib.sha256(canonical(["research.fitness.v1",identity])).digest()[:8],"big",signed=True)
        with self.engine.begin() as connection:
            connection.execute(text("SELECT pg_advisory_xact_lock(:key)"),{"key":lock})
            previous = self._read(connection,identity,record.actor_id)
            if previous is not None:
                require(bounded(previous.model_dump(mode="json")) == document.content,"fitness_identity_conflict")
                return previous
            connection.execute(text("INSERT INTO research.fitness_projections "
                "(tenant_id,project_id,fitness_id,actor_id,sha256,canonical_bytes) VALUES (:tenant,:project,:id,:actor,:digest,:body)"),
                identity|{"actor":record.actor_id,"digest":record.reference.sha256,"body":document.content})
        return record

    def read(self, actor, selection):
        with self.engine.connect() as connection:
            return self._read(connection,key(selection.scope,selection.fitness_id),actor)
