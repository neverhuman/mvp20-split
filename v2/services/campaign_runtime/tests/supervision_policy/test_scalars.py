"""Exact decimal and scientific-unit boundaries, without implicit coercion."""

import pytest
from amphora_campaign_runtime.supervision_policy import ScalarRule
from amphora_campaign_runtime.supervision_policy.records import FieldPolicyRecord
from amphora_contracts_graph_runtime import GraphBinding


def value(kind, payload, unit='1'):
    record = {'kind': kind, 'value': payload}
    if kind in {'number', 'integer'}:
        record['unit'] = unit
    return GraphBinding.model_validate({'port': 'field', 'value': record}).value


def field(kind='number', lower='0', upper='10', unit='1'):
    return FieldPolicyRecord.model_validate({'name': 'temperature',
        'value_type': {'kind': 'scalar', 'scalar': kind, 'unit': unit}, 'constraint': {'kind': 'range',
        'minimum': {'kind': 'number', 'value': lower, 'unit': unit},
        'maximum': {'kind': 'number', 'value': upper, 'unit': unit}}})


def test_decimal_edges_and_units_are_exact():
    policy = ScalarRule(field(lower='0.1000000000000000000000000001', upper='0.1000000000000000000000000002', unit='K'))
    assert policy.allows(value('number', '0.1000000000000000000000000001', 'K'))
    assert policy.allows(value('number', '0.1000000000000000000000000002', 'K'))
    assert not policy.allows(value('number', '0.1', 'K'))
    assert not policy.allows(value('number', '0.1000000000000000000000000003', 'K'))
    assert not policy.allows(value('number', '0.1000000000000000000000000001', 'C'))


def test_integer_never_accepts_float_or_boolean_and_number_can_accept_integer():
    integer = ScalarRule(field('integer'))
    assert integer.allows(value('integer', 5))
    assert not integer.allows(value('number', '5'))
    assert not integer.allows(value('boolean', True))
    assert ScalarRule(field()).allows(value('integer', 5))
    with pytest.raises(ValueError, match='scalar_adjustment_outside_policy'):
        integer.require_allowed(value('integer', 11))
    integer.require_allowed(value('integer', 10))


@pytest.mark.parametrize('kind,items,good,bad', [('string', ['water', 'ethanol'], 'water', 'methanol'),
                                              ('boolean', [True], True, False)])
def test_finite_choices(kind, items, good, bad):
    record = FieldPolicyRecord.model_validate({'name': 'choice', 'value_type': {'kind': 'scalar', 'scalar': kind},
        'constraint': {'kind': 'choices', 'values': tuple(value(kind, item) for item in items)}})
    policy = ScalarRule(record)
    assert policy.allows(value(kind, good)) and not policy.allows(value(kind, bad))


@pytest.mark.parametrize('record,reason', [
    (field(lower='2', upper='1'), 'policy_bound_order'),
    (field('integer', lower='0.5'), 'policy_integer_bounds'),
    (field('integer', upper='9007199254740992'), 'policy_integer_bounds'),
    (field('string'), 'policy_constraint_kind'),
    (field('boolean', unit='K'), 'policy_nonnumeric_unit'),
])
def test_invalid_range_policy(record, reason):
    with pytest.raises(ValueError, match=reason):
        ScalarRule(record)


def test_bound_units_and_duplicate_or_wrong_choice_types_reject():
    record = field().model_dump(mode='json')
    record['constraint']['minimum']['unit'] = 'kg'
    with pytest.raises(ValueError, match='policy_bound_unit'):
        ScalarRule(FieldPolicyRecord.model_validate(record))
    for choices, reason in [([True, True], 'policy_duplicate_choice'), (['true'], 'policy_choice_type')]:
        record = {'name': 'flag', 'value_type': {'kind': 'scalar', 'scalar': 'boolean'},
            'constraint': {'kind': 'choices', 'values': tuple(value('boolean' if type(x) is bool else 'string', x) for x in choices)}}
        with pytest.raises(ValueError, match=reason):
            ScalarRule(FieldPolicyRecord.model_validate(record))


@pytest.mark.parametrize('raw', ['NaN', 'Infinity', '1e5', '01', '0.' + '1' * 325])
def test_nonfinite_or_nonportable_bounds_reject(raw):
    with pytest.raises(ValueError):
        field(lower=raw)
