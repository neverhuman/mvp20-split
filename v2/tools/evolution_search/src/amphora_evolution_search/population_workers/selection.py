"""Whole-pool selection with accepted source and closed observed work counters."""
from dataclasses import dataclass
from amphora_contracts_artifacts import DerivationReceipt
from amphora_contracts_campaigns import ExecutionPlanV4

from amphora_contracts_population import (
    MembershipPageReference,PopulationCheckpoint,PopulationSpecification,
    population_record_schema,population_specification_schema)
from amphora_contracts_population_steps import SelectPopulationRequest

from ..population.closure import GenerationPageClosure
from ..population.retained import PopulationArtifact
from ..population.specification import OriginalPopulation
from ..population.successor import SelectedGeneration
from ..ranking import require
from .collection import publish_root
from .inspection import ObservedMethod,PopulationInspection
from .method_plan import authored_invocation,payload_schema,read_plan
from .payloads import CollectPrimaryRequest,FittedPrimaryGeneration,PrimaryOwnerEvidence,SelectedPrimaryGeneration
from .selection_cut import SelectionReadCut
from .selection_evidence import SelectionEvidence


@dataclass(frozen=True)
class InitialSelection:
    request: SelectPopulationRequest
    original: OriginalPopulation
    fitted: PopulationArtifact
    owner: ObservedMethod
    lineage: DerivationReceipt
    evidence: SelectionEvidence
    counter: SelectionReadCut
    plan: ExecutionPlanV4

    @property
    def evaluations(self): return self.evidence.evaluations

    @property
    def selection(self): return self.evidence.fitness

    @property
    def source_pages(self): return self.evidence.pages

    @classmethod
    def load(cls,request,artifacts,runtime):
        original=OriginalPopulation(artifacts.read(request.specification).decode(PopulationSpecification,
            population_specification_schema(),artifacts.scope))
        require(artifacts.implementation in original.record.implementations,"initial_selection_implementation")
        # The immutable resolution retains its exact collection request carrier;
        # use that public Data lineage to discover the supplied admitted plan.
        resolution_origin=artifacts.derivation(request.resolution)
        carrier_schema=payload_schema(CollectPrimaryRequest,"population-worker.collect-request")
        carriers=tuple(ref for ref in resolution_origin.declaration.inputs if ref.schema_ref==carrier_schema)
        require(len(carriers)==1,"initial_selection_collection_carrier")
        collection_request=artifacts.read(carriers[0]).decode(CollectPrimaryRequest,carrier_schema,artifacts.scope)
        plan=read_plan(collection_request.execution_plan,artifacts)
        reads=PopulationInspection(runtime,artifacts.attempt)
        capture=reads.capture(artifacts.attempt.invocation.run_id,original.record.budget.max_activations)
        require(plan.sha256==capture.snapshot.cut.plan_sha256,"initial_selection_admitted_plan")
        owners=[]
        for node in capture.nodes:
            if node.kind=="invoke" and node.status=="succeeded" and authored_invocation(plan,node).tool==original.record.assembly.tool:
                owners.append(reads.method(capture,node))
        counter=SelectionReadCut.load(reads,capture,plan)
        require(counter.attempts_issued<=original.record.budget.max_attempts
            and counter.activations_created<=original.record.budget.max_activations,"initial_selection_work_budget")
        candidates=[]
        for owner in owners:
            outputs=owner.producer.completion.result.outcome.outputs
            require(len(outputs)==1 and outputs[0].port=="result","initial_selection_fitness_output")
            source=artifacts.read(outputs[0].artifact)
            record=source.decode(FittedPrimaryGeneration,payload_schema(FittedPrimaryGeneration,"population-worker.fitted"),artifacts.scope)
            if (record.specification,record.pool,record.fitness,record.resolution)==(request.specification,request.pool,request.fitness,request.resolution):
                candidates.append((source,record,owner))
        require(len(candidates)==1,"initial_selection_fitness_not_accepted")
        fitted,record,owner=candidates[0]
        lineage=artifacts.derivation(fitted.reference)
        expected=original.record.assembly.tool;actual=lineage.declaration.transformation
        require((actual.transformation_id,actual.version,actual.sha256)==(expected.capability_id,expected.release,expected.image_sha256)
            and lineage.origin.actor_id==owner.producer.worker_id,"initial_selection_fitness_origin")
        invocation=owner.producer.invocation
        require(len(invocation.inputs)==1 and invocation.inputs[0].port=="parameters" and invocation.inputs[0].artifact==record.collected,
            "initial_selection_fitness_input")
        require(all(ref in lineage.declaration.inputs for ref in (record.collected,request.pool,request.fitness,request.resolution)),
            "initial_selection_fitness_ancestry")
        evidence=SelectionEvidence.load(request,original,record,collection_request,artifacts,runtime)
        # Validate cumulative counters before publishing any proposed selection.
        evidence.progress(counter)
        return cls(request,original,fitted,owner,lineage,evidence,counter,plan)

    def publish(self,artifacts):
        owner=self.owner
        proof=artifacts.publish(PrimaryOwnerEvidence(schema_version="1",detail=owner.detail,inputs=owner.inputs,
            producer=owner.producer,completion=owner.completion,derivation=self.lineage),
            payload_schema(PrimaryOwnerEvidence,"population-worker.owner-evidence"),(self.fitted.reference,),"select/source-proof")
        decision=self.selection.selection.decide()
        published=[];refs=[]
        for page in decision.pages():
            artifact=artifacts.publish(page,population_record_schema("population.selection-page"),
                (self.fitted.reference,self.request.pool,self.request.fitness),"select/page/"+str(page.ordinal))
            published.append(artifact)
            refs.append(MembershipPageReference(ordinal=page.ordinal,members=len(page.members),artifact=artifact.reference))
        GenerationPageClosure.verify(decision.pool.identity,(*self.source_pages,*published))
        receipt=publish_root(decision.receipt(self.request.pool,self.request.fitness,tuple(refs)),
            population_record_schema("population.selection-receipt"),(self.fitted.reference,self.request.pool,self.request.fitness,
                *(ref.artifact for ref in refs)),"select/receipt",artifacts)
        progress=self.evidence.progress(self.counter)
        rng=self.evidence.rng
        checkpoint=artifacts.publish(PopulationCheckpoint(schema_version="1",profile="population-checkpoint-v1",
            generation=decision.pool.identity,selection=receipt.reference,rng=rng,progress=progress),
            population_record_schema("population.checkpoint"),(receipt.reference,self.request.resolution),"select/checkpoint")
        parents=tuple(artifacts.read(decision.pool.by_id[candidate].birth) for candidate in decision.selected)
        selected=SelectedGeneration.verify(checkpoint,receipt,decision,self.request.pool,self.request.fitness,parents)
        result=SelectedPrimaryGeneration(schema_version="1",generation=decision.pool.identity,specification=self.request.specification,
            pool=self.request.pool,fitness=self.request.fitness,resolution=self.request.resolution,selection=receipt.reference,
            checkpoint=checkpoint.reference,source_proof=proof.reference,work_cut=self.counter.cut,stopped=selected.stop_reason is not None,stop_reason=selected.stop_reason)
        return artifacts.publish(result,payload_schema(SelectedPrimaryGeneration,"population-worker.selected"),
            (self.fitted.reference,proof.reference,receipt.reference,checkpoint.reference,self.request.resolution),"select/result")
