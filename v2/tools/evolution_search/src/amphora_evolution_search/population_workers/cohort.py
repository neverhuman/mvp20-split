"""Reconstruct the complete frozen primary cohort before any candidate operation."""

import hashlib
from dataclasses import dataclass
from amphora_contracts_core import ArtifactRef

from amphora_contracts_population import (
    EvaluationDeclarationManifest, MembershipManifest, PopulationSpecification,
    candidate_birth_schema, membership_manifest_schema, population_record_schema,
    population_specification_schema,
)

from ..population.declarations import DeclaredEvaluations
from ..population.membership import GenerationMembership
from ..population.planning import PrimaryBirthBatch
from ..population.specification import OriginalPopulation, canonical
from ..ranking import require


@dataclass(frozen=True)
class PrimaryCohort:
    original: OriginalPopulation
    membership_reference: ArtifactRef
    declarations: DeclaredEvaluations
    batch: PrimaryBirthBatch

    @property
    def membership(self):
        return self.declarations.membership

    @classmethod
    def load(cls, specification, declaration_reference, artifacts):
        original = OriginalPopulation(artifacts.read(specification).decode(PopulationSpecification,
            population_specification_schema(), artifacts.scope))
        require(artifacts.implementation in original.record.implementations, "population_worker_implementation")
        require(original.record.representation == candidate_birth_schema(), "population_representation_not_supported")
        declaration_artifact = artifacts.read(declaration_reference)
        declaration = declaration_artifact.decode(EvaluationDeclarationManifest,
            population_record_schema("population.evaluation-declarations"), artifacts.scope)
        cohort_artifact = artifacts.read(declaration.membership)
        cohort_record = cohort_artifact.decode(MembershipManifest, membership_manifest_schema(), artifacts.scope)
        membership = GenerationMembership.verified(original, cohort_artifact.content,
            tuple(artifacts.read(page.artifact).content for page in cohort_record.pages))
        require(membership.identity.run_id == artifacts.attempt.invocation.run_id
                and membership.identity.generation == 0 and membership.role == "cohort", "population_primary_seed_run")
        expected = PrimaryBirthBatch.seed(original)
        by_id = {birth.record.candidate_id: birth.record for birth in expected.proposed}
        require(set(membership.by_id) == set(by_id), "population_slice_birth_membership")
        for member in membership.members:
            raw = canonical(by_id[member.candidate_id])
            require(member.source == "seed" and member.representation == member.birth
                and member.birth.sha256 == hashlib.sha256(raw).hexdigest() and member.birth.size_bytes == len(raw),
                "population_slice_birth_binding")
        declarations = DeclaredEvaluations.verified(membership, declaration.membership, declaration_artifact,
            tuple(artifacts.read(page.artifact).content for page in declaration.pages))
        require(declarations.slots == DeclaredEvaluations.primary(membership).slots, "population_slice_primary_occurrences")
        return cls(original, declaration.membership, declarations, expected)
