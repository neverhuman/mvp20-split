"""Await execution through public owner methods; Artifact client peer remains scripted."""

import copy
import json
import time
import uuid
from dataclasses import replace
from types import SimpleNamespace

import pytest
from amphora_campaign_runtime.compiler import ToolCatalog
from amphora_campaign_runtime.completion.artifacts import ReservationUnavailable
from amphora_campaign_runtime.completion.retention import IntentOutcomes
from amphora_campaign_runtime.coordinator import GraphAdmission, GraphReads, PlanCatalog, ReviewedPlan
from amphora_campaign_runtime.coordinator.advance import GraphAdvancer
from amphora_campaign_runtime.lifecycle.authority import AuthorityCommands
from amphora_campaign_runtime.lifecycle.model import TransitionError
from amphora_campaign_runtime.waits.coordinator import WaitCoordinator
from amphora_campaign_runtime.waits.reads import WaitReads
from amphora_contracts_campaigns import parse_executable_campaign
from amphora_contracts_graph_runtime import parse_graph_command
from export_schemas import ROOT
from sqlalchemy import text

from ..completion.test_acceptance import Peer


def start(graph, *, timeout=60, on_timeout="blocked", mixed=False, modify=None):
    raw = json.loads((ROOT / "contracts/fixtures/v3/await_cases.json").read_bytes())[0]["payload"]
    raw["scope"] = graph.env.principal.scope.model_dump(mode="json")
    node = raw["body"]["nodes"][0]
    node.update(timeout_seconds=timeout, on_timeout=on_timeout)
    if mixed:
        tool = copy.deepcopy(graph.raw["body"]["nodes"][0])
        tool["node_id"] = "work"
        raw["body"]["nodes"].append(tool)
        raw["body"]["edges"].append({"source": tool["node_id"], "target": "finish", "route": "next"})
    if modify:
        modify(raw)
    entry = ReviewedPlan.compile(parse_executable_campaign(json.dumps(raw)),
                                 graph.source.tools if mixed else ToolCatalog([]), graph.source.schemas)
    catalog = PlanCatalog([entry])
    assert catalog.needs_completion
    admission = GraphAdmission(graph.env.engine, catalog)
    command = graph.command("graph.admit", {**graph.payload, "plan_sha256": entry.plan.sha256})
    admitted = admission.admit(graph.env.principal, command)
    assert admitted.outcome.status == "accepted"
    run = admitted.outcome.committed.object_id
    advance = GraphAdvancer(graph.env.engine)
    advanced = advance.advance(graph.env.principal, graph.command("graph.advance", {"run_id": run}))
    assert advanced.outcome.status == "accepted"
    page = GraphReads(graph.env.engine).run(graph.env.principal, run, version=2)
    activation = next(n.activation_id for n in page.nodes if n.kind == "await")
    issuer = replace(graph.env.principal, actor_id=node["issuer_id"], actions=frozenset({"submit_receipt", "read", "outcome"}))
    observation = WaitReads(graph.env.engine).observation(issuer, run, activation)
    return SimpleNamespace(graph=graph, entry=entry, admission=admission, run=run, activation=activation,
                           issuer=issuer, observation=observation, advance=advance)


def submit_command(f, *, status="accepted", mutate=None):
    expected = f.observation.expectation
    receipt = {"issuer_id": expected.issuer_id, "receipt_id": uuid.uuid4().hex, "scope": expected.scope.model_dump(mode="json"),
        "purpose": expected.purpose, "revision": expected.expected_revision, "subject": expected.subject.model_dump(mode="json"),
        "outcome": {"status": status, "reason_code": "scientific_reason"}}
    if status == "accepted":
        receipt["outcome"] = {"status": "accepted", "output": {"kind": "artifact",
            "artifact": {**receipt["subject"], "artifact_id": "domain-result",
                         "schema_ref": expected.output_type.schema_ref.model_dump(mode="json")},
            "representation": expected.output_type.representation, "unit": expected.output_type.unit}}
    elif status == "superseded":
        receipt["outcome"]["replacement_revision"] = "newer"
    if mutate:
        mutate(receipt)
    return parse_graph_command("graph.submit_receipt", json.dumps({"identity": {
        "scope": expected.scope.model_dump(mode="json"), "actor_id": expected.issuer_id,
        "command_family": "graph.submit_receipt", "command_id": uuid.uuid4().hex}, "payload": {
            "run_id": f.run, "activation_id": f.activation, "wait_revision": expected.wait_revision,
            "expectation_sha256": f.observation.expectation_sha256, "receipt": receipt}}))


def observation(f):
    return WaitReads(f.graph.env.engine).observation(f.issuer, f.run, f.activation)


def advance(f):
    reply = f.advance.advance(f.graph.env.principal, f.graph.command("graph.advance", {"run_id": f.run}))
    assert reply.outcome.status == "accepted"
    return GraphReads(f.graph.env.engine).run(f.graph.env.principal, f.run, version=2)


def test_wait_acceptance_retention_output_and_replay_without_attempt_budget(graph_env):
    f = start(graph_env)
    calls = []
    class UnlockedPeer(Peer):
        def reserve(self, reservation):
            with f.graph.env.engine.begin() as conn:
                conn.execute(text("SET LOCAL lock_timeout='200ms'"))
                conn.execute(text("SELECT run_id FROM runtime.runs WHERE run_id=:run FOR UPDATE"), {"run": f.run}).one()
            calls.append(reservation)
            return super().reserve(reservation)
    service = WaitCoordinator(graph_env.env.engine, UnlockedPeer())
    command = submit_command(f)
    reply = service.submit(f.issuer, command)
    assert reply.outcome.status == "accepted" and len(calls) == 1
    assert observation(f).closure.outcome.status == "accepted"
    page = advance(f)
    assert page.status == "completed" and (page.spent, page.reserved) == (0, 0)
    assert WaitCoordinator(graph_env.env.engine, UnlockedPeer()).submit(f.issuer, command) == reply
    assert len(calls) == 1
    with graph_env.env.engine.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM runtime.attempts WHERE run_id=:run"), {"run": f.run}).scalar_one() == 0
        intent = conn.execute(text("SELECT status FROM runtime.wait_retention_intents WHERE run_id=:run"), {"run": f.run}).scalar_one()
        assert intent == "committed"
        output = conn.execute(text("SELECT outputs FROM runtime.graph_runs WHERE run_id=:run"), {"run": f.run}).scalar_one()
        assert output[0]["value"]["artifact"]["artifact_id"] == "domain-result"


@pytest.mark.parametrize("status,closure", [("rejected", "blocked"), ("abstained", "abstained")])
def test_nonaccepted_receipts_close_truthfully_without_reservation(graph_env, status, closure):
    f = start(graph_env)
    class NoReservation(Peer):
        def reserve(self, reservation):
            pytest.fail("Nonaccepted evidence must not reserve an artifact")
    reply = WaitCoordinator(graph_env.env.engine, NoReservation()).submit(f.issuer, submit_command(f, status=status))
    assert reply.outcome.status == "accepted"
    assert observation(f).closure.outcome.status == closure
    assert advance(f).status == "blocked"


@pytest.mark.parametrize("case,reason", [("purpose", "wait_receipt_purpose_mismatch"),
    ("revision", "wait_receipt_revision_mismatch"), ("superseded", "wait_receipt_superseded")])
def test_ineligible_receipt_cannot_unblock_wait(graph_env, case, reason):
    f = start(graph_env)
    command = submit_command(f, status="superseded" if case == "superseded" else "accepted",
                             mutate=None if case == "superseded" else lambda raw: raw.update({case: "wrong"}))
    reply = WaitCoordinator(graph_env.env.engine, Peer()).submit(f.issuer, command)
    assert reply.outcome.status == "rejected" and reply.outcome.reason_code == reason
    assert observation(f).closure is None and advance(f).status == "running"


def test_timeout_aborts_prepared_intent_and_original_command(graph_env):
    f = start(graph_env, timeout=1, on_timeout="abstained")
    class Unavailable(Peer):
        def reserve(self, reservation):
            raise ReservationUnavailable("lost_reply")
    command = submit_command(f)
    service = WaitCoordinator(graph_env.env.engine, Unavailable())
    assert service.submit(f.issuer, command).outcome.status == "pending"
    limit = time.monotonic() + 5
    while time.monotonic() < limit:
        if observation(f).closure is not None:
            break
        advance(f)
        time.sleep(0.025)
    assert observation(f).closure.outcome.status == "abstained"
    reply = service.submit(f.issuer, command)
    assert reply.outcome.status == "rejected" and reply.outcome.reason_code == "wait_deadline_expired"


def test_cancel_wins_during_reserve_and_late_protection_is_reconciled(graph_env):
    f = start(graph_env)
    bindings = []
    class CancellingPeer(Peer):
        def reserve(self, reservation):
            revision = GraphReads(graph_env.env.engine).run(graph_env.env.principal, f.run, version=2).revision
            cancelled = AuthorityCommands(graph_env.env.engine).cancel(graph_env.env.principal,
                graph_env.command("runtime.cancel", {"run_id": f.run, "expected_run_revision": revision, "reason_code": "stop"}))
            assert cancelled.outcome.status == "accepted"
            receipt = super().reserve(reservation)
            bindings.append(receipt.outcome.binding)
            return receipt
    command = submit_command(f)
    service = WaitCoordinator(graph_env.env.engine, CancellingPeer())
    reply = service.submit(f.issuer, command)
    assert reply.outcome.status == "rejected" and observation(f).closure.outcome.status == "cancelled"
    assert service.submit(f.issuer, command) == reply and len(bindings) == 1
    proof = IntentOutcomes(graph_env.env.engine, "runtime").lookup(f.issuer, bindings[0])
    assert proof.proof.status == "aborted"
    with graph_env.env.engine.connect() as conn:
        targets = conn.execute(text("SELECT o.target FROM runtime.outbox o JOIN runtime.audit_events a USING(event_id) "
            "WHERE a.run_id=:run"), {"run": f.run}).scalars().all()
        assert "artifact_reconcile" in targets and "artifact_confirm" not in targets


def test_configured_submit_authority_is_required(graph_env):
    f = start(graph_env)
    with pytest.raises(TransitionError, match="access_denied"):
        WaitCoordinator(graph_env.env.engine, Peer()).submit(replace(f.issuer, actions=frozenset({"read"})), submit_command(f))
