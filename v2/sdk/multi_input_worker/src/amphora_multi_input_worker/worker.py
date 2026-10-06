"""Opt-in multi-input pure worker using only the existing public owner clients."""

import json
import uuid
from hashlib import sha256
from pathlib import Path

from amphora_contracts_artifacts import ContentDescriptor
from amphora_contracts_runtime import CompleteInvocation
from amphora_contracts_tools import Completion, ReleaseDescriptor
from amphora_tool_protocol import (
    ArtifactClient,
    CommandRejected,
    CommandUnresolved,
    ProtocolError,
    RuntimeClient,
    ToolAttemptContext,
    ToolInputRejected,
    TransportLost,
    WorkerConfig,
    WorkerIdentity,
)

from .inputs import MAX_BYTES, InputBundle, ResolvedInput


def failure_outcome(error):
    if isinstance(error, CommandRejected):
        return {"status": "failed", "reason_code": error.reason_code, "retryable": error.reason_code == "capacity_exhausted"}
    retryable = isinstance(error, (TransportLost, CommandUnresolved)) or str(error) in {"stream_unavailable", "run_unavailable"}
    return {"status": "failed", "reason_code": "tool_transport_failure" if retryable else "tool_protocol_violation", "retryable": retryable}


class MultiInputToolWorker:
    def __init__(self, runtime, artifacts, descriptor, compute, *, lease_seconds=30, skew_seconds=1.0):
        descriptor = ReleaseDescriptor.model_validate_json(descriptor.model_dump_json())
        tool = descriptor.tool
        if (tool.side_effects != "pure" or descriptor.authority_ceiling != "synthetic_only"
            or not 2 <= len(tool.inputs) <= 16 or len({p.name for p in tool.inputs}) != len(tool.inputs)
            or not all(p.required for p in tool.inputs) or len(tool.outputs) != 1 or not tool.outputs[0].required
            or tool.checkpoint_schema is not None or descriptor.checkpoint.mode != "none" or descriptor.egress.mode != "deny"):
            raise ProtocolError("unsupported_multi_input_worker_profile")
        if runtime.identity != artifacts.identity:
            raise ProtocolError("worker_identity_mismatch")
        self.runtime, self.artifacts, self.tool, self.compute = runtime, artifacts, tool, compute
        self.lease_seconds, self.skew_seconds = lease_seconds, skew_seconds

    def _execute(self, context):
        invocation = context.invocation
        supplied = {item.port: item.artifact for item in invocation.inputs}
        expected = {port.name: port.schema_ref for port in self.tool.inputs}
        if (invocation.checkpoint is not None or invocation.tool != self.tool.binding
            or invocation.scope != self.runtime.identity.scope
            or len(supplied) != len(invocation.inputs) or supplied.keys() != expected.keys()
            or any(ref.scope != invocation.scope or ref.schema_ref != expected[name] or ref.media_type != "application/json"
                   for name, ref in supplied.items()) or sum(ref.size_bytes for ref in supplied.values()) > MAX_BYTES):
            return {"status": "failed", "reason_code": "tool_input_binding_mismatch", "retryable": False}
        inputs = []
        for port in self.tool.inputs:
            context.refresh()
            reference = supplied[port.name]
            data = self.artifacts.read(reference)
            context.check()
            inputs.append(ResolvedInput(port.name, reference, data))
        try:
            output = self.compute(InputBundle(tuple(inputs)))
        except ToolInputRejected as error:
            return {"status": "failed", "reason_code": error.reason_code, "retryable": False}
        except ProtocolError:
            raise
        except ValueError:
            return {"status": "failed", "reason_code": "invalid_tool_input", "retryable": False}
        context.check()
        if type(output) is not bytes or len(output) > MAX_BYTES:
            raise ProtocolError("invalid_tool_output")
        content = ContentDescriptor(sha256=sha256(output).hexdigest(), size_bytes=len(output),
                                    media_type="application/json", schema_ref=self.tool.outputs[0].schema_ref)
        context.refresh()
        upload = self.artifacts.begin(content, "upload-" + invocation.attempt_id, guard=context.check)
        context.refresh()
        self.artifacts.stream(upload, output, guard=context.check)
        context.refresh()
        finalized = self.artifacts.finalize(upload, "finalize-" + invocation.attempt_id, guard=context.check)
        return {"status": "succeeded", "outputs": [{"port": self.tool.outputs[0].name,
                "artifact": finalized.artifact.model_dump(mode="json")}], "checkpoint": None}

    def run_once(self, run_id):
        result = self.runtime.claim(run_id, self.tool.binding, "claim-" + uuid.uuid4().hex, lease_seconds=self.lease_seconds)
        if result.outcome.status == "no_eligible_work":
            return {"status": "no_eligible_work"}
        context = ToolAttemptContext(self.runtime, result.outcome, self.lease_seconds, skew_seconds=self.skew_seconds)
        if context.invocation.run_id != run_id:
            raise ProtocolError("worker_run_mismatch")
        try:
            outcome = self._execute(context)
        except ProtocolError as error:
            context.refresh()  # Lost/uncertain authority must prevent a failure report too.
            outcome = failure_outcome(error)
        context.refresh()
        invocation = context.invocation
        completion = Completion.model_validate_json(json.dumps({"schema_version": "1", "invocation_id": invocation.invocation_id,
                                                                 "attempt_id": invocation.attempt_id, "fence": invocation.fence,
                                                                 "outcome": outcome}))
        # An ambiguous completion must escape; never send a contradictory fallback outcome.
        receipt = self.runtime.complete(CompleteInvocation(run_id=run_id, completion=completion),
                                        "complete-" + invocation.attempt_id, guard=context.check)
        return {"status": "completion_accepted", "outcome": outcome["status"], "operation_id": receipt.outcome.binding.operation_id}


def run_multi_input_worker(config_path, descriptor_factory, compute):
    config = WorkerConfig.model_validate_json(Path(config_path).read_bytes())
    identity = WorkerIdentity(config.actor_id, config.scope)
    worker = MultiInputToolWorker(RuntimeClient(config.runtime.transport(), identity),
                                  ArtifactClient(config.artifacts.transport(), identity),
                                  descriptor_factory(config.image_sha256), compute,
                                  lease_seconds=config.lease_seconds, skew_seconds=config.max_clock_skew_seconds)
    return worker.run_once(config.run_id)
