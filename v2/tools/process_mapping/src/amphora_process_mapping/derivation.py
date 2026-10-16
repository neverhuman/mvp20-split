"""Build typed lineage only after verifying actual accepted transform execution."""
from dataclasses import dataclass

from amphora_contracts_core import ArtifactRef
from amphora_contracts_population import (ExecutionPointer,MaterialMappingItem,MaterialState,
    ProcessDerivation,population_record_schema)

from .accepted_transform import AcceptedTransform,source_lineage
from .payloads import MaterialCollection,ProposedProcessTransform,DerivedMaterialBatch,schema_ref
from .process import MaterialDerivation
from .transform import TransformPreparation,UNKNOWNS
from .validation import canonical,require


@dataclass(frozen=True)
class DerivationAssembly:
    source: ArtifactRef
    derivation: MaterialDerivation
    collection: MaterialCollection
    parents: tuple[ArtifactRef,...]

    @classmethod
    def load(cls,request,session,runtime,tool):
        source=session.read(request.result)
        result=source.decode(ProposedProcessTransform,schema_ref(ProposedProcessTransform,
            "process-worker.transform-result"),session.scope)
        accepted=AcceptedTransform.load(source,result,session,runtime,tool)
        execution=accepted.execution
        prepared=TransformPreparation.load(accepted.request,session,tool=tool,occurrence_id=result.source.activation_id)
        require(len(result.outputs)==len(prepared.states)
            and tuple((use.port,use.ordinal) for use in result.outputs)==tuple(
                (accepted.request.binding.outputs[0].port,index) for index in range(len(prepared.states))),
            "transform_output_coverage")
        outputs=tuple(session.read(use.material) for use in result.outputs)
        for index,(output,state) in enumerate(zip(outputs,prepared.states,strict=True)):
            actual=output.decode(MaterialState,population_record_schema("population.material-state"),session.scope)
            require(actual==state and output.content==canonical(state),"transform_output_replay")
            source_lineage(session,output.reference,tool,execution.worker_id,result.source.attempt_id,
                "state-"+str(index),(result.request,*prepared.parents))
        completion=execution.completion
        pointer=ExecutionPointer(run_id=completion.run_id,activation_id=completion.activation_id,
            invocation_id=completion.result.invocation_id,attempt_id=completion.result.attempt_id,
            completion_id=completion.completion_id)
        record=ProcessDerivation(schema_version="1",profile="synthetic-process-derivation-v1",context=result.context,
            occurrence_id=result.source.activation_id,tool=tool,inputs=accepted.request.inputs,absent=accepted.request.absent,
            outputs=result.outputs,conditions=accepted.request.conditions,producer=pointer,unknowns=UNKNOWNS)
        derivation=MaterialDerivation.from_record(record,result.context,accepted.request.binding,
            tuple(item.artifact for item in prepared.inputs),outputs)
        collection=MaterialCollection(schema_version="1",profile="synthetic-material-collection-v1",context=result.context,
            items=tuple(MaterialMappingItem(key=str(index),state=use.material) for index,use in enumerate(result.outputs)))
        require(len(canonical(collection))<=262144,"transform_collection_bytes")
        parents=(source.reference,result.request,accepted.request.conditions,
            *(use.material for use in accepted.request.inputs),*(use.material for use in result.outputs))
        session.check_parents(parents)
        return cls(source.reference,derivation,collection,parents)

    def publish(self,session):
        derivation=session.publish(self.derivation.record,population_record_schema("population.process-derivation"),
            self.parents,"derivation")
        collection=session.publish(self.collection,schema_ref(MaterialCollection,"process-worker.material-collection"),
            (derivation.reference,*(item.state for item in self.collection.items)),"collection")
        root=DerivedMaterialBatch(schema_version="1",profile="synthetic-derived-material-batch-v1",
            context=self.collection.context,derivation=derivation.reference,collection=collection.reference)
        return session.publish(root,schema_ref(DerivedMaterialBatch,"process-worker.derived-batch"),
            (self.source,derivation.reference,collection.reference),"derived-batch")
