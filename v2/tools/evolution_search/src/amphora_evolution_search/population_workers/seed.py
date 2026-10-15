"""Publish one complete synthetic birth-as-representation seed generation."""

from dataclasses import dataclass

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
class SeedPreparation:
    original: OriginalPopulation
    source: object
    batch: PrimaryBirthBatch
    identity: GenerationIdentity

    @classmethod
    def load(cls, request, artifacts):
        source = artifacts.read(request.specification)
        original = OriginalPopulation(source.decode(PopulationSpecification,
            population_specification_schema(), artifacts.scope))
        require(artifacts.implementation in original.record.implementations, "population_worker_implementation")
        # This explicit fixture needs no invented numeric-vector schema or encoder.
        # Other scientific representations require their own registered producer.
        require(original.record.representation == candidate_birth_schema(), "population_representation_not_supported")
        batch = PrimaryBirthBatch.seed(original)
        identity = GenerationIdentity(scope=artifacts.scope, run_id=artifacts.attempt.invocation.run_id,
            specification_sha256=original.digest, generation=0, predecessor=None)
        return cls(original, source, batch, identity)

    def publish(self, artifacts):
        spec = self.source.reference
        births = tuple(artifacts.publish(birth.record, candidate_birth_schema(), (spec,),
            "seed/birth/" + str(birth.record.ordinal)) for birth in self.batch.births)
        by_id = {birth.record.candidate_id: artifact.reference
                 for birth, artifact in zip(self.batch.births, births, strict=True)}
        members = tuple(sorted((CandidateMember(candidate_id=b.record.candidate_id,
            birth=by_id[b.record.candidate_id], representation=by_id[b.record.candidate_id], source="seed")
            for b in self.batch.proposed), key=lambda member: member.candidate_id))
        cohort = GenerationMembership(self.original, self.identity, "cohort", members)
        pages = []
        birth_pages = []
        for page in RecordPages(self.identity, "population.birth-page", tuple(b.record for b in self.batch.births)).pack():
            parents = tuple(by_id[b.candidate_id] for b in page.records)
            artifact = artifacts.publish(page, population_record_schema("population.birth-page"),
                (spec, *parents), "seed/birth-page/" + str(page.ordinal))
            pages.append(artifact)
            birth_pages.append(MembershipPageReference(ordinal=page.ordinal, members=len(page.records), artifact=artifact.reference))
        birth_root = artifacts.publish(BirthManifest(schema_version="1", profile="population-birth-manifest-v1",
            generation=self.identity, birth_count=len(births), pages=tuple(birth_pages)),
            population_record_schema("population.birth-manifest"), (spec, *(p.artifact for p in birth_pages)), "seed/births")
        cohort_pages = []
        for page in cohort.pages():
            artifact = artifacts.publish(page, membership_page_schema(),
                (spec, *(m.birth for m in page.members)), "seed/cohort-page/" + str(page.ordinal))
            pages.append(artifact)
            cohort_pages.append(MembershipPageReference(ordinal=page.ordinal, members=len(page.members), artifact=artifact.reference))
        cohort_root = artifacts.publish(MembershipManifest(schema_version="1", profile="population-membership-manifest-v1",
            generation=self.identity, role="cohort", member_count=len(members), pages=tuple(cohort_pages)),
            membership_manifest_schema(), (spec, *(p.artifact for p in cohort_pages)), "seed/cohort")
        declarations = DeclaredEvaluations.primary(cohort)
        slot_pages = []
        for page in RecordPages(self.identity, "population.evaluation-slot-page", declarations.slots).pack():
            artifact = artifacts.publish(page, population_record_schema("population.evaluation-slot-page"),
                (spec, cohort_root.reference), "seed/slot-page/" + str(page.ordinal))
            pages.append(artifact)
            slot_pages.append(MembershipPageReference(ordinal=page.ordinal, members=len(page.records), artifact=artifact.reference))
        declaration_root = artifacts.publish(EvaluationDeclarationManifest(schema_version="1",
            profile="population-evaluation-declaration-manifest-v1", generation=self.identity,
            membership=cohort_root.reference, slot_set_sha256=declarations.digest,
            slot_count=len(declarations.slots), pages=tuple(slot_pages)),
            population_record_schema("population.evaluation-declarations"),
            (spec, cohort_root.reference, *(p.artifact for p in slot_pages)), "seed/declarations")
        record = self.original.record
        GenerationPageClosure.verify(self.identity, tuple(pages))
        pins = (record.method_graph.definition, record.assembly.policy, record.constraints,
                *record.context, *record.knowledge, *(m.conditions for m in record.method_graph.methods))
        root = artifacts.publish(PreparedPopulationGeneration(schema_version="1", generation=self.identity,
            specification=spec, births=birth_root.reference, cohort=cohort_root.reference,
            declarations=declaration_root.reference), population_step_schema("population-step.prepared"),
            (spec, birth_root.reference, cohort_root.reference, declaration_root.reference, *pins), "seed/prepared")
        PreparedGeneration.verify(root, declarations, spec, cohort_root.reference,
                                  birth_root.reference, declaration_root.reference)
        return root
