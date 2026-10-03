"""Pinned scientific intent and atomic result association; no transaction spans input resolution."""
import hashlib
from dataclasses import dataclass

from amphora_contracts_core import Scope
from sqlalchemy import text

from ..eligibility.store import validate_links as eligibility_links
from ..persistence.decision_document import MODELS
from ..persistence.decision_journal import DecisionJournal
from ..synthesis.store import validate_links as synthesis_links
from .boundary import IDENTIFIER, canonical, require
from .intent import ScientificIntent

WHERE = "tenant_id=:tenant AND project_id=:project AND kind=:kind AND decision_id=:id"


@dataclass(frozen=True, slots=True)
class StoredScientificInput:
    intent: ScientificIntent
    decision: object | None

    @property
    def status(self):
        return self.intent.status(self.decision)


class ScientificInputStore:
    def __init__(self, engine):
        self.engine = engine
        self.decisions = DecisionJournal(engine)

    @staticmethod
    def _lock(connection, key):
        body = canonical(["research.scientific-intent",key])
        connection.execute(text("SELECT pg_advisory_xact_lock(:key)"),
            {"key":int.from_bytes(hashlib.sha256(body).digest()[:8],"big",signed=True)})

    @staticmethod
    def _raw(connection, key):
        return connection.execute(text("SELECT canonical_bytes FROM research.scientific_input_intents WHERE "+WHERE),key).scalar_one_or_none()

    def _outcome(self, connection, intent):
        digest = connection.execute(text("SELECT sha256 FROM research.scientific_input_outcomes WHERE "+WHERE),intent.key).scalar_one_or_none()
        if digest is None:
            return StoredScientificInput(intent,None)
        raw = self.decisions.raw(connection,intent.key)
        require(raw is not None,"scientific_intent_result_missing")
        decision = MODELS[intent.key["kind"]].model_validate_json(bytes(raw))
        require(decision.reference.sha256 == digest,"scientific_intent_result_digest_mismatch")
        intent.status(decision)
        return StoredScientificInput(intent,decision)

    def begin(self, bound):
        intent = ScientificIntent.prepare(bound)
        with self.engine.begin() as connection:
            self._lock(connection,intent.key)
            old = self._raw(connection,intent.key)
            if old is None:
                connection.execute(text("INSERT INTO research.scientific_input_intents "
                    "(tenant_id,project_id,kind,decision_id,canonical_bytes) VALUES (:tenant,:project,:kind,:id,:body)"),
                    intent.key|{"body":intent.content})
            else:
                require(bytes(old) == intent.content,"scientific_intent_identity_conflict")
            return self._outcome(connection,intent)

    def complete(self, bound, resolved):
        intent = ScientificIntent.prepare(bound)
        document = intent.document(resolved)
        with self.engine.begin() as connection:
            self._lock(connection,intent.key)
            old = self._raw(connection,intent.key)
            require(old is not None,"scientific_intent_not_started")
            require(bytes(old) == intent.content,"scientific_intent_identity_conflict")
            prior = self._outcome(connection,intent)
            if prior.decision is not None:
                require(prior.decision == document.record,"scientific_intent_result_conflict")
                return prior
            links = eligibility_links if intent.key["kind"] == "eligibility" else synthesis_links
            decision = self.decisions.publish_prepared(connection,document,links)
            connection.execute(text("INSERT INTO research.scientific_input_outcomes "
                "(tenant_id,project_id,kind,decision_id,sha256) VALUES (:tenant,:project,:kind,:id,:sha)"),
                intent.key|{"sha":decision.reference.sha256})
        return StoredScientificInput(intent,decision)

    def read(self, scope, actor, kind, decision_id):
        require(type(scope) is Scope and kind in MODELS,"scientific_intent_scope_or_kind")
        IDENTIFIER.validate_python(actor,strict=True)
        IDENTIFIER.validate_python(decision_id,strict=True)
        key = {"tenant":scope.tenant_id,"project":scope.project_id,"kind":kind,"id":decision_id}
        with self.engine.connect() as connection:
            raw = self._raw(connection,key)
            if raw is None:
                return None
            intent = ScientificIntent.restore(bytes(raw))
            require(intent.bound.actor == actor,"scientific_intent_actor_mismatch")
            return self._outcome(connection,intent)
