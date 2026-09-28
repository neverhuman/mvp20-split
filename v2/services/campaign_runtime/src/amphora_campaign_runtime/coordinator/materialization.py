"""Translate ready invocation intents into the existing worker lifecycle exactly once."""

from datetime import timedelta

from sqlalchemy import text

from ..lifecycle.claims import RUN
from .values import ensure


class InvocationMaterializer:
    @staticmethod
    def apply(conn, params, intent, order, graph_deadline):
        prepared = intent.prepared()
        now = conn.execute(text("SELECT clock_timestamp()")).scalar_one()
        deadline = min(graph_deadline, now + timedelta(seconds=prepared.timeout_seconds))
        ensure(now < deadline, "graph_deadline_exhausted")
        binding = {**params, "activation": prepared.activation_id, "invocation": prepared.invocation_id,
                   "spec": prepared.model_dump_json(), "order": order, "deadline": deadline}
        inserted = conn.execute(text("INSERT INTO runtime.activations (tenant_id,project_id,run_id,activation_id,"
            "invocation_id,specification,status,dispatch_order,deadline) VALUES (:tenant,:project,:run,:activation,:invocation,"
            "CAST(:spec AS jsonb),'queued',:order,:deadline) ON CONFLICT DO NOTHING RETURNING activation_id"), binding).scalar_one_or_none()
        row = conn.execute(text("SELECT specification,dispatch_order FROM runtime.activations WHERE " + RUN +
                                " AND activation_id=:activation"), binding).mappings().one()
        ensure(row["specification"] == prepared.model_dump(mode="json") and row["dispatch_order"] == order,
               "graph_activation_identity_conflict")
        conn.execute(text("UPDATE runtime.graph_nodes SET status='issued' WHERE " + RUN + " AND activation_id=:activation"), binding)
        return inserted is not None
