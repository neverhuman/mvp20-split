"""Private immutable validation evidence; never grants plan execution eligibility."""

import json

from amphora_contracts_graph_runtime import DraftValidation
from sqlalchemy import text


def restore(row):
    if row is None:
        return None
    record = DraftValidation.model_validate_json(json.dumps(row["record"]))
    actual = (record.scope.tenant_id, record.scope.project_id, record.validation_id, record.draft_id,
              record.revision, record.content_sha256, record.universe_sha256)
    expected = tuple(row[key] for key in ("tenant_id", "project_id", "validation_id", "draft_id", "revision", "content_sha256", "universe_sha256"))
    if actual != expected:
        raise ValueError("validation_record_identity_mismatch")
    return record


def persist(conn, params, universe, result):
    bindings = {**params, "universe": universe.sha256, "material": json.dumps(universe.record()),
                "validation": result.validation_id, "revision": result.revision,
                "digest": result.content_sha256, "record": result.model_dump_json()}
    conn.execute(text("INSERT INTO runtime.definition_universes (tenant_id,project_id,universe_sha256,material) "
        "VALUES (:tenant,:project,:universe,CAST(:material AS jsonb)) ON CONFLICT DO NOTHING"), bindings)
    conn.execute(text("INSERT INTO runtime.definition_validations "
        "(tenant_id,project_id,validation_id,draft_id,revision,content_sha256,universe_sha256,record,operation_id) "
        "VALUES (:tenant,:project,:validation,:draft,:revision,:digest,:universe,CAST(:record AS jsonb),:operation)"), bindings)
