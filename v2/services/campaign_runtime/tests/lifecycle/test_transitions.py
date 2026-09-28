"""Deterministic domain oracles; database races belong to subsequent handlers."""

from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest
from amphora_campaign_runtime.lifecycle.model import (
    ActivationState,
    AttemptLease,
    RunBudget,
    RunState,
    TransitionError,
    WorkerAuthority,
)

NOW = datetime(2026, 9, 28, tzinfo=UTC)
DEADLINE = NOW + timedelta(minutes=5)
WORKER = WorkerAuthority("worker")
RUN = RunState()


def claim(activation=None, budget=None, **kwargs):
    return (activation or ActivationState()).claim(RUN, WORKER, budget or RunBudget(3),
        worker_id="worker", attempt_id=kwargs.pop("attempt_id", "attempt-1"), now=kwargs.pop("now", NOW),
        deadline=DEADLINE, **kwargs)


def test_issue_expire_reclaim_spends_and_increases_fence():
    activation, lease, budget = claim()
    assert (budget.available, budget.reserved, budget.spent) == (2, 1, 0)
    activation, expired, budget = activation.terminal(lease, budget, "expired", now=lease.expires_at, run=RUN)
    assert activation.status == "queued"
    assert (budget.available, budget.reserved, budget.spent) == (2, 0, 1)
    assert expired.finish(budget, "expired") == (expired, budget)
    assert activation.terminal(expired, budget, "expired", now=lease.expires_at, run=RUN) == (activation, expired, budget)
    activation, newer, budget = claim(activation, budget, attempt_id="attempt-2", now=lease.expires_at)
    assert newer.fence == 2
    assert newer.attempt_id != expired.attempt_id
    with pytest.raises(TransitionError, match="stale_attempt"):
        lease.authorize(RUN, WORKER, worker_id="worker", attempt_id="attempt-1", current_fence=2, now=NOW)
    assert (budget.available, budget.reserved, budget.spent) == (1, 1, 1)


def test_renewal_preserves_identity_and_never_exceeds_deadline():
    _, lease, _ = claim()
    renewed = lease.renew(RUN, WORKER, worker_id="worker", attempt_id=lease.attempt_id,
                         current_fence=lease.fence, now=NOW + timedelta(seconds=10), seconds=300)
    assert renewed.expires_at == DEADLINE
    assert (renewed.attempt_id, renewed.fence) == (lease.attempt_id, lease.fence)


@pytest.mark.parametrize("offset", [0, 1])
def test_exact_or_past_expiry_denies_renewal(offset):
    _, lease, _ = claim()
    with pytest.raises(TransitionError, match="lease_expired"):
        lease.renew(RUN, WORKER, worker_id="worker", attempt_id=lease.attempt_id,
                    current_fence=lease.fence, now=lease.expires_at + timedelta(microseconds=offset), seconds=30)


@pytest.mark.parametrize("status", ["completed", "failed", "blocked", "cancelled"])
def test_terminal_run_rejects_claim(status):
    with pytest.raises(TransitionError, match="run_not_running"):
        ActivationState().claim(RunState(status), WORKER, RunBudget(3), worker_id="worker", attempt_id="a",
                                now=NOW, deadline=DEADLINE)


@pytest.mark.parametrize("authority,worker,reason", [(None, "worker", "worker_unauthorized"),
    (WORKER.revoke(), "worker", "worker_revoked"), (WORKER, "impostor", "worker_mismatch")])
def test_missing_revoked_or_wrong_worker_rejects(authority, worker, reason):
    with pytest.raises(TransitionError, match=reason):
        ActivationState().claim(RUN, authority, RunBudget(3), worker_id=worker, attempt_id="a", now=NOW, deadline=DEADLINE)


def test_budget_and_attempt_limits_prevent_reissue():
    a, lease, budget = claim(budget=RunBudget(1))
    a, _, budget = a.terminal(lease, budget, "expired", now=lease.expires_at, run=RUN)
    assert a.status == "failed" and budget.spent == 1 and budget.available == 0
    with pytest.raises(TransitionError, match="budget_exhausted"):
        budget.issue()
    a, lease, budget = claim(ActivationState(max_attempts=1))
    a, _, _ = a.terminal(lease, budget, "failed", now=NOW, run=RUN, retryable=True)
    assert a.status == "failed"


def test_uncertainty_retains_budget_and_never_retries_on_expiry():
    a, lease, budget = claim()
    a, lease, same = a.terminal(lease, budget, "uncertain", now=NOW, run=RUN)
    assert a.status == "uncertain" and same == budget and not lease.settled
    with pytest.raises(TransitionError, match="uncertainty_unresolved"):
        lease.finish(budget, "expired")
    resolved, budget = lease.finish(budget, "failed", resolved=True)
    assert resolved.settled and budget.spent == 1


def test_external_effect_expiry_stays_uncertain_and_dispatch_is_forbidden():
    with pytest.raises(TransitionError, match="effectful_fixture_forbidden"):
        claim(ActivationState(effect="external"))
    a, lease, budget = claim()
    a = replace(a, effect="external")
    a, lease, remaining = a.terminal(lease, budget, "expired", now=lease.expires_at, run=RUN)
    assert a.status == "uncertain" and lease.status == "uncertain" and remaining == budget


def test_cancellation_and_abstention_are_not_retryable():
    run = RUN.cancel(expected_revision=0)
    assert run.status == "cancelled" and run.revision == 1
    with pytest.raises(TransitionError, match="run_revision_conflict"):
        run.cancel(expected_revision=0)
    assert ActivationState().cancel_unclaimed().status == "cancelled"
    a, lease, budget = claim()
    a, lease, budget = a.terminal(lease, budget, "abstained", now=NOW, run=RUN, authority=WORKER, retryable=True)
    assert a.status == "abstained" and lease.settled and budget.spent == 1
    with pytest.raises(TransitionError, match="terminal_attempt_conflict"):
        lease.finish(budget, "succeeded")


def test_success_requires_live_authority_and_lease():
    a, lease, budget = claim()
    for authority, now, reason in [(None, NOW, "worker_unauthorized"),
        (WORKER.revoke(), NOW, "worker_revoked"), (WORKER, lease.expires_at, "lease_expired")]:
        with pytest.raises(TransitionError, match=reason):
            a.terminal(lease, budget, "succeeded", now=now, run=RUN, authority=authority)
    assert a.terminal(lease, budget, "succeeded", now=NOW, run=RUN, authority=WORKER)[0].status == "succeeded"


@pytest.mark.parametrize("budget", [(0, 0, 0), (1, 1, 1), (True, 0, 0), (1, -1, 0)])
def test_invalid_budget_state_rejects(budget):
    with pytest.raises(TransitionError):
        RunBudget(*budget)


def test_naive_clock_and_premature_expiry_reject():
    with pytest.raises(TransitionError, match="timezone_required"):
        AttemptLease.issue("a", "worker", 1, NOW.replace(tzinfo=None), DEADLINE, 30)
    a, lease, budget = claim()
    with pytest.raises(TransitionError, match="lease_not_expired"):
        a.terminal(lease, budget, "expired", now=NOW, run=RUN)
