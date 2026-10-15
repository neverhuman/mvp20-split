"""Authenticate the collected Artifact against immutable Data origin and Runtime acceptance."""
from dataclasses import dataclass

from amphora_contracts_tools import ToolBinding
from amphora_contracts_artifacts import DerivationReceipt
from amphora_contracts_campaigns import ExecutionPlanV4

from ..ranking import require
from .inspection import ObservedMethod,PopulationInspection
from .method_plan import PrimaryMethodPlan,authored_invocation,payload_schema,read_plan
from .payloads import CollectPrimaryRequest


@dataclass(frozen=True)
class AcceptedCollectionSource:
    owner: ObservedMethod
    derivation: DerivationReceipt
    request: CollectPrimaryRequest

    @classmethod
    def load(cls,source,record,prepared,artifacts,runtime):
        lineage=artifacts.derivation(source.reference)
        implementation=artifacts.implementation
        tool=ToolBinding(capability_id="numeric.population-collect-primary",release=implementation.version,
            image_sha256=implementation.sha256,contract_version="1")
        actual=lineage.declaration.transformation
        require((actual.transformation_id,actual.version,actual.sha256)==(tool.capability_id,tool.release,tool.image_sha256),
            "primary_fitness_collection_origin")
        plan_refs=tuple(ref for ref in lineage.declaration.inputs if ref.schema_ref==payload_schema(ExecutionPlanV4,ref.schema_ref.schema_id))
        require(1<=len(plan_refs)<=2,"primary_fitness_collection_plans")
        plans=tuple((ref,read_plan(ref,artifacts)) for ref in plan_refs)
        reads=PopulationInspection(runtime,artifacts.attempt)
        capture=reads.capture(record.generation.run_id,prepared.declarations.membership.original.record.budget.max_activations)
        admitted=tuple((ref,plan) for ref,plan in plans if plan.sha256==capture.snapshot.cut.plan_sha256)
        require(len(admitted)==1,"primary_fitness_admitted_plan")
        plan_ref,plan=admitted[0]
        producers=[]
        for node in capture.nodes:
            if node.kind!="invoke" or node.status!="succeeded":continue
            if authored_invocation(plan,node).tool!=tool:continue
            owner=reads.method(capture,node)
            if any(output.artifact==source.reference for output in owner.producer.completion.result.outcome.outputs):
                producers.append(owner)
        require(len(producers)==1,"primary_fitness_collection_not_accepted")
        owner=producers[0]
        require(owner.producer.worker_id==lineage.origin.actor_id and len(owner.producer.completion.result.outcome.outputs)==1,
            "primary_fitness_collection_actor")
        invocation=owner.producer.invocation
        require(len(invocation.inputs)==1 and invocation.inputs[0].port=="parameters","primary_fitness_collection_input")
        request=artifacts.read(invocation.inputs[0].artifact).decode(CollectPrimaryRequest,
            payload_schema(CollectPrimaryRequest,"population-worker.collect-request"),artifacts.scope)
        require(request.prepared==record.prepared and request.execution_plan==plan_ref,"primary_fitness_collection_request")
        for ref in (request.prepared,request.execution_plan,request.method_plan,record.evaluations,record.observations,record.resolution):
            require(ref in lineage.declaration.inputs,"primary_fitness_collection_ancestry")
        PrimaryMethodPlan.load(request,prepared.declarations.membership.original,artifacts)
        return cls(owner,lineage,request)
