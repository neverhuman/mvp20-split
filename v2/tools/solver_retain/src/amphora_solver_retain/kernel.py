"""Ordered association and one immutable current/cumulative generation checkpoint."""

from dataclasses import dataclass

from amphora_contracts_solver_fixture import Checkpoint, MissingResult, RetainInput, SolverState

from .boundary import Baseline


@dataclass(frozen=True)
class GenerationFold:
    request: RetainInput
    baseline: Baseline

    def to_state(self):
        batch, slots = self.request.batch, self.request.results
        previous = batch.state
        if batch.generation != previous.generation + 1 or batch.generation > previous.config.generations:
            raise ValueError("generation_cut_mismatch")
        old_ids = tuple(result.candidate.candidate_id for result in previous.cumulative)
        proposed_ids = tuple(item.candidate.candidate_id for item in batch.candidates)
        if len(set(old_ids)) != len(old_ids) or len(set(proposed_ids)) != len(proposed_ids) or set(old_ids) & set(proposed_ids):
            raise ValueError("duplicate_candidate_identity")
        if len(previous.checkpoints) != previous.generation + 1:
            raise ValueError("checkpoint_cut_mismatch")
        if previous.checkpoints:
            last = previous.checkpoints[-1]
            if last.generation != previous.generation or last.cumulative_ids != old_ids or last.current_ids != tuple(
                    result.candidate.candidate_id for result in previous.current):
                raise ValueError("checkpoint_cut_mismatch")
        elif previous.current or previous.cumulative:
            raise ValueError("nonempty_initial_state")
        if any(item not in previous.cumulative for item in previous.current):
            raise ValueError("current_not_in_cumulative")
        if len(slots) != len(batch.candidates):
            raise ValueError("result_membership_mismatch")
        current, failed = [], []
        for expected, observed in zip(batch.candidates, slots, strict=True):
            self.baseline.require(expected.source_pins)
            if isinstance(observed, MissingResult):
                failed.append(expected.candidate.candidate_id)
                continue
            if observed.candidate != expected.candidate:
                raise ValueError("result_candidate_mismatch")
            if tuple(item.module_id for item in observed.modules) != self.baseline.module_ids:
                raise ValueError("module_order_mismatch")
            current.append(observed)
        if not current:
            raise ValueError("no_successful_candidates")
        cumulative = (*previous.cumulative, *current)
        checkpoint = Checkpoint(generation=batch.generation, current_ids=tuple(item.candidate.candidate_id for item in current),
            cumulative_ids=tuple(item.candidate.candidate_id for item in cumulative), failed_ids=tuple(failed),
            rejection_seeds=tuple(item.proposal_seed for item in batch.rejections))
        return SolverState(config=previous.config, generation=batch.generation, current=tuple(current), cumulative=cumulative,
                           checkpoints=(*previous.checkpoints, checkpoint))


def compute(payload):
    request = RetainInput.model_validate_json(payload)
    baseline = Baseline.packaged()
    baseline.require(request.batch.state.config.source_pins)
    return GenerationFold(request, baseline).to_state().model_dump_json().encode()
