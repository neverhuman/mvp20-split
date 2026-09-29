"""One initial proposal batch; no candidate evaluation or generation loop."""

from dataclasses import dataclass

from amphora_contracts_solver_fixture import (
    Candidate,
    ProposalBatch,
    Rejection,
    ScoreRequest,
    SolverConfig,
    SolverState,
)

from .boundary import Baseline


@dataclass(frozen=True)
class InitialPopulation:
    config: SolverConfig

    def to_batch(self):
        requests, rejected = [], []
        for index in range(self.config.population):
            seed = self.config.seed + index
            if index and seed in self.config.reject_mutation_seeds:
                rejected.append(Rejection(generation=0, proposal_index=index, proposal_seed=seed, parent_id="c0"))
                continue
            candidate = Candidate(candidate_id=f"c{index}", parent_ids=() if index == 0 else ("c0",),
                generation=0, proposal_index=index, proposal_seed=seed, scoring_seed=self.config.seed + len(requests))
            requests.append(ScoreRequest(source_pins=self.config.source_pins, candidate=candidate,
                fail_scoring=candidate.scoring_seed in self.config.fail_scoring_seeds, error_modules=self.config.error_modules))
        empty = SolverState(config=self.config, generation=-1, current=(), cumulative=(), checkpoints=())
        return ProposalBatch(state=empty, generation=0, candidates=tuple(requests), rejections=tuple(rejected))


def compute(payload):
    config = SolverConfig.model_validate_json(payload)
    baseline = Baseline.packaged()
    baseline.require(config.source_pins)
    if set(config.error_modules) - set(baseline.module_ids):
        raise ValueError("unknown_fixture_module")
    return InitialPopulation(config).to_batch().model_dump_json().encode()
