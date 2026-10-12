"""Configuration/payload changes cannot evade the original durable handoff slot."""

import json
from dataclasses import replace

import pytest
from amphora_agent_planning.access import Principal
from amphora_agent_planning.campaign_authoring import AuthoringPlan
from amphora_agent_planning.campaign_context.records import canonical
from amphora_agent_planning.campaign_dispatch import CompilerSelection
from amphora_agent_planning.campaign_eligibility import EligibilityConfiguration
from amphora_contracts_core import Scope

from ..campaign_authoring.test_values import plan


@pytest.fixture(scope='module')
def inputs():
    authoring = plan()
    request = authoring.review.composition.evidence.proposal.attempt.request.document()
    principal = Principal(request.actor_id, request.reference.scope, frozenset({'read_attempts', 'record_attempts'}))
    config = EligibilityConfiguration.bind(owner_id='registry', actor_id='planning-agent', policy_sha256='e' * 64)
    return principal, authoring, config


def test_selection_can_restore_with_read_grant_only(inputs):
    principal, authoring, config = inputs
    selected = CompilerSelection.bind(*inputs)
    reader = replace(principal, actions=frozenset({'read_attempts'}))
    assert CompilerSelection.restore(selected.canonical, reader) == selected
    assert selected.verify_origin(reader, authoring, config) == selected
    with pytest.raises(PermissionError):
        CompilerSelection.bind(reader, authoring, config)
    assert selected.document().origin.proposal_sha256 == authoring.review.composition.evidence.proposal.sha256
    assert len(selected.canonical) < 131072 and len(selected.sha256) == 64


@pytest.mark.parametrize('field', ['runtime_owner', 'runtime_actor', 'registry_owner', 'registry_actor', 'policy', 'age', 'output'])
def test_changed_configuration_or_payload_retains_slot_but_conflicts(inputs, field):
    principal, authoring, config = inputs
    original = CompilerSelection.bind(*inputs)
    if field.startswith('runtime'):
        authoring = AuthoringPlan.bind(authoring.review, authoring.budget,
            owner_id='changed' if field == 'runtime_owner' else authoring.owner_id,
            actor_id='changed' if field == 'runtime_actor' else authoring.actor_id)
    elif field == 'output':
        authoring = plan(change=lambda value: value['candidate'].update(title='Changed candidate'))
    else:
        value = config.document()
        config = EligibilityConfiguration.bind(owner_id='changed' if field == 'registry_owner' else value.owner_id,
            actor_id='changed' if field == 'registry_actor' else value.actor_id,
            policy_sha256='a' * 64 if field == 'policy' else value.policy_sha256,
            maximum_age_seconds=10 if field == 'age' else value.maximum_age_seconds)
    changed = CompilerSelection.bind(principal, authoring, config)
    assert changed.effect_id == original.effect_id and changed.canonical != original.canonical
    with pytest.raises(ValueError, match='compiler_selection_origin'):
        original.verify_origin(principal, authoring, config)


@pytest.mark.parametrize('case', ['actor', 'scope', 'grant'])
def test_foreign_reader_cannot_restore(inputs, case):
    principal, _, _ = inputs
    original = CompilerSelection.bind(*inputs)
    reader = replace(principal, actor_id='other') if case == 'actor' else replace(principal,
        scope=Scope(tenant_id='other', project_id='other')) if case == 'scope' else replace(principal, actions=frozenset())
    with pytest.raises((ValueError, PermissionError)):
        CompilerSelection.restore(original.canonical, reader)


@pytest.mark.parametrize('case', ['whitespace', 'duplicate', 'unknown', 'huge', 'version', 'witness_scope'])
def test_invalid_stored_selection_rejected(inputs, case):
    principal, _, _ = inputs
    selected = CompilerSelection.bind(*inputs)
    raw = selected.canonical
    if case == 'whitespace':
        raw += b' '
    elif case == 'duplicate':
        raw = b'{"actor_id":"fixture",' + raw[1:]
    elif case == 'huge':
        raw = b'x' * 131073
    else:
        value = json.loads(raw)
        if case == 'version':
            value['format'] = 'unknown'
        elif case == 'unknown':
            value['authority'] = True
        else:
            value['origin']['attempt']['engagement']['engagement_id'] = 'foreign'
        raw = canonical(value)
    with pytest.raises(ValueError):
        CompilerSelection.restore(raw, principal)


def test_rehashed_origin_requires_original_reconstruction(inputs):
    principal, authoring, config = inputs
    selected = CompilerSelection.bind(*inputs)
    value = json.loads(selected.canonical)
    value['origin']['proposal_sha256'] = 'f' * 64
    shaped = CompilerSelection.restore(canonical(value), principal)
    assert shaped.effect_id == selected.effect_id
    with pytest.raises(ValueError, match='compiler_selection_origin'):
        shaped.verify_origin(principal, authoring, config)


def test_original_slot_can_be_recovered_without_current_configuration(inputs):
    import hashlib
    principal, authoring, config = inputs
    selected = CompilerSelection.bind(*inputs)
    attempt = authoring.review.composition.evidence.proposal.attempt.reference()
    expected = 'compiler-' + hashlib.sha256(canonical({'format': 'planning-compiler-effect.v1',
        'actor_id': principal.actor_id, 'attempt': attempt.model_dump(mode='json')})).hexdigest()
    assert CompilerSelection.identity_for(principal.actor_id, attempt) == selected.effect_id == expected
