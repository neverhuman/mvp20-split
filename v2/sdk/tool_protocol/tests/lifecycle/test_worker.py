"""Scripted lifecycle oracles; real owner/process acceptance remains separate."""

import hashlib
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace as NS

import pytest
from amphora_contracts_artifacts import FinalizedReceipt, UploadReceipt
from amphora_contracts_core import ArtifactRef, Scope
from amphora_contracts_tools import Invocation, ReleaseDescriptor
from amphora_tool_protocol import (
    CommandRejected,
    ProtocolError,
    PureToolWorker,
    ToolAttemptContext,
    ToolInputRejected,
    TransportLost,
    WorkerIdentity,
)

ROOT = Path(__file__).resolve().parents[4]
DESCRIPTOR = ReleaseDescriptor.model_validate_json(json.dumps(json.loads(
    (ROOT / "contracts/fixtures/v1/tool_releases.json").read_bytes())[0]["descriptor"]))
IDENTITY = WorkerIdentity("worker", Scope(tenant_id="fixture", project_id="worker"))
INPUT = b'{"values":[1]}'


class TestClock:
    __test__ = False
    elapsed = 0

    def utc(self):
        return datetime(2026, 9, 28, tzinfo=UTC) + timedelta(seconds=self.elapsed)

    def monotonic(self):
        return self.elapsed


class Runtime:
    identity = IDENTITY

    def __init__(self):
        self.tool = DESCRIPTOR.tool
        self.renewals = 0
        self.completions = []
        self.changed_fence = False
        self.no_work = False
        self.fail_completion = False
        self.clock = None
        self.input = ArtifactRef(artifact_id="input", scope=IDENTITY.scope,
            sha256=hashlib.sha256(INPUT).hexdigest(), size_bytes=len(INPUT), media_type="application/json",
            schema_ref=self.tool.inputs[0].schema_ref)
        self.invocation = Invocation.model_validate_json(json.dumps({"schema_version": "1",
            "scope": IDENTITY.scope.model_dump(), "run_id": "run", "node_id": "node", "activation_id": "activation",
            "invocation_id": "invocation", "attempt_id": "attempt", "fence": 1,
            "tool": self.tool.binding.model_dump(), "inputs": [{"port": self.tool.inputs[0].name,
            "artifact": self.input.model_dump()}], "timeout_seconds": 60, "grant_id": "grant"}))

    def now(self):
        return self.clock.utc() if self.clock else datetime.now(UTC)

    def claim(self, *_args, **_kwargs):
        return NS(outcome=NS(status="no_eligible_work" if self.no_work else "claimed", invocation=self.invocation,
            lease_expires_at=(self.now() + timedelta(seconds=30)).isoformat().replace("+00:00", "Z")))

    def renew(self, _attempt, _command_id, **kwargs):
        kwargs["guard"]()
        self.renewals += 1
        return NS(outcome=NS(committed=NS(revision=self.renewals)))

    def run(self, _run_id):
        return NS(status="running", revision=self.renewals, activations=[NS(invocation_id="invocation", status="leased",
            fence=2 if self.changed_fence else 1, latest_attempt=NS(attempt_id="attempt", fence=1,
                worker_id="worker", status="leased", lease_expires_at=(self.now() + timedelta(seconds=20)).isoformat(),
                deadline=(self.now() + timedelta(seconds=60)).isoformat()))])

    def complete(self, completion, command_id, **kwargs):
        kwargs["guard"]()
        self.completions.append((completion, command_id))
        if self.fail_completion:
            raise TransportLost("completion_unknown")
        return NS(outcome=NS(binding=NS(operation_id="completed-operation")))


class Artifacts:
    identity = IDENTITY

    def __init__(self):
        self.stages = []
        self.fail_stream = False

    def read(self, _reference):
        self.stages.append("read")
        return INPUT

    def begin(self, content, _command_id, **kwargs):
        kwargs["guard"]()
        self.stages.append("begin")
        return UploadReceipt(upload_id="output-upload", scope=IDENTITY.scope, content=content)

    def stream(self, _upload, _payload, **kwargs):
        kwargs["guard"]()
        self.stages.append("stream")
        if self.fail_stream:
            raise TransportLost("stream_unknown")

    def finalize(self, upload, _command_id, **kwargs):
        kwargs["guard"]()
        self.stages.append("finalize")
        return FinalizedReceipt(upload_id=upload.upload_id,
            artifact=ArtifactRef(artifact_id="output", scope=IDENTITY.scope, **upload.content.model_dump()))


def test_worker_uses_public_stages_and_same_attempt_completion():
    runtime, artifacts = Runtime(), Artifacts()
    worker = PureToolWorker(runtime, artifacts, DESCRIPTOR, lambda _body: b'{"values":[3]}')
    assert worker.run_once("run") == {"status": "completion_accepted", "outcome": "succeeded",
                                      "operation_id": "completed-operation"}
    assert artifacts.stages == ["read", "begin", "stream", "finalize"]
    assert runtime.renewals == 5
    completion, key = runtime.completions[0]
    assert key == "complete-attempt" and completion.completion.attempt_id == "attempt"
    assert completion.completion.fence == 1 and completion.completion.outcome.outputs[0].artifact.artifact_id == "output"


def test_no_work_and_invalid_input_do_not_publish():
    runtime, artifacts = Runtime(), Artifacts()
    runtime.no_work = True
    worker = PureToolWorker(runtime, artifacts, DESCRIPTOR, lambda _body: b"output")
    assert worker.run_once("run") == {"status": "no_eligible_work"}
    assert not artifacts.stages and not runtime.completions
    runtime.no_work = False
    def invalid(_body):
        raise ValueError("invalid_input")
    worker.compute = invalid
    assert worker.run_once("run")["outcome"] == "failed"
    assert artifacts.stages == ["read"]
    assert runtime.completions[0][0].completion.outcome.retryable is False


def test_stream_loss_never_finalizes_and_completion_loss_never_contradicts():
    runtime, artifacts = Runtime(), Artifacts()
    artifacts.fail_stream = True
    worker = PureToolWorker(runtime, artifacts, DESCRIPTOR, lambda _body: b"{}")
    assert worker.run_once("run")["outcome"] == "failed"
    assert artifacts.stages == ["read", "begin", "stream"]
    assert runtime.completions[0][0].completion.outcome.retryable is True
    runtime, artifacts = Runtime(), Artifacts()
    runtime.fail_completion = True
    with pytest.raises(TransportLost, match="completion_unknown"):
        PureToolWorker(runtime, artifacts, DESCRIPTOR, lambda _body: b"{}").run_once("run")
    assert len(runtime.completions) == 1
    assert runtime.completions[0][0].completion.outcome.status == "succeeded"


def test_changed_fence_stops_all_publication():
    runtime, artifacts = Runtime(), Artifacts()
    runtime.changed_fence = True
    with pytest.raises(ProtocolError, match="attempt_authority_lost"):
        PureToolWorker(runtime, artifacts, DESCRIPTOR, lambda _body: b"{}").run_once("run")
    assert artifacts.stages == [] and runtime.completions == []


def test_lease_is_monotonic_and_capped_by_observed_expiry():
    runtime = Runtime()
    runtime.clock = TestClock()
    context = ToolAttemptContext(runtime, runtime.claim().outcome, clock=runtime.clock)
    renewal = context.refresh()
    assert (renewal.expires_at - runtime.clock.utc()).total_seconds() == 20
    runtime.clock.elapsed = 18
    context.check()
    runtime.clock.elapsed = 19  # One-second configured skew allowance.
    with pytest.raises(ProtocolError, match="attempt_authority_lost"):
        context.check()
    runtime.clock.elapsed = 0
    with pytest.raises(ProtocolError, match="attempt_authority_lost"):
        context.refresh()


@pytest.mark.parametrize("lease,skew", [(0, 1), (301, 1), (True, 1), (30, -1), (30, 6), (30, float("nan")), (30, True)])
def test_invalid_direct_lease_profiles_never_renew(lease, skew):
    runtime = Runtime()
    with pytest.raises(ProtocolError, match="invalid_lease_profile"):
        ToolAttemptContext(runtime, runtime.claim().outcome, lease, skew_seconds=skew)
    assert runtime.renewals == 0


@pytest.mark.parametrize("reason,retryable", [("content_schema_mismatch", False), ("unsupported_content", False),
                                             ("capacity_exhausted", True)])
def test_publication_rejections_preserve_terminal_or_capacity_policy(reason, retryable):
    runtime, artifacts = Runtime(), Artifacts()
    def rejected(*_args, **_kwargs):
        raise CommandRejected(reason)
    artifacts.begin = rejected
    result = PureToolWorker(runtime, artifacts, DESCRIPTOR, lambda _body: b"{}").run_once("run")
    assert result["outcome"] == "failed"
    outcome = runtime.completions[0][0].completion.outcome
    assert outcome.reason_code == reason and outcome.retryable is retryable
    assert artifacts.stages == ["read"]


def test_safe_tool_error_and_protocol_violation_are_not_retried():
    runtime, artifacts = Runtime(), Artifacts()
    def rejected(_body):
        raise ToolInputRejected("invalid_sequence_symbol")
    PureToolWorker(runtime, artifacts, DESCRIPTOR, rejected).run_once("run")
    outcome = runtime.completions[0][0].completion.outcome
    assert outcome.reason_code == "invalid_sequence_symbol" and outcome.retryable is False
    runtime, artifacts = Runtime(), Artifacts()
    PureToolWorker(runtime, artifacts, DESCRIPTOR, lambda _body: "not-bytes").run_once("run")
    outcome = runtime.completions[0][0].completion.outcome
    assert outcome.reason_code == "tool_protocol_violation" and outcome.retryable is False
    assert artifacts.stages == ["read"]


def test_expired_computation_never_publishes(monkeypatch):
    runtime, artifacts = Runtime(), Artifacts()
    clock = TestClock()
    runtime.clock = clock
    import amphora_tool_protocol.worker as worker_module
    constructor = worker_module.ToolAttemptContext
    monkeypatch.setattr(worker_module, "ToolAttemptContext", lambda *args, **kwargs: constructor(*args, clock=clock, **kwargs))
    def slow(_body):
        clock.elapsed += 30
        return b"{}"
    with pytest.raises(ProtocolError, match="attempt_authority_lost"):
        PureToolWorker(runtime, artifacts, DESCRIPTOR, slow).run_once("run")
    assert artifacts.stages == ["read"] and runtime.completions == []


def test_misbound_input_never_runs_kernel_and_ineligible_profiles_never_claim():
    runtime, artifacts = Runtime(), Artifacts()
    runtime.invocation = runtime.invocation.model_copy(update={"inputs": ()})
    def forbidden(_payload):
        raise AssertionError("Mismatched input cannot invoke computation")
    PureToolWorker(runtime, artifacts, DESCRIPTOR, forbidden).run_once("run")
    assert artifacts.stages == []
    assert runtime.completions[0][0].completion.outcome.reason_code == "tool_input_binding_mismatch"
    external = DESCRIPTOR.model_copy(update={"tool": DESCRIPTOR.tool.model_copy(update={"side_effects": "external"})})
    with pytest.raises(ProtocolError, match="unsupported_worker_profile"):
        PureToolWorker(runtime, artifacts, external, forbidden)
    artifacts.identity = WorkerIdentity("other", IDENTITY.scope)
    with pytest.raises(ProtocolError, match="worker_identity_mismatch"):
        PureToolWorker(runtime, artifacts, DESCRIPTOR, forbidden)
