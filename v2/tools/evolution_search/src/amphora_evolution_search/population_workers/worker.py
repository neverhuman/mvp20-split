"""Reference-backed worker composed from public SDK clients and lease context.

Lifecycle adapted from v2/sdk/tool_protocol PureToolWorker; kept tool-owned because
that byte-in/byte-out convenience helper does not support child Artifact publication.
No private SDK/peer imports or new execution authority.
"""

import json
import uuid
from pathlib import Path

from amphora_contracts_runtime import CompleteInvocation
from amphora_contracts_search import ImplementationPin
from amphora_contracts_tools import Completion
from amphora_tool_protocol import (
    ArtifactClient, CommandRejected, CommandUnresolved, ProtocolError, RuntimeClient,
    ToolAttemptContext, TransportLost, WorkerConfig, WorkerIdentity,
)

from ..ranking import require
from .artifacts import PopulationArtifacts
from .capabilities import PopulationCapability
from .seed import SeedPreparation
from .slices import SeedSlices
from .methods import PrimaryMethod


class PopulationWorker:
    def __init__(self, runtime, artifacts, capability, image_sha256, *, lease_seconds=30, skew_seconds=1):
        require(runtime.identity == artifacts.identity, "population_worker_identity")
        self.runtime, self.artifacts, self.capability = runtime, artifacts, capability
        self.tool = capability.descriptor(image_sha256).tool
        self.implementation = ImplementationPin(name="numeric-population-steps", version=capability.release, sha256=image_sha256)
        self.lease_seconds, self.skew_seconds = lease_seconds, skew_seconds

    def execute(self, attempt):
        invocation = attempt.invocation
        if (invocation.checkpoint is not None or len(invocation.inputs) != 1
                or invocation.inputs[0].port != self.tool.inputs[0].name
                or invocation.inputs[0].artifact.schema_ref != self.tool.inputs[0].schema_ref
                or invocation.inputs[0].artifact.media_type != "application/json"):
            return {"status": "failed", "reason_code": "population_input_binding_mismatch", "retryable": False}
        session = PopulationArtifacts(self.artifacts, attempt, self.implementation,
                                      transformation_id=self.tool.binding.capability_id)
        source = session.read(invocation.inputs[0].artifact)
        try:
            request = source.decode(self.capability.input_model, self.tool.inputs[0].schema_ref, session.scope)
            if self.capability.operation == "seed":
                result = SeedPreparation.load(request, session).publish(session)
            elif self.capability.operation == "slice":
                result = SeedSlices.load(request.prepared, session).publish(request, session)
            else:
                result = PrimaryMethod.load(source, session, self.tool.binding).publish(
                    self.capability.operation, self.tool.outputs[0].schema_ref, session)
        except ProtocolError:
            raise
        except (ValueError, TypeError, KeyError, OverflowError):
            return {"status": "failed", "reason_code": "invalid_population_step", "retryable": False}
        require(result.reference.schema_ref == self.tool.outputs[0].schema_ref, "population_output_schema")
        attempt.check()
        return {"status": "succeeded", "outputs": [{"port": "result", "artifact": result.reference.model_dump(mode="json")}], "checkpoint": None}

    def run_once(self, run_id):
        claimed = self.runtime.claim(run_id, self.tool.binding, "claim-" + uuid.uuid4().hex,
                                     lease_seconds=self.lease_seconds)
        if claimed.outcome.status == "no_eligible_work":
            return {"status": "no_eligible_work"}
        attempt = ToolAttemptContext(self.runtime, claimed.outcome, self.lease_seconds, skew_seconds=self.skew_seconds)
        try:
            outcome = self.execute(attempt)
        except ProtocolError as error:
            attempt.refresh()  # Lost authority cannot report a failure.
            retryable = isinstance(error, (TransportLost, CommandUnresolved)) or str(error) in {"stream_unavailable", "run_unavailable"}
            reason = "population_transport_failure" if retryable else "population_protocol_violation"
            if isinstance(error, CommandRejected):
                reason, retryable = error.reason_code, error.reason_code == "capacity_exhausted"
            outcome = {"status": "failed", "reason_code": reason, "retryable": retryable}
        attempt.refresh()
        invocation = attempt.invocation
        completion = Completion.model_validate_json(json.dumps({"schema_version": "1",
            "invocation_id": invocation.invocation_id, "attempt_id": invocation.attempt_id,
            "fence": invocation.fence, "outcome": outcome}))
        # Keep ambiguous completion outside failure handling: never contradict it.
        receipt = self.runtime.complete(CompleteInvocation(run_id=run_id, completion=completion),
            "complete-" + invocation.attempt_id, guard=attempt.check)
        return {"status": "completion_accepted", "outcome": outcome["status"], "operation_id": receipt.outcome.binding.operation_id}


def run_population_worker(config_path, operation):
    config = WorkerConfig.model_validate_json(Path(config_path).read_bytes())
    require(config.execution_profile is None, "population_worker_requires_synthetic_profile")
    identity = WorkerIdentity(config.actor_id, config.scope)
    worker = PopulationWorker(RuntimeClient(config.runtime.transport(), identity),
        ArtifactClient(config.artifacts.transport(), identity), PopulationCapability(operation), config.image_sha256,
        lease_seconds=config.lease_seconds, skew_seconds=config.max_clock_skew_seconds)
    return worker.run_once(config.run_id)
