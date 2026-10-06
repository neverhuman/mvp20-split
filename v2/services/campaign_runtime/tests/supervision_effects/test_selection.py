"""Independent scalar selection and replay oracles; no execution authority claim."""

import hashlib
import json

import pytest
from amphora_campaign_runtime.supervision_checkpoints.values import ValueCheckpointSeed
from amphora_campaign_runtime.supervision_effects import (
    FieldChange,
    ScalarSelection,
    scalar_digest,
)
from amphora_contracts_campaigns import ActivationPath

from ..supervision_checkpoints.test_seed import seed
from ..supervision_checkpoints.test_values import binding
from .support import typed_seed


def original(*, nested=False):
    legacy = seed(nested=nested)
    return ValueCheckpointSeed.capture(legacy.policy, legacy.footprint(), (binding(),))


def path(value):
    return value.document().observations[0].node.path


def change(*, value=2, name='a', prior=None, kind='integer', unit='1'):
    return FieldChange(name=name, previous_value_sha256=prior or scalar_digest(binding().value),
                       value=binding(value, kind=kind, unit=unit).value)


def test_exact_selection_roundtrip_and_overlay_preserve_original_and_other_fields():
    value = original(nested=True)
    selected = ScalarSelection.bind(value, path(value), (change(),))
    assert ScalarSelection(selected.canonical, value) == selected
    assert selected.sha256 == hashlib.sha256(selected.canonical).hexdigest()
    inputs = (binding(port='other', value=9), binding())
    assert selected.resolve(inputs) == (binding(port='other', value=9), binding(2))
    assert value.document().original_fields == (binding(),)
    assert inputs == (binding(port='other', value=9), binding())
    assert scalar_digest(binding().value) == hashlib.sha256(b'{"kind":"integer","unit":"1","value":1}').hexdigest()


@pytest.mark.parametrize('proposed,reason', [
    (change(name='unknown'), 'selection_field_not_permitted'),
    (change(prior='f' * 64), 'selection_prior_value'),
    (change(value=11), 'scalar_adjustment_outside_policy'),
    (change(value=-1), 'scalar_adjustment_outside_policy'),
    (change(unit='kg'), 'scalar_adjustment_outside_policy'),
    (change(value='2', kind='number'), 'scalar_adjustment_outside_policy'),
    (change(value='2', kind='string'), 'scalar_adjustment_outside_policy'),
    (change(value=True, kind='boolean'), 'scalar_adjustment_outside_policy'),
])
def test_unauthorized_changes_reject(proposed, reason):
    value = original()
    with pytest.raises(ValueError, match=reason):
        ScalarSelection.bind(value, path(value), (proposed,))


def test_legacy_seed_duplicate_fields_and_other_occurrence_reject():
    legacy = seed()
    with pytest.raises(ValueError, match='selection_requires_scalar_seed'):
        ScalarSelection.bind(legacy, path(legacy), (change(),))
    value = original(nested=True)
    with pytest.raises(ValueError, match='selection_field_order_or_duplicate'):
        ScalarSelection.bind(value, path(value), (change(), change()))
    other = ActivationPath.model_validate_json(json.dumps({'schema_version': '2', 'node_id': 'pack',
        'occurrences': [{'kind': 'loop', 'node_id': 'loop', 'index': 1}]}))
    with pytest.raises(ValueError, match='selection_target_occurrence'):
        ScalarSelection.bind(value, other, (change(),))


@pytest.mark.parametrize('fields,reason', [
    ((), 'selection_current_original_mismatch'),
    ((binding(3),), 'selection_current_original_mismatch'),
    ((binding(), binding()), 'selection_duplicate_original'),
])
def test_overlay_revalidates_original_values(fields, reason):
    value = original()
    selected = ScalarSelection.bind(value, path(value), (change(),))
    with pytest.raises(ValueError, match=reason):
        selected.resolve(fields)


@pytest.mark.parametrize('alteration,reason', [
    ('padding', 'noncanonical_scalar_selection'), ('empty', 'selection_size'),
    ('seed_sha256', 'selection_seed_binding'), ('decision_id', 'selection_seed_binding'),
])
def test_corrupted_durable_selection_rejects(alteration, reason):
    value = original()
    selected = ScalarSelection.bind(value, path(value), (change(),))
    raw = selected.canonical
    if alteration == 'padding':
        raw += b' '
    elif alteration == 'empty':
        raw = b''
    else:
        data = json.loads(raw)
        data[alteration] = 'f' * 64
        raw = json.dumps(data, sort_keys=True, separators=(',', ':')).encode()
    with pytest.raises(ValueError, match=reason):
        ScalarSelection(raw, value)


@pytest.mark.parametrize('kind,initial,allowed,proposed', [
    ('number', '0.25', ('0', '1'), '0.12345678901234567890123456789'),
    ('number', '0.25', ('0', '1'), '1.000'),
    ('boolean', False, (True, False), True),
    ('string', 'water', ('water', 'ethanol'), 'ethanol'),
])
def test_exact_decimal_and_choice_values_survive_selection(kind, initial, allowed, proposed):
    value = typed_seed(kind, initial, allowed)
    before, after = binding(initial, kind=kind), binding(proposed, kind=kind)
    selected = ScalarSelection.bind(value, path(value), (FieldChange(name='a',
        previous_value_sha256=scalar_digest(before.value), value=after.value),))
    assert selected.resolve((before,)) == (after,)
    assert selected.document().changes[0].value.value == proposed


def test_exact_decimal_bound_does_not_round_into_range():
    value = typed_seed('number', '0.25', ('0', '1'))
    after = binding('1.00000000000000000000000000001', kind='number')
    with pytest.raises(ValueError, match='scalar_adjustment_outside_policy'):
        ScalarSelection.bind(value, path(value), (FieldChange(name='a',
            previous_value_sha256=scalar_digest(binding('0.25', kind='number').value), value=after.value),))


def test_outside_range_original_can_be_corrected_without_rewriting_seed():
    legacy = seed()
    value = ValueCheckpointSeed.capture(legacy.policy, legacy.footprint(), (binding(11),))
    selected = ScalarSelection.bind(value, path(value), (change(value=10, prior=scalar_digest(binding(11).value)),))
    assert selected.resolve((binding(11),)) == (binding(10),)
    assert value.document().original_fields == (binding(11),)
