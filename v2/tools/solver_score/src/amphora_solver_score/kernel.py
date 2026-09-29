"""One candidate's ordered synthetic envelopes; no molecular computation or authority."""

from dataclasses import dataclass

from amphora_contracts_solver_fixture import ModuleEnvelope, ScoreRequest, ScoreResult

from .boundary import Baseline


@dataclass(frozen=True)
class CandidateEvaluation:
    request: ScoreRequest
    baseline: Baseline

    def to_result(self):
        if self.request.fail_scoring:
            raise ValueError("synthetic_scoring_failure")
        if set(self.request.error_modules) - set(self.baseline.module_ids):
            raise ValueError("unknown_fixture_module")
        return ScoreResult(candidate=self.request.candidate, modules=tuple(
            ModuleEnvelope(module_id=name, status="ERROR" if name in self.request.error_modules else "SYNTHETIC")
            for name in self.baseline.module_ids))


def compute(payload):
    request = ScoreRequest.model_validate_json(payload)
    baseline = Baseline.packaged()
    baseline.require(request.source_pins)
    return CandidateEvaluation(request, baseline).to_result().model_dump_json().encode()
