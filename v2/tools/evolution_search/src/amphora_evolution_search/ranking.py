"""Bounded constrained Pareto fronts and deterministic normalized crowding."""

import math
import re
from dataclasses import dataclass


def require(condition, code):
    if not condition:
        raise ValueError(code)


@dataclass(frozen=True)
class CandidateScore:
    candidate_id: str
    objectives: tuple[float, ...]
    violation: float
    eligible: bool = True

    def __post_init__(self):
        require(type(self.candidate_id) is str and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}", self.candidate_id), "candidate_id")
        require(type(self.objectives) is tuple and 1 <= len(self.objectives) <= 16, "objective_vector")
        require(all(type(v) is float and math.isfinite(v) for v in self.objectives), "objective_nonfinite")
        require(type(self.violation) is float and math.isfinite(self.violation) and self.violation >= 0, "constraint_violation")
        require(type(self.eligible) is bool, "fitness_eligibility")


@dataclass(frozen=True)
class CandidateRank:
    candidate_id: str
    front: int
    boundary: bool
    distance: float
    feasible: bool

    def ordering(self):
        return self.front, not self.boundary, -self.distance, self.candidate_id


@dataclass(frozen=True)
class Selection:
    requested: int
    selected: tuple[str, ...]
    ranks: tuple[CandidateRank, ...]
    disposition: str


@dataclass(frozen=True)
class ObjectiveSpace:
    directions: tuple[str, ...]

    def __post_init__(self):
        require(type(self.directions) is tuple and 1 <= len(self.directions) <= 16, "objective_directions")
        require(all(type(d) is str and d in {"minimize", "maximize"} for d in self.directions), "objective_direction")

    def _dominates(self, left, right):
        if left.violation != right.violation:
            return left.violation < right.violation
        if left.violation > 0:
            return False
        comparisons = [(a <= b, a < b) if direction == "minimize" else (a >= b, a > b)
                       for a, b, direction in zip(left.objectives, right.objectives, self.directions, strict=True)]
        return all(pair[0] for pair in comparisons) and any(pair[1] for pair in comparisons)

    def select(self, scores, count):
        require(type(scores) is tuple and 1 <= len(scores) <= 256, "population_bound")
        require(type(count) is int and 0 <= count <= len(scores), "selection_count")
        require(all(type(s) is CandidateScore for s in scores), "candidate_score")
        require(len({s.candidate_id for s in scores}) == len(scores), "duplicate_candidate")
        require(all(s.eligible for s in scores), "fitness_not_eligible")
        require(all(len(s.objectives) == len(self.directions) for s in scores), "objective_dimension")
        members = {s.candidate_id: s for s in scores}
        identifiers = sorted(members)
        incoming = {key: 0 for key in identifiers}
        edges = {key: [] for key in identifiers}
        for index, a in enumerate(identifiers):
            for b in identifiers[index + 1:]:
                if self._dominates(members[a], members[b]):
                    edges[a].append(b)
                    incoming[b] += 1
                elif self._dominates(members[b], members[a]):
                    edges[b].append(a)
                    incoming[a] += 1
        frontier = [key for key in identifiers if incoming[key] == 0]
        rows = []
        level = 0
        while frontier:
            distance = dict.fromkeys(frontier, 0.0)
            boundary = set()
            for axis in range(len(self.directions)):
                ordered = sorted(frontier, key=lambda key: (members[key].objectives[axis], key))
                low, high = members[ordered[0]].objectives[axis], members[ordered[-1]].objectives[axis]
                if low == high:
                    continue  # A constant axis conveys no diversity and creates no arbitrary extremes.
                boundary.update((ordered[0], ordered[-1]))
                scale = max(abs(low), abs(high))
                width = high / scale - low / scale
                for index in range(1, len(ordered) - 1):
                    before = members[ordered[index - 1]].objectives[axis] / scale
                    after = members[ordered[index + 1]].objectives[axis] / scale
                    distance[ordered[index]] += (after - before) / width
            for key in sorted(frontier):
                rows.append(CandidateRank(key, level, key in boundary, distance[key], members[key].violation == 0))
            following = []
            for key in frontier:
                for other in edges[key]:
                    incoming[other] -= 1
                    if incoming[other] == 0:
                        following.append(other)
            frontier = sorted(following)
            level += 1
        ordered_rows = tuple(sorted(rows, key=lambda row: row.ordering()))
        feasible = tuple(row.candidate_id for row in ordered_rows if row.feasible)
        chosen = feasible[:count]
        disposition = ("zero_requested" if count == 0 else "no_feasible_candidates" if not feasible else
                       "insufficient_feasible_candidates" if len(chosen) < count else "selected")
        return Selection(count, chosen, ordered_rows, disposition)
