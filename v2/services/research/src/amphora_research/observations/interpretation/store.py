"""Atomic immutable interpretations; network authentication is an outer workflow responsibility."""
import hashlib
from dataclasses import dataclass

from amphora_contracts_core import Scope
from amphora_contracts_research import NormalizationProjection, ObservationUseProjection
from sqlalchemy import text

from ..identity import identifier, require
from .document import canonical
from .intent import InterpretationIntent
from .preparation import PreparedInterpretation

MODELS = {"normalization":NormalizationProjection,"observation-use":ObservationUseProjection}
WHERE = "tenant_id=:tenant AND project_id=:project AND kind=:kind AND interpretation_id=:id"


@dataclass(frozen=True, slots=True)
class StoredInterpretation:
    intent: InterpretationIntent
    result: NormalizationProjection | ObservationUseProjection | None

    @property
    def status(self):
        return "pending" if self.result is None else "interpreted"


class InterpretationStore:
    def __init__(self, engine):
        self.engine = engine

    @staticmethod
    def _lock(connection, key):
        digest = hashlib.sha256(canonical(["research.interpretation-intent",key])).digest()
        connection.execute(text("SELECT pg_advisory_xact_lock(:key)"),{"key":int.from_bytes(digest[:8],"big",signed=True)})

    @staticmethod
    def _intent(connection, key):
        raw = connection.execute(text("SELECT canonical_bytes FROM research.interpretation_intents WHERE "+WHERE),key).scalar_one_or_none()
        return None if raw is None else InterpretationIntent.restore(bytes(raw))

    @staticmethod
    def _result(connection, intent):
        row = connection.execute(text("SELECT sha256,canonical_bytes FROM research.interpretation_results WHERE "+WHERE),intent.key).first()
        if row is None:
            return StoredInterpretation(intent,None)
        record = MODELS[intent.profile.kind].model_validate_json(bytes(row.canonical_bytes))
        require(record.reference.sha256 == row.sha256 and record.reference.scope == intent.profile.scope
            and record.reference.kind == intent.profile.kind and record.reference.interpretation_id == intent.request.interpretation_id
            and record.actor_id == intent.actor and record.profile == intent.profile.to_wire(),"interpretation_stored_result_mismatch")
        return StoredInterpretation(intent,record)

    def begin(self, profile, request, actor):
        intent = InterpretationIntent.prepare(profile,request,actor)
        with self.engine.begin() as connection:
            self._lock(connection,intent.key)
            old = self._intent(connection,intent.key)
            if old is None:
                connection.execute(text("INSERT INTO research.interpretation_intents "
                    "(tenant_id,project_id,kind,interpretation_id,canonical_bytes) VALUES (:tenant,:project,:kind,:id,:body)"),
                    intent.key|{"body":intent.content})
            else:
                require(old.content == intent.content,"interpretation_intent_conflict")
            return self._result(connection,intent)

    def prepare(self, intent):
        with self.engine.connect() as connection:
            old = self._intent(connection,intent.key)
            require(old is not None,"interpretation_intent_not_started")
            require(old.content == intent.content,"interpretation_intent_conflict")
            return PreparedInterpretation.load(connection,old)

    def complete(self, prepared, consumed):
        require(type(prepared) is PreparedInterpretation,"prepared_interpretation_required")
        intent = InterpretationIntent.prepare(prepared.intent.profile,prepared.intent.request,prepared.intent.actor)
        document = prepared.document(consumed)
        with self.engine.begin() as connection:
            self._lock(connection,intent.key)
            old = self._intent(connection,intent.key)
            require(old is not None,"interpretation_intent_not_started")
            require(old.content == intent.content,"interpretation_intent_conflict")
            prior = self._result(connection,intent)
            if prior.result is not None:
                require(prior.result == document.record,"interpretation_result_conflict")
                return prior
            # A same-reference forged object is not an owned observation/experiment.
            exact = PreparedInterpretation.load(connection,intent)
            require(exact == prepared,"interpretation_owned_input_mismatch")
            connection.execute(text("INSERT INTO research.interpretation_results "
                "(tenant_id,project_id,kind,interpretation_id,sha256,canonical_bytes) VALUES (:tenant,:project,:kind,:id,:sha,:body)"),
                intent.key|{"sha":document.record.reference.sha256,"body":document.canonical_bytes})
            self._index(connection,prepared,document.record)
        return StoredInterpretation(intent,document.record)

    @staticmethod
    def _index(connection, prepared, record):
        key = prepared.intent.key
        for source in record.sources:
            connection.execute(text("INSERT INTO research.interpretation_sources "
                "(tenant_id,project_id,kind,interpretation_id,artifact_id,reference_bytes) VALUES (:tenant,:project,:kind,:id,:artifact,:reference)"),
                key|{"artifact":source.artifact_id,"reference":canonical(source.model_dump(mode="json"))})
        for observation in prepared.observations:
            ref = observation.identity.reference
            connection.execute(text("INSERT INTO research.interpretation_observations "
                "(tenant_id,project_id,kind,interpretation_id,observation_id,observation_revision) VALUES (:tenant,:project,:kind,:id,:observation,:revision)"),
                key|{"observation":ref.observation_id,"revision":ref.revision})
        for ref in prepared.material_states:
            connection.execute(text("INSERT INTO research.interpretation_material_states "
                "(tenant_id,project_id,kind,interpretation_id,state_id,state_revision) VALUES (:tenant,:project,:kind,:id,:state,:revision)"),
                key|{"state":ref.material_state_id,"revision":ref.revision})
        if prepared.experiment is not None:
            ref = prepared.experiment.identity.reference
            connection.execute(text("INSERT INTO research.interpretation_experiments "
                "(tenant_id,project_id,kind,interpretation_id,experiment_id,experiment_revision) VALUES (:tenant,:project,:kind,:id,:experiment,:revision)"),
                key|{"experiment":ref.experiment_id,"revision":ref.revision})

    def read(self, scope, actor, kind, interpretation_id):
        require(type(scope) is Scope and kind in MODELS,"interpretation_read_scope_or_kind")
        identifier(actor)
        identifier(interpretation_id)
        key = {"tenant":scope.tenant_id,"project":scope.project_id,"kind":kind,"id":interpretation_id}
        with self.engine.connect() as connection:
            intent = self._intent(connection,key)
            if intent is None:
                return None
            require(intent.actor == actor,"interpretation_actor_mismatch")
            return self._result(connection,intent)
