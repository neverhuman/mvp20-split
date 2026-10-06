"""The score is deliberately meaningless scientifically and exact computationally."""
import hashlib
import json
from dataclasses import dataclass

from amphora_contracts_evaluation_identity import EvaluationIdentityInput
from amphora_contracts_synthetic_evaluation import SyntheticEvaluationReceipt
from amphora_contracts_tools import ToolBinding

from .profile import APPLICABILITY, METHOD, UNCERTAINTY

MAX_PAYLOAD = 262144


def unique_object(pairs):
    result = {}
    for name, value in pairs:
        if name in result:
            raise ValueError('duplicate_json_key')
        result[name] = value
    return result


def reject_constant(_value):
    raise ValueError('nonfinite_json_constant')


@dataclass(frozen=True, slots=True)
class DigestEvaluation:
    declaration: EvaluationIdentityInput
    input_sha256: str

    @classmethod
    def parse(cls, payload, binding: ToolBinding):
        if type(payload) is not bytes or len(payload) > MAX_PAYLOAD:
            raise ValueError('invalid_payload_capacity')
        value = json.loads(payload.decode('utf-8'), object_pairs_hook=unique_object, parse_constant=reject_constant)
        request = EvaluationIdentityInput.model_validate_json(json.dumps(value, allow_nan=False))
        policy, representation, context = request.policy, request.representation, request.context
        if (policy.method.evaluator != binding or policy.method.method != METHOD
                or policy.method.applicability != APPLICABILITY or policy.purpose != 'synthetic-cache-qualification'):
            raise ValueError('unsupported_evaluation_method')
        if len(policy.objectives) != 1:
            raise ValueError('unsupported_objectives')
        axis = policy.objectives[0]
        if (axis.objective_id != 'synthetic-digest-score' or axis.unit != '1'
                or axis.direction != 'minimize' or axis.uncertainty_policy != UNCERTAINTY):
            raise ValueError('unsupported_objective')
        if (representation.scope != context.scope or representation.source.scope != context.scope
                or representation.policy != policy.representation
                or (context.material_state is not None and context.material_state.scope != context.scope)
                or any(item.artifact.scope != context.scope for item in context.inputs)):
            raise ValueError('incoherent_evaluation_declaration')
        names = [item.name for item in context.inputs]
        if (len(set(names)) != len(names) or len(set(policy.required_context)) != len(policy.required_context)
                or set(names) != set(policy.required_context)
                or (policy.material_state_required and context.material_state is None)):
            raise ValueError('incomplete_evaluation_context')
        return cls(request, hashlib.sha256(payload).hexdigest())

    def to_wire(self):
        record = self.declaration
        digest = record.representation.canonical_sha256
        return SyntheticEvaluationReceipt(wire_version='1', authority='synthetic_evaluation',
            scope=record.context.scope, input_sha256=self.input_sha256, canonical_sha256=digest,
            method=record.policy.method, objective_id='synthetic-digest-score', unit='1',
            value=int(digest[:6], 16))

    def output(self):
        return json.dumps(self.to_wire().model_dump(mode='json'), sort_keys=True,
                          separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode('utf-8')
