"""Shared primary birth/cohort/declaration publication; adapted from this owner's seed.py."""

from dataclasses import dataclass
from amphora_contracts_core import ArtifactRef
from ..population.retained import PopulationArtifact
from .collection import publish_root

from amphora_contracts_population import (
    BirthManifest, CandidateMember, EvaluationDeclarationManifest, GenerationIdentity,
    MembershipManifest, MembershipPageReference, PopulationSpecification,
    candidate_birth_schema, membership_manifest_schema, membership_page_schema,
    population_record_schema, population_specification_schema,
)
from amphora_contracts_population_steps import PreparedPopulationGeneration, population_step_schema

from ..population.declarations import DeclaredEvaluations
from ..population.closure import GenerationPageClosure
from ..population.dispatch import PreparedGeneration
from ..population.membership import GenerationMembership
from ..population.pages import RecordPages
from ..population.planning import PrimaryBirthBatch
from ..population.specification import OriginalPopulation
from ..ranking import require


@dataclass(frozen=True)
class PublishedGeneration:
    prepared: PreparedGeneration
    pages: tuple[PopulationArtifact,...]


@dataclass(frozen=True)
class GenerationPublication:
    original: OriginalPopulation
    source: PopulationArtifact
    batch: PrimaryBirthBatch
    identity: GenerationIdentity
    prefix: str = "seed"
    ancestry: tuple[ArtifactRef,...] = ()
    parent_births: tuple[tuple[str,ArtifactRef],...] = ()

    def publish(self, artifacts):
        spec = self.source.reference
        births=[]
        known=dict(self.parent_births)
        for birth in self.batch.births:
            parents=[spec,*self.ancestry]
            if self.identity.generation:
                for identity in birth.record.parents:
                    require(identity in known,"successor_parent_birth_unavailable")
                    parents.append(known[identity])
                if birth.record.duplicate_of is not None:
                    require(birth.record.duplicate_of in known,"successor_duplicate_birth_unavailable")
                    parents.append(known[birth.record.duplicate_of])
            artifact=artifacts.publish(birth.record,candidate_birth_schema(),tuple(parents),
                self.prefix+"/birth/"+str(birth.record.ordinal))
            births.append(artifact);known[birth.record.candidate_id]=artifact.reference
        births=tuple(births)
        by_id = {birth.record.candidate_id: artifact.reference
                 for birth, artifact in zip(self.batch.births, births, strict=True)}
        members = tuple(sorted((CandidateMember(candidate_id=b.record.candidate_id,
            birth=by_id[b.record.candidate_id], representation=by_id[b.record.candidate_id], source="seed" if self.identity.generation==0 else "offspring")
            for b in self.batch.proposed), key=lambda member: member.candidate_id))
        cohort = GenerationMembership(self.original, self.identity, "cohort", members)
        pages = []
        birth_pages = []
        for page in RecordPages(self.identity, "population.birth-page", tuple(b.record for b in self.batch.births)).pack():
            parents = tuple(by_id[b.candidate_id] for b in page.records)
            artifact = artifacts.publish(page, population_record_schema("population.birth-page"),
                (spec, *parents), self.prefix+"/birth-page/" + str(page.ordinal))
            pages.append(artifact)
            birth_pages.append(MembershipPageReference(ordinal=page.ordinal, members=len(page.records), artifact=artifact.reference))
        birth_root = publish_root(BirthManifest(schema_version="1", profile="population-birth-manifest-v1",
            generation=self.identity, birth_count=len(births), pages=tuple(birth_pages)),
            population_record_schema("population.birth-manifest"), (spec, *(p.artifact for p in birth_pages)), self.prefix+"/births",artifacts)
        cohort_pages = []
        for page in cohort.pages():
            artifact = artifacts.publish(page, membership_page_schema(),
                (spec, *(m.birth for m in page.members)), self.prefix+"/cohort-page/" + str(page.ordinal))
            pages.append(artifact)
            cohort_pages.append(MembershipPageReference(ordinal=page.ordinal, members=len(page.members), artifact=artifact.reference))
        cohort_root = publish_root(MembershipManifest(schema_version="1", profile="population-membership-manifest-v1",
            generation=self.identity, role="cohort", member_count=len(members), pages=tuple(cohort_pages)),
            membership_manifest_schema(), (spec, *(p.artifact for p in cohort_pages)), self.prefix+"/cohort",artifacts)
        declarations = DeclaredEvaluations.primary(cohort)
        slot_pages = []
        for page in RecordPages(self.identity, "population.evaluation-slot-page", declarations.slots).pack():
            artifact = artifacts.publish(page, population_record_schema("population.evaluation-slot-page"),
                (spec, cohort_root.reference), self.prefix+"/slot-page/" + str(page.ordinal))
            pages.append(artifact)
            slot_pages.append(MembershipPageReference(ordinal=page.ordinal, members=len(page.records), artifact=artifact.reference))
        declaration_root = publish_root(EvaluationDeclarationManifest(schema_version="1",
            profile="population-evaluation-declaration-manifest-v1", generation=self.identity,
            membership=cohort_root.reference, slot_set_sha256=declarations.digest,
            slot_count=len(declarations.slots), pages=tuple(slot_pages)),
            population_record_schema("population.evaluation-declarations"),
            (spec, cohort_root.reference, *(p.artifact for p in slot_pages)), self.prefix+"/declarations",artifacts)
        record = self.original.record
        GenerationPageClosure.verify(self.identity, tuple(pages))
        pins = (record.method_graph.definition, record.assembly.policy, record.constraints,
                *record.context, *record.knowledge, *(m.conditions for m in record.method_graph.methods))
        root = artifacts.publish(PreparedPopulationGeneration(schema_version="1", generation=self.identity,
            specification=spec, births=birth_root.reference, cohort=cohort_root.reference,
            declarations=declaration_root.reference), population_step_schema("population-step.prepared"),
            (spec, birth_root.reference, cohort_root.reference, declaration_root.reference, *pins, *self.ancestry), self.prefix+"/prepared")
        prepared=PreparedGeneration.verify(root,declarations,spec,cohort_root.reference,birth_root.reference,declaration_root.reference)
        return PublishedGeneration(prepared,tuple(pages))
