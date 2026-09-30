"""Scoped immutable revision and original authoring receipt reads."""

from amphora_contracts_graph_runtime import DraftCommandReceipt, DraftPage
from sqlalchemy import text

from . import storage


class DefinitionReadError(ValueError):
    pass


class DefinitionReads:
    def __init__(self, engine):
        self.engine = engine

    @staticmethod
    def bindings(principal):
        principal.require("read")
        return {"tenant": principal.scope.tenant_id, "project": principal.scope.project_id}

    def revision(self, principal, draft_id, revision=None):
        params = {**self.bindings(principal), "draft": draft_id}
        if revision is not None and (type(revision) is not int or not 1 <= revision <= 9007199254740991):
            raise DefinitionReadError("invalid_draft_revision")
        with self.engine.connect() as conn:
            result = storage.head(conn, params) if revision is None else storage.version(conn.execute(text(
                "SELECT * FROM runtime.definition_revisions WHERE " + storage.KEY + " AND revision=:revision"),
                {**params, "revision": revision}).mappings().one_or_none())
        if result is None:
            raise DefinitionReadError("draft_unavailable")
        return result.to_wire()

    def page(self, principal, *, limit=20, after=None):
        params = self.bindings(principal)
        if type(limit) is not int or not 1 <= limit <= 50:
            raise DefinitionReadError("invalid_draft_page")
        with self.engine.connect() as conn:
            rows = conn.execute(text("SELECT r.draft_id,r.revision,r.content_sha256,r.record->'head' AS head "
                "FROM runtime.definition_revisions r JOIN runtime.definition_heads h "
                "USING(tenant_id,project_id,draft_id) WHERE r.tenant_id=:tenant AND r.project_id=:project "
                "AND r.revision=h.head_revision AND r.draft_id>:after ORDER BY r.draft_id LIMIT :limit"),
                {**params, "after": after or "", "limit": limit + 1}).mappings().all()
        items = tuple(storage.header(row) for row in rows[:limit])
        return DraftPage(scope=principal.scope, drafts=items, next_after=items[-1].draft_id if len(rows) > limit else None)

    def receipt(self, principal, family, command_id):
        params = self.bindings(principal)
        if family not in {"definition.save", "definition.validate"}:
            raise DefinitionReadError("draft_command_unavailable")
        with self.engine.connect() as conn:
            row = conn.execute(text("SELECT operation_id,request_sha256,status,receipt FROM runtime.commands "
                "WHERE tenant_id=:tenant AND project_id=:project AND actor_id=:actor AND family=:family AND command_id=:command"),
                {**params, "actor": principal.actor_id, "family": family, "command": command_id}).mappings().one_or_none()
        if row is None:
            raise DefinitionReadError("draft_command_unavailable")
        if row["receipt"] is not None:
            return DraftCommandReceipt.model_validate(row["receipt"])
        return DraftCommandReceipt.model_validate({"outcome": {"status": "pending", "binding": {
            "identity": {"scope": principal.scope, "actor_id": principal.actor_id, "command_family": family, "command_id": command_id},
            "operation_id": row["operation_id"], "request_sha256": row["request_sha256"]}}})
