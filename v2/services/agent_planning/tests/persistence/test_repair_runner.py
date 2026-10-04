"""Repair orchestration against owned SQL; scripted input/provider boundaries."""

import json
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from amphora_agent_planning.context import AttemptBinding
from amphora_agent_planning.persistence.budget import BudgetLedger
from amphora_agent_planning.persistence.dispatch import DispatchJournal
from amphora_agent_planning.persistence.preparation import PreparationJournal
from amphora_agent_planning.providers.capture import unknown_usage
from amphora_agent_planning.providers.port import ProviderReply
from amphora_agent_planning.repair.runner import RepairRunner
from sqlalchemy import create_engine

from .test_dispatch import expire
from .test_preparation import enrolled

pytestmark = pytest.mark.postgres


class Inputs:
    def __init__(self, prepared):
        self.prepared, self.calls = prepared, 0
        self.denied = False

    def prepare(self, history, feedback, interpretation):
        self.calls += 1
        if self.denied:
            raise ValueError("source_access_denied")
        assert history == self.prepared.history
        assert feedback == self.prepared.plan.feedback_reference()
        assert interpretation == self.prepared.plan.interpretation_reference()
        return self.prepared


class Provider:
    def __init__(self):
        self.packets = []

    def supports(self, model):
        return True

    def reply(self, binding, packet):
        record = json.loads(packet)
        assert record["profile"] == "planning-repair-extraction-input.v1"
        assert record["repair_feedback"]["authority"] == "diagnostic_only"
        self.packets.append(packet)
        return ProviderReply((b"{",), unknown_usage())


def execute(s, inputs, provider, *, engine=None):
    p = inputs.prepared
    return RepairRunner(s.engine if engine is None else engine, inputs, provider, timeout_seconds=10).execute(
        s.principal, p.history.root.task.document().engagement, p.history.projection.reference(),
        p.plan.feedback_reference(), p.plan.interpretation_reference())


def test_actual_packet_reaches_adapter_and_replacement_replays_without_input_reads(stored):
    s = stored
    inputs, provider = Inputs(enrolled(s)), Provider()
    first = execute(s, inputs, provider)
    assert len(provider.packets) == inputs.calls == 1
    assert provider.packets[0] == inputs.prepared.packet
    assert first.trace.document().prior == inputs.prepared.history.projection.reference()
    assert first.attempt.observation.capture.content == b"{"
    inputs.denied = True
    engine = create_engine(s.engine.url)
    try:
        assert execute(s, inputs, provider, engine=engine) == first
    finally:
        engine.dispose()
    assert len(provider.packets) == inputs.calls == 1


def test_unissued_reservation_requires_fresh_preparation(stored):
    s = stored
    inputs, provider = Inputs(enrolled(s)), Provider()
    p = inputs.prepared
    bound = AttemptBinding(p.plan.task.request, 1)
    BudgetLedger(s.engine).reserve(s.principal, bound, p.history.root.policy)
    PreparationJournal(s.engine).register(s.principal, p)
    inputs.denied = True
    with pytest.raises(ValueError, match="source_access_denied"):
        execute(s, inputs, provider)
    assert inputs.calls == 1 and not provider.packets
    assert not PreparationJournal(s.engine).issued(s.principal, bound)
    inputs.denied = False
    assert execute(s, inputs, provider).trace is not None
    assert inputs.calls == 2 and len(provider.packets) == 1


def test_issued_pending_and_deadline_recovery_never_reprocess_or_call(stored):
    s = stored
    inputs, provider = Inputs(enrolled(s)), Provider()
    p = inputs.prepared
    bound = AttemptBinding(p.plan.task.request, 1)
    PreparationJournal(s.engine).register(s.principal, p)
    BudgetLedger(s.engine).reserve(s.principal, bound, p.history.root.policy)
    ticket = DispatchJournal(s.engine).issue(s.principal, bound, 2)
    inputs.denied = True
    pending = execute(s, inputs, provider)
    assert pending.stop_reason == "attempt_pending" and pending.trace is None
    expire(s, ticket)
    recovered = execute(s, inputs, provider)
    assert recovered.stop_reason == "unknown"
    assert recovered.attempt.observation.document().reason_code == "attempt_deadline"
    assert recovered.trace is not None
    assert inputs.calls == 0 and not provider.packets
    assert execute(s, inputs, provider) == recovered


def test_concurrent_step_replay_has_one_physical_call(stored):
    s = stored
    inputs, provider = Inputs(enrolled(s)), Provider()
    gate = Barrier(2)
    def run(_):
        gate.wait(timeout=5)
        return execute(s, inputs, provider)
    with ThreadPoolExecutor(2) as workers:
        results = list(workers.map(run, range(2)))
    assert len(provider.packets) == 1
    final = execute(s, inputs, provider)
    assert final.trace is not None
    assert all(item == final or item.stop_reason == "attempt_pending" for item in results)


def test_observed_call_without_preparation_is_not_retroactively_attested(stored):
    s = stored
    inputs, provider = Inputs(enrolled(s)), Provider()
    p = inputs.prepared
    bound = AttemptBinding(p.plan.task.request, 1)
    BudgetLedger(s.engine).reserve(s.principal, bound, p.history.root.policy)
    DispatchJournal(s.engine).issue(s.principal, bound, 10)
    with pytest.raises(ValueError, match="repair_preparation_unknown"):
        execute(s, inputs, provider)
    assert inputs.calls == 0 and not provider.packets


@pytest.mark.parametrize("failures", [1, 3])
def test_membership_reconciliation_is_bounded_and_preserves_exact_step(stored, failures):
    s = stored
    inputs, provider = Inputs(enrolled(s, enroll_child=False)), Provider()
    p = inputs.prepared
    runner = RepairRunner(s.engine, inputs, provider, timeout_seconds=10)
    original, attempts = runner.families.enroll_child, []
    def enroll(*args):
        attempts.append(args)
        if len(attempts) <= failures:
            raise ValueError("repair_membership_changed")
        return original(*args)
    runner.families.enroll_child = enroll
    args = (s.principal, p.history.root.task.document().engagement, p.history.projection.reference(),
            p.plan.feedback_reference(), p.plan.interpretation_reference())
    if failures == 3:
        with pytest.raises(ValueError, match="repair_membership_changed"):
            runner.execute(*args)
        assert not provider.packets
    else:
        assert runner.execute(*args).trace is not None
        assert len(provider.packets) == 1
    assert len(attempts) == inputs.calls == min(failures + 1, 3)
    assert all(attempt == attempts[0] for attempt in attempts)


def test_abstained_parent_stops_without_peer_reads_or_provider_call(stored):
    s = stored
    history, feedback, interpretation, _, _ = enrolled(s, root_only=True, abstain=True)
    class NoReads:
        def prepare(self, *args):
            raise AssertionError("terminal parent must not read inputs")
    provider = Provider()
    result = RepairRunner(s.engine, NoReads(), provider, timeout_seconds=10).execute(
        s.principal, history.root.task.document().engagement, history.projection.reference(), feedback, interpretation)
    assert result.stop_reason == "abstained" and result.attempt is result.trace is None
    assert not provider.packets
