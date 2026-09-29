"""Source-order parent intersection and fallback; no ranking authority."""

from dataclasses import dataclass

from amphora_contracts_solver_fixture import Selection, SolverState

from .boundary import Baseline


@dataclass(frozen=True)
class ParentPool:
    state: SolverState

    def select(self):
        state = self.state
        if not 0 <= state.generation < state.config.generations:
            raise ValueError("no_next_generation")
        current = {result.candidate.candidate_id: result for result in state.current}
        cumulative = {result.candidate.candidate_id: result for result in state.cumulative}
        if len(current) != len(state.current) or len(cumulative) != len(state.cumulative):
            raise ValueError("duplicate_candidate_identity")
        if any(cumulative.get(key) != value for key, value in current.items()):
            raise ValueError("current_not_in_cumulative")
        if not current:
            raise ValueError("empty_parent_population")
        # Equal synthetic display/feasibility keys: frozen source finally sorts candidate IDs.
        top = sorted(cumulative)[:state.config.population]
        selected = tuple(current[key].candidate for key in top if key in current)
        return Selection(state=state, parents=selected or tuple(result.candidate for result in state.current),
                         used_fallback=not selected)


def compute(payload):
    state = SolverState.model_validate_json(payload)
    Baseline.packaged().require(state.config.source_pins)
    return ParentPool(state).select().model_dump_json().encode()
