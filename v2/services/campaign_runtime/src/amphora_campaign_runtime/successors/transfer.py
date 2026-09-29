"""Resolve a precise committed source cut without external I/O."""

import hashlib
import json
from dataclasses import dataclass

from amphora_contracts_graph_runtime import GraphBinding, PredecessorCut, SuccessorLineage
from pydantic import ValidationError
from sqlalchemy import text

from ..coordinator.values import BoundValues, ensure
from ..lifecycle.claims import RUN
from ..lifecycle.model import TransitionError


def digest(document):
    return hashlib.sha256(json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()


def value_digest(value):
    return digest({"profile": "amphora-carried-value-v1", "value": value.model_dump(mode="json")})


@dataclass(frozen=True)
class SourceCut:
    run: object
    graph: object
    params: dict

    @classmethod
    def load(cls, conn, scope, run_id, *, lock=False):
        params = {"tenant": scope.tenant_id, "project": scope.project_id, "run": run_id}
        run = conn.execute(text("SELECT * FROM runtime.runs WHERE " + RUN +
            " AND execution_mode='graph'" + (" FOR UPDATE" if lock else "")), params).mappings().one_or_none()
        ensure(run is not None, "predecessor_unavailable")
        graph = conn.execute(text("SELECT * FROM runtime.graph_runs WHERE " + RUN), params).mappings().one()
        return cls(run, graph, params)

    def to_wire(self):
        return PredecessorCut(run_id=self.run["run_id"], plan_sha256=self.graph["plan_sha256"], revision=self.run["revision"])

    def require_ready(self, conn):
        ensure(self.run["status"] != "running", "predecessor_not_terminal")
        ensure(self.run["reserved"] == 0, "predecessor_unsettled")
        pending = conn.execute(text("SELECT EXISTS(SELECT 1 FROM runtime.attempts WHERE " + RUN +
            " AND (NOT settled OR status IN ('leased','uncertain')))"), self.params).scalar_one()
        ensure(not pending, "predecessor_unsettled")
        for table in ("completion_intents", "binding_intents", "wait_retention_intents"):
            pending = conn.execute(text(f"SELECT EXISTS(SELECT 1 FROM runtime.{table} WHERE " + RUN +
                " AND status='prepared')"), self.params).scalar_one()
            ensure(not pending, "predecessor_unsettled")

    def outputs(self, conn, activation_id=None):
        records = self.graph["outputs"]
        if activation_id is not None:
            row = conn.execute(text("SELECT status,outputs FROM runtime.graph_nodes WHERE " + RUN +
                " AND activation_id=:activation"), {**self.params, "activation": activation_id}).mappings().one_or_none()
            ensure(row is not None and row["status"] == "succeeded", "carry_source_unavailable")
            records = row["outputs"]
        ensure(records is not None, "carry_source_unavailable")
        try:
            return BoundValues.from_records(records)
        except (ValidationError, TypeError, ValueError) as error:
            raise TransitionError("carry_source_invalid") from error


@dataclass(frozen=True)
class CarryTransfer:
    proposal: object
    values: BoundValues
    sha256: str

    @classmethod
    def resolve(cls, conn, scope, proposal):
        source = SourceCut.load(conn, scope, proposal.predecessor.run_id, lock=True)
        ensure(source.to_wire() == proposal.predecessor, "predecessor_cut_changed")
        source.require_ready(conn)
        bindings = list(proposal.inputs)
        for carry in proposal.carried:
            values = source.outputs(conn, getattr(carry.source, "activation_id", None)).values
            ensure(carry.source.port in values, "carry_source_unavailable")
            value = values[carry.source.port]
            ensure(value_digest(value) == carry.expected_value_sha256, "carry_value_changed")
            bindings.append(GraphBinding(port=carry.target_port, value=value))
        values = BoundValues(tuple(bindings))
        document = {"profile": "amphora-successor-transfer-v1", "predecessor": proposal.predecessor.model_dump(mode="json"),
            "plan_sha256": proposal.plan_sha256,
            "carried": [item.model_dump(mode="json") for item in sorted(proposal.carried, key=lambda item: item.target_port)],
            "inputs": values.record()}
        return cls(proposal, values, digest(document))

    def persist(self, conn, params, run_id):
        predecessor = self.proposal.predecessor
        conn.execute(text("INSERT INTO runtime.graph_successors "
            "(tenant_id,project_id,run_id,parent_run_id,parent_plan_sha256,parent_revision,carried,transfer_sha256) "
            "VALUES (:tenant,:project,:successor,:parent,:plan,:revision,CAST(:carried AS jsonb),:transfer)"),
            {**params, "successor": run_id, "parent": predecessor.run_id, "plan": predecessor.plan_sha256,
             "revision": predecessor.revision, "transfer": self.sha256,
             "carried": json.dumps([item.model_dump(mode="json") for item in self.proposal.carried])})

    @staticmethod
    def lineage(scope, run_id, plan_sha256, row):
        return SuccessorLineage.model_validate_json(json.dumps({"scope": scope.model_dump(mode="json"),
            "run_id": run_id, "plan_sha256": plan_sha256, "predecessor": {"run_id": row["parent_run_id"],
                "plan_sha256": row["parent_plan_sha256"], "revision": row["parent_revision"]},
            "carried": row["carried"], "transfer_sha256": row["transfer_sha256"]}))
