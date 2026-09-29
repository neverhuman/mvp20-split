"""One lineage-only proposal generation with explicit compacted scoring indices."""

from dataclasses import dataclass

from amphora_contracts_solver_fixture import Candidate, ProposalBatch, Rejection, ScoreRequest, Selection

from .boundary import Baseline


@dataclass(frozen=True)
class ProposalGeneration:
    selection: Selection

    def to_batch(self):
        state, parents = self.selection.state, self.selection.parents
        generation = state.generation + 1
        if not 1 <= generation <= state.config.generations:
            raise ValueError("no_next_generation")
        if any(parent not in tuple(result.candidate for result in state.current) for parent in parents):
            raise ValueError("parent_not_current")
        if len({parent.candidate_id for parent in parents}) != len(parents):
            raise ValueError("duplicate_parent")
        base_seed = state.config.seed + generation * 10_000
        requests, rejected = [], []
        for index in range(state.config.population):
            parent = parents[index % len(parents)]
            seed = base_seed + index
            if seed in state.config.reject_mutation_seeds:
                rejected.append(Rejection(generation=generation, proposal_index=index, proposal_seed=seed,
                                          parent_id=parent.candidate_id))
                continue
            candidate = Candidate(candidate_id=f"g{generation}p{index}", parent_ids=(parent.candidate_id,),
                generation=generation, proposal_index=index, proposal_seed=seed, scoring_seed=base_seed + len(requests))
            requests.append(ScoreRequest(source_pins=state.config.source_pins, candidate=candidate,
                fail_scoring=candidate.scoring_seed in state.config.fail_scoring_seeds, error_modules=state.config.error_modules))
        return ProposalBatch(state=state, generation=generation, candidates=tuple(requests), rejections=tuple(rejected))


def compute(payload):
    selection = Selection.model_validate_json(payload)
    Baseline.packaged().require(selection.state.config.source_pins)
    return ProposalGeneration(selection).to_batch().model_dump_json().encode()
