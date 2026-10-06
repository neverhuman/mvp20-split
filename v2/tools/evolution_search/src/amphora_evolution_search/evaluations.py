"""Evidence-bound fitness and independently recomputed selection receipts."""

import json
from hashlib import sha256

from amphora_contracts_search import EvaluatedFitness, SelectionRank, SelectionReceipt

from .attempts import request_digest
from .ranking import CandidateScore, require


def validate_evaluations(original, record, attempts):
    pending = {p.candidate_id: p for p in record.pending}
    observations = {o.candidate_id: o for o in record.observations}
    require(len(pending) == len(record.pending), "duplicate_pending")
    require(len(observations) == len(record.observations), "duplicate_observation")
    require(not pending.keys() & observations.keys(), "pending_terminal_overlap")
    expected = {a.candidate_id for a in record.attempts if a.disposition == "proposed"}
    require(pending.keys() | observations.keys() == expected, "evaluation_membership")
    evaluation_ids = [e.evaluation_id for e in (*record.pending, *record.observations)]
    require(len(set(evaluation_ids)) == len(evaluation_ids), "duplicate_evaluation_identity")
    for item in (*record.pending, *record.observations):
        attempt = attempts[item.candidate_id]
        require(item.evaluation_id == "ev-" + attempt.candidate_id, "evaluation_identity")
        require(item.request_sha256 == request_digest(original, attempt), "evaluation_request_binding")
    for observation in record.observations:
        require(observation.scope == original.record.scope, "observation_scope")
        outcome = observation.outcome
        require(all(ref.scope == original.record.scope for ref in outcome.evidence), "fitness_evidence_scope")
        if isinstance(outcome, EvaluatedFitness):
            require(outcome.evaluator == original.record.evaluator.tool, "fitness_evaluator")
            require(outcome.constraints_sha256 == original.record.evaluator.constraints.sha256, "fitness_constraints")
            expected_objectives = tuple((o.objective_id, o.unit) for o in original.record.objectives)
            require(tuple((o.objective_id, o.unit) for o in outcome.objectives) == expected_objectives, "fitness_objectives")
    return observations


def recompute_selection(original, observations):
    require(bool(observations), "empty_selection")
    scores = []
    for item in observations:
        require(isinstance(item.outcome, EvaluatedFitness), "unavailable_selection")
        scores.append(CandidateScore(item.candidate_id, tuple(o.value for o in item.outcome.objectives),
                                     item.outcome.constraint_violation))
    count = min(original.record.budget.population_size, len(scores))
    selected = original.objectives.select(tuple(scores), count)
    membership = json.dumps(sorted(item.candidate_id for item in observations), separators=(",", ":")).encode()
    return SelectionReceipt(policy=original.record.operators.selection,
                            membership_sha256=sha256(membership).hexdigest(), requested=selected.requested,
                            selected=selected.selected,
                            ranks=tuple(SelectionRank(candidate_id=r.candidate_id, front=r.front,
                                                      boundary=r.boundary, distance=r.distance, feasible=r.feasible)
                                        for r in selected.ranks), disposition=selected.disposition)
