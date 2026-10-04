import json
from concurrent.futures import ThreadPoolExecutor
from threading import Event

import pytest
from amphora_agent_planning.budget import BudgetPolicy
from amphora_agent_planning.orchestration import PlanningRunner
from amphora_agent_planning.providers import FixtureProvider

pytestmark = pytest.mark.postgres


def policy(s, units=40):
    context = s.snapshot.document().context.model_dump(mode="json")
    raw = {key: context[key] for key in ("model", "prompt", "policy", "output_schema", "allowed_actions", "limits")}
    raw.update(format="planning-budget-policy.v1", per_attempt_accounting_units=units)
    return BudgetPolicy.from_bytes(json.dumps(raw).encode())


@pytest.mark.parametrize("variant,reason,calls", [
    ("proposal", "proposed", 1), ("abstain", "abstained", 1),
    ("malformed", "attempt_limit", 2), ("unavailable", "attempt_limit", 2),
    ("interrupted", "attempt_limit", 2), ("invented_action", "attempt_limit", 2),
])
def test_bounded_outcomes_preserve_context_and_exact_replay(stored, variant, reason, calls):
    s = stored
    invoked = []
    class Counted:
        def supports(self, model):
            return True
        def reply(self, binding):
            invoked.append(binding)
            return FixtureProvider(variant).reply(binding)
    runner = PlanningRunner(s.engine, Counted(), timeout_seconds=30)
    result = runner.run(s.principal, s.snapshot, policy(s))
    assert result.stop_reason == reason and len(result.attempts) == calls
    assert [b.ordinal for b in invoked] == list(range(1, calls + 1))
    assert all(b.request.canonical == s.snapshot.canonical for b in invoked)
    assert runner.run(s.principal, s.snapshot, policy(s)) == result
    assert len(invoked) == calls
    assert result.latest == result.attempts[-1]


def test_unknown_attempt_consumes_budget_and_stops_retry(stored):
    s = stored
    runner = PlanningRunner(s.engine, FixtureProvider("interrupted"), timeout_seconds=30)
    result = runner.run(s.principal, s.snapshot, policy(s, units=60))
    assert result.stop_reason == "accounting_budget_exhausted"
    assert len(result.attempts) == 1 and result.latest.observation.document().status == "unknown"
    assert runner.journal.read_attempt(s.principal, s.second.reference()) is None


def test_competing_runner_returns_pending_without_waiting_for_adapter(stored):
    s = stored
    entered, released = Event(), Event()
    def barrier():
        entered.set()
        assert released.wait(10)
    runner = PlanningRunner(s.engine, FixtureProvider("delayed", barrier), timeout_seconds=30)
    with ThreadPoolExecutor(max_workers=1) as pool:
        first = pool.submit(runner.run, s.principal, s.snapshot, policy(s))
        try:
            assert entered.wait(5)
            concurrent = runner.run(s.principal, s.snapshot, policy(s))
            assert concurrent.stop_reason == "attempt_pending"
            assert concurrent.latest.observation is None
        finally:
            released.set()
        assert first.result(5).stop_reason == "abstained"


def test_adapter_preflight_exception_is_redacted_and_bounded(stored):
    s = stored
    class Broken:
        def supports(self, model):
            raise RuntimeError("secret-do-not-retain")
    runner = PlanningRunner(s.engine, Broken(), timeout_seconds=30)
    result = runner.run(s.principal, s.snapshot, policy(s))
    assert result.stop_reason == "attempt_limit"
    assert all(a.observation.document().reason_code == "adapter_failure" for a in result.attempts)
    assert all(b"secret-do-not-retain" not in a.observation.canonical for a in result.attempts)


def test_invalid_timeout_is_rejected_before_any_request_write(stored):
    with pytest.raises(ValueError, match="dispatch_timeout"):
        PlanningRunner(stored.engine, FixtureProvider("abstain"), timeout_seconds=True)
    assert stored.journal.read_request(stored.principal, stored.snapshot.document().reference) is None


def test_explicit_provider_policy_rejection_stops_without_reply(stored):
    s = stored
    class Unsupported:
        def supports(self, model):
            return False
        def reply(self, binding):
            raise AssertionError("Unsupported provider must not be called")
    runner = PlanningRunner(s.engine, Unsupported(), timeout_seconds=30)
    result = runner.run(s.principal, s.snapshot, policy(s))
    assert result.stop_reason == "policy_rejected" and len(result.attempts) == 1
    assert result.latest.observation.document().reason_code == "provider_or_profile_mismatch"
