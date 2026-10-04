"""Owner-configured ceilings cannot be widened by a request or model output."""

import hashlib
import json
from dataclasses import dataclass
from typing import Annotated, Literal

from amphora_contracts_core import ArtifactRef, SafePositiveInt, SchemaRef, WireModel
from amphora_contracts_planning import CallLimits, ModelBinding, ProposalAction, ProviderAttemptRef
from pydantic import Field, ValidationError

from ..context import AttemptBinding
from ..context.policy import require
from ..context.snapshot import _constant, _object


class _PolicyRecord(WireModel):
    format: Literal["planning-budget-policy.v1"]
    model: ModelBinding
    prompt: ArtifactRef
    policy: ArtifactRef
    output_schema: SchemaRef
    allowed_actions: Annotated[tuple[ProposalAction, ...], Field(min_length=1, max_length=4)]
    limits: CallLimits
    per_attempt_accounting_units: SafePositiveInt


@dataclass(frozen=True)
class ReservationDemand:
    attempt: ProviderAttemptRef
    policy_sha256: str
    input_tokens: int
    output_tokens: int
    accounting_units: int

    @property
    def tokens(self):
        return self.input_tokens + self.output_tokens


@dataclass(frozen=True)
class BudgetPolicy:
    canonical: bytes

    @classmethod
    def from_bytes(cls, raw: bytes) -> "BudgetPolicy":
        require(type(raw) is bytes and 0 < len(raw) <= 16384, "budget_policy_size")
        try:
            value = json.loads(raw.decode("utf-8"), object_pairs_hook=_object, parse_constant=_constant)
            record = _PolicyRecord.model_validate_json(json.dumps(value, allow_nan=False))
        except (UnicodeDecodeError, json.JSONDecodeError, ValidationError, RecursionError) as exc:
            raise ValueError("invalid_budget_policy") from exc
        require(record.model.configuration.scope == record.prompt.scope == record.policy.scope,
                "budget_policy_scope")
        require(len(set(record.allowed_actions)) == len(record.allowed_actions), "budget_policy_actions")
        tokens = record.limits.max_input_tokens + record.limits.max_output_tokens
        require(tokens <= record.model.context_window_tokens and tokens <= record.limits.total_tokens,
                "budget_policy_tokens")
        require(record.per_attempt_accounting_units <= record.limits.total_accounting_units,
                "budget_policy_accounting")
        canonical = json.dumps(record.model_dump(mode="json"), sort_keys=True, separators=(",", ":"),
                               ensure_ascii=False, allow_nan=False).encode("utf-8")
        require(len(canonical) <= 16384, "budget_policy_size")
        return cls(canonical)

    @property
    def sha256(self):
        return hashlib.sha256(self.canonical).hexdigest()

    def document(self):
        return _PolicyRecord.model_validate_json(self.canonical)

    def demand(self, attempt: AttemptBinding) -> ReservationDemand:
        policy = self.document()
        context = attempt.request.document().context
        require(context.model == policy.model and context.prompt == policy.prompt and context.policy == policy.policy
                and context.output_schema == policy.output_schema, "budget_policy_binding")
        require(set(context.allowed_actions) <= set(policy.allowed_actions), "budget_actions_exceeded")
        require(context.limits.accounting_unit == policy.limits.accounting_unit, "budget_unit_mismatch")
        for name in ("max_input_tokens", "max_output_tokens", "max_attempts", "total_tokens", "total_accounting_units"):
            require(getattr(context.limits, name) <= getattr(policy.limits, name), "budget_ceiling_exceeded")
        require(policy.per_attempt_accounting_units <= context.limits.total_accounting_units,
                "attempt_accounting_exceeded")
        return ReservationDemand(attempt.reference(), self.sha256, context.limits.max_input_tokens,
                                 context.limits.max_output_tokens, policy.per_attempt_accounting_units)
