"""Bounded explicit dependency/consumer lookup; no global discovery, invalidation or policy rerun."""
from amphora_contracts_core import ArtifactRef, Scope
from amphora_contracts_research import (
    DecisionConsumerPage,
    ObservationRevisionRef,
    ScientificDecisionRef,
    ScientificImpactPage,
)
from sqlalchemy import text

from .decision_document import IDENTIFIER, MODELS, canonical, require
from .decision_journal import DecisionJournal


def page_limit(limit):
    require(type(limit) is int and 1 <= limit <= 128,"scientific_index_page_limit")


class DecisionIndex:
    def __init__(self, engine):
        self.engine = engine
        self.journal = DecisionJournal(engine)

    def affected(self, scope, source, *, after=None, limit=128):
        page_limit(limit)
        require(type(scope) is Scope and type(source) in (ArtifactRef,ObservationRevisionRef) and source.scope == scope,
                "scientific_impact_source_scope")
        if after is not None:
            self.journal.key(scope,after)
        key = {"tenant":scope.tenant_id,"project":scope.project_id,"limit":limit+1,
               "after_kind":"" if after is None else after.kind,"after_id":"" if after is None else after.decision_id}
        if type(source) is ArtifactRef:
            table = "decision_sources"
            predicate = "i.artifact_id=:source AND i.reference_bytes=:body"
            key |= {"source":source.artifact_id,"body":canonical(source.model_dump(mode="json"))}
        else:
            table = "decision_observations"
            predicate = "i.observation_id=:source AND i.revision=:revision"
            key |= {"source":source.observation_id,"revision":source.revision}
        with self.engine.connect() as connection:
            rows = connection.execute(text(f"SELECT d.kind,d.decision_id,d.sha256 FROM research.{table} i "
                "JOIN research.scientific_decisions d USING (tenant_id,project_id,kind,decision_id) "
                "WHERE i.tenant_id=:tenant AND i.project_id=:project AND "+predicate+
                ' AND (d.kind COLLATE "C",d.decision_id COLLATE "C") > (:after_kind,:after_id) '
                'ORDER BY d.kind COLLATE "C",d.decision_id COLLATE "C" LIMIT :limit'),key).all()
        references = tuple(ScientificDecisionRef(scope=scope,kind=row.kind,decision_id=row.decision_id,sha256=row.sha256)
                           for row in rows[:limit])
        return ScientificImpactPage(wire_version="1",policy="future_campaigns_only",decisions=references,
                                    next_after=references[-1] if len(rows) > limit else None)

    def register_consumer(self, scope, actor, decision, consumer):
        key = self.journal.key(scope,decision)
        IDENTIFIER.validate_python(actor,strict=True)
        require(type(consumer) is ArtifactRef and consumer.scope == scope,"scientific_consumer_scope")
        consumer = ArtifactRef.model_validate_json(consumer.model_dump_json())
        body = canonical(consumer.model_dump(mode="json"))
        with self.engine.begin() as connection:
            self.journal.lock(connection,key)
            original = self.journal.raw(connection,key)
            require(original is not None,"unknown_consumer_decision")
            # Digest is part of the exact dependency; id-only registration must not silently retarget it.
            require(MODELS[decision.kind].model_validate_json(bytes(original)).reference == decision,
                    "scientific_decision_digest_mismatch")
            query = key|{"artifact":consumer.artifact_id}
            old = connection.execute(text("SELECT reference_bytes FROM research.decision_consumers WHERE "
                "tenant_id=:tenant AND project_id=:project AND kind=:kind AND decision_id=:id AND artifact_id=:artifact"),query).scalar_one_or_none()
            if old is not None:
                require(bytes(old) == body,"immutable_scientific_consumer_conflict")
                return consumer
            connection.execute(text("INSERT INTO research.decision_consumers "
                "(tenant_id,project_id,kind,decision_id,artifact_id,reference_bytes,actor_id) "
                "VALUES (:tenant,:project,:kind,:id,:artifact,:body,:actor)"),query|{"body":body,"actor":actor})
        return consumer

    def consumers(self, scope, decision, *, after=None, limit=128):
        page_limit(limit)
        key = self.journal.key(scope,decision)
        if after is not None:
            IDENTIFIER.validate_python(after,strict=True)
        require(self.journal.read(scope,decision) is not None,"unknown_consumer_decision")
        with self.engine.connect() as connection:
            rows = connection.execute(text("SELECT reference_bytes FROM research.decision_consumers WHERE "
                "tenant_id=:tenant AND project_id=:project AND kind=:kind AND decision_id=:id "
                'AND artifact_id COLLATE "C" > :after ORDER BY artifact_id COLLATE "C" LIMIT :limit'),
                key|{"after":after or "","limit":limit+1}).scalars().all()
        consumers = tuple(ArtifactRef.model_validate_json(bytes(row)) for row in rows[:limit])
        return DecisionConsumerPage(wire_version="1",decision=decision,consumers=consumers,
                                    next_after=consumers[-1].artifact_id if len(rows) > limit else None)
