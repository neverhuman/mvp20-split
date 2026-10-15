"""Original retained scope/invocation inputs, independent of live frontier cursors."""
import json
from dataclasses import dataclass

from amphora_contracts_node_inputs import NodeInputObservation, ScopeInputSummary
from amphora_contracts_runtime import PreparedInvocation
from sqlalchemy import text

from ..coordinator.values import BoundValues
from ..inspection.cursors import InspectionError
from .policy import ObservedCut, read_transaction


class InputObservationError(ValueError):
    """Persisted owner state cannot safely produce the bounded public projection."""


@dataclass(frozen=True)
class RetainedInputs:
    bindings: tuple
    invocation: object

    @classmethod
    def load(cls, row, scope):
        records = row["scope_inputs"]
        if not isinstance(records, list) or len(records) > 64:
            raise InputObservationError("scope_inputs_inconsistent")
        bindings = BoundValues.from_records(records).bindings
        for binding in bindings:
            value = binding.value
            members = value.items if value.kind == "collection" else (value,)
            if any(item.kind == "artifact" and item.artifact.scope != scope for item in members):
                raise InputObservationError("scope_inputs_inconsistent")
        invocation = (PreparedInvocation.model_validate_json(json.dumps(row["specification"]))
                      if row["specification"] is not None else None)
        # A materialized activation must always retain its immutable specification.
        if row["invocation_id"] is not None and (invocation is None or
                invocation.invocation_id != row["invocation_id"] or invocation.node_id != row["node_id"]):
            raise InputObservationError("invocation_inputs_inconsistent")
        return cls(bindings, invocation)

    def to_wire(self, cut, row):
        def summary(binding):
            value = binding.value
            items = value.items if value.kind == "collection" else (value,)
            return ScopeInputSummary(port=binding.port, kind=value.kind,
                item_count=len(items), missing_count=sum(item.kind == "missing" for item in items),
                artifact=value.artifact if value.kind == "artifact" else None)
        return NodeInputObservation(schema_version="1", profile="runtime-node-inputs-v1",
            scope=cut.scope, run_id=cut.row["run_id"], activation_id=row["activation_id"],
            scope_key=row["scope_key"], observed_run_revision=cut.revision,
            scope_inputs=tuple(summary(binding) for binding in self.bindings), invocation=self.invocation)


class NodeInputs:
    def __init__(self, engine):
        self.engine = engine

    def read(self, principal, run_id, activation_id):
        principal.require("read")
        principal.require("inspect_receipts")
        with read_transaction(self.engine) as conn:
            cut = ObservedCut.load(conn, principal, run_id)
            row = conn.execute(text("""SELECT n.activation_id,n.scope_key,s.inputs AS scope_inputs,
                    a.specification,a.invocation_id,n.node_id
                FROM runtime.graph_nodes n
                JOIN runtime.graph_scopes s USING (tenant_id,project_id,run_id,scope_key)
                LEFT JOIN runtime.activations a USING (tenant_id,project_id,run_id,activation_id)
                WHERE n.tenant_id=:tenant AND n.project_id=:project AND n.run_id=:run
                  AND n.activation_id=:activation"""),
                {**cut.params, "activation": activation_id}).mappings().one_or_none()
            if row is None:
                raise InspectionError("graph_node_unavailable")
            try:
                return RetainedInputs.load(row, cut.scope).to_wire(cut, row)
            except (ValueError, TypeError, KeyError) as error:
                raise InputObservationError("input_observation_inconsistent") from error
