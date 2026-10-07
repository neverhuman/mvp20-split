import pytest
from amphora_agent_planning.checkpoint_budget import CheckpointAllowance

from ..checkpoint_openai.test_adapter import source


@pytest.mark.parametrize('field,value', [('max_input_tokens', 65537), ('max_output_tokens', 2049),
    ('max_attempts', 2), ('total_accounting_units', 500000001), ('accounting_unit', 'other'),
    ('max_input_tokens', True)])
def test_cost_profile_rejects_widened_or_forged_limits(field, value):
    context = source().request.document().context
    with pytest.raises(ValueError):
        CheckpointAllowance.cost(context.model, context.limits.model_copy(update={field: value}))


def test_full_request_reservation_uses_pinned_integer_rates():
    context = source().request.document().context
    assert CheckpointAllowance.cost(context.model, context.limits) == 58368000
    assert CheckpointAllowance().maximum_calls * 58368000 == 350208000
    assert 350208000 < CheckpointAllowance().maximum_units == 500000000
