"""Resolve a known attempt locator to immutable public accepted execution proof."""
from dataclasses import dataclass
import uuid

from amphora_contracts_execution_proofs import AcceptedToolExecution
from amphora_contracts_graph_runtime import GraphNodeDetail,GraphSnapshotPage
from amphora_tool_protocol import ProtocolError

from .payloads import TransformMaterialsRequest,schema_ref
from .validation import consistent_references,require


def public_get(runtime,session,model,path,query=None,*,refresh=True):
    if refresh:session.attempt.refresh()
    else:session.attempt.check()
    reply=runtime.transport.request("GET",path,**({"query":query} if query else {}))
    session.attempt.check()
    if reply.status in {409,410,503}:raise ProtocolError("process_observation_unavailable")
    if reply.status!=200:raise ProtocolError("process_observation_rejected")
    try:return model.model_validate_json(reply.body)
    except ValueError as error:raise ProtocolError("process_observation_invalid") from error


def source_lineage(session,reference,tool,worker_id,attempt_id,label,parents):
    lineage=session.derivation(reference)
    expected="begin-"+uuid.uuid5(uuid.NAMESPACE_URL,
        "amphora.process/publication-v1:"+attempt_id+":"+label).hex
    require(lineage.artifact==reference and lineage.origin.scope==session.scope
        and lineage.origin.actor_id==worker_id and lineage.origin.command_id==expected
        and lineage.origin.command_family=="artifacts.begin_derived_upload","transform_source_origin")
    actual=lineage.declaration.transformation
    require((actual.transformation_id,actual.version,actual.sha256)==(tool.capability_id,tool.release,tool.image_sha256),
        "transform_source_transformation")
    consistent_references(parents)
    unique={ref.artifact_id:ref for ref in parents}
    require(lineage.declaration.inputs==tuple(unique[key] for key in sorted(unique)),"transform_source_ancestry")
    return lineage


@dataclass(frozen=True)
class AcceptedTransform:
    execution: AcceptedToolExecution
    request: TransformMaterialsRequest

    @classmethod
    def load(cls,source,result,session,runtime,tool):
        run=result.context.generation.run_id
        require(run==session.attempt.invocation.run_id and result.context.generation.scope==session.scope,
            "transform_source_context")
        locator=result.source
        page=public_get(runtime,session,GraphSnapshotPage,f"/v1/graph-observations/{run}/nodes",{"limit":1})
        snapshot=page.snapshot
        require(snapshot.cut.scope==session.scope and snapshot.cut.run_id==run,"transform_source_snapshot")
        # Renewing here would change the run revision and invalidate our own cut.
        detail=public_get(runtime,session,GraphNodeDetail,
            f"/v1/graph-observations/{run}/nodes/{locator.activation_id}",
            {"snapshot_token":snapshot.snapshot_token,"limit":100},refresh=False)
        require(detail.cut.scope==session.scope and detail.cut.run_id==run and detail.next_cursor is None
            and detail.cut==snapshot.cut
            and detail.node.kind=="invoke" and detail.node.status=="succeeded"
            and detail.node.activation_id==locator.activation_id,"transform_source_node")
        accepted=tuple(a for a in detail.attempts if a.settled and a.status=="succeeded" and a.canonical_result)
        require(len(accepted)==1 and accepted[0].completion_id is not None,"transform_source_not_accepted")
        attempt=accepted[0]
        require((attempt.attempt_id,attempt.invocation_id,attempt.fence)==
            (locator.attempt_id,locator.invocation_id,locator.fence),"transform_source_attempt")
        execution=public_get(runtime,session,AcceptedToolExecution,
            f"/v1/runs/{run}/completions/{attempt.completion_id}/producer")
        invocation,completion=execution.invocation,execution.completion
        require(completion.scope==session.scope and completion.run_id==run and completion.canonical_result
            and completion.activation_id==locator.activation_id and completion.completion_id==attempt.completion_id
            and completion.accepted_run_revision<=detail.cut.revision and completion.result.outcome.status=="succeeded"
            and (completion.result.attempt_id,completion.result.invocation_id,completion.result.fence)==
                (locator.attempt_id,locator.invocation_id,locator.fence),"transform_source_completion")
        require(invocation.activation_id==locator.activation_id and invocation.invocation_id==locator.invocation_id
            and invocation.node_id==detail.node.path.node_id
            and invocation.tool==tool and invocation.checkpoint is None and execution.worker_id==attempt.worker_id
            and len(invocation.inputs)==1 and invocation.inputs[0].port=="parameters"
            and invocation.inputs[0].artifact==result.request
            and len(completion.result.outcome.outputs)==1
            and completion.result.outcome.outputs[0].port=="result"
            and completion.result.outcome.outputs[0].artifact==source.reference,"transform_source_binding")
        request=session.read(result.request).decode(TransformMaterialsRequest,
            schema_ref(TransformMaterialsRequest,"process-worker.transform-request"),session.scope)
        require(request.context==result.context and request.binding.tool==tool,"transform_source_request")
        source_lineage(session,source.reference,tool,execution.worker_id,locator.attempt_id,"transform",
            (result.request,*(use.material for use in result.outputs)))
        return cls(execution,request)
