"""A bounded initial numeric population; returns requests without dispatching them."""

from dataclasses import dataclass

from amphora_contracts_search import (
    CandidateAttempt,
    EvaluationRequest,
    PendingEvaluation,
    RngInterval,
    SearchCheckpoint,
    SearchProgress,
)

from .attempts import AttemptIdentity, evaluation_request, request_digest
from .checkpoint import CheckpointSnapshot
from .randomness import CounterRandom
from .ranking import require
from .specification import OriginalSearch


@dataclass(frozen=True)
class InitialPopulation:
    original: OriginalSearch
    attempts: tuple[CandidateAttempt, ...]
    requests: tuple[EvaluationRequest, ...]
    random: CounterRandom

    def __post_init__(self):
        expected = tuple(evaluation_request(self.original, a) for a in self.attempts if a.disposition == "proposed")
        require(self.requests == expected, "initial_request_set")
        self.checkpoint()

    @classmethod
    def generate(cls, original: OriginalSearch):
        rng = original.initial_random()
        attempts, requests, seen = [], [], {}
        budget = original.record.budget
        for ordinal in range(budget.population_size):
            start = rng.counter
            genes, rng = original.box.sample(rng)
            identity = AttemptIdentity(0, ordinal, "seed", genes, (), RngInterval(start=start, end=rng.counter))
            if genes in seen:
                attempt = identity.to_record(original, disposition="duplicate", reason_code="duplicate_genes",
                                             duplicate_of=seen[genes])
            elif len(requests) >= budget.max_evaluations:
                attempt = identity.to_record(original, disposition="rejected", reason_code="evaluation_budget")
            else:
                attempt = identity.to_record(original, disposition="proposed")
                seen[genes] = attempt.candidate_id
                requests.append(evaluation_request(original, attempt))
            attempts.append(attempt)
        return cls(original, tuple(attempts), tuple(requests), rng)

    def checkpoint(self) -> CheckpointSnapshot:
        pending = tuple(PendingEvaluation(evaluation_id=request.evaluation_id,
                                          candidate_id=request.candidate.candidate_id,
                                          request_sha256=request_digest(self.original, request.candidate))
                        for request in self.requests)
        progress = SearchProgress(evaluations_issued=len(pending), evaluations_terminal=0,
                                  generations_completed=0, unchanged_front_generations=0)
        record = SearchCheckpoint(schema_version="1", specification=self.original.record,
                                  specification_sha256=self.original.digest, previous=None, generation=0,
                                  phase="awaiting_evaluations" if pending else "stopped", rng=self.random.to_record(),
                                  attempts=self.attempts, population=(), pending=pending, observations=(), selection=None,
                                  progress=progress, stop_reason=None if pending else "evaluation_budget")
        return CheckpointSnapshot(self.original, record)
