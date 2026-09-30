"""Draft-specific guards within the existing Runtime admission authority."""

from types import MappingProxyType

from sqlalchemy import text

from ..coordinator.values import ensure
from . import storage
from .material import ValidationMaterial


class DraftAdmissionGuard:
    def __init__(self, engine, universes):
        self.material = ValidationMaterial(engine)
        self.universes = MappingProxyType(dict(universes))

    def prepare(self, scope, request):
        verified = self.material.load(scope, request.draft.validation_id)
        verified.require_selection(request)
        # Until the public Registry eligibility adapter exists, tool-bearing drafts fail closed.
        ensure(not verified.entry.descriptors, "draft_tool_eligibility_unavailable")
        return verified

    def check(self, conn, scope, request, verified):
        params = {"tenant": scope.tenant_id, "project": scope.project_id, "draft": request.draft.draft_id}
        row = conn.execute(text("SELECT head_revision FROM runtime.definition_heads WHERE " + storage.KEY + " FOR UPDATE"), params).mappings().one_or_none()
        ensure(row is not None and row["head_revision"] == request.draft.revision, "draft_head_changed")
        universe = self.universes.get((scope.tenant_id, scope.project_id))
        ensure(universe is not None and universe.sha256 == verified.universe.sha256, "draft_universe_changed")
        return verified.require_selection(request)

    @staticmethod
    def record(conn, params, run_id, operation_id, verified):
        conn.execute(text("INSERT INTO runtime.definition_admissions "
            "(tenant_id,project_id,run_id,plan_sha256,validation_id,operation_id) "
            "VALUES (:tenant,:project,:run,:plan,:validation,:operation)"),
            {**params, "run": run_id, "plan": verified.entry.plan.sha256,
             "validation": verified.validation.validation_id, "operation": operation_id})
