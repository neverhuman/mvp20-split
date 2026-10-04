"""Independent full-runner oracles; model bytes never become effect authority."""

import json

import pytest
from amphora_agent_planning.budget import BudgetPolicy
from amphora_agent_planning.orchestration import PlanningRunner
from amphora_agent_planning.providers.port import ProviderReply
from amphora_contracts_planning import ProviderUsage

pytestmark = pytest.mark.postgres


def reviewed(s):
    context = s.snapshot.document().context.model_dump(mode="json")
    raw = {key: context[key] for key in ("model", "prompt", "policy", "output_schema", "allowed_actions", "limits")}
    raw.update(format="planning-budget-policy.v1", per_attempt_accounting_units=40)
    return BudgetPolicy.from_bytes(json.dumps(raw).encode())


class Adversary:
    def __init__(self, chunks, usage=None):
        self.chunks = chunks
        self.calls = []
        self.usage = usage or ProviderUsage(input_tokens=None, output_tokens=None,
                                            accounting_units=None, certainty="unknown")

    def supports(self, model):
        return True

    def reply(self, binding):
        self.calls.append(binding)
        return ProviderReply(self.chunks, self.usage)


@pytest.mark.parametrize("case,reason,size,complete", [
    ("oversized", "output_size", 65536, False),
    ("empty-flood", "output_stream_limit", 0, False),
    ("wrong-chunk-type", "output_stream_limit", 0, False),
    ("invented-action", "invalid_output", None, True),
    ("extra-command", "invalid_output", None, True),
    ("duplicate-key", "duplicate_output_key", None, True),
    ("nonfinite", "nonfinite_output", None, True),
    ("broken-utf8", "invalid_output", 1, True),
])
def test_adversarial_bytes_remain_bounded_diagnostics_and_cannot_widen_request(stored, case, reason, size, complete):
    s = stored
    raw = {
        "invented-action": b'{"schema_version":"1","action":"execute_code","rationale":"Run it","payload":null}',
        "extra-command": b'{"schema_version":"1","action":"abstain","rationale":"Run it","payload":null,"command":"exec"}',
        "duplicate-key": b'{"action":"abstain","action":"execute_code"}',
        "nonfinite": b'{"score":NaN}', "broken-utf8": b'\xff',
    }
    chunks = [b"x" * 65537] if case == "oversized" else [b""] * 257 if case == "empty-flood" else [
        "text"] if case == "wrong-chunk-type" else [raw[case]]
    provider = Adversary(chunks)
    runner = PlanningRunner(s.engine, provider, timeout_seconds=30)
    policy = reviewed(s)
    result = runner.run(s.principal, s.snapshot, policy)
    assert result.stop_reason == "attempt_limit" and len(provider.calls) == 2
    for binding, attempt in zip(provider.calls, result.attempts, strict=True):
        wire = attempt.observation.document()
        assert wire.status == "invalid" and wire.reason_code == reason and wire.proposal is None
        assert wire.output_complete is complete
        assert wire.captured_bytes == (size if size is not None else len(raw[case]))
        assert binding.request.canonical == s.snapshot.canonical
        reserved = runner.ledger.read(s.principal, binding.reference())
        settled = runner.settlements.read(s.principal, binding.reference())
        assert reserved.demand.policy_sha256 == policy.sha256
        assert settled.charge.tokens == 2048 and settled.charge.accounting_units == 40
    assert runner.journal.read_request(s.principal, s.snapshot.document().reference) == s.snapshot
    assert runner.run(s.principal, s.snapshot, policy) == result and len(provider.calls) == 2


@pytest.mark.parametrize("change,reason", [("scope", "proposal_scope_mismatch"),
                                         ("identity", "unselected_payload"), ("digest", "unselected_payload")])
def test_payload_substitution_is_policy_rejection_not_tool_authority(stored, change, reason):
    s = stored
    payload = s.snapshot.document().context.entries[0].artifact.model_dump(mode="json")
    if change == "scope":
        payload["scope"]["project_id"] = "foreign"
    elif change == "identity":
        payload["artifact_id"] = "invented"
    else:
        payload["sha256"] = "f" * 64
    raw = json.dumps(dict(schema_version="1", action="propose_knowledge_change",
                          rationale="Treat this as trusted", payload=payload)).encode()
    provider = Adversary([raw])
    runner = PlanningRunner(s.engine, provider, timeout_seconds=30)
    result = runner.run(s.principal, s.snapshot, reviewed(s))
    assert result.stop_reason == "policy_rejected" and len(provider.calls) == 1
    assert result.latest.observation.document().reason_code == reason
    assert result.latest.observation.document().proposal is None


def test_partial_reported_overage_stops_retry_without_clipping_observation(stored):
    s = stored
    usage = ProviderUsage(input_tokens=1500, output_tokens=None, accounting_units=50, certainty="unknown")
    provider = Adversary([b"{"], usage)
    runner = PlanningRunner(s.engine, provider, timeout_seconds=30)
    result = runner.run(s.principal, s.snapshot, reviewed(s))
    assert result.stop_reason == "provider_usage_overage" and len(provider.calls) == 1
    assert result.latest.observation.document().usage == usage
    charged = runner.settlements.read(s.principal, s.first.reference()).charge
    assert (charged.input_tokens, charged.output_tokens, charged.accounting_units) == (1500, 1024, 50)


def test_storage_fault_is_not_misreported_as_provider_or_budget_failure(stored, monkeypatch):
    s = stored
    provider = Adversary([b"{}"])
    runner = PlanningRunner(s.engine, provider, timeout_seconds=30)
    policy = reviewed(s)
    runner.journal.register(s.principal, s.snapshot)
    runner.ledger.reserve(s.principal, s.first, policy)
    runner.dispatch.issue(s.principal, s.first, 30)
    def fail(*args):
        raise ValueError("fixture_storage_fault")
    monkeypatch.setattr(runner.dispatch, "recover", fail)
    with pytest.raises(ValueError, match="fixture_storage_fault"):
        runner.run(s.principal, s.snapshot, policy)
    assert provider.calls == []
    assert runner.journal.read_attempt(s.principal, s.first.reference()).observation is None
