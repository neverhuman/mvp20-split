"""Research-local immutable revision mechanics; scientific/link policies stay in owning modules."""
import hashlib
import json
from dataclasses import dataclass

from amphora_contracts_core import Identifier, Scope
from amphora_contracts_research import ExperimentDefinition, MaterialStateRevision, ObservationRevision
from pydantic import TypeAdapter, ValidationError
from sqlalchemy import text

TABLES = {MaterialStateRevision:("material_state_revisions","material_state_id"),
          ExperimentDefinition:("experiment_revisions","experiment_id"),
          ObservationRevision:("observation_revisions","observation_id")}
IDENTIFIER = TypeAdapter(Identifier)


class ScientificStoreError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class RevisionDocument:
    record: MaterialStateRevision | ExperimentDefinition | ObservationRevision
    table: str
    identity_id: str
    canonical_bytes: bytes

    @classmethod
    def prepare(cls, scope, actor, record, model):
        if model not in TABLES or type(record) is not model:
            raise ScientificStoreError("scientific_record_type")
        if type(scope) is not Scope:
            raise ScientificStoreError("scientific_record_scope_mismatch")
        try:
            IDENTIFIER.validate_python(actor,strict=True)
            # Revalidate boundary records even when a caller used model_copy/model_construct.
            record = model.model_validate_json(record.model_dump_json())
            body = json.dumps(record.model_dump(mode="json"),sort_keys=True,separators=(",", ":"),
                              ensure_ascii=False,allow_nan=False).encode("utf-8")
        except (ValidationError,UnicodeError) as error:
            raise ScientificStoreError("scientific_record_shape") from error
        if record.reference.scope != scope:
            raise ScientificStoreError("scientific_record_scope_mismatch")
        if len(body) > 1048576:
            raise ScientificStoreError("scientific_record_limit")
        table, field = TABLES[model]
        return cls(record,table,getattr(record.reference,field),body)

    @property
    def key(self):
        ref = self.record.reference
        return {"tenant":ref.scope.tenant_id,"project":ref.scope.project_id,"id":self.identity_id,"revision":ref.revision}

    @property
    def lock(self):
        ref = self.record.reference
        body = json.dumps(["research.scientific",self.table,ref.scope.tenant_id,ref.scope.project_id,self.identity_id],
                          separators=(",", ":")).encode()
        return int.from_bytes(hashlib.sha256(body).digest()[:8],"big",signed=True)


class RevisionJournal:
    def __init__(self, engine, model, validate, link):
        if model not in TABLES:
            raise ScientificStoreError("scientific_record_type")
        self.engine, self.model, self.validate, self.link = engine,model,validate,link
        self.table, self.identity_field = TABLES[model]

    def publish(self, scope, actor, record):
        document = RevisionDocument.prepare(scope,actor,record,self.model)
        self.validate(document.record)
        with self.engine.begin() as connection:
            return self.publish_prepared(connection,actor,document)

    def publish_prepared(self, connection, actor, document):
        """Internal owner transaction composition; prepare and domain-validate before opening it."""
        if type(document.record) is not self.model or document.table != self.table:
            raise ScientificStoreError("scientific_record_type")
        key = document.key
        connection.execute(text("SELECT pg_advisory_xact_lock(:key)"),{"key":document.lock})
        raw = self._read(connection,key)
        if raw is not None:
            if bytes(raw) != document.canonical_bytes:
                raise ScientificStoreError("immutable_scientific_revision_conflict")
            return self.model.model_validate_json(bytes(raw))
        head = connection.execute(text(f"SELECT max(revision) FROM research.{self.table} "
            "WHERE tenant_id=:tenant AND project_id=:project AND identity_id=:id"),key).scalar_one()
        if document.record.reference.revision != (head or 0)+1:
            raise ScientificStoreError("scientific_revision_head_conflict")
        connection.execute(text(f"INSERT INTO research.{self.table} "
            "(tenant_id,project_id,identity_id,revision,prior_revision,actor_id,canonical_bytes) "
            "VALUES (:tenant,:project,:id,:revision,:prior,:actor,:body)"),
            key|{"prior":head,"actor":actor,"body":document.canonical_bytes})
        self.link(connection,document.record,key)
        return document.record

    def _read(self, connection, key):
        return connection.execute(text(f"SELECT canonical_bytes FROM research.{self.table} "
            "WHERE tenant_id=:tenant AND project_id=:project AND identity_id=:id AND revision=:revision"),key).scalar_one_or_none()

    def read(self, scope, reference):
        expected = self.model.model_fields["reference"].annotation
        if type(reference) is not expected or type(scope) is not Scope or reference.scope != scope:
            raise ScientificStoreError("scientific_read_scope_or_reference")
        key = {"tenant":scope.tenant_id,"project":scope.project_id,"id":getattr(reference,self.identity_field),"revision":reference.revision}
        with self.engine.connect() as connection:
            raw = self._read(connection,key)
        return None if raw is None else self.model.model_validate_json(bytes(raw))
