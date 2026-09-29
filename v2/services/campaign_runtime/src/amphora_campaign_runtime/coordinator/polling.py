"""Scoped recovery polling; commands and PostgreSQL, not notifications, own progress."""

import json
import time
import uuid

from amphora_contracts_graph_runtime import parse_graph_command
from sqlalchemy import text

from ..completion.recovery import StaleIntents
from ..lifecycle.model import TransitionError
from ..waits.recovery import WaitRecovery
from .projections import ProjectionUnavailable


class GraphPoller:
    def __init__(self, engine, advancer):
        self.engine, self.advancer = engine, advancer
        self.pending = None

    def tick(self, principal):
        principal.require("maintain")
        recovered = WaitRecovery(self.engine).tick(principal)
        params = {"tenant": principal.scope.tenant_id, "project": principal.scope.project_id}
        with self.engine.connect() as conn:
            run = conn.execute(text("SELECT run_id FROM runtime.runs WHERE tenant_id=:tenant AND project_id=:project "
                "AND status='running' AND execution_mode='graph'"), params).scalar_one_or_none()
        if run is None:
            self.pending = None
            if self.advancer.bindings is not None:
                recovered = self.advancer.bindings.tick(principal) or recovered
            return recovered
        StaleIntents(self.engine).sweep(principal, run, limit=100)
        if self.pending is None or self.pending[0] != run:
            command = parse_graph_command("graph.advance", json.dumps({"identity": {
                "scope": principal.scope.model_dump(mode="json"), "actor_id": principal.actor_id,
                "command_family": "graph.advance", "command_id": uuid.uuid4().hex}, "payload": {"run_id": run}}))
            self.pending = run, command
        try:
            self.advancer.advance(principal, self.pending[1])
        except TransitionError as error:
            if str(error) != "prepared_intent_requires_reconciliation":
                raise
            return False
        self.pending = None
        return True

    def sweep(self, principal, *, seconds=20, interval=1):
        if not 0 < seconds <= 86400 or not 0.05 <= interval <= 60:
            raise ValueError("Bounded polling duration and interval required")
        principal.require("maintain")
        deadline = time.monotonic() + seconds
        ticks, advanced, unavailable = 0, 0, 0
        while time.monotonic() < deadline:
            ticks += 1
            try:
                advanced += int(self.tick(principal))
            except ProjectionUnavailable:
                unavailable += 1
            remaining = deadline - time.monotonic()
            if remaining > 0:
                time.sleep(min(interval, remaining))
        return {"ticks": ticks, "advanced": advanced, "projection_unavailable": unavailable}
