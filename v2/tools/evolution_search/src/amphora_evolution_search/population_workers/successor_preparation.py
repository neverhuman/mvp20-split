"""Accepted initial checkpoint to declared successor work; no invented future input keys."""
from dataclasses import dataclass
from amphora_contracts_artifacts import DerivationReceipt
from ..population.retained import PopulationArtifact
from .inspection import ObservedMethod

from amphora_contracts_population import (
    CandidateMember,GenerationIdentity,MembershipManifest,MembershipPageReference,
    PopulationCheckpoint,PopulationSelectionReceipt,membership_manifest_schema,membership_page_schema,population_record_schema)
from amphora_contracts_population_steps import SelectPopulationRequest,population_step_schema
from amphora_contracts_tools import ToolBinding

from ..population.closure import GenerationPageClosure
from ..population.membership import GenerationMembership
from ..population.planning import EvaluationCapacity,PrimaryBirthBatch
from ..population.pages import RecordPages
from ..population.successor import SelectedGeneration
from ..ranking import require
from .collection import publish_root
from .generation_publication import GenerationPublication
from .inspection import PopulationInspection
from .method_plan import authored_invocation,payload_schema
from .payloads import PreparedPrimarySuccessor,PrimaryOwnerEvidence,PrimarySuccessorDecision,SelectedPrimaryGeneration
from .selection import InitialSelection
from .selection_cut import SelectionReadCut


@dataclass(frozen=True)
class SuccessorPreparation:
    initial: InitialSelection
    selected: SelectedGeneration
    source_selected: PopulationArtifact
    owner: ObservedMethod
    lineage: DerivationReceipt
    counter: SelectionReadCut
    capacity: EvaluationCapacity
    stop_reason: str | None
    selection_pages: tuple[PopulationArtifact,...]

    @classmethod
    def load(cls,request,artifacts,runtime):
        checkpoint=artifacts.read(request.checkpoint)
        record=checkpoint.decode(PopulationCheckpoint,population_record_schema("population.checkpoint"),artifacts.scope)
        require(record.generation.generation==0 and record.generation.run_id==artifacts.attempt.invocation.run_id,
            "successor_preparation_initial_only")
        lineage=artifacts.derivation(request.checkpoint)
        schema=population_step_schema("population-step.select")
        carriers=tuple(ref for ref in lineage.declaration.inputs if ref.schema_ref==schema)
        require(len(carriers)==1,"successor_selection_carrier")
        selection_request=artifacts.read(carriers[0]).decode(SelectPopulationRequest,schema,artifacts.scope)
        require(selection_request.specification==request.specification,"successor_original_specification")
        initial=InitialSelection.load(selection_request,artifacts,runtime)
        decision=initial.selection.selection.decide()
        receipt=artifacts.read(record.selection)
        parent_artifacts=tuple(artifacts.read(decision.pool.by_id[candidate].birth) for candidate in decision.selected)
        selected=SelectedGeneration.verify(checkpoint,receipt,decision,selection_request.pool,selection_request.fitness,parent_artifacts)
        receipt_record=receipt.decode(PopulationSelectionReceipt,population_record_schema("population.selection-receipt"),artifacts.scope)
        selection_pages=tuple(artifacts.read(page.artifact) for page in receipt_record.pages)
        RecordPages.verified(record.generation,"population.selection-page",receipt_record.pages,
            tuple(page.content for page in selection_pages),receipt_record.member_count)
        GenerationPageClosure.verify(record.generation,(*initial.source_pages,*selection_pages))
        expected=ToolBinding(capability_id="numeric.population-select-primary",release=artifacts.implementation.version,
            image_sha256=artifacts.implementation.sha256,contract_version="1")
        reads=PopulationInspection(runtime,artifacts.attempt)
        capture=reads.capture(record.generation.run_id,initial.original.record.budget.max_activations)
        owners=[]
        for node in capture.nodes:
            if node.kind=="invoke" and node.status=="succeeded" and authored_invocation(initial.plan,node).tool==expected:
                owners.append(reads.method(capture,node))
        counter=SelectionReadCut.load(reads,capture,initial.plan)
        candidates=[]
        for owner in owners:
            outputs=owner.producer.completion.result.outcome.outputs
            require(len(outputs)==1 and outputs[0].port=="result","successor_selected_output")
            source=artifacts.read(outputs[0].artifact)
            envelope=source.decode(SelectedPrimaryGeneration,payload_schema(SelectedPrimaryGeneration,"population-worker.selected"),artifacts.scope)
            if envelope.checkpoint==request.checkpoint:candidates.append((source,envelope,owner))
        require(len(candidates)==1,"successor_checkpoint_not_accepted")
        source,envelope,owner=candidates[0]
        origin=artifacts.derivation(source.reference)
        cp_origin=lineage.declaration.transformation
        require((cp_origin.transformation_id,cp_origin.version,cp_origin.sha256)==(expected.capability_id,expected.release,expected.image_sha256)
            and lineage.origin.actor_id==owner.producer.worker_id,"successor_checkpoint_origin")
        actual=origin.declaration.transformation
        require((actual.transformation_id,actual.version,actual.sha256)==(expected.capability_id,expected.release,expected.image_sha256)
            and origin.origin.actor_id==owner.producer.worker_id,"successor_selected_origin")
        require(envelope.specification==request.specification and envelope.generation==record.generation
            and envelope.selection==record.selection and envelope.pool==selection_request.pool
            and envelope.fitness==selection_request.fitness and envelope.resolution==selection_request.resolution,
            "successor_selected_sources")
        require(envelope.stop_reason==selected.stop_reason and envelope.stopped==(selected.stop_reason is not None),
            "successor_selected_stop_policy")
        require(envelope.work_cut.scope==counter.cut.scope and envelope.work_cut.run_id==counter.cut.run_id
            and envelope.work_cut.plan_sha256==counter.cut.plan_sha256 and envelope.work_cut.revision<=counter.cut.revision,
            "successor_selected_cut")
        invocation=owner.producer.invocation
        require(len(invocation.inputs)==1 and invocation.inputs[0].artifact==carriers[0],"successor_selected_invocation")
        require(request.checkpoint in origin.declaration.inputs and record.selection in origin.declaration.inputs,
            "successor_selected_ancestry")
        progress=record.progress;budget=initial.original.record.budget
        require(progress.attempts_issued<=counter.attempts_issued<=budget.max_attempts
            and progress.activations_created<=counter.activations_created<=budget.max_activations,
            "successor_counter_monotonic")
        available=capture.snapshot.budget.limit-capture.snapshot.budget.spent-capture.snapshot.budget.reserved
        capacity=EvaluationCapacity(budget.max_evaluations-progress.evaluations_issued,
            min(budget.max_attempts-counter.attempts_issued,max(0,available)))
        reason=selected.stop_reason or capacity.reason(len(initial.original.record.method_graph.methods))
        return cls(initial,selected,source,owner,origin,counter,capacity,reason,selection_pages)

    def publish(self,artifacts):
        checkpoint=self.selected.artifact.reference
        owner=self.owner
        proof=artifacts.publish(PrimaryOwnerEvidence(schema_version="1",detail=owner.detail,inputs=owner.inputs,
            producer=owner.producer,completion=owner.completion,derivation=self.lineage),
            payload_schema(PrimaryOwnerEvidence,"population-worker.owner-evidence"),(self.source_selected.reference,),"successor/source-proof")
        successor=None
        if self.stop_reason is None:
            original=self.initial.original
            batch=PrimaryBirthBatch.successor(self.selected,self.capacity)
            identity=GenerationIdentity(scope=artifacts.scope,run_id=self.selected.record.generation.run_id,
                specification_sha256=original.digest,generation=1,predecessor=checkpoint)
            selected_members=self.selected.decision.pool.by_id
            parent_refs=tuple((candidate,selected_members[candidate].birth) for candidate in self.selected.decision.selected)
            published=GenerationPublication(original,artifacts.read(self.initial.request.specification),batch,identity,
                prefix="successor",ancestry=(checkpoint,self.source_selected.reference),parent_births=parent_refs).publish(artifacts)
            cohort=published.prepared.declarations.membership
            parents=tuple(selected_members[candidate].model_copy(update={"source":"parent"}) for candidate in self.selected.decision.selected)
            pool=GenerationMembership(original,identity,"selection_pool",tuple(sorted((*parents,*cohort.members),key=lambda member:member.candidate_id)))
            pool_pages=[];page_refs=[]
            for page in pool.pages():
                artifact=artifacts.publish(page,membership_page_schema(),(checkpoint,published.prepared.artifact.reference),
                    "successor/pool-page/"+str(page.ordinal))
                pool_pages.append(artifact);page_refs.append(MembershipPageReference(ordinal=page.ordinal,members=len(page.members),artifact=artifact.reference))
            GenerationPageClosure.verify(identity,(*self.initial.source_pages,*self.selection_pages,*published.pages,*pool_pages))
            pool_root=publish_root(MembershipManifest(schema_version="1",profile="population-membership-manifest-v1",generation=identity,
                role="selection_pool",member_count=len(pool.members),pages=tuple(page_refs)),membership_manifest_schema(),
                (checkpoint,published.prepared.artifact.reference,*(ref.artifact for ref in page_refs)),"successor/pool",artifacts)
            detail=PreparedPrimarySuccessor(schema_version="1",generation=identity,prepared=published.prepared.artifact.reference,
                pool=pool_root.reference,source_selected=self.source_selected.reference,rng=batch.rng.to_record(),
                evaluations_planned=batch.evaluations_reserved,logical_evaluation_capacity=self.capacity.evaluations,
                method_attempt_capacity=self.capacity.attempts,disposition=batch.disposition)
            successor=artifacts.publish(detail,payload_schema(PreparedPrimarySuccessor,"population-worker.prepared-successor"),
                (checkpoint,self.source_selected.reference,published.prepared.artifact.reference,pool_root.reference,proof.reference),"successor/preparation-detail").reference
        result=PrimarySuccessorDecision(schema_version="1",checkpoint=checkpoint,source_selected=self.source_selected.reference,
            stopped=self.stop_reason is not None,reason_code=self.stop_reason,successor=successor,work_cut=self.counter.cut)
        return artifacts.publish(result,payload_schema(PrimarySuccessorDecision,"population-worker.successor-decision"),
            (checkpoint,self.source_selected.reference,proof.reference,*(() if successor is None else (successor,))),"successor/result")
