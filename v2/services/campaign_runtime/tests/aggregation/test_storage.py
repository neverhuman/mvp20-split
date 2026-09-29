"""Real PostgreSQL cut identity, deferred audit atomicity and immutable-role proof."""

import uuid
from dataclasses import replace

import pytest
from amphora_campaign_runtime.aggregation import (
    AggregateCuts,
    AggregateIdentity,
    JoinAccumulator,
    SnapshotCut,
)
from amphora_campaign_runtime.lifecycle.model import TransitionError
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from ..scheduling.test_advancement import admit
from .test_snapshot import member


def setup(graph):
    inputs = [*graph.payload["inputs"], {"port": "flag", "value": {"kind": "boolean", "value": True}}]
    run = admit(graph, 1, inputs)
    with graph.env.engine.connect() as conn:
        revision = conn.execute(text("SELECT revision FROM runtime.runs WHERE run_id=:run"), {"run": run}).scalar_one()
        activation = conn.execute(text("SELECT activation_id FROM runtime.graph_nodes WHERE run_id=:run AND kind='join'"),
                                  {"run": run}).scalar_one()
    return SnapshotCut(AggregateIdentity(graph.env.principal.scope, run, activation), revision, revision + 1,
                       "all_terminal", (member(revision=revision),))


def audit(conn, cut):
    # Storage-only test harness: production coordinator integration is the later B2 gate.
    params = {"tenant": cut.identity.scope.tenant_id, "project": cut.identity.scope.project_id,
              "run": cut.identity.run_id, "revision": cut.closure_revision, "event": uuid.uuid4().hex}
    conn.execute(text("UPDATE runtime.runs SET revision=:revision WHERE run_id=:run"), params)
    conn.execute(text("INSERT INTO runtime.audit_events(event_id,tenant_id,project_id,run_id,revision,ordinal,payload) "
                      "VALUES(:event,:tenant,:project,:run,:revision,0,'{}')"), params)


def test_policy_decision_exact_replay_and_changed_policy_denied(graph_env):
    cut = setup(graph_env)
    decision = JoinAccumulator({"kind": "all"}).close(cut)
    with graph_env.env.engine.begin() as conn:
        assert AggregateCuts.decide(conn, decision) == decision.sha256
        audit(conn, cut)
    with graph_env.env.engine.begin() as conn:
        assert AggregateCuts.decide(conn, decision) == decision.sha256
        with pytest.raises(TransitionError, match="aggregate_decision_conflict"):
            AggregateCuts.decide(conn, JoinAccumulator({"kind": "all", "skipped": "fail"}).close(cut))


def test_cut_cannot_acquire_policy_after_its_commit(graph_env):
    cut = setup(graph_env)
    with graph_env.env.engine.begin() as conn:
        AggregateCuts.persist(conn, cut)
        audit(conn, cut)
    with graph_env.env.engine.begin() as conn:
        with pytest.raises(TransitionError, match="aggregate_stale_decision"):
            AggregateCuts.decide(conn, JoinAccumulator({"kind": "all"}).close(cut))


def test_decision_without_audit_rolls_back_both_rows(graph_env):
    cut = setup(graph_env)
    with pytest.raises(DBAPIError):
        with graph_env.env.engine.begin() as conn:
            AggregateCuts.decide(conn, JoinAccumulator({"kind": "all"}).close(cut))
    with graph_env.env.engine.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM runtime.graph_aggregate_decisions WHERE run_id=:run"),
                            {"run": cut.identity.run_id}).scalar_one() == 0


@pytest.mark.parametrize("mutation", ["UPDATE runtime.graph_aggregate_decisions SET document='{}' WHERE run_id=:run",
                                    "DELETE FROM runtime.graph_aggregate_decisions WHERE run_id=:run"])
def test_service_cannot_mutate_policy_history(graph_env, mutation):
    cut = setup(graph_env)
    with graph_env.env.engine.begin() as conn:
        AggregateCuts.decide(conn, JoinAccumulator({"kind": "all"}).close(cut))
        audit(conn, cut)
    with pytest.raises(DBAPIError):
        with graph_env.env.engine.begin() as conn:
            conn.execute(text(mutation), {"run": cut.identity.run_id})


def test_atomic_cut_exact_replay_and_late_rewrite_denied(graph_env):
    cut = setup(graph_env)
    with graph_env.env.engine.begin() as conn:
        assert AggregateCuts.persist(conn, cut) == cut.sha256
        audit(conn, cut)
    with graph_env.env.engine.begin() as conn:
        assert AggregateCuts.persist(conn, cut) == cut.sha256
        with pytest.raises(TransitionError, match="aggregate_already_closed"):
            AggregateCuts.persist(conn, replace(cut, members=(member("different", revision=cut.observed_revision),)))
        row = conn.execute(text("SELECT document,cut_sha256 FROM runtime.graph_aggregate_cuts WHERE run_id=:run"),
                           {"run": cut.identity.run_id}).mappings().one()
        assert row["document"] == cut.record() and row["cut_sha256"] == cut.sha256


def test_missing_closure_audit_rolls_back_cut(graph_env):
    cut = setup(graph_env)
    with pytest.raises(DBAPIError):
        with graph_env.env.engine.begin() as conn:
            AggregateCuts.persist(conn, cut)
    with graph_env.env.engine.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM runtime.graph_aggregate_cuts WHERE run_id=:run"),
                            {"run": cut.identity.run_id}).scalar_one() == 0


@pytest.mark.parametrize("mutation", ["UPDATE runtime.graph_aggregate_cuts SET document='{}' WHERE run_id=:run",
                                    "DELETE FROM runtime.graph_aggregate_cuts WHERE run_id=:run"])
def test_service_cannot_rewrite_or_delete_closed_evidence(graph_env, mutation):
    cut = setup(graph_env)
    with graph_env.env.engine.begin() as conn:
        AggregateCuts.persist(conn, cut)
        audit(conn, cut)
    with pytest.raises(DBAPIError):
        with graph_env.env.engine.begin() as conn:
            conn.execute(text(mutation), {"run": cut.identity.run_id})


@pytest.mark.parametrize("case,reason", [("stale", "aggregate_stale_cut"), ("node", "aggregate_node_unavailable"),
                                       ("run", "run_unavailable"), ("cancelled", "run_not_running")])
def test_invalid_storage_authority(graph_env, case, reason):
    cut = setup(graph_env)
    if case == "stale":
        cut = replace(cut, observed_revision=cut.observed_revision + 1, closure_revision=cut.closure_revision + 1)
    elif case == "node":
        cut = replace(cut, identity=replace(cut.identity, activation_id="f" * 64))
    elif case == "run":
        cut = replace(cut, identity=replace(cut.identity, run_id="unavailable"))
    with graph_env.env.engine.begin() as conn:
        if case == "cancelled":
            conn.execute(text("UPDATE runtime.runs SET status='cancelled' WHERE run_id=:run"), {"run": cut.identity.run_id})
        with pytest.raises(TransitionError, match=reason):
            AggregateCuts.persist(conn, cut)
