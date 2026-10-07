"""Compact framing preserves validation semantics and prior replay/cost profiles."""

import copy
import json
from dataclasses import replace

import pytest
from amphora_agent_planning.campaign_packet import prepare
from amphora_agent_planning.checkpoint_budget import CheckpointAllowance
from amphora_agent_planning.checkpoint_input import CheckpointEnvelope, checkpoint_tokenizer_reference
from amphora_agent_planning.checkpoint_input.schema import guidance, without_titles
from amphora_agent_planning.context import RequestSnapshot
from jsonschema import Draft202012Validator

from .test_profile import live_plan


def compact(source):
    record = source.request.document().model_dump(mode='json')
    record['context']['model']['tokenizer'] = checkpoint_tokenizer_reference('2').model_dump(mode='json')
    request = RequestSnapshot.from_bytes(json.dumps(record).encode(), actor_id=record['actor_id'],
                                         scope=source.request.document().reference.scope)
    return replace(source, request=request)


def test_schema_positions_preserve_named_title_properties_and_instance_values():
    original = {'title': 'Annotation', 'type': 'object', 'properties': {
        'title': {'title': 'Field annotation', 'type': 'string', 'const': 'Required title'}},
        'required': ['title'], 'additionalProperties': False,
        'default': {'title': 'Must remain data'}, 'examples': [{'title': 'Also data'}]}
    before = copy.deepcopy(original)
    result = without_titles(original)
    assert original == before and 'title' not in result
    assert result['properties']['title'] == {'type': 'string', 'const': 'Required title'}
    assert result['default'] == original['default'] and result['examples'] == original['examples']
    for value in ({'title': 'Required title'}, {}, {'title': 1}, {'title': 'other'}, {'title': 'Required title', 'extra': 1}):
        assert Draft202012Validator(original).is_valid(value) == Draft202012Validator(result).is_valid(value)
    assert without_titles(True) is True and without_titles(False) is False


def test_real_checkpoint_guidance_keeps_all_constraints_and_both_profiles():
    original, reduced = guidance('1'), guidance('2')
    assert reduced == without_titles(original)
    assert len(json.dumps(reduced)) < len(json.dumps(original)) - 5000
    Draft202012Validator.check_schema(reduced)
    assert checkpoint_tokenizer_reference().sha256 == '3a80e73a4be13c0681f1f87e56c672b7ac0ce623a8456b1b1f92c892b640d9d5'
    assert checkpoint_tokenizer_reference('1') != checkpoint_tokenizer_reference('2')
    with pytest.raises(ValueError):
        guidance('3')
    with pytest.raises(ValueError):
        checkpoint_tokenizer_reference('3')


def test_compact_profile_fits_required_content_without_raising_limits():
    # Extra required content models actual declaration overhead, not optional omission.
    source = live_plan(root_body=b'Synthetic required context. ' * 100)
    old = prepare(source)
    new = prepare(compact(source))
    assert old.failure == 'required_input_limit' and new.packet is not None
    assert new.packet.fit.measurement.input_tokens <= 65536
    assert CheckpointEnvelope.bind(compact(source).request, new.packet.canonical).input_bound <= 65536


def test_compact_profile_still_uses_existing_scope_cost_fence():
    source = compact(live_plan())
    assert CheckpointAllowance.applies(source.request)
    value = source.request.document().context
    limits = value.limits.model_copy(update={'max_input_tokens': 65536, 'max_output_tokens': 2048,
        'max_attempts': 1, 'total_tokens': 67584, 'total_accounting_units': 500000000,
        'accounting_unit': 'usd_nanodollars'})
    assert CheckpointAllowance.cost(value.model, limits) == 58368000
    with pytest.raises(ValueError):
        CheckpointAllowance.cost(value.model, limits.model_copy(update={'max_input_tokens': 65537}))
