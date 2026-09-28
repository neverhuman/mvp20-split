"""Real owner transactions conserve attempt units across contention and stops."""

import copy
import json
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from threading import Barrier

import pytest
from amphora_campaign_runtime.lifecycle.admission import FixtureCatalog
from amphora_campaign_runtime.lifecycle.claims import RuntimeLeases
from amphora_campaign_runtime.lifecycle.settlement import BudgetSettlement
from amphora_contracts_runtime import AdmitFixtureRun, parse_command
from sqlalchemy import event, text


def command(e, family, payload):
    return parse_command(family, json.dumps({"identity": {"command_family": family, "command_id": uuid.uuid4().hex,
        "actor_id": e.principal.actor_id, "scope": e.principal.scope.model_dump()}, "payload": payload}))


def setup(e, limit=1):
    payload = copy.deepcopy(e.raw["payload"])
    payload["budget"]["limit"] = limit
    other = copy.deepcopy(payload["invocations"][0])
    other.update(node_id="n2", activation_id="iteration-1.n2", invocation_id="i2")
    payload["invocations"].append(other)
    e.service.catalog = FixtureCatalog([AdmitFixtureRun.model_validate_json(json.dumps(payload))])
    e.principal = replace(e.principal, actions=e.principal.actions | {"maintain"})
    return e.service.admit(e.principal, command(e, "runtime.admit_fixture", payload)).outcome.committed.object_id


def claim(e, run):
    return RuntimeLeases(e.engine).claim(e.principal, command(e, "runtime.claim", {"run_id": run,
        "worker_id": e.principal.actor_id, "tool": e.raw["payload"]["invocations"][0]["tool"], "lease_seconds": 10}))


def row(e, run):
    with e.engine.connect() as conn:
        return conn.execute(text("SELECT * FROM runtime.runs WHERE run_id=:run"), {"run": run}).mappings().one()


def expire(e, run):
    with e.engine.begin() as conn:
        conn.execute(text("UPDATE runtime.attempts SET lease_expires_at=clock_timestamp()-interval '1 second' "
                          "WHERE run_id=:run"), {"run": run})


def test_two_activations_contend_for_one_budget_unit(fixture_env):
    e = fixture_env
    run = setup(e)
    barrier = Barrier(2)

    def compete(_):
        barrier.wait(timeout=10)
        return claim(e, run)

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(compete, range(2)))
    assert sorted(r.outcome.status for r in results) == ["claimed", "no_eligible_work"]
    assert (row(e, run)["reserved"], row(e, run)["spent"]) == (1, 0)
    expire(e, run)
    service = BudgetSettlement(e.engine)
    first = service.sweep(e.principal, run)
    assert first.status == "failed" and first.budget.spent == 1 and first.budget.reserved == 0
    revision = row(e, run)["revision"]
    assert not service.sweep(e.principal, run).changed
    assert row(e, run)["revision"] == revision


def test_cancelled_unclaimed_work_costs_zero_and_issued_work_spends_once(fixture_env):
    e = fixture_env
    run = setup(e, limit=3)
    claim(e, run)
    with e.engine.begin() as conn:
        # Fixture supplies the already-authorized cancellation state. I5 owns the real command.
        conn.execute(text("UPDATE runtime.runs SET status='cancelled' WHERE run_id=:run"), {"run": run})
    service = BudgetSettlement(e.engine)
    decision = service.sweep(e.principal, run)
    assert decision.status == "cancelled"
    assert (decision.budget.available, decision.budget.reserved, decision.budget.spent) == (2, 0, 1)
    assert not service.sweep(e.principal, run).changed
    with e.engine.connect() as conn:
        states = conn.execute(text("SELECT status FROM runtime.activations WHERE run_id=:run"), {"run": run}).scalars().all()
    assert states == ["cancelled", "cancelled"]


def test_settlement_fault_rolls_back_all_budget_and_attempt_changes(fixture_env):
    e = fixture_env
    run = setup(e)
    claim(e, run)
    expire(e, run)

    def fault(_conn, _cursor, statement, *_args):
        if statement.startswith("UPDATE runtime.runs SET revision="):
            raise RuntimeError("injected settlement fault")

    event.listen(e.engine, "after_cursor_execute", fault)
    try:
        with pytest.raises(RuntimeError, match="injected"):
            BudgetSettlement(e.engine).sweep(e.principal, run)
    finally:
        event.remove(e.engine, "after_cursor_execute", fault)
    assert (row(e, run)["reserved"], row(e, run)["spent"]) == (1, 0)
    assert BudgetSettlement(e.engine).sweep(e.principal, run).budget.spent == 1


def test_cancel_before_any_claim_spends_nothing(fixture_env):
    e = fixture_env
    run = setup(e, limit=3)
    with e.engine.begin() as conn:
        conn.execute(text("UPDATE runtime.runs SET status='cancelled' WHERE run_id=:run"), {"run": run})
    decision = BudgetSettlement(e.engine).sweep(e.principal, run)
    assert (decision.budget.available, decision.budget.reserved, decision.budget.spent) == (3, 0, 0)


def test_prepared_intent_blocks_blind_expiry_settlement(fixture_env):
    from amphora_campaign_runtime.lifecycle.model import TransitionError
    e = fixture_env
    run = setup(e)
    issued = claim(e, run).outcome
    invocation = issued.invocation
    with e.engine.begin() as conn:
        conn.execute(text("INSERT INTO runtime.completion_intents "
            "(tenant_id,project_id,intent_id,run_id,activation_id,attempt_id,fence,operation_id,semantic_sha256,output_bindings,status) "
            "VALUES (:tenant,:project,:intent,:run,:activation,:attempt,:fence,:operation,:digest,'{}','prepared')"),
            {"tenant": e.principal.scope.tenant_id, "project": e.principal.scope.project_id, "intent": uuid.uuid4().hex,
             "run": run, "activation": invocation.activation_id, "attempt": invocation.attempt_id,
             "fence": invocation.fence, "operation": issued.receipt.binding.operation_id, "digest": "b" * 64})
    expire(e, run)
    with pytest.raises(TransitionError, match="prepared_intent_requires_reconciliation"):
        BudgetSettlement(e.engine).sweep(e.principal, run)
    with pytest.raises(TransitionError, match="prepared_intent_requires_reconciliation"):
        claim(e, run)
    assert (row(e, run)["reserved"], row(e, run)["spent"]) == (1, 0)
