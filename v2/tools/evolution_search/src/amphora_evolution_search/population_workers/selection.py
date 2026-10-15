"""Initial whole-pool selection with accepted source and closed observed work counters."""
from dataclasses import dataclass
from amphora_contracts_artifacts import DerivationReceipt
from amphora_contracts_campaigns import ExecutionPlanV4

from amphora_contracts_population import (
    EvaluationManifest,EvaluationResolutionManifest,FitnessManifest,MembershipManifest,MembershipPageReference,
    ObservationManifest,PopulationCheckpoint,PopulationProgress,PopulationSpecification,
    membership_manifest_schema,population_record_schema,population_specification_schema)
from amphora_contracts_population_steps import SelectPopulationRequest

from ..population.closure import GenerationPageClosure
from ..population.membership import GenerationMembership
from ..population.planning import PrimaryBirthBatch
from ..population.retained import PopulationArtifact,RetainedEvaluations,RetainedFitness
from ..population.specification import OriginalPopulation
from ..population.successor import SelectedGeneration
from ..ranking import require
from .collection import prepared_pages,publish_root
from .inspection import ObservedMethod,PopulationInspection
from .method_plan import authored_invocation,payload_schema,read_plan
from .payloads import CollectedPrimaryGeneration,CollectPrimaryRequest,FittedPrimaryGeneration,PrimaryOwnerEvidence,SelectedPrimaryGeneration
from .selection_cut import SelectionReadCut
from .slices import SeedSlices


@dataclass(frozen=True)
class InitialSelection:
    request: SelectPopulationRequest
    original: OriginalPopulation
    fitted: PopulationArtifact
    owner: ObservedMethod
    lineage: DerivationReceipt
    evaluations: RetainedEvaluations
    selection: RetainedFitness
    counter: SelectionReadCut
    source_pages: tuple[PopulationArtifact,...]
    plan: ExecutionPlanV4

    @classmethod
    def load(cls,request,artifacts,runtime):
        require(request.predecessor is None,"initial_selection_predecessor")
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
        retained,selection,pages=cls.evidence(request,original,record,collection_request,artifacts)
        return cls(request,original,fitted,owner,lineage,retained,selection,counter,pages,plan)

    @staticmethod
    def evidence(request,original,record,collection_request,artifacts):
        collected=artifacts.read(record.collected).decode(CollectedPrimaryGeneration,
            payload_schema(CollectedPrimaryGeneration,"population-worker.collected"),artifacts.scope)
        prepared=SeedSlices.load(collected.prepared,artifacts).prepared
        membership=prepared.declarations.membership
        require(membership.original==original and membership.identity==record.generation and record.generation.generation==0
            and collected.generation==record.generation and collected.specification==request.specification
            and collected.resolution==request.resolution and collection_request.prepared==collected.prepared
            and collected.cohort==prepared.record.cohort and collected.declarations==prepared.record.declarations,
            "initial_selection_generation")
        pool_artifact=artifacts.read(request.pool)
        pool_record=pool_artifact.decode(MembershipManifest,membership_manifest_schema(),artifacts.scope)
        pool_pages=tuple(artifacts.read(page.artifact) for page in pool_record.pages)
        pool=GenerationMembership.verified(original,pool_artifact.content,tuple(page.content for page in pool_pages))
        require(pool.identity==membership.identity and pool.role=="selection_pool" and pool.members==membership.members,
            "initial_selection_complete_pool")
        evaluation=artifacts.read(collected.evaluations)
        evaluation_record=evaluation.decode(EvaluationManifest,population_record_schema("population.evaluation-manifest"),artifacts.scope)
        key_pages=tuple(artifacts.read(page.artifact) for page in evaluation_record.pages)
        retained=RetainedEvaluations.verify(membership,collected.cohort,evaluation,tuple(page.content for page in key_pages))
        resolution=artifacts.read(request.resolution).decode(EvaluationResolutionManifest,
            population_record_schema("population.evaluation-resolution"),artifacts.scope)
        prepared.declarations.verify_resolution(prepared.record.declarations,collected.evaluations,resolution,retained.frozen)
        observations=artifacts.read(collected.observations)
        observation_record=observations.decode(ObservationManifest,population_record_schema("population.observation-manifest"),artifacts.scope)
        observation_pages=tuple(artifacts.read(page.artifact) for page in observation_record.pages)
        evidence=retained.observations(observations,tuple(page.content for page in observation_pages))
        fitness=artifacts.read(request.fitness)
        fitness_record=fitness.decode(FitnessManifest,population_record_schema("population.fitness-manifest"),artifacts.scope)
        fitness_pages=tuple(artifacts.read(page.artifact) for page in fitness_record.pages)
        selection=RetainedFitness.verify(pool,request.pool,fitness,tuple(page.content for page in fitness_pages),(evidence,))
        pages=(*prepared_pages(prepared,artifacts),*pool_pages,*key_pages,*observation_pages,*fitness_pages)
        GenerationPageClosure.verify(record.generation,pages)
        return retained,selection,pages

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
        logical=len(self.evaluations.frozen.keys)
        rng=PrimaryBirthBatch.seed(self.original).rng.to_record()
        checkpoint=artifacts.publish(PopulationCheckpoint(schema_version="1",profile="population-checkpoint-v1",
            generation=decision.pool.identity,selection=receipt.reference,rng=rng,progress=PopulationProgress(
                evaluations_issued=logical,evaluations_terminal=logical,attempts_issued=self.counter.attempts_issued,
                activations_created=self.counter.activations_created,unchanged_front_generations=0)),
            population_record_schema("population.checkpoint"),(receipt.reference,self.request.resolution),"select/checkpoint")
        parents=tuple(artifacts.read(decision.pool.by_id[candidate].birth) for candidate in decision.selected)
        selected=SelectedGeneration.verify(checkpoint,receipt,decision,self.request.pool,self.request.fitness,parents)
        result=SelectedPrimaryGeneration(schema_version="1",generation=decision.pool.identity,specification=self.request.specification,
            pool=self.request.pool,fitness=self.request.fitness,resolution=self.request.resolution,selection=receipt.reference,
            checkpoint=checkpoint.reference,source_proof=proof.reference,work_cut=self.counter.cut,stopped=selected.stop_reason is not None,stop_reason=selected.stop_reason)
        return artifacts.publish(result,payload_schema(SelectedPrimaryGeneration,"population-worker.selected"),
            (self.fitted.reference,proof.reference,receipt.reference,checkpoint.reference,self.request.resolution),"select/result")
