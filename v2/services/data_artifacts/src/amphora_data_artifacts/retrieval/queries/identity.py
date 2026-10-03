"""Full query provenance; neither a generation ref nor a digest grants access."""

from dataclasses import dataclass

from amphora_contracts_representations import RepresentationBinding

from ...representations.bindings.receipts import validate_binding_projection
from ..identity import GenerationPlan
from ..validation import fingerprint, identifier, require
from .policy import QueryPolicy


@dataclass(frozen=True, slots=True)
class QueryPlan:
    retrieval_id: str
    actor_id: str
    generation: GenerationPlan
    query: RepresentationBinding
    policy: QueryPolicy

    def __post_init__(self):
        identifier(self.retrieval_id)
        identifier(self.actor_id)
        require(type(self.generation) is GenerationPlan, "retrieval_plan_required")
        require(type(self.policy) is QueryPolicy, "retrieval_policy_required")
        manifest = self.generation.manifest
        validate_binding_projection(manifest.scope, self.query)
        require(self.query.profile == manifest.profile_reference, "retrieval_query_profile")
        require(manifest.profile.space.metric == "dot", "retrieval_query_metric")
        self.policy.select(manifest)

    def descriptor(self):
        return {
            "format": "data.retrieval-query.v1",
            "retrieval_id": self.retrieval_id,
            "actor_id": self.actor_id,
            "generation": self.generation.reference.descriptor(),
            "query": self.query.model_dump(mode="json"),
            "policy": self.policy.descriptor(),
        }

    @property
    def sha256(self):
        return fingerprint(self.descriptor())
