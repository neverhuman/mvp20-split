"""Transaction-local graph persistence, called only under the Runtime admission/run locks."""

import json

from amphora_contracts_campaigns import parse_execution_plan
from sqlalchemy import text

from ..lifecycle.claims import RUN
from .values import ensure


class GraphStorage:
    @staticmethod
    def retain_plan(conn, params, entry):
        document = entry.plan.model_dump(mode="json")
        descriptors = [value.model_dump(mode="json") for value in entry.descriptors]
        binding = {**params, "digest": entry.plan.sha256, "document": json.dumps(document), "descriptors": json.dumps(descriptors)}
        conn.execute(text("INSERT INTO runtime.graph_plans (tenant_id,project_id,plan_sha256,document,tool_descriptors) "
                          "VALUES (:tenant,:project,:digest,CAST(:document AS jsonb),CAST(:descriptors AS jsonb)) ON CONFLICT DO NOTHING"), binding)
        row = conn.execute(text("SELECT document,tool_descriptors FROM runtime.graph_plans WHERE tenant_id=:tenant "
                                "AND project_id=:project AND plan_sha256=:digest"), binding).mappings().one()
        # JSONB may expand exponent notation; reapply the wire types before comparing numeric values.
        stored = parse_execution_plan(json.dumps(row["document"])).model_dump(mode="json")
        ensure(stored == document and row["tool_descriptors"] == descriptors, "graph_plan_identity_conflict")

    @staticmethod
    def create_scope(conn, params, address, inputs, intents, parent=None):
        conn.execute(text("INSERT INTO runtime.graph_scopes (tenant_id,project_id,run_id,scope_key,definition_path,"
            "occurrences,status,inputs,parent_activation_id) VALUES (:tenant,:project,:run,:scope,CAST(:definition AS jsonb),"
            "CAST(:occurrences AS jsonb),'active',CAST(:inputs AS jsonb),:parent)"),
            {**params, "scope": address.key, "definition": json.dumps(address.definition_path),
             "occurrences": json.dumps([value.model_dump(mode="json") for value in address.occurrences]),
             "inputs": json.dumps(inputs.record()), "parent": parent})
        for intent in intents:
            conn.execute(text("INSERT INTO runtime.graph_nodes (tenant_id,project_id,run_id,activation_id,scope_key,node_id,"
                "path,kind,priority,status) VALUES (:tenant,:project,:run,:activation,:scope,:node,CAST(:path AS jsonb),"
                ":kind,CAST(:priority AS jsonb),:status)"), {**params, "activation": intent.address.key, "scope": address.key,
                "node": intent.address.path.node_id, "path": intent.address.path.model_dump_json(), "kind": intent.kind,
                "priority": json.dumps(intent.priority), "status": intent.status})

    @staticmethod
    def graph(conn, params):
        row = conn.execute(text("SELECT * FROM runtime.graph_runs WHERE " + RUN), params).mappings().one_or_none()
        ensure(row is not None, "graph_run_unavailable")
        return row
