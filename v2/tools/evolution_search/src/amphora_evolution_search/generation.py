"""One successor population transition; the authored graph owns iteration."""

from dataclasses import dataclass

from amphora_contracts_search import PendingEvaluation, RngInterval

from .attempts import AttemptIdentity, evaluation_request, request_digest
from .checkpoint import CheckpointSnapshot
from .ranking import require
from .step_context import BoundCheckpoint
from .variation import BoxVariation, ParentVector


@dataclass(frozen=True)
class SuccessorPopulation:
    source: BoundCheckpoint

    def create(self) -> CheckpointSnapshot:
        snapshot = self.source.snapshot
        original, state = snapshot.original, snapshot.record
        if state.phase == "stopped":
            return snapshot
        require(state.phase == "selected" and bool(state.population), "variation_source_phase")
        budget = original.record.budget
        require(state.generation < budget.max_generations
                and state.progress.evaluations_issued < budget.max_evaluations, "variation_budget")
        by_id = {a.candidate_id: a for a in state.attempts}
        retained = tuple(by_id[c] for c in state.population)
        parents = tuple(ParentVector(a.candidate_id, a.genes) for a in retained)
        observations = tuple(o for o in state.observations if o.candidate_id in state.population)
        seen = {a.genes: a.candidate_id for a in retained}
        rng = original.resume_random(state.rng)
        operator = BoxVariation(original)
        attempts, pending = [], []
        for ordinal in range(budget.population_size):
            draw = operator.draw(parents, rng)
            rng = draw.after
            identity = AttemptIdentity(state.generation + 1, ordinal, "variation", draw.genes, draw.parents,
                                       RngInterval(start=draw.before.counter, end=draw.after.counter))
            if draw.genes in seen:
                attempt = identity.to_record(original, disposition="duplicate", reason_code="duplicate_genes",
                                             duplicate_of=seen[draw.genes])
            elif state.progress.evaluations_issued + len(pending) >= budget.max_evaluations:
                attempt = identity.to_record(original, disposition="rejected", reason_code="evaluation_budget")
            else:
                attempt = identity.to_record(original, disposition="proposed")
                request = evaluation_request(original, attempt)
                pending.append(PendingEvaluation(evaluation_id=request.evaluation_id,
                                                 candidate_id=attempt.candidate_id,
                                                 request_sha256=request_digest(original, attempt)))
                seen[draw.genes] = attempt.candidate_id
            attempts.append(attempt)
        progress = state.progress.model_copy(update={"evaluations_issued": state.progress.evaluations_issued + len(pending)})
        record = state.model_copy(update={"previous": self.source.reference, "generation": state.generation + 1,
                                          "phase": "awaiting_evaluations" if pending else "ready_to_select",
                                          "rng": rng.to_record(), "attempts": (*retained, *attempts),
                                          "pending": tuple(pending), "observations": observations,
                                          "selection": None, "progress": progress, "stop_reason": None})
        return CheckpointSnapshot(original, record)
