"""Actual admission pins retention once and keeps terminal replay peer-independent."""

from sqlalchemy import text
from amphora_campaign_runtime.coordinator import GraphAdmission, PlanCatalog
from amphora_campaign_runtime.completion.artifacts import ReservationUnavailable
from amphora_campaign_runtime.completion.profiles import KEY
from amphora_campaign_runtime.completion.closures import PROFILE
from amphora_campaign_runtime.lifecycle.authority import AuthorityCommands


class Support:
    def __init__(self, engine):
        self.engine, self.calls, self.available = engine, 0, True

    def require_available(self):
        assert self.engine.pool.checkedout() == 0, "Remote preflight must run outside owner SQL"
        self.calls += 1
        if not self.available:
            raise ReservationUnavailable("unavailable")


def test_new_graph_pins_profile_and_replay_ignores_current_peer(graph_env):
    g = graph_env
    peer = Support(g.env.engine)
    admission = GraphAdmission(g.env.engine, PlanCatalog([g.entry]), retention=peer)
    command = g.command("graph.admit", g.payload)
    result = admission.admit(g.env.principal, command)
    assert result.outcome.status == "accepted"
    peer.available = False
    assert admission.admit(g.env.principal, command) == result
    assert peer.calls == 1
    with g.env.engine.connect() as conn:
        snapshot = conn.execute(text("SELECT tool_snapshot FROM runtime.runs WHERE run_id=:run"),
            {"run": result.outcome.committed.object_id}).scalar_one()
    assert snapshot[KEY] == PROFILE
    AuthorityCommands(g.env.engine).cancel(g.env.principal,
        g.command("runtime.cancel", {"run_id": result.outcome.committed.object_id, "reason_code": "test_cleanup"}))


def test_incompatible_peer_rejects_before_creating_execution_state(graph_env):
    g = graph_env
    peer = Support(g.env.engine)
    peer.available = False
    admission = GraphAdmission(g.env.engine, PlanCatalog([g.entry]), retention=peer)
    result = admission.admit(g.env.principal, g.command("graph.admit", g.payload))
    assert result.outcome.reason_code == "artifact_closure_unavailable"
    with g.env.engine.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM runtime.runs WHERE tenant_id=:tenant AND project_id=:project"),
            g.env.principal.scope.model_dump() | {"tenant": g.env.principal.scope.tenant_id,
                                                "project": g.env.principal.scope.project_id}).scalar_one() == 0


def test_unconfigured_graph_remains_legacy(graph_env):
    g = graph_env
    result = g.admission.admit(g.env.principal, g.command("graph.admit", g.payload))
    with g.env.engine.connect() as conn:
        snapshot = conn.execute(text("SELECT tool_snapshot FROM runtime.runs WHERE run_id=:run"),
            {"run": result.outcome.committed.object_id}).scalar_one()
    assert KEY not in snapshot
