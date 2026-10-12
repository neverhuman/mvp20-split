import pytest
from amphora_agent_planning.curation_budget import CurationAllowance
from ..curation_openai.test_adapter import source


def test_fixed_integer_ceiling_and_full_envelope_reservation():
    context = source().request.document().context
    assert CurationAllowance.cost(context.model, context.limits) == 233472000
    assert CurationAllowance.maximum_calls == 4
    assert CurationAllowance.maximum_units == 1000000000
    assert CurationAllowance.maximum_per_call == 250000000


@pytest.mark.parametrize('field,value', [('max_input_tokens', 262145), ('max_output_tokens', 8193),
    ('max_attempts', 2), ('total_accounting_units', 250000001), ('accounting_unit', 'other'),
    ('max_input_tokens', True)])
def test_limits_cannot_be_widened(field, value):
    context = source().request.document().context
    with pytest.raises(ValueError):
        CurationAllowance.cost(context.model, context.limits.model_copy(update={field: value}))
