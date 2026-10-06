"""A fixed synthetic problem with explicit applicability and provenance checks."""

import json
from dataclasses import dataclass
from hashlib import sha256

from amphora_contracts_core import ArtifactRef
from amphora_contracts_search import (
    EvaluatedFitness,
    EvaluationObservation,
    EvaluationRequest,
    ObjectiveValue,
)
from amphora_contracts_tools import ToolBinding

from .metadata import policy_bytes, schema_ref, tool_binding


def require(condition, code):
    if not condition:
        raise ValueError(code)


@dataclass(frozen=True)
class PolicyBinding:
    reference: ArtifactRef
    data: bytes

    def __post_init__(self):
        checked = ArtifactRef.model_validate_json(self.reference.model_dump_json())
        object.__setattr__(self, "reference", checked)
        require(type(self.data) is bytes and self.data == policy_bytes(), "synthetic_policy_content")
        require(checked.schema_ref == schema_ref("policy") and checked.media_type == "application/json"
                and checked.sha256 == sha256(self.data).hexdigest() and checked.size_bytes == len(self.data), "synthetic_policy_binding")


@dataclass(frozen=True)
class SyntheticProblem:
    request: EvaluationRequest
    binding: ToolBinding
    policy: PolicyBinding

    def __post_init__(self):
        checked = EvaluationRequest.model_validate_json(self.request.model_dump_json())
        object.__setattr__(self, "request", checked)
        require(checked.evaluator.tool == self.binding == tool_binding(self.binding.image_sha256), "synthetic_evaluator_binding")
        require(checked.evaluation_id == "ev-" + checked.candidate.candidate_id, "synthetic_evaluation_identity")
        require(checked.candidate.disposition == "proposed" and checked.candidate.reason_code is None
                and checked.candidate.duplicate_of is None, "synthetic_candidate_disposition")
        require(all(abs(gene) <= 1e6 for gene in checked.candidate.genes), "synthetic_gene_bounds")
        ids = [o.objective_id for o in checked.objectives]
        require(len(ids) == len(set(ids)) and set(ids) <= {"cost", "distance"}, "synthetic_objectives")
        require(all(o.unit == "dimensionless" for o in checked.objectives), "synthetic_units")
        require(not checked.evaluator.context, "synthetic_context_unsupported")
        require(self.policy.reference == checked.evaluator.constraints and self.policy.reference.scope == checked.scope,
                "synthetic_policy_identity")

    def evaluate(self) -> EvaluationObservation:
        request = self.request
        genes = request.candidate.genes
        values = {"cost": sum(gene * gene for gene in genes), "distance": sum((gene - 1) ** 2 for gene in genes)}
        raw = json.dumps(request.model_dump(mode="json"), sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False, allow_nan=False).encode()
        outcome = EvaluatedFitness(status="evaluated", evaluator=self.binding,
                                   objectives=tuple(ObjectiveValue(objective_id=o.objective_id, unit=o.unit,
                                                                   value=values[o.objective_id]) for o in request.objectives),
                                   constraint_violation=0.0, constraints_sha256=request.evaluator.constraints.sha256,
                                   quality="synthetic", evidence=(request.evaluator.constraints,))
        return EvaluationObservation(schema_version="1", scope=request.scope, evaluation_id=request.evaluation_id,
                                     candidate_id=request.candidate.candidate_id, request_sha256=sha256(raw).hexdigest(), outcome=outcome)
