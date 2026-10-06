"""Reduce a complete frozen result set exactly once as a pure state transition."""

from dataclasses import dataclass

from amphora_contracts_graph_runtime import MissingValue
from amphora_contracts_search import (
    EvaluatedFitness,
    EvaluationObservation,
    UnavailableFitness,
)

from .checkpoint import CheckpointSnapshot
from .evaluations import recompute_selection
from .ranking import CandidateScore, require
from .step_context import BoundCheckpoint


def _front(original, observations, membership):
    if not membership:
        return frozenset()
    by_id = {o.candidate_id: o for o in observations}
    scores = tuple(CandidateScore(c, tuple(v.value for v in by_id[c].outcome.objectives),
                                  by_id[c].outcome.constraint_violation) for c in membership)
    ranked = original.objectives.select(scores, len(scores))
    front = {r.candidate_id for r in ranked.ranks if r.front == 0 and r.feasible}
    return frozenset(s.objectives for s in scores if s.candidate_id in front)


@dataclass(frozen=True)
class GenerationReducer:
    source: BoundCheckpoint

    def collect(self, results: tuple[EvaluationObservation | MissingValue, ...]) -> CheckpointSnapshot:
        snapshot = self.source.snapshot
        original, state = snapshot.original, snapshot.record
        require(type(results) is tuple and len(results) == len(state.pending), "terminal_result_count")
        if state.phase == "stopped":
            return snapshot
        require(state.phase in {"awaiting_evaluations", "ready_to_select"}, "reduction_source_phase")
        incoming = []
        for index, result in enumerate(results):
            if isinstance(result, MissingValue):
                require(result.member_id == str(index), "missing_result_position")
                pending = state.pending[index]
                result = EvaluationObservation(schema_version="1", scope=original.record.scope,
                                                evaluation_id=pending.evaluation_id, candidate_id=pending.candidate_id,
                                                request_sha256=pending.request_sha256,
                                                outcome=UnavailableFitness(status="failed", reason_code=result.reason_code, evidence=()))
            require(isinstance(result, EvaluationObservation), "terminal_result_shape")
            incoming.append(result)
        observations = tuple(sorted((*state.observations, *incoming), key=lambda o: o.candidate_id))
        progress = state.progress.model_copy(update={"evaluations_terminal": state.progress.evaluations_terminal + len(incoming)})
        ready = state.model_copy(update={"previous": self.source.reference, "pending": (), "observations": observations,
                                         "phase": "ready_to_select", "progress": progress})
        CheckpointSnapshot(original, ready)  # Validate the complete membership before using any numeric fitness.
        if any(not isinstance(o.outcome, EvaluatedFitness) for o in observations):
            progress = progress.model_copy(update={"generations_completed": state.generation})
            return CheckpointSnapshot(original, ready.model_copy(update={"phase": "stopped", "stop_reason": "unavailable_fitness",
                                                                         "progress": progress}))
        selection = recompute_selection(original, observations)
        unchanged = 0
        if state.generation > 0 and _front(original, observations, state.population) == _front(original, observations, selection.selected):
            unchanged = progress.unchanged_front_generations + 1
        progress = progress.model_copy(update={"generations_completed": state.generation, "unchanged_front_generations": unchanged})
        budget = original.record.budget
        reason = None
        if not selection.selected:
            reason = "no_feasible_candidates"
        elif state.generation == budget.max_generations:
            reason = "generation_budget"
        elif progress.evaluations_issued == budget.max_evaluations:
            reason = "evaluation_budget"
        elif budget.unchanged_front_limit is not None and unchanged >= budget.unchanged_front_limit:
            reason = "unchanged_front"
        record = ready.model_copy(update={"phase": "stopped" if reason else "selected", "selection": selection,
                                          "population": selection.selected, "progress": progress, "stop_reason": reason})
        return CheckpointSnapshot(original, record)
