"""One bounded pure invocation, using public owner clients and tool-owned computation."""

import hashlib
import json
import os
import uuid
from pathlib import Path
from typing import Annotated, Literal

from amphora_contracts_artifacts import ContentDescriptor
from amphora_contracts_core import Digest, Identifier, Scope, SchemaRef, WireModel
from amphora_contracts_runtime import CompleteInvocation
from amphora_contracts_tools import Completion, LockEntry
from pydantic import Field, TypeAdapter

from .attempts import ToolAttemptContext
from .clients import ArtifactClient, RuntimeClient
from .commands import WorkerIdentity
from .failures import ExecutionFailure
from .execution_profiles import StructuralExecutionProfile
from .transport import HttpTransport, ProtocolError


class ToolInputRejected(ValueError):
    def __init__(self, reason_code):
        # Tool adapters provide a safe, bounded vocabulary instead of payload diagnostics.
        self.reason_code = TypeAdapter(Identifier).validate_python(reason_code)
        super().__init__(reason_code)


class ServiceEndpoint(WireModel):
    endpoint: str
    token_env: Annotated[str, Field(pattern=r"^[A-Z][A-Z0-9_]{0,127}$")]

    def transport(self):
        return HttpTransport(self.endpoint, os.environ[self.token_env])


class StructuralProfileConfig(WireModel):
    profile: Literal["supplied-finite-structure-v1"]
    scope: Scope
    release: LockEntry
    semantic_profile: SchemaRef
    context: Literal["supplied-finite-molecules"]

    def to_domain(self):
        return StructuralExecutionProfile.from_record(self.model_dump(mode="json"))


class WorkerConfig(WireModel):
    actor_id: Identifier
    scope: Scope
    run_id: Identifier
    image_sha256: Digest
    execution_profile: StructuralProfileConfig | None = None
    runtime: ServiceEndpoint
    artifacts: ServiceEndpoint
    lease_seconds: Annotated[int, Field(ge=10, le=300)] = 30
    max_clock_skew_seconds: Annotated[float, Field(ge=0, le=5)] = 1.0


class PureToolWorker:
    def __init__(self, runtime, artifacts, descriptor, compute, *, lease_seconds=30, skew_seconds=1.0, execution_profile=None):
        tool = descriptor.tool
        if execution_profile is None:
            authority_allowed = descriptor.authority_ceiling == "synthetic_only"
        else:
            try:
                if type(execution_profile) is not StructuralExecutionProfile:
                    raise ValueError("unknown_execution_profile")
                execution_profile.require_descriptor(descriptor)
                execution_profile.require_scope(runtime.identity.scope)
            except ValueError as error:
                raise ProtocolError("unsupported_worker_profile") from error
            authority_allowed = True
        if (tool.side_effects != "pure" or not authority_allowed
            or len(tool.inputs) != 1 or len(tool.outputs) != 1 or not tool.inputs[0].required
            or not tool.outputs[0].required or tool.checkpoint_schema is not None
            or descriptor.checkpoint.mode != "none" or descriptor.egress.mode != "deny"):
            raise ProtocolError("unsupported_worker_profile")
        if runtime.identity != artifacts.identity:
            raise ProtocolError("worker_identity_mismatch")
        self.runtime, self.artifacts = runtime, artifacts
        self.tool, self.compute = tool, compute
        self.lease_seconds, self.skew_seconds = lease_seconds, skew_seconds

    def _execute(self, context):
        invocation = context.invocation
        if (invocation.checkpoint is not None or len(invocation.inputs) != 1
            or invocation.inputs[0].port != self.tool.inputs[0].name
            or invocation.inputs[0].artifact.schema_ref != self.tool.inputs[0].schema_ref
            or invocation.inputs[0].artifact.media_type != "application/json"):
            return {"status": "failed", "reason_code": "tool_input_binding_mismatch", "retryable": False}
        context.refresh()
        payload = self.artifacts.read(invocation.inputs[0].artifact)
        context.check()
        try:
            output = self.compute(payload)
        except ToolInputRejected as error:
            return {"status": "failed", "reason_code": error.reason_code, "retryable": False}
        except ValueError:
            return {"status": "failed", "reason_code": "invalid_tool_input", "retryable": False}
        context.check()
        if not isinstance(output, bytes) or len(output) > 262144:
            raise ProtocolError("invalid_tool_output")
        content = ContentDescriptor(sha256=hashlib.sha256(output).hexdigest(), size_bytes=len(output),
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
        result = self.runtime.claim(run_id, self.tool.binding, "claim-" + uuid.uuid4().hex,
                                    lease_seconds=self.lease_seconds)
        if result.outcome.status == "no_eligible_work":
            return {"status": "no_eligible_work"}
        context = ToolAttemptContext(self.runtime, result.outcome, self.lease_seconds,
                                     skew_seconds=self.skew_seconds)
        try:
            outcome = self._execute(context)
        except ProtocolError as error:
            # A pure attempt may fail retryably; a lost/uncertain lease cannot report it.
            context.refresh()
            outcome = ExecutionFailure.from_protocol(error).to_wire()
        context.refresh()
        invocation = context.invocation
        completion = Completion.model_validate_json(json.dumps({"schema_version": "1",
            "invocation_id": invocation.invocation_id, "attempt_id": invocation.attempt_id,
            "fence": invocation.fence, "outcome": outcome}))
        # Completion ambiguity must never be followed by a contradictory failure report.
        receipt = self.runtime.complete(CompleteInvocation(run_id=run_id, completion=completion),
            "complete-" + invocation.attempt_id, guard=context.check)
        return {"status": "completion_accepted", "outcome": outcome["status"],
                "operation_id": receipt.outcome.binding.operation_id}


def run_worker(config_path, descriptor_factory, compute):
    config = WorkerConfig.model_validate_json(Path(config_path).read_bytes())
    identity = WorkerIdentity(config.actor_id, config.scope)
    profile_options = {} if config.execution_profile is None else {
        "execution_profile": config.execution_profile.to_domain()
    }
    worker = PureToolWorker(RuntimeClient(config.runtime.transport(), identity),
        ArtifactClient(config.artifacts.transport(), identity), descriptor_factory(config.image_sha256), compute,
        lease_seconds=config.lease_seconds, skew_seconds=config.max_clock_skew_seconds,
        **profile_options)
    return worker.run_once(config.run_id)
