"""Immutable result identity, without a claim of database or access authority."""

from dataclasses import dataclass

from ..validation import fingerprint, require
from .identity import QueryPlan
from .policy import BindingScore, binding_key


@dataclass(frozen=True, slots=True)
class QueryRecord:
    plan: QueryPlan
    matches: tuple[BindingScore, ...]

    def __post_init__(self):
        require(type(self.plan) is QueryPlan, "retrieval_query_required")
        require(
            type(self.matches) is tuple and len(self.matches) <= self.plan.policy.top_k,
            "retrieval_matches_bound",
        )
        members = {binding_key(b.reference): b for b in self.plan.policy.select(self.plan.generation.manifest)}
        selected = []
        for match in self.matches:
            require(type(match) is BindingScore, "retrieval_score_required")
            binding = members.get(binding_key(match.binding))
            require(binding is not None and binding.reference == match.binding, "retrieval_match_member")
            selected.append(binding)
        require(
            self.plan.policy.rank(tuple(selected), self.matches) == self.matches,
            "retrieval_matches_order",
        )

    def descriptor(self):
        return {
            "format": "data.retrieval-result.v1",
            "query_sha256": self.plan.sha256,
            "matches": [
                {"binding": match.binding.model_dump(mode="json"), "score": match.value}
                for match in self.matches
            ],
        }

    @property
    def sha256(self):
        return fingerprint(self.descriptor())
