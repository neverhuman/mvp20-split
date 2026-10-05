"""Persistable effect bytes must derive from the exact original selected proposal."""

import json
from dataclasses import replace

import pytest
from amphora_agent_planning.access import Principal
from amphora_agent_planning.campaign_context.records import canonical
from amphora_agent_planning.campaign_dispatch import CompilerEffect, CompilerSelection
from amphora_agent_planning.campaign_eligibility import EligibilityConfiguration

from ..campaign_authoring.test_values import plan, saved


@pytest.fixture(scope='module')
def inputs():
    authoring = plan(tools=True)
    request = authoring.review.composition.evidence.proposal.attempt.request.document()
    principal = Principal(request.actor_id, request.reference.scope, frozenset({'read_attempts', 'record_attempts'}))
    config = EligibilityConfiguration.bind(owner_id='registry', actor_id='planning-agent', policy_sha256='e' * 64)
    return CompilerSelection.bind(principal, authoring, config), principal, authoring, config


def test_save_validate_and_resolve_have_distinct_stable_exact_bytes(inputs):
    selection, principal, authoring, config = inputs
    save = CompilerEffect.authoring(*inputs)
    validate = CompilerEffect.authoring(*inputs, saved=saved(authoring))
    digest = authoring.review.composition.uses[0].release.record.document().lock.descriptor_sha256
    check = CompilerEffect.eligibility(*inputs, 'check-1', digest)
    assert len({item.effect_id for item in (save, validate, check)}) == 3
    assert save.command().canonical_bytes == authoring.save().canonical
    assert save.command().profile == 'amphora-command-v2' and validate.command().profile == 'amphora-command-v1'
    assert check.command().identity.command_family == 'registry.resolve'
    reader = replace(principal, actions=frozenset({'read_attempts'}))
    for effect, dependency in [(save, None), (validate, saved(authoring)), (check, None)]:
        assert CompilerEffect.restore(effect.canonical, selection, reader, authoring, config, saved=dependency) == effect
        assert len(effect.sha256) == 64
    newer = CompilerEffect.eligibility(*inputs, 'check-2', digest)
    assert newer.effect_id != check.effect_id and newer.command().identity != check.command().identity


def test_only_original_selected_tools_can_get_check_payloads(inputs):
    with pytest.raises(ValueError, match='compiler_effect_selected_tool'):
        CompilerEffect.eligibility(*inputs, 'check-1', 'f' * 64)


@pytest.mark.parametrize('case', ['missing', 'extra', 'foreign'])
def test_validation_requires_exact_saved_dependency(inputs, case):
    selection, principal, authoring, config = inputs
    save = CompilerEffect.authoring(*inputs)
    validate = CompilerEffect.authoring(*inputs, saved=saved(authoring))
    if case == 'foreign':
        with pytest.raises(ValueError, match='authoring_saved_readback_required'):
            CompilerEffect.authoring(*inputs, saved=saved(plan()))
    else:
        with pytest.raises(ValueError, match='compiler_effect_dependency'):
            CompilerEffect.restore(validate.canonical if case == 'missing' else save.canonical,
                selection, principal, authoring, config, saved=None if case == 'missing' else saved(authoring))


@pytest.mark.parametrize('field', ['selection_id', 'selection_sha256', 'owner_id', 'command_json'])
def test_rehashed_payload_cannot_escape_original_derivation(inputs, field):
    effect = CompilerEffect.authoring(*inputs)
    value = json.loads(effect.canonical)
    if field == 'command_json':
        command = json.loads(value[field])
        command['payload']['title'] = 'Changed'
        value[field] = canonical(command).decode()
    else:
        value[field] = 'f' * 64 if field.endswith('sha256') else 'foreign'
    with pytest.raises(ValueError, match='compiler_effect_binding'):
        CompilerEffect.restore(canonical(value), *inputs)


def test_noncanonical_and_oversized_records_reject(inputs):
    effect = CompilerEffect.authoring(*inputs)
    for raw in [effect.canonical + b' ', b'x' * 1048577, b'{"kind":"save","kind":"validate"}']:
        with pytest.raises(ValueError):
            CompilerEffect.restore(raw, *inputs)


def test_configuration_change_cannot_create_a_second_save_operation(inputs):
    _selection, principal, authoring, config = inputs
    first = CompilerEffect.authoring(*inputs)
    changed = replace(authoring, owner_id='replacement-owner')
    new_selection = CompilerSelection.bind(principal, changed, config)
    second = CompilerEffect.authoring(new_selection, principal, changed, config)
    assert second.effect_id == first.effect_id and second.canonical != first.canonical
    assert second.command().identity != first.command().identity
    with pytest.raises(ValueError, match='compiler_effect_binding'):
        CompilerEffect.restore(first.canonical, new_selection, principal, changed, config)


@pytest.mark.parametrize('fault', ['unexpected_check', 'missing_check', 'family', 'command_whitespace'])
def test_raw_values_do_not_bypass_command_shape_checks(inputs, fault):
    effect = CompilerEffect.authoring(*inputs)
    value = json.loads(effect.canonical)
    if fault == 'unexpected_check':
        value['check_id'] = 'unexpected'
    elif fault == 'missing_check':
        value['kind'] = 'resolve'
    elif fault == 'family':
        value['kind'] = 'validate'
    else:
        value['command_json'] += ' '
    with pytest.raises(ValueError):
        CompilerEffect(canonical(value)).command()
