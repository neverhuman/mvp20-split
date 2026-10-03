"""Exact material-state eligibility dependencies; no synthesis-state inference or live invalidation."""
from amphora_contracts_core import Scope
from amphora_contracts_research import MaterialStateRevisionRef, ScientificDecisionRef, ScientificImpactPage
from sqlalchemy import text

from .decision_document import require
from .decision_index import page_limit
from .decision_journal import DecisionJournal


class MaterialDecisionIndex:
    def __init__(self, engine):
        self.engine = engine
        self.journal = DecisionJournal(engine)

    def affected(self, scope, source, *, after=None, limit=128):
        page_limit(limit)
        require(type(scope) is Scope and type(source) is MaterialStateRevisionRef and source.scope == scope,
            "material_impact_source_scope")
        if after is not None:
            require(self.journal.read(scope,after) is not None,"material_impact_cursor_unknown")
        key = {"tenant":scope.tenant_id,"project":scope.project_id,"state":source.material_state_id,"revision":source.revision,
            "after_kind":"" if after is None else after.kind,"after_id":"" if after is None else after.decision_id,"limit":limit+1}
        with self.engine.connect() as connection:
            rows = connection.execute(text("SELECT d.kind,d.decision_id,d.sha256 FROM research.decision_material_states i "
                "JOIN research.scientific_decisions d USING (tenant_id,project_id,kind,decision_id) "
                "WHERE i.tenant_id=:tenant AND i.project_id=:project AND i.state_id=:state AND i.state_revision=:revision "
                'AND (d.kind COLLATE "C",d.decision_id COLLATE "C") > (:after_kind,:after_id) '
                'ORDER BY d.kind COLLATE "C",d.decision_id COLLATE "C" LIMIT :limit'),key).all()
        references = tuple(ScientificDecisionRef(scope=scope,kind=row.kind,decision_id=row.decision_id,sha256=row.sha256) for row in rows[:limit])
        return ScientificImpactPage(wire_version="1",policy="future_campaigns_only",decisions=references,
            next_after=references[-1] if len(rows) > limit else None)
