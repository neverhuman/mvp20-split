"""Bounded exact-Dot ranking with explicit selection and no quality threshold."""

import math
from dataclasses import dataclass

from amphora_contracts_representations import RepresentationBindingRef

from ...representations.mapping import _validated
from ..validation import require


def binding_key(reference):
    return reference.binding_id, reference.sha256


@dataclass(frozen=True, slots=True)
class QueryPolicy:
    top_k: int
    bindings: tuple[RepresentationBindingRef, ...] | None = None

    def __post_init__(self):
        require(type(self.top_k) is int and 1 <= self.top_k <= 256, "retrieval_top_k")
        if self.bindings is not None:
            require(type(self.bindings) is tuple and len(self.bindings) <= 256, "retrieval_filter_bound")
            for ref in self.bindings:
                _validated(ref, RepresentationBindingRef)
            keys = [binding_key(ref) for ref in self.bindings]
            require(len(set(keys)) == len(keys), "retrieval_filter_duplicate")
            object.__setattr__(self, "bindings", tuple(sorted(self.bindings, key=binding_key)))

    def descriptor(self):
        return {
            "format": "data.exact-dot-ranking.v1",
            "top_k": self.top_k,
            "bindings": None if self.bindings is None else [b.model_dump(mode="json") for b in self.bindings],
            "metric": "dot",
            "order": "score_desc_binding_asc",
            "quality_filter": "none",
        }

    def select(self, manifest):
        if self.bindings is None:
            return manifest.bindings
        by_key = {binding_key(b.reference): b for b in manifest.bindings}
        for ref in self.bindings:
            require(ref.scope == manifest.scope, "retrieval_filter_scope")
            require(binding_key(ref) in by_key, "retrieval_filter_member")
        return tuple(by_key[binding_key(ref)] for ref in self.bindings)

    def rank(self, eligible, scores):
        """Eligibility is an owner input, never inferred from similarity or caller claims."""
        require(type(eligible) is tuple and len(eligible) <= 256, "retrieval_eligible_bound")
        expected = {}
        for binding in eligible:
            key = binding_key(binding.reference)
            require(key not in expected, "retrieval_eligible_duplicate")
            expected[key] = binding.reference
        require(type(scores) is tuple and len(scores) <= 256, "retrieval_scores_bound")
        seen = set()
        for score in scores:
            require(type(score) is BindingScore, "retrieval_score_required")
            key = binding_key(score.binding)
            require(expected.get(key) == score.binding, "retrieval_score_member")
            require(key not in seen, "retrieval_score_duplicate")
            seen.add(key)
        require(seen == set(expected), "retrieval_scores_incomplete")
        return tuple(sorted(scores, key=lambda s: (-s.value, *binding_key(s.binding))))[:self.top_k]


@dataclass(frozen=True, slots=True)
class BindingScore:
    binding: RepresentationBindingRef
    value: float

    def __post_init__(self):
        _validated(self.binding, RepresentationBindingRef)
        try:
            valid = type(self.value) in (int, float) and math.isfinite(float(self.value))
        except OverflowError:
            valid = False
        require(valid, "retrieval_score_finite")
        object.__setattr__(self, "value", float(self.value) if self.value else 0.0)
