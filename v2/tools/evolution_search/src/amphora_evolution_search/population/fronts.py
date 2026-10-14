"""Numerical front continuity compares objective vectors, never candidate identity."""

from dataclasses import dataclass

from ..ranking import ObjectiveSpace, require


@dataclass(frozen=True)
class FitnessFront:
    vectors: frozenset[tuple[float, ...]]

    @classmethod
    def from_scores(cls, directions, scores):
        if not scores:
            return cls(frozenset())
        result = ObjectiveSpace(directions).select_population(scores, len(scores))
        front = {r.candidate_id for r in result.ranks if r.front == 0 and r.feasible}
        return cls(frozenset(s.objectives for s in scores if s.candidate_id in front))

    def unchanged_count(self, previous, prior_count):
        require(type(prior_count) is int and 0 <= prior_count < 100, "front_prior_count")
        return prior_count + 1 if self == previous else 0
