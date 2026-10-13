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


@pytest.mark.parametrize('version', ['1', '2', '3', '4', '6', '7', '8'])
def test_old_profiles_cannot_select_larger_output_even_in_approved_scope(version, monkeypatch):
    from amphora_agent_planning.curation_budget import ceiling
    context = source(version=version).request.document().context
    scope = context.model.configuration.scope
    monkeypatch.setattr(ceiling, 'REVIEWED_EXTENSION', (scope.tenant_id, scope.project_id))
    with pytest.raises(ValueError, match='curation_cost_limits'):
        CurationAllowance.cost(context.model, context.limits.model_copy(update={'max_output_tokens': 16384}))


def test_v5_larger_cost_requires_exact_scope_and_retains_hard_limits(monkeypatch):
    from amphora_agent_planning.curation_budget import ceiling
    context = source(version='5', max_output_tokens=16384, total_tokens=278528,
                     total_accounting_units=300000000).request.document().context
    with pytest.raises(ValueError, match='curation_extended_scope'):
        CurationAllowance.cost(context.model, context.limits)
    scope = context.model.configuration.scope
    monkeypatch.setattr(ceiling, 'REVIEWED_EXTENSION', (scope.tenant_id, scope.project_id))
    assert CurationAllowance.cost(context.model, context.limits) == 270336000
    for field, value in [('max_input_tokens', 262145), ('max_output_tokens', 16385),
                         ('max_attempts', 2), ('total_accounting_units', 300000001)]:
        with pytest.raises(ValueError, match='curation_cost_limits'):
            CurationAllowance.cost(context.model, context.limits.model_copy(update={field: value}))
