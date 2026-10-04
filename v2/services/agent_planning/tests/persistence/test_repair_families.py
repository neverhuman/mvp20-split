import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from threading import Barrier, Event

import pytest
from amphora_agent_planning.context import AttemptBinding, RequestSnapshot
from amphora_agent_planning.extraction import ExtractionSnapshot
from amphora_agent_planning.orchestration.runner import PlanningRunner
from amphora_agent_planning.persistence import family_state
from amphora_agent_planning.persistence.budget import BudgetLedger
from amphora_agent_planning.persistence.dispatch import DispatchJournal
from amphora_agent_planning.persistence.extraction import ExtractionJournal
from amphora_agent_planning.persistence.repair import RepairJournal
from amphora_agent_planning.persistence.settlement import SettlementJournal
from amphora_agent_planning.providers import observe
from amphora_agent_planning.providers.capture import Observation
from amphora_contracts_planning import ProviderUsage
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError

from .test_dispatch import expire
from .test_extraction import Response, inputs
from .test_reservations import policy

pytestmark = pytest.mark.postgres


def register(s, task):
    s.journal.register(s.principal, task.request)
    ExtractionJournal(s.engine).register(s.principal, task)
    return task


def variant(s, original, name, *, limits=None, context_edit=None, task_edit=None):
    request = original.request.document().model_dump(mode="json")
    request["reference"]["engagement_id"] = name
    if limits:
        request["context"]["limits"].update(limits)
    if context_edit:
        context_edit(request["context"])
    snapshot = RequestSnapshot.from_bytes(json.dumps(request).encode(), actor_id=s.principal.actor_id, scope=s.principal.scope)
    document = original.document().model_dump(mode="json")
    document.update(task_id=name, engagement=request["reference"], request_sha256=snapshot.sha256)
    if task_edit:
        task_edit(document)
    return register(s, ExtractionSnapshot.from_bytes(json.dumps(document).encode(), snapshot))


def setup(s, *, limits=None, enroll=True):
    original, raw = inputs(s)
    root = variant(s, original, "root", limits=limits)
    reviewed = policy(root.request, units=10)
    families = RepairJournal(s.engine)
    if enroll:
        families.enroll_root(s.principal, "root", reviewed)
    binding = AttemptBinding(root.request, 1)
    BudgetLedger(s.engine).reserve(s.principal, binding, reviewed)
    s.journal.record(s.principal, binding, observe(binding, Response(raw)))
    SettlementJournal(s.engine).settle(s.principal, binding)
    trace = ExtractionJournal(s.engine).record(s.principal, "root", binding.reference(), "parent")
    return root, reviewed, families, trace.projection.reference()


def child(s, root, families, parent, name="child"):
    task = variant(s, root, name)
    membership = families.enroll_child(s.principal, root.document().engagement, name, parent)
    return task, membership


def test_exact_enrollment_replay_replacement_and_sql_immutability(stored):
    s = stored
    root, reviewed, families, parent = setup(s)
    first = families.enroll_root(s.principal, "root", reviewed)
    assert first == families.read(s.principal, root.document().engagement)
    task, enrolled = child(s, root, families, parent)
    assert enrolled == families.enroll_child(s.principal, root.document().engagement, "child", parent)
    engine = create_engine(s.engine.url)
    try:
        assert RepairJournal(engine).read(s.principal, task.document().engagement) == enrolled
    finally:
        engine.dispose()
    for table in ("repair_families", "repair_members"):
        with pytest.raises(DBAPIError) as caught, s.engine.begin() as connection:
            connection.execute(text(f"DELETE FROM planning.{table} WHERE false"))
        assert caught.value.orig.sqlstate == "42501"


def test_concurrent_siblings_share_last_attempt_and_replay_does_not_spend(stored):
    s = stored
    root, reviewed, families, parent = setup(s, limits={"max_attempts": 2, "total_tokens": 100000, "total_accounting_units": 100})
    left, _ = child(s, root, families, parent, "left")
    right, _ = child(s, root, families, parent, "right")
    barrier = Barrier(2)
    def reserve(task):
        barrier.wait(timeout=5)
        try:
            return BudgetLedger(s.engine).reserve(s.principal, AttemptBinding(task.request, 1), reviewed)
        except ValueError as exc:
            return str(exc)
    with ThreadPoolExecutor(2) as workers:
        results = list(workers.map(reserve, (left, right)))
    assert sum(isinstance(result, str) for result in results) == 1
    assert "repair_attempt_budget_exhausted" in results
    for task, result in zip((left, right), results, strict=True):
        bound = AttemptBinding(task.request, 1)
        if isinstance(result, str):
            assert s.journal.read_attempt(s.principal, bound.reference()) is None
            with s.engine.connect() as connection:
                assert BudgetLedger._policy(connection, s.journal._key(task.document().engagement)) is None
        else:
            assert BudgetLedger(s.engine).reserve(s.principal, bound, reviewed) == result


@pytest.mark.parametrize("limits,reason", [
    ({"total_tokens": 2048, "max_input_tokens": 1024, "max_output_tokens": 1024}, "repair_token_budget_exhausted"),
    ({"total_accounting_units": 10}, "repair_accounting_budget_exhausted")])
def test_legacy_root_adoption_counts_existing_floor(stored, limits, reason):
    s = stored
    root, reviewed, families, parent = setup(s, limits=limits, enroll=False)
    before = BudgetLedger(s.engine).read(s.principal, AttemptBinding(root.request, 1).reference())
    families.enroll_root(s.principal, "root", reviewed)
    task, _ = child(s, root, families, parent)
    with pytest.raises(ValueError, match=reason):
        BudgetLedger(s.engine).reserve(s.principal, AttemptBinding(task.request, 1), reviewed)
    assert BudgetLedger(s.engine).read(s.principal, AttemptBinding(root.request, 1).reference()) == before


def test_unbudgeted_root_and_prereserved_child_cannot_be_adopted(stored):
    s = stored
    original, _ = inputs(s)
    legacy = register(s, original)
    s.journal.begin_attempt(s.principal, AttemptBinding(legacy.request, 1))
    families = RepairJournal(s.engine)
    with pytest.raises(ValueError, match="unbudgeted_attempt_history"):
        families.enroll_root(s.principal, legacy.document().task_id, policy(legacy.request))
    assert families.read(s.principal, legacy.document().engagement) is None
    root, reviewed, families, parent = setup(s)
    task = variant(s, root, "child")
    BudgetLedger(s.engine).reserve(s.principal, AttemptBinding(task.request, 1), reviewed)
    with pytest.raises(ValueError, match="repair_child_has_attempts"):
        families.enroll_child(s.principal, root.document().engagement, "child", parent)
    assert families.read(s.principal, task.document().engagement) is None


def test_enrolled_legacy_begin_cannot_bypass_budget(stored):
    s = stored
    root, _, families, parent = setup(s)
    task, _ = child(s, root, families, parent)
    with pytest.raises(ValueError, match="repair_requires_budget_admission"):
        s.journal.begin_attempt(s.principal, AttemptBinding(task.request, 1))


def test_actor_scope_and_changed_policy_rejected(stored):
    s = stored
    root, reviewed, families, _ = setup(s)
    with pytest.raises(ValueError, match="actor"):
        families.read(replace(s.principal, actor_id="other"), root.document().engagement)
    with pytest.raises(PermissionError, match="planning_access_denied"):
        families.read(replace(s.principal, scope=s.principal.scope.model_copy(update={"project_id": "foreign"})), root.document().engagement)
    with pytest.raises(ValueError, match="repair_membership_conflict"):
        families.enroll_root(s.principal, "root", policy(root.request, units=11))
    assert families.enroll_root(s.principal, "root", reviewed).root.policy == reviewed


def test_trace_requires_enrolled_parent_and_rejects_posthoc_child(stored):
    s = stored
    root, reviewed, families, parent = setup(s)
    task, _ = child(s, root, families, parent)
    _, raw = inputs(s)
    bound = AttemptBinding(task.request, 1)
    PlanningRunner(s.engine, Response(raw), timeout_seconds=10).execute(s.principal, bound, reviewed)
    traces = ExtractionJournal(s.engine)
    with pytest.raises(ValueError, match="repair_trace_parent_required"):
        traces.record(s.principal, "child", bound.reference(), "child-trace")
    accepted = traces.record(s.principal, "child", bound.reference(), "child-trace", parent)
    assert accepted.projection.document().prior == parent
    outsider = variant(s, root, "outside")
    outside_bound = AttemptBinding(outsider.request, 1)
    PlanningRunner(s.engine, Response(raw), timeout_seconds=10).execute(s.principal, outside_bound, reviewed)
    with pytest.raises(ValueError, match="repair_trace_membership"):
        traces.record(s.principal, "outside", outside_bound.reference(), "outside-trace", parent)


def test_ordinary_runner_enforces_family_ceiling_without_provider_call(stored):
    s = stored
    root, reviewed, families, parent = setup(s, limits={"max_attempts": 1})
    task, _ = child(s, root, families, parent)
    class Forbidden:
        def supports(self, model):
            raise AssertionError("provider must not be called")
    outcome = PlanningRunner(s.engine, Forbidden(), timeout_seconds=10).run(s.principal, task.request, reviewed)
    assert outcome.stop_reason == "repair_attempt_budget_exhausted" and not outcome.attempts


@pytest.mark.parametrize("settle", [False, True])
def test_known_family_overage_blocks_already_reserved_sibling_issuance(stored, settle):
    s = stored
    root, reviewed, families, parent = setup(s, limits={"max_attempts": 4, "total_tokens": 100000, "total_accounting_units": 1000})
    left, _ = child(s, root, families, parent, "left")
    right, _ = child(s, root, families, parent, "right")
    ledger, dispatch = BudgetLedger(s.engine), DispatchJournal(s.engine)
    first, second = AttemptBinding(left.request, 1), AttemptBinding(right.request, 1)
    ledger.reserve(s.principal, first, reviewed)
    ledger.reserve(s.principal, second, reviewed)
    _, raw = inputs(s)
    observed = observe(first, Response(raw))
    overage = Observation.record(first, observed.capture, "invalid", "invalid_json",
        ProviderUsage(input_tokens=999999, output_tokens=1, accounting_units=999, certainty="reported"))
    s.journal.record(s.principal, first, overage)
    if settle:
        SettlementJournal(s.engine).settle(s.principal, first)
    with pytest.raises(ValueError, match="provider_usage_overage"):
        dispatch.issue(s.principal, second, 10)
    third, _ = child(s, root, families, parent, "third")
    with pytest.raises(ValueError, match="provider_usage_overage"):
        ledger.reserve(s.principal, AttemptBinding(third.request, 1), reviewed)


def test_membership_race_aborts_without_reverse_locking(stored, monkeypatch):
    s = stored
    root, reviewed, families, parent = setup(s)
    task = variant(s, root, "child")
    selected, enrolled = Event(), Event()
    original = family_state.request_lock
    first_call = Event()
    def pause(connection, key):
        if key["engagement"] == "child" and not first_call.is_set():
            first_call.set()
            selected.set()
            assert enrolled.wait(5)
        original(connection, key)
    monkeypatch.setattr(family_state, "request_lock", pause)
    with ThreadPoolExecutor(1) as worker:
        future = worker.submit(BudgetLedger(s.engine).reserve, s.principal, AttemptBinding(task.request, 1), reviewed)
        assert selected.wait(5)
        families.enroll_child(s.principal, root.document().engagement, "child", parent)
        enrolled.set()
        with pytest.raises(ValueError, match="repair_membership_changed"):
            future.result(timeout=5)
    assert s.journal.read_attempt(s.principal, AttemptBinding(task.request, 1).reference()) is None


def test_late_family_overage_keeps_unknown_history_and_fences_sibling(stored):
    s = stored
    root, reviewed, families, parent = setup(s, limits={"max_attempts": 4, "total_tokens": 100000, "total_accounting_units": 1000})
    left, _ = child(s, root, families, parent, "left")
    right, _ = child(s, root, families, parent, "right")
    ledger, dispatch = BudgetLedger(s.engine), DispatchJournal(s.engine)
    first, second = AttemptBinding(left.request, 1), AttemptBinding(right.request, 1)
    ledger.reserve(s.principal, first, reviewed)
    ticket = dispatch.issue(s.principal, first, 1)
    expire(s, ticket)
    unknown = dispatch.recover(s.principal, first)
    SettlementJournal(s.engine).settle(s.principal, first)
    ledger.reserve(s.principal, second, reviewed)
    late = observe(first, Response(b"{"))
    wire = late.document().model_dump(mode="json")
    wire["usage"]["accounting_units"] = 9999
    late = Observation(late.capture, json.dumps(wire).encode())
    dispatch.complete(s.principal, first, ticket, late)
    assert s.journal.read_attempt(s.principal, first.reference()) == unknown
    assert dispatch.read_late(s.principal, first).document() == late.document()
    with pytest.raises(ValueError, match="provider_usage_overage"):
        dispatch.issue(s.principal, second, 10)
    third, _ = child(s, root, families, parent, "third")
    with pytest.raises(ValueError, match="provider_usage_overage"):
        ledger.reserve(s.principal, AttemptBinding(third.request, 1), reviewed)


def test_parent_membership_and_different_parent_replay_rejected(stored):
    s = stored
    root, reviewed, families, parent = setup(s, limits={"max_attempts": 4, "total_tokens": 100000, "total_accounting_units": 1000})
    task, _ = child(s, root, families, parent)
    _, raw = inputs(s)
    bound = AttemptBinding(task.request, 1)
    PlanningRunner(s.engine, Response(raw), timeout_seconds=10).execute(s.principal, bound, reviewed)
    other_parent = ExtractionJournal(s.engine).record(s.principal, "child", bound.reference(), "child-trace", parent).projection.reference()
    next_task, first = child(s, root, families, parent, "next")
    with pytest.raises(ValueError, match="repair_membership_conflict"):
        families.enroll_child(s.principal, root.document().engagement, "next", other_parent)
    outsider = variant(s, root, "outside")
    outside_bound = AttemptBinding(outsider.request, 1)
    PlanningRunner(s.engine, Response(raw), timeout_seconds=10).execute(s.principal, outside_bound, reviewed)
    outside_trace = ExtractionJournal(s.engine).record(s.principal, "outside", outside_bound.reference(), "outside-trace")
    variant(s, root, "new")
    with pytest.raises(ValueError, match="repair_parent_membership"):
        families.enroll_child(s.principal, root.document().engagement, "new", outside_trace.projection.reference())
    assert families.read(s.principal, next_task.document().engagement) == first


def test_root_enrollment_winning_trace_race_prevents_unenrolled_link(stored, monkeypatch):
    from amphora_agent_planning.persistence import extraction

    s = stored
    root, reviewed, families, parent = setup(s, enroll=False)
    outside = variant(s, root, "outside")
    bound = AttemptBinding(outside.request, 1)
    PlanningRunner(s.engine, Response(b"{"), timeout_seconds=10).execute(s.principal, bound, reviewed)
    started, enrolled = Event(), Event()
    original = extraction.lineage_lock
    def pause(connection, key):
        started.set()
        assert enrolled.wait(5)
        original(connection, key)
    monkeypatch.setattr(extraction, "lineage_lock", pause)
    with ThreadPoolExecutor(1) as workers:
        future = workers.submit(ExtractionJournal(s.engine).record, s.principal, "outside", bound.reference(), "outside-trace", parent)
        assert started.wait(5)
        families.enroll_root(s.principal, "root", reviewed)
        enrolled.set()
        with pytest.raises(ValueError, match="repair_trace_membership"):
            future.result(timeout=5)
