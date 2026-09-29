"""Scoped consistent observation of the exact external evidence expectation and closure."""

from amphora_contracts_graph_runtime import WaitObservation
from sqlalchemy import text

from ..lifecycle.claims import RUN
from .closures import load_wait


class WaitReads:
    def __init__(self, engine):
        self.engine = engine

    def observation(self, principal, run_id, activation_id):
        principal.require("read")
        params = {"tenant": principal.scope.tenant_id, "project": principal.scope.project_id,
                  "run": run_id, "activation": activation_id}
        with self.engine.connect().execution_options(isolation_level="REPEATABLE READ") as conn, conn.begin():
            conn.execute(text("SET TRANSACTION READ ONLY"))
            wait = load_wait(conn, params)
            closure = conn.execute(text("SELECT document FROM runtime.graph_wait_closures WHERE " + RUN +
                " AND activation_id=:activation"), params).scalar_one_or_none()
            return WaitObservation.model_validate({"expectation": wait.expectation,
                "expectation_sha256": wait.sha256, "closure": closure})
