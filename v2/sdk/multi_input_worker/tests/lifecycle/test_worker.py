from dataclasses import replace

import pytest
from amphora_multi_input_worker import InputBundle, MultiInputToolWorker, ResolvedInput
from amphora_tool_protocol import (
    CommandRejected,
    ProtocolError,
    PureToolWorker,
    ToolInputRejected,
    TransportLost,
)


def test_named_inputs_retain_verified_bytes_and_metadata(descriptor, peers):
    runtime, artifacts = peers
    observed = []

    def compute(inputs):
        observed.append(inputs)
        assert inputs["parameters"].data == b'{"x":2}'
        assert inputs["policy"].artifact == runtime.invocation.inputs[1].artifact
        return b'{"result":4}'

    assert MultiInputToolWorker(runtime, artifacts, descriptor, compute).run_once("run")["outcome"] == "succeeded"
    assert artifacts.events == ["read:parameters", "read:policy", "begin:upload-attempt", "stream", "finalize:finalize-attempt"]
    assert len(runtime.completions) == 1 and runtime.completions[0][1] == "complete-attempt"
    assert isinstance(observed[0], InputBundle)


@pytest.mark.parametrize("case", ["missing", "duplicate", "schema", "scope", "size", "tool"])
def test_complete_binding_checked_before_any_read(descriptor, peers, case):
    runtime, artifacts = peers
    invocation = runtime.invocation
    values = list(invocation.inputs)
    if case == "missing":
        values.pop()
    elif case == "duplicate":
        values.append(values[0])
    elif case == "tool":
        invocation = invocation.model_copy(update={"tool": invocation.tool.model_copy(update={"image_sha256": "f" * 64})})
    else:
        ref = values[1].artifact
        update = {"schema_ref": ref.schema_ref.model_copy(update={"sha256": "f" * 64})} if case == "schema" else (
            {"scope": ref.scope.model_copy(update={"project_id": "other"})} if case == "scope" else {"size_bytes": 262144})
        values[1] = values[1].model_copy(update={"artifact": ref.model_copy(update=update)})
    runtime.invocation = invocation.model_copy(update={"inputs": tuple(values)})
    assert MultiInputToolWorker(runtime, artifacts, descriptor, lambda _inputs: b"{}").run_once("run")["outcome"] == "failed"
    assert artifacts.events == []
    assert runtime.completions[0][0].completion.outcome.reason_code == "tool_input_binding_mismatch"


def test_revocation_between_inputs_prevents_further_io_and_completion(descriptor, peers):
    runtime, artifacts = peers
    artifacts.revoke_after_read = True
    with pytest.raises(ProtocolError):
        MultiInputToolWorker(runtime, artifacts, descriptor, lambda _inputs: b"{}").run_once("run")
    assert artifacts.events == ["read:parameters"] and runtime.completions == []


def test_corrupt_input_is_terminal_without_publication(descriptor, peers):
    runtime, artifacts = peers
    artifacts.corrupt = True
    MultiInputToolWorker(runtime, artifacts, descriptor, lambda _inputs: b"{}").run_once("run")
    assert artifacts.events == ["read:parameters"]
    outcome = runtime.completions[0][0].completion.outcome
    assert outcome.reason_code == "tool_protocol_violation" and not outcome.retryable


@pytest.mark.parametrize("error,reason,retryable", [(TransportLost("stream_unknown"), "tool_transport_failure", True),
    (CommandRejected("capacity_exhausted"), "capacity_exhausted", True),
    (CommandRejected("permission_denied"), "permission_denied", False),
    (ProtocolError("stream_unavailable"), "tool_transport_failure", True)])
def test_transport_failure_preserves_classification(descriptor, peers, error, reason, retryable):
    runtime, artifacts = peers
    artifacts.stream_error = error
    MultiInputToolWorker(runtime, artifacts, descriptor, lambda _inputs: b"{}").run_once("run")
    outcome = runtime.completions[0][0].completion.outcome
    assert outcome.reason_code == reason and outcome.retryable == retryable
    assert not any(event.startswith("finalize") for event in artifacts.events)


def test_unknown_completion_never_sends_contradictory_failure(descriptor, peers):
    runtime, artifacts = peers
    runtime.completion_unknown = True
    with pytest.raises(TransportLost):
        MultiInputToolWorker(runtime, artifacts, descriptor, lambda _inputs: b"{}").run_once("run")
    assert len(runtime.completions) == 1
    assert runtime.completions[0][0].completion.outcome.status == "succeeded"


@pytest.mark.parametrize("error,reason", [(ToolInputRejected("fixture_rejected"), "fixture_rejected"),
                                        (ValueError("private detail"), "invalid_tool_input")])
def test_pure_callback_rejection_has_safe_terminal_outcome(descriptor, peers, error, reason):
    runtime, artifacts = peers

    def compute(_inputs):
        raise error

    MultiInputToolWorker(runtime, artifacts, descriptor, compute).run_once("run")
    assert artifacts.events == ["read:parameters", "read:policy"]
    assert runtime.completions[0][0].completion.outcome.reason_code == reason


def test_old_single_input_profile_does_not_silently_expand(descriptor, peers):
    runtime, artifacts = peers
    with pytest.raises(ProtocolError, match="unsupported_worker_profile"):
        PureToolWorker(runtime, artifacts, descriptor, lambda _inputs: b"{}")
    single = descriptor.model_copy(update={"tool": descriptor.tool.model_copy(update={"inputs": descriptor.tool.inputs[:1]})})
    with pytest.raises(ProtocolError, match="unsupported_multi_input_worker_profile"):
        MultiInputToolWorker(runtime, artifacts, single, lambda _inputs: b"{}")


def test_bundle_identity_and_lookup_invariants(peers):
    runtime, _artifacts = peers
    values = tuple(ResolvedInput(item.port, item.artifact, runtime.data[item.port]) for item in runtime.invocation.inputs)
    bundle = InputBundle(values)
    with pytest.raises(ProtocolError, match="tool_input_port_missing"):
        bundle["absent"]
    with pytest.raises(ProtocolError, match="tool_input_bundle_invalid"):
        InputBundle((values[0], values[0]))
    with pytest.raises(ProtocolError, match="tool_input_content_mismatch"):
        replace(values[0], data=b"wrong")


def test_no_work_or_wrong_run_never_reads(descriptor, peers):
    runtime, artifacts = peers
    worker = MultiInputToolWorker(runtime, artifacts, descriptor, lambda _inputs: b"{}")
    runtime.no_work = True
    assert worker.run_once("run") == {"status": "no_eligible_work"}
    runtime.no_work = False
    with pytest.raises(ProtocolError, match="worker_run_mismatch"):
        worker.run_once("different-run")
    assert not artifacts.events and not runtime.completions


def test_mixed_owner_clients_reject_before_claim(descriptor, peers):
    runtime, artifacts = peers
    artifacts.identity = replace(runtime.identity, actor_id="another-worker")
    with pytest.raises(ProtocolError, match="worker_identity_mismatch"):
        MultiInputToolWorker(runtime, artifacts, descriptor, lambda _inputs: b"{}")
    assert runtime.completions == [] and artifacts.events == []


@pytest.mark.parametrize("output", [b"x" * 262145, bytearray(b"{}")], ids=["oversized", "mutable_bytes"])
def test_invalid_callback_output_never_publishes(descriptor, peers, output):
    runtime, artifacts = peers
    MultiInputToolWorker(runtime, artifacts, descriptor, lambda _inputs: output).run_once("run")
    assert artifacts.events == ["read:parameters", "read:policy"]
    assert runtime.completions[0][0].completion.outcome.reason_code == "tool_protocol_violation"
