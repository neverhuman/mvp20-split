"""Private draft row mapping and writes; caller owns the short transaction."""

import json

from amphora_contracts_graph_runtime import DraftHead, DraftRevision
from sqlalchemy import text

from .revisions import DraftVersion

KEY = "tenant_id=:tenant AND project_id=:project AND draft_id=:draft"


def header(row):
    record = DraftHead.model_validate_json(json.dumps(row["head"]))
    if (record.draft_id, record.revision, record.content_sha256) != (row["draft_id"], row["revision"], row["content_sha256"]):
        raise ValueError("draft_header_identity_mismatch")
    return record


def version(row):
    if row is None:
        return None
    record = DraftRevision.model_validate_json(json.dumps(row["record"]))
    if (record.scope.tenant_id, record.scope.project_id, record.head.draft_id, record.head.revision,
        record.head.content_sha256) != (row["tenant_id"], row["project_id"], row["draft_id"], row["revision"], row["content_sha256"]):
        raise ValueError("draft_record_identity_mismatch")
    return DraftVersion.from_wire(record)


def head(conn, params):
    return version(conn.execute(text("SELECT r.* FROM runtime.definition_revisions r JOIN runtime.definition_heads h "
        "USING(tenant_id,project_id,draft_id) WHERE r.tenant_id=:tenant AND r.project_id=:project "
        "AND r.draft_id=:draft AND r.revision=h.head_revision"), params).mappings().one_or_none())


def persist(conn, params, draft):
    record = draft.to_wire()
    bindings = {**params, "revision": draft.revision, "parent": draft.revision - 1 if draft.revision > 1 else None,
        "digest": draft.content.sha256, "record": record.model_dump_json()}
    conn.execute(text("INSERT INTO runtime.definition_revisions "
        "(tenant_id,project_id,draft_id,revision,parent_revision,content_sha256,record,operation_id) "
        "VALUES (:tenant,:project,:draft,:revision,:parent,:digest,CAST(:record AS jsonb),:operation)"), bindings)
    conn.execute(text("INSERT INTO runtime.definition_heads (tenant_id,project_id,draft_id,head_revision) "
        "VALUES (:tenant,:project,:draft,:revision) ON CONFLICT (tenant_id,project_id,draft_id) "
        "DO UPDATE SET head_revision=EXCLUDED.head_revision"), bindings)
    conn.execute(text("INSERT INTO runtime.definition_audit (tenant_id,project_id,draft_id,revision,operation_id,kind) "
        "VALUES (:tenant,:project,:draft,:revision,:operation,'draft_saved')"), bindings)
