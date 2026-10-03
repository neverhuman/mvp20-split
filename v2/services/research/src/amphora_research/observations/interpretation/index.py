"""Read known exact interpretation dependencies; append-only pagination is not a global snapshot."""
from amphora_contracts_core import ArtifactRef, Scope
from amphora_contracts_research import (
    InterpretationImpactPage,
    InterpretationRef,
    MaterialStateRevisionRef,
    ObservationRevisionRef,
)
from sqlalchemy import text

from ..identity import require
from .document import canonical


class InterpretationIndex:
    def __init__(self, engine):
        self.engine = engine

    def affected(self, scope, source, *, after=None, limit=128):
        require(type(limit) is int and 1 <= limit <= 128,"interpretation_impact_page_limit")
        require(type(scope) is Scope and type(source) in (ArtifactRef,ObservationRevisionRef,MaterialStateRevisionRef)
            and source.scope == scope,"interpretation_impact_source_scope")
        if after is not None:
            require(type(after) is InterpretationRef and after.scope == scope,"interpretation_cursor_scope")
        key = {"tenant":scope.tenant_id,"project":scope.project_id,"limit":limit+1,
            "after_kind":"" if after is None else after.kind,"after_id":"" if after is None else after.interpretation_id}
        if type(source) is ArtifactRef:
            table,predicate = "interpretation_sources","i.artifact_id=:source AND i.reference_bytes=:reference"
            key |= {"source":source.artifact_id,"reference":canonical(source.model_dump(mode="json"))}
        elif type(source) is ObservationRevisionRef:
            table,predicate = "interpretation_observations","i.observation_id=:source AND i.observation_revision=:revision"
            key |= {"source":source.observation_id,"revision":source.revision}
        else:
            table,predicate = "interpretation_material_states","i.state_id=:source AND i.state_revision=:revision"
            key |= {"source":source.material_state_id,"revision":source.revision}
        with self.engine.connect() as connection:
            if after is not None:
                digest = connection.execute(text("SELECT sha256 FROM research.interpretation_results WHERE tenant_id=:tenant "
                    "AND project_id=:project AND kind=:after_kind AND interpretation_id=:after_id"),key).scalar_one_or_none()
                require(digest == after.sha256,"interpretation_cursor_unknown_or_digest_mismatch")
            rows = connection.execute(text(f"SELECT d.kind,d.interpretation_id,d.sha256 FROM research.{table} i "
                "JOIN research.interpretation_results d USING (tenant_id,project_id,kind,interpretation_id) "
                "WHERE i.tenant_id=:tenant AND i.project_id=:project AND "+predicate+
                ' AND (d.kind COLLATE "C",d.interpretation_id COLLATE "C") > (:after_kind,:after_id) '
                'ORDER BY d.kind COLLATE "C",d.interpretation_id COLLATE "C" LIMIT :limit'),key).all()
        references = tuple(InterpretationRef(scope=scope,kind=row.kind,interpretation_id=row.interpretation_id,sha256=row.sha256) for row in rows[:limit])
        return InterpretationImpactPage(wire_version="1",policy="future_campaigns_only",interpretations=references,
            next_after=references[-1] if len(rows) > limit else None)
