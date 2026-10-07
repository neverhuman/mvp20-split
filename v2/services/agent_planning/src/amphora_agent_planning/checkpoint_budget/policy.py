"""Explicit first-demo cost profile; no refunds or in-memory call counters."""

from dataclasses import dataclass

from amphora_contracts_planning import CallLimits

from ..checkpoint_input import CheckpointInputBound, checkpoint_tokenizer_reference
from ..context.policy import require
from ..openai_provider.pricing import UNIT, OpenAIPrice


@dataclass(frozen=True)
class CheckpointAllowance:
    maximum_calls: int = 6
    maximum_units: int = 500000000

    @staticmethod
    def applies(request):
        model = request.document().context.model
        return model.provider_id == 'openai' and model.tokenizer == checkpoint_tokenizer_reference()

    @staticmethod
    def cost(model, limits):
        CheckpointInputBound.bind(model)
        limits = CallLimits.model_validate(limits.model_dump(mode='python', warnings=False))
        require(limits.accounting_unit == UNIT, 'checkpoint_cost_unit')
        require(limits.max_input_tokens <= 65536 and limits.max_output_tokens <= 2048 and
                limits.max_attempts == 1 and limits.total_accounting_units <= 500000000,
                'checkpoint_cost_limits')
        return OpenAIPrice().estimate(limits.max_input_tokens, limits.max_output_tokens)

    @classmethod
    def validate_policy(cls, policy):
        record = policy.document()
        cost = cls.cost(record.model, record.limits)
        require(record.per_attempt_accounting_units >= cost, 'checkpoint_cost_underreserved')
        return cost
