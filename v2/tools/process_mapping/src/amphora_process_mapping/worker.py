"""One claimed mapping attempt; lifecycle adapted from public SDK/Search pattern."""
import json
import uuid
from pathlib import Path

from amphora_contracts_runtime import CompleteInvocation
from amphora_contracts_tools import Completion
from amphora_tool_protocol import (ArtifactClient,CommandRejected,CommandUnresolved,ProtocolError,
    RuntimeClient,ToolAttemptContext,TransportLost,WorkerConfig,WorkerIdentity)

from .artifacts import ProcessArtifacts
from .capability import ProcessCapability
from .derivation import DerivationAssembly
from .transform import TransformPreparation
from .publication import MappingPublication
from .validation import ProcessInputError,require


class ProcessWorker:
    def __init__(self,runtime,artifacts,image_sha256,*,operation="map-materials",lease_seconds=30,skew_seconds=1):
        require(runtime.identity==artifacts.identity,"process_worker_identity")
        self.runtime,self.artifacts=runtime,artifacts
        self.capability=ProcessCapability(operation)
        self.tool=self.capability.descriptor(image_sha256).tool
        self.image_sha256=image_sha256
        self.lease_seconds,self.skew_seconds=lease_seconds,skew_seconds

    def execute(self,attempt):
        invocation=attempt.invocation
        try:
            require(invocation.tool==self.tool.binding and invocation.checkpoint is None
                and len(invocation.inputs)==1 and invocation.inputs[0].port=="parameters"
                and invocation.inputs[0].artifact.schema_ref==self.tool.inputs[0].schema_ref
                and invocation.inputs[0].artifact.media_type=="application/json"
                and invocation.inputs[0].artifact.scope==self.artifacts.identity.scope,
                "process_input_binding")
            session=ProcessArtifacts(self.artifacts,attempt,self.capability.release,self.image_sha256)
            source=session.read(invocation.inputs[0].artifact)
            request=source.decode(self.capability.input_model,self.tool.inputs[0].schema_ref,session.scope)
            if self.capability.operation=="map-materials":
                root=MappingPublication.load(request,session).publish(session)
            elif self.capability.operation=="transform-materials":
                root=TransformPreparation.load(request,session).publish(session,source.reference)
            else:
                transform=ProcessCapability("transform-materials").descriptor(self.image_sha256).tool.binding
                root=DerivationAssembly.load(request,session,self.runtime,transform).publish(session)
            require(root.reference.schema_ref==self.tool.outputs[0].schema_ref,"process_output_schema")
            attempt.check()
            return dict(status="succeeded",outputs=[dict(port="result",artifact=root.reference.model_dump(mode="json"))],checkpoint=None)
        except ProtocolError:
            raise
        except ProcessInputError as error:
            reason="invalid_process_mapping" if self.capability.operation=="map-materials" else error.code
            return dict(status="failed",reason_code=reason,retryable=False)
        except ValueError:
            kind={"map-materials":"mapping","transform-materials":"transform","derive-process":"derivation"}[self.capability.operation]
            return dict(status="failed",reason_code="invalid_process_"+kind,retryable=False)

    def run_once(self,run_id):
        claimed=self.runtime.claim(run_id,self.tool.binding,"claim-"+uuid.uuid4().hex,lease_seconds=self.lease_seconds)
        if claimed.outcome.status=="no_eligible_work":return dict(status="no_eligible_work")
        attempt=ToolAttemptContext(self.runtime,claimed.outcome,self.lease_seconds,skew_seconds=self.skew_seconds)
        try:
            outcome=self.execute(attempt)
        except ProtocolError as error:
            attempt.refresh()
            retryable=isinstance(error,(TransportLost,CommandUnresolved)) or str(error) in {"stream_unavailable","process_observation_unavailable"}
            reason="process_transport_failure" if retryable else "process_protocol_violation"
            if self.capability.operation!="map-materials" and str(error) in {"process_observation_unavailable",
                "process_observation_rejected","process_observation_invalid","derivation_unavailable","derivation_reference_mismatch"}:
                reason=str(error)
            if isinstance(error,CommandRejected):reason,retryable=error.reason_code,error.reason_code=="capacity_exhausted"
            outcome=dict(status="failed",reason_code=reason,retryable=retryable)
        attempt.refresh()
        invocation=attempt.invocation
        completion=Completion.model_validate_json(json.dumps(dict(schema_version="1",invocation_id=invocation.invocation_id,
            attempt_id=invocation.attempt_id,fence=invocation.fence,outcome=outcome)))
        # Ambiguous completion must never cause a contradictory failure submission.
        receipt=self.runtime.complete(CompleteInvocation(run_id=run_id,completion=completion),
            "complete-"+invocation.attempt_id,guard=attempt.check)
        return dict(status="completion_accepted",outcome=outcome["status"],operation_id=receipt.outcome.binding.operation_id)


def run_process_worker(path,operation="map-materials"):
    config=WorkerConfig.model_validate_json(Path(path).read_bytes())
    require(config.execution_profile is None,"process_requires_synthetic_profile")
    identity=WorkerIdentity(config.actor_id,config.scope)
    return ProcessWorker(RuntimeClient(config.runtime.transport(),identity),ArtifactClient(config.artifacts.transport(),identity),
        config.image_sha256,operation=operation,lease_seconds=config.lease_seconds,skew_seconds=config.max_clock_skew_seconds).run_once(config.run_id)


MappingWorker=ProcessWorker


def run_mapping_worker(path):return run_process_worker(path)
