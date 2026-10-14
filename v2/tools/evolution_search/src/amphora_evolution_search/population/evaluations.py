"""Bind a method occurrence to one immutable cohort; no accepted-execution claim."""

import hashlib
import json
from dataclasses import dataclass

from amphora_contracts_population import EvaluationKey, MethodObservation

from ..ranking import require
from .membership import GenerationMembership
from .specification import canonical


def consistent_references(references):
    known = {}
    for reference in references:
        require(known.setdefault(reference.artifact_id, reference) == reference, "evaluation_reference_conflict")


@dataclass(frozen=True)
class BoundEvaluation:
    membership: GenerationMembership
    record: EvaluationKey

    def __post_init__(self):
        record = EvaluationKey.model_validate_json(self.record.model_dump_json())
        object.__setattr__(self, "record", record)
        require(len(canonical(record)) <= 8192, "evaluation_key_bytes")
        require(record.generation == self.membership.identity, "evaluation_generation")
        candidates = {member.candidate_id: member for member in self.membership.members}
        require(record.candidate_id in candidates, "evaluation_candidate")
        require(record.material == candidates[record.candidate_id].representation, "evaluation_material")
        original = self.membership.original.record
        methods = {method.method_id: method for method in original.method_graph.methods}
        require(record.method_id in methods, "evaluation_method")
        method = methods[record.method_id]
        require(record.tool == method.tool and record.conditions == method.conditions, "evaluation_method_pins")
        require(record.objective_policy_sha256 == original.assembly.policy.sha256, "evaluation_objective_policy")
        require(len({r.artifact_id for r in record.inputs}) == len(record.inputs), "evaluation_input_duplicate")
        require(record.material in record.inputs, "evaluation_material_input")
        require(all(r.scope == record.generation.scope for r in record.inputs), "evaluation_input_scope")
        consistent_references((record.material, record.conditions, *record.inputs, original.constraints,
                               *original.context, *original.knowledge, original.assembly.policy, original.method_graph.definition))

    @property
    def digest(self):
        return hashlib.sha256(b"amphora.population/evaluation-v1\0" + canonical(self.record)).hexdigest()

    def observation(self, record):
        checked = MethodObservation.model_validate_json(record.model_dump_json())
        require(len(canonical(checked)) <= 8192, "evaluation_observation_bytes")
        require(checked.key == self.record and checked.evaluation_sha256 == self.digest, "evaluation_observation_key")
        outcome = checked.outcome
        if outcome.producer is not None:
            require(outcome.producer.run_id == self.record.generation.run_id, "evaluation_producer_run")
        if outcome.status == "evaluated":
            require(len({o.port for o in outcome.outputs}) == len(outcome.outputs), "evaluation_output_duplicate")
            references = tuple(output.artifact for output in outcome.outputs)
            method = next(m for m in self.membership.original.record.method_graph.methods if m.method_id == self.record.method_id)
            require(sum(r.schema_ref == method.output_schema for r in references) == 1, "evaluation_primary_output")
        else:
            references = outcome.evidence
        require(all(r.scope == self.record.generation.scope for r in references), "evaluation_output_scope")
        consistent_references((*references, self.record.material, self.record.conditions, *self.record.inputs))
        return checked


@dataclass(frozen=True)
class FrozenEvaluations:
    membership: GenerationMembership
    keys: tuple[BoundEvaluation, ...]

    def __post_init__(self):
        ceiling = 8000 if self.membership.role == "cohort" else 16000
        require(type(self.keys) is tuple and len(self.keys) <= ceiling, "evaluation_set_bound")
        require(all(key.membership == self.membership for key in self.keys), "evaluation_mixed_membership")
        require(len({key.digest for key in self.keys}) == len(self.keys), "evaluation_expected_duplicate")
        required = {method.method_id for method in self.membership.original.record.method_graph.methods if method.required}
        covered = {(key.record.candidate_id, key.record.method_id) for key in self.keys}
        require(all((member.candidate_id, method) in covered for member in self.membership.members for method in required),
                "evaluation_required_coverage")

    @property
    def digest(self):
        value = {"generation": self.membership.identity.model_dump(mode="json"), "role": self.membership.role,
                 "members": [member.candidate_id for member in self.membership.members],
                 "keys": sorted(key.digest for key in self.keys)}
        raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
        return hashlib.sha256(b"amphora.population/evaluation-set-v1\0" + raw).hexdigest()

    def terminal(self, observations):
        return frozen_terminal_set(self.keys, observations)


def frozen_terminal_set(expected, observations):
    """Match exactly the supplied keys; FrozenEvaluations separately validates coverage."""
    require(type(expected) is tuple and len(expected) <= 16000, "evaluation_set_bound")
    require(type(observations) is tuple and len(observations) == len(expected), "evaluation_terminal_coverage")
    if expected:
        require(all(item.membership == expected[0].membership for item in expected), "evaluation_mixed_membership")
    keys = {item.digest: item for item in expected}
    require(len(keys) == len(expected), "evaluation_expected_duplicate")
    records = {}
    for observation in observations:
        key = observation.evaluation_sha256
        require(key in keys and key not in records, "evaluation_terminal_duplicate_or_unknown")
        records[key] = keys[key].observation(observation)
    return tuple(records[key] for key in sorted(records))
