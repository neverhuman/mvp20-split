"""Append-only intake journal; observation batch and terminal share one owner transaction."""
import hashlib
import json
from dataclasses import dataclass

from amphora_contracts_core import ArtifactRef, Scope
from amphora_contracts_research import LabIntakeStatus
from sqlalchemy import text

from ..persistence.revisions import RevisionDocument
from .identity import require
from .intake import IDENTIFIER, IntakeIntent, IntakeTerminal, canonical
from .store import ObservationStore


@dataclass(frozen=True, slots=True)
class StoredIntake:
    intent: IntakeIntent
    terminal: IntakeTerminal | None

    @property
    def status(self):
        return self.intent.pending() if self.terminal is None else self.terminal.status


class LabIntakeStore:
    def __init__(self, engine):
        self.engine = engine
        self.observations = ObservationStore(engine)

    @staticmethod
    def _lock(connection, key):
        content = canonical(["research.lab-intake",key["tenant"],key["project"],key["id"]],4096)
        lock = int.from_bytes(hashlib.sha256(content).digest()[:8],"big",signed=True)
        connection.execute(text("SELECT pg_advisory_xact_lock(:key)"),{"key":lock})

    @staticmethod
    def _read(connection, key, terminal=False):
        table = "lab_terminals" if terminal else "lab_intents"
        return connection.execute(text(f"SELECT canonical_bytes FROM research.{table} WHERE "
            "tenant_id=:tenant AND project_id=:project AND intake_id=:id"),key).scalar_one_or_none()

    @staticmethod
    def _insert(connection, key, content, terminal=False):
        table = "lab_terminals" if terminal else "lab_intents"
        connection.execute(text(f"INSERT INTO research.{table} "
            "(tenant_id,project_id,intake_id,canonical_bytes) VALUES (:tenant,:project,:id,:body)"),key|{"body":content})

    @staticmethod
    def _terminal(raw):
        if raw is None:
            return None
        data = json.loads(bytes(raw))
        require(data["format"] == "research.lab-terminal.v1","lab_intake_storage_format")
        return IntakeTerminal.prepare(LabIntakeStatus.model_validate_json(json.dumps(data["status"])),
            tuple(ArtifactRef.model_validate_json(json.dumps(item)) for item in data["inputs"]))

    def begin(self, intent):
        intent = IntakeIntent.restore(intent.content)
        with self.engine.begin() as connection:
            self._lock(connection,intent.key)
            existing = self._read(connection,intent.key)
            if existing is None:
                self._insert(connection,intent.key,intent.content)
            else:
                require(bytes(existing) == intent.content,"lab_intake_identity_conflict")
            return StoredIntake(intent,self._terminal(self._read(connection,intent.key,True)))

    def complete(self, intent, resolved):
        intent = IntakeIntent.restore(intent.content)
        terminal = intent.resolve(resolved)
        documents = tuple(RevisionDocument.prepare(intent.request.profile.scope,intent.actor,record,self.observations.model)
                          for record in terminal.status.outcome.resolution.observations)
        for document in documents:
            self.observations.validate(document.record)
        return self._finish(intent,terminal,documents)

    def fail(self, intent, reason):
        intent = IntakeIntent.restore(intent.content)
        return self._finish(intent,intent.fail(reason),())

    def _finish(self, intent, terminal, documents):
        with self.engine.begin() as connection:
            self._lock(connection,intent.key)
            original = self._read(connection,intent.key)
            require(original is not None,"lab_intake_not_started")
            require(bytes(original) == intent.content,"lab_intake_identity_conflict")
            previous = self._read(connection,intent.key,True)
            if previous is not None:
                require(bytes(previous) == terminal.content,"lab_intake_terminal_conflict")
                return StoredIntake(intent,self._terminal(previous))
            # Every caller acquires observation locks in the same order, after its intake lock.
            for document in sorted(documents,key=lambda item:item.identity_id):
                self.observations.publish_prepared(connection,intent.actor,document)
            self._insert(connection,intent.key,terminal.content,True)
            for document in documents:
                connection.execute(text("INSERT INTO research.lab_observations "
                    "(tenant_id,project_id,intake_id,observation_id,revision) VALUES (:tenant,:project,:id,:observation,:revision)"),
                    intent.key|{"observation":document.identity_id,"revision":document.record.reference.revision})
        return StoredIntake(intent,terminal)

    def read(self, scope, actor, intake_id):
        require(type(scope) is Scope,"lab_intake_scope_mismatch")
        IDENTIFIER.validate_python(actor,strict=True)
        IDENTIFIER.validate_python(intake_id,strict=True)
        key = {"tenant":scope.tenant_id,"project":scope.project_id,"id":intake_id}
        with self.engine.connect() as connection:
            raw = self._read(connection,key)
            if raw is None:
                return None
            intent = IntakeIntent.restore(bytes(raw))
            require(intent.actor == actor,"lab_intake_actor_mismatch")
            return StoredIntake(intent,self._terminal(self._read(connection,key,True)))
