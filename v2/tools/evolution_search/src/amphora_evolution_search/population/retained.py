"""Verify supplied population Artifact bytes; no filesystem/network/owner acceptance."""

import hashlib
from dataclasses import dataclass

from amphora_contracts_core import ArtifactRef
from amphora_contracts_population import EvaluationManifest, ObservationManifest, FitnessManifest, membership_manifest_schema, population_record_schema

from ..ranking import require
from .evaluations import BoundEvaluation, FrozenEvaluations, observation_cut
from .fitness import FitnessEvidence
from .pages import RecordPages
from .specification import canonical
from .selection import PopulationSelection


@dataclass(frozen=True)
class PopulationArtifact:
    reference: ArtifactRef
    content: bytes

    def decode(self, model, schema, scope):
        reference = ArtifactRef.model_validate_json(self.reference.model_dump_json())
        require(reference.scope == scope and reference.schema_ref == schema and reference.media_type == "application/json",
                "population_artifact_binding")
        require(type(self.content) is bytes and len(self.content) <= 262144, "population_artifact_bytes")
        require(reference.size_bytes == len(self.content) and reference.sha256 == hashlib.sha256(self.content).hexdigest(),
                "population_artifact_digest")
        record = model.model_validate_json(self.content)
        require(canonical(record) == self.content, "population_artifact_canonical")
        return record


@dataclass(frozen=True)
class RetainedEvaluations:
    artifact: PopulationArtifact
    frozen: FrozenEvaluations

    @classmethod
    def verify(cls, membership, membership_reference, artifact, payloads):
        require(membership_reference.scope == membership.identity.scope
                and membership_reference.schema_ref == membership_manifest_schema(), "evaluation_membership_reference")
        root = artifact.decode(EvaluationManifest, population_record_schema("population.evaluation-manifest"), membership.identity.scope)
        require(root.generation == membership.identity and root.membership == membership_reference, "evaluation_manifest_source")
        pages = RecordPages.verified(root.generation, "population.evaluation-key-page", root.pages, payloads, root.evaluation_count)
        frozen = FrozenEvaluations(membership, tuple(BoundEvaluation(membership, key) for key in pages.records))
        require(frozen.digest == root.evaluation_set_sha256, "evaluation_manifest_set")
        return cls(artifact, frozen)

    def observations(self, artifact, payloads):
        root = artifact.decode(ObservationManifest, population_record_schema("population.observation-manifest"),
                               self.frozen.membership.identity.scope)
        require(root.generation == self.frozen.membership.identity and root.evaluations == self.artifact.reference
                and root.evaluation_set_sha256 == self.frozen.digest, "observation_manifest_source")
        pages = RecordPages.verified(root.generation, "population.method-observation-page", root.pages, payloads, root.terminal_count)
        evidence = FitnessEvidence(self.frozen, pages.records)
        require(observation_cut(evidence.observations) == root.observation_cut_sha256, "observation_manifest_cut")
        return RetainedObservations(artifact, evidence)


@dataclass(frozen=True)
class RetainedObservations:
    artifact: PopulationArtifact
    evidence: FitnessEvidence


@dataclass(frozen=True)
class RetainedFitness:
    artifact: PopulationArtifact
    selection: PopulationSelection

    @classmethod
    def verify(cls, pool, pool_reference, artifact, payloads, sources):
        require(pool_reference.scope == pool.identity.scope and pool_reference.schema_ref == membership_manifest_schema(),
                "fitness_pool_reference")
        root = artifact.decode(FitnessManifest, population_record_schema("population.fitness-manifest"), pool.identity.scope)
        require(root.generation == pool.identity and root.pool == pool_reference, "fitness_manifest_source")
        require(type(sources) is tuple and root.observations == tuple(source.artifact.reference for source in sources),
                "fitness_observation_sources")
        require(len({source.artifact.reference.artifact_id for source in sources}) == len(sources), "fitness_observation_duplicate")
        evidence = {source.evidence.evaluations.digest: source.evidence for source in sources}
        require(len(evidence) == len(sources), "fitness_observation_cut_ambiguous")
        rows = RecordPages.verified(root.generation, "population.fitness-page", root.pages, payloads, root.member_count)
        require(all(row.evaluation_set_sha256 in evidence for row in rows.records), "fitness_observation_missing")
        fitness = tuple(evidence[row.evaluation_set_sha256].bind(row) for row in rows.records)
        return cls(artifact, PopulationSelection(pool, fitness))
