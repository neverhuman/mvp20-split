"""Stable numeric attempt identity and evaluation correlation."""

import json
import math
from dataclasses import dataclass
from hashlib import sha256

from amphora_contracts_search import CandidateAttempt, EvaluationRequest, RngInterval

from .randomness import CounterRandom
from .ranking import require
from .specification import OriginalSearch, canonical_bytes


@dataclass(frozen=True)
class AttemptIdentity:
    generation: int
    ordinal: int
    operator: str
    genes: tuple[float, ...]
    parents: tuple[str, ...]
    draws: RngInterval

    @classmethod
    def from_record(cls, attempt: CandidateAttempt):
        return cls(attempt.generation, attempt.ordinal, attempt.operator, attempt.genes, attempt.parents, attempt.draws)

    def digest(self, original: OriginalSearch) -> str:
        # Outcome labels are excluded: marking a duplicate/rejection preserves identity.
        parts = ["numeric-attempt-v1", original.digest, self.generation, self.ordinal,
                 self.operator, [v.hex() for v in self.genes], list(self.parents), self.draws.start, self.draws.end]
        return sha256(json.dumps(parts, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()

    def to_record(self, original, *, disposition, reason_code=None, duplicate_of=None):
        return CandidateAttempt(candidate_id=self.digest(original), generation=self.generation,
                                ordinal=self.ordinal, operator=self.operator, genes=self.genes, parents=self.parents,
                                draws=self.draws, disposition=disposition, reason_code=reason_code, duplicate_of=duplicate_of)


def attempt_digest(original: OriginalSearch, attempt: CandidateAttempt) -> str:
    return AttemptIdentity.from_record(attempt).digest(original)


def validate_attempt(original: OriginalSearch, attempt: CandidateAttempt) -> None:
    require(all(math.isfinite(v) for v in attempt.genes), "attempt_finite")
    require(len(attempt.genes) == len(original.record.variables), "attempt_dimensions")
    require(attempt.candidate_id == attempt_digest(original, attempt), "attempt_identity")
    require(attempt.draws.start <= attempt.draws.end, "attempt_draws")
    require(len(set(attempt.parents)) == len(attempt.parents), "attempt_parents")
    if attempt.operator == "seed":
        require(attempt.generation == 0 and not attempt.parents, "seed_ancestry")
        require(attempt.draws.end - attempt.draws.start == len(attempt.genes), "seed_draws")
        genes, _ = original.box.sample(CounterRandom(original.record.seed, attempt.draws.start))
        require(attempt.genes == genes, "seed_replay")
    else:
        require(attempt.generation > 0 and bool(attempt.parents), "variation_ancestry")
    if attempt.disposition == "proposed":
        require(attempt.reason_code is None and attempt.duplicate_of is None, "proposed_disposition")
        require(original.box.contains(attempt.genes), "attempt_bounds")
    elif attempt.disposition == "duplicate":
        require(attempt.reason_code == "duplicate_genes" and attempt.duplicate_of is not None, "duplicate_disposition")
        require(original.box.contains(attempt.genes), "attempt_bounds")
    else:
        require(attempt.reason_code is not None and attempt.duplicate_of is None, "rejected_disposition")


def evaluation_request(original: OriginalSearch, attempt: CandidateAttempt) -> EvaluationRequest:
    validate_attempt(original, attempt)
    require(attempt.disposition == "proposed", "not_evaluable")
    return EvaluationRequest(schema_version="1", scope=original.record.scope,
                             evaluation_id="ev-" + attempt.candidate_id,
                             specification_sha256=original.digest, candidate=attempt,
                             objectives=original.record.objectives, evaluator=original.record.evaluator)


def request_digest(original: OriginalSearch, attempt: CandidateAttempt) -> str:
    return sha256(canonical_bytes(evaluation_request(original, attempt))).hexdigest()


def validate_seed_batch(original, attempts):
    require(len(attempts) == original.record.budget.population_size, "seed_population_size")
    proposed = {}
    for attempt in attempts:
        if attempt.genes in proposed:
            require(attempt.disposition == "duplicate" and attempt.duplicate_of == proposed[attempt.genes], "seed_disposition")
        elif len(proposed) >= original.record.budget.max_evaluations:
            require(attempt.disposition == "rejected" and attempt.reason_code == "evaluation_budget", "seed_disposition")
        else:
            require(attempt.disposition == "proposed", "seed_disposition")
            proposed[attempt.genes] = attempt.candidate_id
