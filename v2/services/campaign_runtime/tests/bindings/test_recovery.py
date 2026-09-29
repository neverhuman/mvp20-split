"""Conversion commit, cancellation and retry invariants against real owner state."""

import json
from dataclasses import replace

import pytest
from amphora_campaign_runtime.completion.artifacts import ReservationUnavailable
from amphora_campaign_runtime.completion.retention import IntentOutcomes
from amphora_campaign_runtime.coordinator.projections import ProjectionUnavailable
from amphora_campaign_runtime.coordinator.reads import GraphReads
from amphora_campaign_runtime.lifecycle.authority import AuthorityCommands
from amphora_campaign_runtime.lifecycle.model import TransitionError
from amphora_contracts_artifacts import ReservationReceipt
from sqlalchemy import text

from .test_execution import advance, setup


def intent(e, run):
    with e.env.engine.connect() as conn:
        return dict(conn.execute(text("SELECT * FROM runtime.binding_intents WHERE run_id=:run"), {"run": run}).mappings().one())


def test_cancel_during_unlocked_reservation_reconciles_late_response(graph_env):
    e = graph_env
    run, bindings, advancer, peer = setup(e, 1)
    advance(e, run, advancer)

    def cancel(_request):
        revision = GraphReads(e.env.engine).run(e.env.principal, run, version=3).revision
        reply = AuthorityCommands(e.env.engine).cancel(e.env.principal, e.command("runtime.cancel", {
            "run_id": run, "expected_run_revision": revision, "reason_code": "test_cancel"}))
        assert reply.outcome.status == "accepted"
    peer.on_reserve = cancel
    bindings.tick(e.env.principal)
    row = intent(e, run)
    assert row["status"] == "aborted" and row["outputs"] is None
    with e.env.engine.connect() as conn:
        raw = conn.execute(text("SELECT receipt FROM runtime.binding_reservations WHERE intent_id=:intent"),
                           {"intent": row["intent_id"]}).scalar_one()
        targets = conn.execute(text("SELECT target FROM runtime.outbox JOIN runtime.audit_events USING(event_id) WHERE run_id=:run"),
                               {"run": run}).scalars().all()
    principal = replace(e.env.principal, actions=e.env.principal.actions | {"outcome"})
    proof = IntentOutcomes(e.env.engine, peer.owner).lookup(principal, ReservationReceipt.model_validate_json(json.dumps(raw)).outcome.binding)
    assert proof.proof.status == "aborted" and proof.proof.reason_code == "test_cancel"
    assert "artifact_reconcile" in targets and "artifact_confirm" not in targets


@pytest.mark.parametrize("boundary", ["reserve", "read", "publish"])
def test_uncertain_io_retries_original_intent_and_protection(graph_env, boundary):
    e = graph_env
    run, bindings, advancer, peer = setup(e, 2)
    advance(e, run, advancer)
    original = intent(e, run)
    name = "fetch" if boundary == "read" else boundary
    method = getattr(peer, name)
    calls = []

    def interrupted(*args):
        result = method(*args)
        calls.append(result)
        setattr(peer, name, method)
        if boundary == "reserve":
            raise ReservationUnavailable("lost_response")
        raise ProjectionUnavailable("lost_response")
    setattr(peer, name, interrupted)
    try:
        bindings.tick(e.env.principal)
    except ProjectionUnavailable:
        pass
    prepared = intent(e, run)
    assert prepared["status"] == "prepared" and prepared["outputs"] is None and prepared["lease_token"] is None
    advance(e, run, advancer)
    committed = intent(e, run)
    assert committed["intent_id"] == original["intent_id"] and committed["semantic_sha256"] == original["semantic_sha256"]
    assert committed["status"] == "committed" and len(calls) == 1


def test_commit_failure_rolls_back_output_closure_and_confirmation(graph_env, monkeypatch):
    e = graph_env
    run, bindings, advancer, _peer = setup(e, 1)
    advance(e, run, advancer)
    changed = bindings.changed

    def fail(conn, params, row, kind):
        if kind == "binding_committed":
            raise RuntimeError("injected commit failure")
        return changed(conn, params, row, kind)
    monkeypatch.setattr(bindings, "changed", fail)
    with pytest.raises(RuntimeError, match="injected"):
        bindings.tick(e.env.principal)
    assert intent(e, run)["outputs"] is None
    with e.env.engine.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM runtime.binding_closures WHERE run_id=:run"), {"run": run}).scalar_one() == 0
    monkeypatch.setattr(bindings, "changed", changed)
    advance(e, run, advancer)
    assert intent(e, run)["status"] == "committed"


def test_forged_output_cannot_commit_without_exact_protection(graph_env, monkeypatch):
    e = graph_env
    run, bindings, advancer, peer = setup(e, 2)
    advance(e, run, advancer)
    commit = bindings.commit

    def forge(conn, work, outputs, resources):
        raw = outputs.record()
        raw[0]["value"]["items"][0]["artifact"]["artifact_id"] = "unprotected"
        from amphora_campaign_runtime.coordinator.values import BoundValues
        return commit(conn, work, BoundValues.from_records(raw), resources)
    monkeypatch.setattr(bindings, "commit", forge)
    bindings.tick(e.env.principal)
    row = intent(e, run)
    assert row["status"] == "aborted" and row["outcome"]["reason_code"] == "binding_unprotected_output"


def test_source_schema_failure_is_a_terminal_disposition(graph_env):
    e = graph_env
    run, bindings, advancer, peer = setup(e, 1)
    advance(e, run, advancer)
    peer.fetch = lambda _ref: {"values": ["invalid"], "count": 1}
    bindings.tick(e.env.principal)
    row = intent(e, run)
    assert row["status"] == "aborted" and row["outcome"]["reason_code"] == "binding_schema_invalid"
    advance(e, run, advancer)
    assert GraphReads(e.env.engine).run(e.env.principal, run, version=3).status == "blocked"


def test_old_observation_cannot_hide_binding_nodes(graph_env):
    e = graph_env
    run, _bindings, _advancer, _peer = setup(e, 1)
    for version in (1, 2):
        with pytest.raises(TransitionError, match="graph_observation_v3_required"):
            GraphReads(e.env.engine).run(e.env.principal, run, version=version)


def test_deadline_wins_after_reservation_without_exposing_output(graph_env):
    import time
    e = graph_env
    run, bindings, advancer, peer = setup(e, 1, timeout=1)
    advance(e, run, advancer)
    peer.on_reserve = lambda _request: time.sleep(1.05)
    bindings.tick(e.env.principal)
    row = intent(e, run)
    assert row["status"] == "aborted" and row["outputs"] is None
    assert row["outcome"]["reason_code"] == "binding_deadline_expired"
    advance(e, run, advancer)
    assert GraphReads(e.env.engine).run(e.env.principal, run, version=3).status == "blocked"


def test_another_live_lease_cannot_start_io(graph_env):
    e = graph_env
    run, bindings, advancer, peer = setup(e, 1)
    advance(e, run, advancer)
    row = intent(e, run)
    params = {"tenant": e.env.principal.scope.tenant_id, "project": e.env.principal.scope.project_id,
              "run": run, "intent": row["intent_id"]}
    work = bindings.leases.commands.transact(lambda conn: bindings.claim(conn, e.env.principal, params))
    assert work is not None
    assert not bindings.tick(e.env.principal) and not peer.reservations
    with e.env.engine.begin() as conn:
        conn.execute(text("UPDATE runtime.binding_intents SET lease_until=clock_timestamp()-interval '1 second' WHERE intent_id=:intent"), params)
    advance(e, run, advancer)
    assert intent(e, run)["status"] == "committed"


def test_committed_scope_inputs_cannot_be_rewritten_by_service_role(graph_env):
    from sqlalchemy.exc import ProgrammingError
    e = graph_env
    run, _bindings, advancer, _peer = setup(e, 1)
    advance(e, run, advancer)
    with pytest.raises(ProgrammingError, match="permission denied"), e.env.engine.begin() as conn:
        conn.execute(text("UPDATE runtime.graph_scopes SET inputs=jsonb_set(inputs,'{0,value,artifact,artifact_id}', '\"changed\"') WHERE run_id=:run"),
                     {"run": run})
    advance(e, run, advancer)
    assert intent(e, run)["status"] == "committed"
