"""Advertise only implemented Runtime projections, scoped to an authorized observation cut."""

from dataclasses import dataclass

from amphora_contracts_graph_runtime import (
    DigestViewFilter,
    GraphViewCatalog,
    GraphViewDefinition,
    RadiusViewFilter,
)

from ..graph_inspection.policy import ObservedCut, read_transaction


@dataclass(frozen=True)
class RuntimeView:
    name: str
    schema: str
    capability: str
    bound: int
    filters: tuple

    def definition(self):
        return GraphViewDefinition(view_id=self.name, result_schema=self.schema,
            required_capability=self.capability, result_bound=self.bound, filters=self.filters)


VIEWS = (
    RuntimeView("execution_topology", "graph-runtime.topology-page", "runtime.authored-topology.v1", 256,
        (DigestViewFilter(name="scope_key", required=True), DigestViewFilter(name="focus_activation_id", required=False),
         RadiusViewFilter())),
    RuntimeView("successor_lineage", "graph-runtime.successor-lineage", "runtime.successor-lineage.v1", 64, ()),
)


class RuntimeViewCatalog:
    def __init__(self, engine, cursors):
        self.engine, self.cursors = engine, cursors

    def read(self, principal, run_id, snapshot_token):
        with read_transaction(self.engine) as conn:
            cut = ObservedCut.load(conn, principal, run_id)
            cut.snapshot_position(self.cursors, snapshot_token)
            return GraphViewCatalog(cut=cut.to_wire(), views=tuple(view.definition() for view in VIEWS))
