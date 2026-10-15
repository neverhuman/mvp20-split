"""Accepted primary collection to explicit initial-pool fitness; no selection or dispatch."""
from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .successor_source import PreparedSuccessorSource

from amphora_contracts_population import (
    EvaluationManifest,EvaluationResolutionManifest,FitnessManifest,MembershipManifest,MembershipPageReference,
    ObservationManifest,membership_manifest_schema,membership_page_schema,population_record_schema)
from amphora_contracts_search import ObjectiveValue

from ..population.closure import GenerationPageClosure
from ..population.membership import CLOSURE_BYTES,GenerationMembership
from ..population.pages import RecordPages
from ..population.selection import PopulationSelection
from ..population.retained import PopulationArtifact,RetainedEvaluations
from ..population.dispatch import PreparedGeneration
from ..population.specification import canonical
from ..ranking import require
from .accepted_source import AcceptedCollectionSource
from .collection import prepared_pages,publish_root
from .fitness_policy import PrimaryFitness
from .method_plan import payload_schema
from .payloads import CollectedPrimaryGeneration,FittedPrimaryGeneration,PrimaryOwnerEvidence,PrimarySumPolicy,UnconstrainedSynthetic
from .slices import SeedSlices


@dataclass(frozen=True)
class PrimaryAssembly:
    source: PopulationArtifact
    record: CollectedPrimaryGeneration
    prepared: PreparedGeneration
    accepted: AcceptedCollectionSource
    fitness: PrimaryFitness
    source_pages: tuple[PopulationArtifact, ...]
    successor: PreparedSuccessorSource | None = None

    @classmethod
    def load(cls,source,artifacts,runtime,binding):
        record=source.decode(CollectedPrimaryGeneration,payload_schema(CollectedPrimaryGeneration,"population-worker.collected"),artifacts.scope)
        reconstructed=SeedSlices.load(record.prepared,artifacts,runtime)
        prepared=reconstructed.prepared
        require(record.generation==prepared.record.generation and record.specification==prepared.record.specification
            and record.cohort==prepared.record.cohort and record.declarations==prepared.record.declarations,
            "primary_fitness_collected_binding")
        original=prepared.declarations.membership.original.record
        policy=artifacts.read(original.assembly.policy).decode(PrimarySumPolicy,
            payload_schema(PrimarySumPolicy,"population-worker.fitness-policy"),artifacts.scope)
        constraints=artifacts.read(original.constraints).decode(UnconstrainedSynthetic,
            payload_schema(UnconstrainedSynthetic,"population-worker.synthetic-constraints"),artifacts.scope)
        accepted=AcceptedCollectionSource.load(source,record,prepared,artifacts,runtime)
        evaluation=artifacts.read(record.evaluations)
        manifest=evaluation.decode(EvaluationManifest,population_record_schema("population.evaluation-manifest"),artifacts.scope)
        key_pages=tuple(artifacts.read(page.artifact) for page in manifest.pages)
        retained=RetainedEvaluations.verify(prepared.declarations.membership,record.cohort,evaluation,tuple(page.content for page in key_pages))
        prepared.declarations.resolve(retained.frozen.keys)
        resolution=artifacts.read(record.resolution).decode(EvaluationResolutionManifest,
            population_record_schema("population.evaluation-resolution"),artifacts.scope)
        prepared.declarations.verify_resolution(record.declarations,record.evaluations,resolution,retained.frozen)
        observations=artifacts.read(record.observations)
        observation_manifest=observations.decode(ObservationManifest,population_record_schema("population.observation-manifest"),artifacts.scope)
        observation_pages=tuple(artifacts.read(page.artifact) for page in observation_manifest.pages)
        evidence=retained.observations(observations,tuple(page.content for page in observation_pages)).evidence
        previous=() if reconstructed.successor is None else reconstructed.successor.source_pages
        pages=(*previous,*prepared_pages(prepared,artifacts),*key_pages,*observation_pages)
        GenerationPageClosure.verify(record.generation,pages)
        values=[]
        for row in evidence.observations:
            if row.outcome.status!="evaluated":continue
            require(len(row.outcome.outputs)==1 and row.outcome.outputs[0].port=="result","primary_fitness_output_arity")
            value=artifacts.read(row.outcome.outputs[0].artifact).decode(ObjectiveValue,
                payload_schema(ObjectiveValue,"population-method.objective-value"),artifacts.scope)
            values.append((row.evaluation_sha256,value))
        fitness=PrimaryFitness(evidence,tuple(values),binding,policy,constraints)
        return cls(source,record,prepared,accepted,fitness,pages,reconstructed.successor)

    def selection_pool(self):
        cohort=self.prepared.declarations.membership
        records=self.fitness.records()
        parents=()
        if self.successor is not None:
            selected=set(self.successor.selected.decision.selected)
            parents=tuple(member.model_copy(update={"source":"parent"})
                for member in self.successor.selected.decision.pool.members if member.candidate_id in selected)
            records=(*records,*(item for item in self.successor.fitness.selection.fitness
                if item.record.candidate_id in selected))
        members=tuple(sorted((*parents,*cohort.members),key=lambda m:m.candidate_id))
        pool=GenerationMembership(cohort.original,cohort.identity,"selection_pool",members)
        return PopulationSelection(pool,tuple(records))

    def publish(self,artifacts):
        identity=self.record.generation
        cohort=self.prepared.declarations.membership
        selection=self.selection_pool()
        pool=selection.pool
        records=selection.fitness
        membership_pages=pool.pages()
        fitness_pages=RecordPages(identity,"population.fitness-page",tuple(item.record for item in records)).pack()
        require(len(self.source_pages)+len(membership_pages)+len(fitness_pages)<=512,"generation_closure_pages")
        require(sum(page.reference.size_bytes for page in self.source_pages)+
            sum(len(canonical(page)) for page in (*membership_pages,*fitness_pages))<=CLOSURE_BYTES,"generation_closure_bytes")
        owner=self.accepted.owner
        proof=artifacts.publish(PrimaryOwnerEvidence(schema_version="1",detail=owner.detail,inputs=owner.inputs,
            producer=owner.producer,completion=owner.completion,derivation=self.accepted.derivation),
            payload_schema(PrimaryOwnerEvidence,"population-worker.owner-evidence"),(self.source.reference,),"fitness/source-proof")
        published=[]
        def pages(packed,schema,label):
            references=[]
            for page in packed:
                artifact=artifacts.publish(page,schema,(self.source.reference,proof.reference),label+"/"+str(page.ordinal))
                published.append(artifact)
                rows=page.members if hasattr(page,"members") else page.records
                references.append(MembershipPageReference(ordinal=page.ordinal,members=len(rows),artifact=artifact.reference))
            return tuple(references)
        pool_refs=pages(membership_pages,membership_page_schema(),"fitness/pool-page")
        pool_root=publish_root(MembershipManifest(schema_version="1",profile="population-membership-manifest-v1",
            generation=identity,role="selection_pool",member_count=len(pool.members),pages=pool_refs),membership_manifest_schema(),
            (self.record.cohort,*(page.artifact for page in pool_refs)),"fitness/pool",artifacts)
        fitness_refs=pages(fitness_pages,population_record_schema("population.fitness-page"),"fitness/page")
        GenerationPageClosure.verify(identity,(*self.source_pages,*published))
        observations=(*(() if self.successor is None else tuple(source.artifact.reference for source in self.successor.observations)),
            self.record.observations)
        manifest=publish_root(FitnessManifest(schema_version="1",profile="population-fitness-manifest-v1",generation=identity,
            pool=pool_root.reference,observations=observations,member_count=len(records),pages=fitness_refs),
            population_record_schema("population.fitness-manifest"),(*observations,pool_root.reference,proof.reference,
                *(page.artifact for page in fitness_refs)),"fitness/manifest",artifacts)
        result=FittedPrimaryGeneration(schema_version="1",generation=identity,collected=self.source.reference,
            specification=self.record.specification,pool=pool_root.reference,fitness=manifest.reference,resolution=self.record.resolution)
        return artifacts.publish(result,payload_schema(FittedPrimaryGeneration,"population-worker.fitted"),
            (self.source.reference,pool_root.reference,manifest.reference,proof.reference,self.record.resolution,
                cohort.original.record.assembly.policy,cohort.original.record.constraints),"fitness/result")
