"""Metadata identity is necessary for reuse but never grants it by itself."""

import hashlib
import json
from dataclasses import dataclass

from amphora_contracts_evaluation_identity import EvaluationIdentity, EvaluationIdentityInput

from ..candidate_registration.profiles import schema_reference


class EvaluationIdentityError(ValueError):
    pass


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


@dataclass(frozen=True)
class EvaluationKey:
    record: EvaluationIdentityInput

    def __post_init__(self):
        record = EvaluationIdentityInput.model_validate_json(self.record.model_dump_json())
        object.__setattr__(self, "record", record)
        representation, policy, context = record.representation, record.policy, record.context
        if representation.scope != context.scope or representation.source.scope != context.scope:
            raise EvaluationIdentityError("evaluation_scope_mismatch")
        if representation.policy != policy.representation:
            raise EvaluationIdentityError("evaluation_representation_policy_mismatch")
        allowed = (schema_reference("candidate-space." + representation.policy.kind), schema_reference("candidate-space.change"))
        if representation.source.schema_ref not in allowed or representation.source.media_type != "application/json":
            raise EvaluationIdentityError("evaluation_source_encoding_mismatch")
        if context.material_state is not None and context.material_state.scope != context.scope:
            raise EvaluationIdentityError("evaluation_material_scope_mismatch")
        if policy.material_state_required and context.material_state is None:
            raise EvaluationIdentityError("evaluation_material_state_required")
        axes = [axis.objective_id for axis in policy.objectives]
        if len(set(axes)) != len(axes) or any(not axis.unit.strip() for axis in policy.objectives):
            raise EvaluationIdentityError("evaluation_objectives_invalid")
        required = policy.required_context
        supplied = [item.name for item in context.inputs]
        if len(set(required)) != len(required) or len(set(supplied)) != len(supplied) or set(required) != set(supplied):
            raise EvaluationIdentityError("evaluation_context_incomplete")
        refs = {}
        for item in context.inputs:
            reference = item.artifact
            if reference.scope != context.scope:
                raise EvaluationIdentityError("evaluation_context_scope_mismatch")
            previous = refs.setdefault(reference.artifact_id, reference)
            if previous != reference:
                raise EvaluationIdentityError("evaluation_context_identity_conflict")

    def _parts(self):
        representation = self.record.representation.model_dump(mode="json", exclude={"source"})
        policy = self.record.policy.model_dump(mode="json")
        policy["required_context"].sort()
        context = self.record.context.model_dump(mode="json")
        context["inputs"].sort(key=lambda item: item["name"])
        return representation, policy, context

    @property
    def bytes(self):
        representation, policy, context = self._parts()
        return canonical({"algorithm": "research-evaluation-key-v1", "representation": representation,
                          "policy": policy, "context": context})

    def same_declared_identity(self, other):
        return self.bytes == other.bytes

    def to_wire(self):
        representation, policy, context = self._parts()
        return EvaluationIdentity(wire_version="1", authority="identity_only", algorithm="research-evaluation-key-v1",
            sha256=hashlib.sha256(self.bytes).hexdigest(), source=self.record.representation.source,
            representation_sha256=digest(representation), policy_sha256=digest(policy), context_sha256=digest(context))
