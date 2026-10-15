"""Explicit primary-occurrence collection; no arrival-order identities or zero fitness."""
import json
from dataclasses import dataclass
from amphora_contracts_core import ArtifactRef
from amphora_contracts_artifacts import DerivationReceipt
from ..population.dispatch import PreparedGeneration

from amphora_contracts_population import (
    BirthManifest, EvaluationDeclarationManifest, MembershipManifest, membership_manifest_schema,
    EvaluationKey, EvaluationManifest, EvaluationResolutionManifest, ExecutionPointer,
    MembershipPageReference, MethodObservation, ObservationManifest, population_record_schema,
)
from amphora_contracts_population_steps import PopulationCandidateContext, population_step_schema

from ..population.closure import GenerationPageClosure
from ..population.evaluations import BoundEvaluation, observation_cut
from ..population.membership import CLOSURE_BYTES
from ..population.retained import PopulationArtifact
from ..population.specification import canonical
from ..population.pages import RecordPages
from ..ranking import require
from .inspection import ObservedMethod, PopulationInspection
from .method_plan import PrimaryMethodPlan, payload_schema
from .payloads import CollectedPrimaryGeneration, PopulationReferenceGroup, PrimaryOwnerEvidence
from .slices import SeedSlices


def publish_root(record,schema,parents,label,artifacts):
    # Public manifests can name512 pages; retention declarations allow128 parents.
    # Explicit tool-owned grouping keeps the complete ancestry, with no truncation.
    unique={ref.artifact_id:ref for ref in parents}
    require(all(unique[ref.artifact_id]==ref for ref in parents),"population_root_parent_conflict")
    refs=tuple(unique[key] for key in sorted(unique))
    while len(refs)>120:
        groups=[]
        for offset in range(0,len(refs),120):
            chunk=refs[offset:offset+120]
            group=PopulationReferenceGroup(schema_version="1",references=chunk)
            groups.append(artifacts.publish(group,payload_schema(PopulationReferenceGroup,"population-worker.reference-group"),
                chunk,label+"/group/"+str(len(refs))+"/"+str(offset)).reference)
        refs=tuple(groups)
    return artifacts.publish(record,schema,refs,label)


def prepared_pages(prepared,artifacts):
    source_pages=[]
    for reference,model,schema in (
        (prepared.record.births,BirthManifest,population_record_schema("population.birth-manifest")),
        (prepared.record.cohort,MembershipManifest,membership_manifest_schema()),
        (prepared.record.declarations,EvaluationDeclarationManifest,population_record_schema("population.evaluation-declarations"))):
        manifest=artifacts.read(reference).decode(model,schema,artifacts.scope)
        source_pages.extend(artifacts.read(page.artifact) for page in manifest.pages)
    GenerationPageClosure.verify(prepared.record.generation,tuple(source_pages))
    return tuple(source_pages)


@dataclass(frozen=True)
class CollectedMethod:
    key: BoundEvaluation
    observation: MethodObservation
    context: ArtifactRef
    owner: ObservedMethod
    derivation: DerivationReceipt | None


@dataclass(frozen=True)
class PrimaryCollection:
    prepared: PreparedGeneration
    plan: PrimaryMethodPlan
    methods: tuple[CollectedMethod, ...]
    source_pages: tuple[PopulationArtifact, ...]

    @property
    def keys(self):
        return tuple(method.key for method in self.methods)

    @property
    def observations(self):
        return tuple(method.observation for method in self.methods)

    @classmethod
    def load(cls,request,artifacts,runtime):
        prepared=SeedSlices.load(request.prepared,artifacts).prepared
        original=prepared.declarations.membership.original
        plan=PrimaryMethodPlan.load(request,original,artifacts)
        source_pages=prepared_pages(prepared,artifacts)
        reads=PopulationInspection(runtime,artifacts.attempt)
        capture=reads.capture(prepared.record.generation.run_id,original.record.budget.max_activations)
        require(capture.snapshot.cut.plan_sha256==plan.execution.sha256,"population_collection_admitted_plan")
        # All cut-bound HTTP reads precede Artifact reads/publications (which renew
        # this worker's lease and therefore may advance Runtime's run revision).
        observed=[]
        for node in capture.nodes:
            method=plan.binding(node)
            if method is not None:
                observed.append((method,reads.method(capture,node)))
        collected=[]
        for method,owner in observed:
            refs={item.artifact.artifact_id:item.artifact for item in owner.inputs.scope_inputs
                if item.artifact is not None and item.artifact.schema_ref==population_step_schema("population-step.candidate-context")}
            invocation=owner.inputs.invocation
            if invocation is not None:
                require(invocation.tool==method.tool and invocation.node_id==method.node_path[0]
                    and len(invocation.inputs)==1 and invocation.inputs[0].port=="parameters",
                    "population_collection_method_invocation")
                ref=invocation.inputs[0].artifact
                require(ref.schema_ref==population_step_schema("population-step.candidate-context"),"population_collection_context_schema")
                require(refs.setdefault(ref.artifact_id,ref)==ref,"population_collection_context_conflict")
            require(len(refs)==1,"population_collection_context_ambiguity")
            reference=next(iter(refs.values()))
            context=artifacts.read(reference).decode(PopulationCandidateContext,
                population_step_schema("population-step.candidate-context"),artifacts.scope)
            membership=prepared.declarations.membership
            require(context.generation==membership.identity and context.specification==prepared.record.specification
                and context.declarations==prepared.record.declarations
                and membership.by_id.get(context.member.candidate_id)==context.member,"population_collection_candidate_binding")
            key=BoundEvaluation(membership,EvaluationKey(schema_version="1",profile="population-evaluation-key-v1",
                generation=membership.identity,candidate_id=context.member.candidate_id,occurrence_id="primary",
                method_id=method.method_id,tool=method.tool,material=context.member.representation,
                inputs=tuple(sorted({reference.artifact_id:reference,context.member.representation.artifact_id:context.member.representation}.values(),
                    key=lambda ref:ref.artifact_id)),conditions=method.conditions,objective_policy_sha256=original.record.assembly.policy.sha256))
            completion=owner.completion
            pointer=None
            if completion is not None:
                pointer=ExecutionPointer(run_id=completion.run_id,activation_id=completion.activation_id,
                    invocation_id=completion.result.invocation_id,attempt_id=completion.result.attempt_id,
                    completion_id=completion.completion_id)
            derivation=None
            if owner.producer is not None:
                outputs=completion.result.outcome.outputs
                require(len(outputs)==1 and outputs[0].port=="result" and outputs[0].artifact.schema_ref==method.output_schema,
                    "population_collection_method_output")
                derivation=artifacts.derivation(outputs[0].artifact)
                require(derivation.origin.actor_id==owner.producer.worker_id,"population_collection_producer_actor")
                transformation=derivation.declaration.transformation
                require((transformation.transformation_id,transformation.version,transformation.sha256)==
                    (method.tool.capability_id,method.tool.release,method.tool.image_sha256),"population_collection_producer_derivation")
                direct_contexts=tuple(ref for ref in derivation.declaration.inputs
                    if ref.schema_ref==population_step_schema("population-step.candidate-context"))
                require(direct_contexts==(reference,),"population_collection_output_context")
                outcome={"status":"evaluated","producer":pointer.model_dump(mode="json"),
                    "outputs":[item.model_dump(mode="json") for item in outputs]}
            else:
                status=owner.detail.node.status
                outcome={"status":"inapplicable" if status=="skipped" else "failed" if owner.detail.attempts else "unknown",
                    "reason_code":owner.detail.node.reason_code or "primary_method_unavailable",
                    "producer":None if pointer is None else pointer.model_dump(mode="json"),"evidence":[reference.model_dump(mode="json")]}
            observation=MethodObservation.model_validate_json(json.dumps({"schema_version":"1",
                "profile":"population-method-observation-v1","key":key.record.model_dump(mode="json"),
                "evaluation_sha256":key.digest,"outcome":outcome}))
            collected.append(CollectedMethod(key,key.observation(observation),reference,owner,derivation))
        frozen=prepared.declarations.resolve(tuple(method.key for method in collected))
        frozen.terminal(tuple(method.observation for method in collected))
        indexed={method.key.digest:method for method in collected}
        return cls(prepared,plan,tuple(indexed[key.digest] for key in frozen.keys),tuple(source_pages))

    def publish(self,request,artifacts):
        prepared=self.prepared;generation=prepared.record.generation
        frozen=prepared.declarations.resolve(self.keys)
        packed_keys=RecordPages(generation,"population.evaluation-key-page",tuple(key.record for key in frozen.keys)).pack()
        packed_observations=RecordPages(generation,"population.method-observation-page",self.observations).pack()
        require(len(self.source_pages)+len(packed_keys)+len(packed_observations)<=512,"generation_closure_pages")
        require(sum(page.reference.size_bytes for page in self.source_pages)+
            sum(len(canonical(page)) for page in (*packed_keys,*packed_observations))<=CLOSURE_BYTES,"generation_closure_bytes")
        published_pages=[]
        evidence_refs={}
        for method in self.methods:
            key,context,owner=method.key,method.context,method.owner
            record=PrimaryOwnerEvidence(schema_version="1",detail=owner.detail,inputs=owner.inputs,
                producer=owner.producer,completion=owner.completion,derivation=method.derivation)
            outputs=tuple(item.artifact for item in owner.producer.completion.result.outcome.outputs) if owner.producer else ()
            evidence_refs[key.digest]=artifacts.publish(record,payload_schema(PrimaryOwnerEvidence,"population-worker.owner-evidence"),
                (request.prepared,request.execution_plan,request.method_plan,context,key.record.material,*outputs),
                "collect/evidence/"+key.digest).reference
        def pages(packed,name,label):
            refs=[]
            for page in packed:
                digests = (tuple(row.evaluation_sha256 for row in page.records)
                    if name == "population.method-observation-page" else
                    tuple(BoundEvaluation(frozen.membership,row).digest for row in page.records))
                artifact=artifacts.publish(page,population_record_schema(name),
                    (request.prepared,*(evidence_refs[digest] for digest in digests)),label+"/"+str(page.ordinal))
                published_pages.append(artifact)
                refs.append(MembershipPageReference(ordinal=page.ordinal,members=len(page.records),artifact=artifact.reference))
            return tuple(refs)
        key_pages=pages(packed_keys,"population.evaluation-key-page","collect/keys")
        evaluation=publish_root(EvaluationManifest(schema_version="1",profile="population-evaluation-manifest-v1",
            generation=generation,membership=prepared.record.cohort,evaluation_set_sha256=frozen.digest,
            evaluation_count=len(frozen.keys),pages=key_pages),population_record_schema("population.evaluation-manifest"),
            (request.prepared,*(page.artifact for page in key_pages)),"collect/evaluations",artifacts)
        observation_pages=pages(packed_observations,"population.method-observation-page","collect/observations")
        GenerationPageClosure.verify(generation,(*self.source_pages,*published_pages))
        observations=publish_root(ObservationManifest(schema_version="1",profile="population-observation-manifest-v1",
            generation=generation,evaluations=evaluation.reference,evaluation_set_sha256=frozen.digest,
            observation_cut_sha256=observation_cut(self.observations),terminal_count=len(self.observations),pages=observation_pages),
            population_record_schema("population.observation-manifest"),(evaluation.reference,*(page.artifact for page in observation_pages)),
            "collect/observation-manifest",artifacts)
        resolution=artifacts.publish(EvaluationResolutionManifest(schema_version="1",profile="population-evaluation-resolution-manifest-v1",
            generation=generation,declarations=prepared.record.declarations,evaluations=evaluation.reference,
            slot_set_sha256=prepared.declarations.digest,evaluation_set_sha256=frozen.digest),
            population_record_schema("population.evaluation-resolution"),(prepared.record.declarations,evaluation.reference),"collect/resolution")
        result=CollectedPrimaryGeneration(schema_version="1",generation=generation,prepared=request.prepared,
            specification=prepared.record.specification,cohort=prepared.record.cohort,declarations=prepared.record.declarations,
            evaluations=evaluation.reference,observations=observations.reference,resolution=resolution.reference)
        return artifacts.publish(result,payload_schema(CollectedPrimaryGeneration,"population-worker.collected"),
            (request.prepared,request.execution_plan,request.method_plan,evaluation.reference,observations.reference,resolution.reference),"collect/result")
