"""Approved four-call/$1 scope group with at most$0.25 reserved per request."""
from dataclasses import dataclass

from amphora_contracts_campaign_curation import campaign_curation_draft_schema
from amphora_contracts_planning import CallLimits

from ..curation_input import CurationInputBound
from ..context.policy import require
from ..openai_provider.pricing import UNIT, OpenAIPrice


@dataclass(frozen=True)
class CallCeiling:
    output_tokens: int = 8192
    reservation_units: int = 250000000

    @classmethod
    def for_model(cls, model):
        from . import ceiling
        profile = CurationInputBound.bind(model)
        if profile.envelope_version == '5':
            scope = model.configuration.scope
            require((scope.tenant_id, scope.project_id) == ceiling.REVIEWED_EXTENSION,
                    'curation_extended_scope')
            return cls(16384, 300000000)
        return cls()


class CurationAllowance:
    maximum_calls = 4
    maximum_units = 1000000000
    maximum_per_call = 250000000

    @staticmethod
    def applies(request):
        context = request.document().context
        return context.model.provider_id == 'openai' and (
            context.output_schema.schema_id == 'planning.campaign-curation-draft'
            or context.model.tokenizer.schema_id in {'planning.curation-openai-input-bound', 'planning.curation-openai-input-bound.v2', 'planning.curation-openai-input-bound.v3', 'planning.curation-openai-input-bound.v4', 'planning.curation-openai-input-bound.v5'})

    @classmethod
    def cost(cls, model, limits):
        ceiling = CallCeiling.for_model(model)
        limits = CallLimits.model_validate(limits.model_dump(mode='python', warnings=False))
        require(limits.accounting_unit == UNIT, 'curation_cost_unit')
        require(limits.max_input_tokens <= 262144 and limits.max_output_tokens <= ceiling.output_tokens
                and limits.max_attempts == 1 and limits.total_accounting_units <= ceiling.reservation_units,
                'curation_cost_limits')
        return OpenAIPrice().estimate(limits.max_input_tokens, limits.max_output_tokens)

    @classmethod
    def validate_policy(cls, policy):
        record = policy.document()
        require(record.output_schema == campaign_curation_draft_schema(), 'curation_cost_output_profile')
        cost = cls.cost(record.model, record.limits)
        require(cost <= record.per_attempt_accounting_units <= CallCeiling.for_model(record.model).reservation_units, 'curation_cost_reservation')
        return cost
