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
        from .generation_publication import GenerationPublication
        return GenerationPublication(self.original,self.source,self.batch,self.identity).publish(artifacts).prepared.artifact
