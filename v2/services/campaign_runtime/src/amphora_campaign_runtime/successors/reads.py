"""Bounded, consistent carry-source and immutable ancestry observations."""

import re

from amphora_contracts_graph_runtime import CarrySources, CarrySourceView, NodeOutputSource, RunOutputSource
from sqlalchemy import text

from ..coordinator.values import ensure
from ..lifecycle.claims import RUN
from ..lifecycle.model import TransitionError
from .transfer import CarryTransfer, SourceCut, value_digest


class SuccessorReads:
    def __init__(self, engine):
        self.engine = engine

    def sources(self, principal, run_id, *, activation_id=None):
        principal.require("read")
        ensure(activation_id is None or re.fullmatch(r"[0-9a-f]{64}", activation_id), "invalid_activation_id")
        with self.engine.connect().execution_options(isolation_level="REPEATABLE READ") as conn, conn.begin():
            conn.execute(text("SET TRANSACTION READ ONLY"))
            cut = SourceCut.load(conn, principal.scope, run_id)
            ready = True
            try:
                cut.require_ready(conn)
            except TransitionError:
                ready = False
            values = cut.outputs(conn, activation_id)
            views = tuple(CarrySourceView(source=(NodeOutputSource(activation_id=activation_id, port=binding.port)
                if activation_id is not None else RunOutputSource(port=binding.port)),
                value_sha256=value_digest(binding.value)) for binding in values.bindings)
            return CarrySources(scope=principal.scope, predecessor=cut.to_wire(), predecessor_ready=ready, sources=views)

    def lineage(self, principal, run_id):
        principal.require("read")
        with self.engine.connect().execution_options(isolation_level="REPEATABLE READ") as conn, conn.begin():
            conn.execute(text("SET TRANSACTION READ ONLY"))
            cut = SourceCut.load(conn, principal.scope, run_id)
            row = conn.execute(text("SELECT * FROM runtime.graph_successors WHERE " + RUN), cut.params).mappings().one_or_none()
            ensure(row is not None, "successor_lineage_unavailable")
            return CarryTransfer.lineage(principal.scope, run_id, cut.graph["plan_sha256"], row)
