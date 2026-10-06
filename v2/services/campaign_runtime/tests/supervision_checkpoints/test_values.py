"""Explicit original scalar profile preserves legacy checkpoint bytes."""

import json

import pytest
from amphora_campaign_runtime.supervision_checkpoints import CheckpointSeed
from amphora_campaign_runtime.supervision_checkpoints.values import (
    ValueCheckpointSeed,
    read_seed,
)
from amphora_campaign_runtime.supervision_policy import ScalarRule
from amphora_contracts_graph_runtime import GraphBinding

from .test_seed import seed


def binding(value=1, *, kind='integer', port='a', unit='1'):
    record = {'kind': kind, 'value': value}
    if kind in {'integer', 'number'}:
        record['unit'] = unit
    return GraphBinding.model_validate({'port': port, 'value': record})


def test_original_fields_have_exact_digest_without_reinterpreting_legacy_seed():
    old = seed()
    current = ValueCheckpointSeed.capture(old.policy, old.footprint(), (binding(),))
    assert read_seed(old.canonical, old.policy) == old
    assert read_seed(current.canonical, old.policy) == current
    assert current.document().original_fields[0].value.value == 1
    changed = ValueCheckpointSeed.capture(old.policy, old.footprint(), (binding(2),))
    assert changed.original_fields_sha256 != current.original_fields_sha256
    assert changed.decision_id == current.decision_id == old.decision_id
    with pytest.raises(ValueError):
        CheckpointSeed(current.canonical, old.policy)
    with pytest.raises(ValueError):
        ValueCheckpointSeed(old.canonical, old.policy)


def test_unchanged_original_outside_adjustment_range_is_retained():
    old = seed()
    original = binding(11)
    current = ValueCheckpointSeed.capture(old.policy, old.footprint(), (original,))
    assert current.document().original_fields == (original,)
    assert not ScalarRule(old.policy.document().checkpoints[0].fields[0]).allows(original.value)


@pytest.mark.parametrize('values,reason', [
    ((), 'checkpoint_original_fields'),
    ((binding(), binding()), 'checkpoint_original_fields'),
    ((binding(port='other'),), 'checkpoint_original_fields'),
    ((binding(unit='kg'),), 'checkpoint_original_scalar_type'),
    ((binding('1', kind='string'),), 'checkpoint_original_scalar_type'),
    ((binding('1', kind='number'),), 'checkpoint_original_scalar_type'),
])
def test_incomplete_or_wrong_original_fields_reject(values, reason):
    old = seed()
    with pytest.raises(ValueError, match=reason):
        ValueCheckpointSeed.capture(old.policy, old.footprint(), values)


@pytest.mark.parametrize('raw,reason', [(b'', 'checkpoint_seed_size'), (b'[]', 'checkpoint_seed_profile'),
                                     (json.dumps({'profile': 'latest'}).encode(), 'checkpoint_seed_profile')])
def test_unknown_or_unbounded_seed_profile_rejects(raw, reason):
    with pytest.raises(ValueError, match=reason):
        read_seed(raw, seed().policy)
