"""Independent implementation of the documented fixed quadratic problem."""

import json
import math
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


def canonical(record):
    return json.dumps(record.model_dump(mode="json"), sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode()


@dataclass(frozen=True)
class PolicyBinding:
    reference: ArtifactRef
    content: bytes

    def __post_init__(self):
        if self.content != policy_bytes():
            raise ValueError("synthetic_policy_content")
        if (self.reference.sha256 != sha256(self.content).hexdigest()
                or self.reference.size_bytes != len(self.content)
                or self.reference.media_type != "application/json"
                or self.reference.schema_ref != schema_ref("policy")):
            raise ValueError("synthetic_policy_binding")


@dataclass(frozen=True)
class SyntheticProblem:
    request: EvaluationRequest
    binding: ToolBinding
    policy: PolicyBinding

    def __post_init__(self):
        request = self.request
        candidate = request.candidate
        objectives = request.objectives
        if (self.binding != tool_binding(self.binding.image_sha256)
                or request.evaluator.tool != self.binding
                or request.evaluator.constraints != self.policy.reference
                or self.policy.reference.scope != request.scope
                or request.evaluator.context
                or request.evaluation_id != "ev-" + candidate.candidate_id
                or candidate.disposition != "proposed"
                or not 1 <= len(candidate.genes) <= 32
                or any(not math.isfinite(gene) or abs(gene) > 1000000 for gene in candidate.genes)
                or not objectives
                or len({item.objective_id for item in objectives}) != len(objectives)
                or any(item.objective_id not in {"cost", "distance"}
                       or item.unit != "dimensionless" for item in objectives)):
            raise ValueError("invalid_synthetic_objective_input")

    def evaluate(self):
        genes = self.request.candidate.genes
        values = {"cost": sum(gene * gene for gene in genes),
                  "distance": sum((gene - 1) * (gene - 1) for gene in genes)}
        fitness = EvaluatedFitness(
            status="evaluated", evaluator=self.binding,
            objectives=tuple(ObjectiveValue(objective_id=item.objective_id,
                                           unit=item.unit, value=values[item.objective_id])
                             for item in self.request.objectives),
            constraint_violation=0.0, constraints_sha256=self.policy.reference.sha256,
            quality="synthetic", evidence=(self.policy.reference,))
        return EvaluationObservation(
            schema_version="1", scope=self.request.scope, evaluation_id=self.request.evaluation_id,
            candidate_id=self.request.candidate.candidate_id,
            request_sha256=sha256(canonical(self.request)).hexdigest(), outcome=fitness)
