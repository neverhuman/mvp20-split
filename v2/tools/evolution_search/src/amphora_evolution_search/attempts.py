"""Stable numeric attempt identity and evaluation correlation."""

import json
import math
from hashlib import sha256

from amphora_contracts_search import CandidateAttempt, EvaluationRequest

from .randomness import CounterRandom
from .ranking import require
from .specification import OriginalSearch, canonical_bytes


def attempt_digest(original: OriginalSearch, attempt: CandidateAttempt) -> str:
    # Outcome labels are excluded: marking a duplicate/rejection preserves attempt identity.
    parts = ["numeric-attempt-v1", original.digest, attempt.generation, attempt.ordinal,
             attempt.operator, [v.hex() for v in attempt.genes], list(attempt.parents),
             attempt.draws.start, attempt.draws.end]
    return sha256(json.dumps(parts, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


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
