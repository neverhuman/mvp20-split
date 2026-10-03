"""Research-local immutable journal mechanics for two closed scientific decision kinds."""
import hashlib

from amphora_contracts_core import Scope
from amphora_contracts_research import ObservationRevision, ScientificDecisionRef
from sqlalchemy import text

from .decision_document import MODELS, canonical, require


class DecisionJournal:
    def __init__(self, engine):
        self.engine = engine

    @staticmethod
    def key(scope, reference):
        require(type(scope) is Scope and type(reference) is ScientificDecisionRef and reference.scope == scope,
                "scientific_decision_reference_scope")
        return {"tenant":scope.tenant_id,"project":scope.project_id,"kind":reference.kind,"id":reference.decision_id}

    @staticmethod
    def lock(connection, key):
        body = canonical(["research.scientific-decision",key["tenant"],key["project"],key["kind"],key["id"]])
        connection.execute(text("SELECT pg_advisory_xact_lock(:key)"),
            {"key":int.from_bytes(hashlib.sha256(body).digest()[:8],"big",signed=True)})

    @staticmethod
    def raw(connection, key):
        return connection.execute(text("SELECT canonical_bytes FROM research.scientific_decisions WHERE "
            "tenant_id=:tenant AND project_id=:project AND kind=:kind AND decision_id=:id"),key).scalar_one_or_none()

    def publish(self, document, validate_links):
        with self.engine.begin() as connection:
            return self.publish_prepared(connection,document,validate_links)

    def publish_prepared(self, connection, document, validate_links):
        """Compose a prepared owner-policy result into an existing Research transaction."""
        key,record = document.key,document.record
        self.lock(connection,key)
        prior = self.raw(connection,key)
        if prior is not None:
            require(bytes(prior) == document.canonical_bytes,"immutable_scientific_decision_conflict")
            return MODELS[key["kind"]].model_validate_json(bytes(prior))
        validate_links(connection,record)
        connection.execute(text("INSERT INTO research.scientific_decisions "
            "(tenant_id,project_id,kind,decision_id,sha256,canonical_bytes) VALUES (:tenant,:project,:kind,:id,:sha,:body)"),
            key|{"sha":record.reference.sha256,"body":document.canonical_bytes})
        for source in record.sources:
            connection.execute(text("INSERT INTO research.decision_sources "
                "(tenant_id,project_id,kind,decision_id,artifact_id,reference_bytes) VALUES (:tenant,:project,:kind,:id,:artifact,:body)"),
                key|{"artifact":source.artifact_id,"body":canonical(source.model_dump(mode="json"))})
        for observation in getattr(record,"observations",()):
            connection.execute(text("INSERT INTO research.decision_observations "
                "(tenant_id,project_id,kind,decision_id,observation_id,revision) VALUES (:tenant,:project,:kind,:id,:observation,:revision)"),
                key|{"observation":observation.observation_id,"revision":observation.revision})
        return record

    def read(self, scope, reference):
        key = self.key(scope,reference)
        with self.engine.connect() as connection:
            raw = self.raw(connection,key)
        if raw is None:
            return None
        record = MODELS[reference.kind].model_validate_json(bytes(raw))
        require(record.reference == reference,"scientific_decision_digest_mismatch")
        return record


def require_candidate(connection, candidate):
    found = connection.execute(text("SELECT 1 FROM research.identity_records WHERE tenant_id=:tenant "
        "AND project_id=:project AND kind='candidate' AND identity_id=:id AND revision=:revision"),
        {"tenant":candidate.scope.tenant_id,"project":candidate.scope.project_id,"id":candidate.candidate_id,
         "revision":candidate.revision}).scalar_one_or_none()
    require(found is not None,"unknown_decision_candidate")


def require_observation(connection, reference, source):
    raw = connection.execute(text("SELECT canonical_bytes FROM research.observation_revisions WHERE tenant_id=:tenant "
        "AND project_id=:project AND identity_id=:id AND revision=:revision"),
        {"tenant":reference.scope.tenant_id,"project":reference.scope.project_id,"id":reference.observation_id,
         "revision":reference.revision}).scalar_one_or_none()
    require(raw is not None,"unknown_decision_observation")
    observation = ObservationRevision.model_validate_json(bytes(raw))
    require(observation.source == source,"decision_observation_source_mismatch")
