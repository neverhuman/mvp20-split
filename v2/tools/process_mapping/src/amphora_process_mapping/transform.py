"""Explicit synthetic state generation; no chemical or physical production claim."""
from dataclasses import dataclass
import hashlib
import json

from amphora_contracts_core import ArtifactRef
from amphora_contracts_population import MaterialState,MaterialUse,population_record_schema

from .payloads import ProposedProcessTransform,ProcessAttemptLocator,TransformMaterialsRequest,schema_ref
from .process import BoundMaterial,MaterialDerivation
from .validation import canonical,consistent_references,require


UNKNOWNS=("composition","amount","phase","physical_batch","reaction_feasibility","conservation")


@dataclass(frozen=True)
class TransformPreparation:
    request: TransformMaterialsRequest
    inputs: tuple[BoundMaterial,...]
    states: tuple[MaterialState,...]
    parents: tuple[ArtifactRef,...]
    occurrence_id: str

    @classmethod
    def load(cls,request,session,*,tool=None,occurrence_id=None):
        request=TransformMaterialsRequest.model_validate_json(request.model_dump_json())
        context=request.context
        tool=session.attempt.invocation.tool if tool is None else tool
        occurrence_id=session.attempt.invocation.activation_id if occurrence_id is None else occurrence_id
        require(len(occurrence_id)==64 and all(char in "0123456789abcdef" for char in occurrence_id),"transform_occurrence")
        require(context.generation.scope==session.scope and context.generation.run_id==session.attempt.invocation.run_id,
            "transform_context")
        require(request.binding.tool==tool and tool.capability_id=="process.synthetic-transform-materials",
            "transform_tool_binding")
        require(len(request.binding.outputs)==1,"transform_single_output_role")
        consistent_references((request.conditions,*(use.material for use in request.inputs)))
        materials=tuple(session.read(use.material) for use in request.inputs)
        bound=MaterialDerivation._ports(context,request.binding.inputs,request.inputs,request.absent,materials,True)
        output=request.binding.outputs[0]
        require(request.output_count<=output.maximum,"transform_output_count")
        require(output.representation==bound[0].record.representation.schema_ref,"transform_representation")
        metadata={request.conditions.artifact_id:request.conditions}
        if context.generation.predecessor is not None:
            ref=context.generation.predecessor
            require(metadata.setdefault(ref.artifact_id,ref)==ref,"transform_metadata_conflict")
        for item in bound:
            record=item.record
            for ref in (record.representation,record.conditions,*((record.composition,) if record.composition else ())):
                require(metadata.setdefault(ref.artifact_id,ref)==ref,"transform_metadata_conflict")
        parents=(*(use.material for use in request.inputs),*metadata.values())
        consistent_references(parents)
        for key in sorted(metadata):session.read(metadata[key])
        session.check_parents(parents)
        digest=hashlib.sha256(canonical(request)+b":"+occurrence_id.encode()).hexdigest()
        states=tuple(MaterialState(schema_version="1",profile="synthetic-process-material-v1",context=context,
            state_id="synthetic-"+hashlib.sha256((digest+":"+str(index)).encode()).hexdigest(),revision=1,
            kind="intermediate",representation=bound[0].record.representation,composition=None,material_batch_id=None,
            amount=None,phase=None,conditions=request.conditions,unknowns=UNKNOWNS) for index in range(request.output_count))
        require(all(len(canonical(state))<=8192 for state in states),"transform_state_bytes")
        require(not {(item.record.state_id,item.record.revision) for item in bound}&{(state.state_id,state.revision) for state in states},
            "transform_state_not_new")
        # Size bound only: maximum-length future identifiers are never published,
        # returned as references, or treated as an accepted execution pointer.
        outputs=[dict(port=output.port,ordinal=index,material=dict(artifact_id="x"*128,
            scope=session.scope.model_dump(mode="json"),sha256=hashlib.sha256(canonical(state)).hexdigest(),
            size_bytes=len(canonical(state)),media_type="application/json",
            schema_ref=population_record_schema("population.material-state").model_dump())) for index,state in enumerate(states)]
        envelope=dict(schema_version="1",profile="synthetic-process-derivation-v1",context=context.model_dump(mode="json"),
            occurrence_id=occurrence_id,tool=tool.model_dump(mode="json"),inputs=[use.model_dump(mode="json") for use in request.inputs],
            absent=[value.model_dump(mode="json") for value in request.absent],outputs=outputs,
            conditions=request.conditions.model_dump(mode="json"),producer=dict(run_id=context.generation.run_id,
                activation_id=occurrence_id,invocation_id="x"*128,attempt_id="x"*128,completion_id="x"*128),unknowns=list(UNKNOWNS))
        require(len(json.dumps(envelope,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False).encode())<=8192,
            "transform_derivation_envelope")
        session.check_parents((*parents,*(binding.artifact for binding in session.attempt.invocation.inputs)))
        return cls(request,bound,states,parents,occurrence_id)

    def publish(self,session,source):
        artifacts=tuple(session.publish(state,population_record_schema("population.material-state"),self.parents,
            "state-"+str(index)) for index,state in enumerate(self.states))
        invocation=session.attempt.invocation
        locator=ProcessAttemptLocator(activation_id=invocation.activation_id,invocation_id=invocation.invocation_id,
            attempt_id=invocation.attempt_id,fence=invocation.fence)
        record=ProposedProcessTransform(schema_version="1",profile="synthetic-process-transform-result-v1",
            context=self.request.context,request=source,source=locator,outputs=tuple(MaterialUse(
                port=self.request.binding.outputs[0].port,ordinal=index,material=artifact.reference)
                for index,artifact in enumerate(artifacts)))
        return session.publish(record,schema_ref(ProposedProcessTransform,"process-worker.transform-result"),
            (source,*(artifact.reference for artifact in artifacts)),"transform")
