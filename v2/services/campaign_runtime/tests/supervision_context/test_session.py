"""Pure projection/request oracles; synthetic references do not prove publication."""

import hashlib
import json
from dataclasses import replace

import pytest
from amphora_campaign_runtime.supervision_checkpoints.values import ValueCheckpointSeed
from amphora_campaign_runtime.supervision_context import ContextBasis, ContextSession
from amphora_campaign_runtime.supervision_policy import ReviewedPolicy
from amphora_campaign_runtime.supervision_policy.records import RecipePolicyRecord
from amphora_campaign_runtime.supervision_preparation import (
    CallReservations,
    RequestCharge,
)
from amphora_contracts_core import ArtifactRef
from amphora_contracts_supervision import checkpoint_context_schema

from ..supervision_effects.test_selection import original
from ..supervision_preparation.test_recipe import bind, document


def basis(*, calls=None):
    seed = original(nested=True)
    data = document()
    scope = seed.footprint().cut.scope.model_dump(mode='json')
    data['scope'] = scope
    for ref in (data['objective'], data['prompt'], data['budget_policy'], data['model']['configuration'],
                *(item['artifact'] for item in (*data['entries'], *data['omissions']))):
        ref['scope'] = scope
    recipe = bind(data)
    data = seed.policy.document().model_dump(mode='json')
    data.update(profile='runtime-supervision-policy.v2', context_recipe_sha256=recipe.sha256)
    if calls is not None:
        data['checkpoints'][0]['max_model_calls'] = calls
        data['ceilings']['max_model_calls'] = calls
    policy = ReviewedPolicy.bind(seed.policy.plan, RecipePolicyRecord.model_validate_json(json.dumps(data)))
    seed = ValueCheckpointSeed.capture(policy, seed.footprint(), seed.document().original_fields)
    return ContextBasis(seed, recipe, CallReservations(), 1791226800000)


def reference(session, raw, *, policy=False):
    data = session.basis.recipe.document().objective.model_dump(mode='json')
    data.update(artifact_id='policy' if policy else 'declaration', sha256=hashlib.sha256(raw).hexdigest(),
                media_type='application/json', size_bytes=len(raw))
    if not policy:
        data['schema_ref'] = checkpoint_context_schema().model_dump(mode='json')
    return ArtifactRef.model_validate_json(json.dumps(data))


def references(session):
    policy = reference(session, session.basis.seed.policy.canonical, policy=True)
    return policy, reference(session, session.declaration_bytes(policy))


def test_exact_original_scalars_concrete_occurrence_and_deterministic_request():
    session = ContextSession(basis(), (), 'fixture')
    policy, declaration = references(session)
    record = session.declaration(policy)
    assert record.fields[0].name == 'a' and record.fields[0].original_value.value == 1
    assert record.fields[0].constraint.maximum.value == '10'
    assert record.target.occurrences[0].kind == 'loop'
    assert record.remaining.slot_requests == 2 and record.remaining.slot_model_calls == 4
    assert record.future_proposals == 'retained_only'
    first = session.frame(policy, declaration, prepared_by='runtime-fixture')
    replacement = ContextSession(basis(), (), 'fixture')
    assert replacement.frame(policy, declaration, prepared_by='runtime-fixture') == first
    assert first.request.planning_request.decision_scope == declaration.sha256
    assert first.request.planning_request.reference == record.engagement
    assert first.request.planning_request.context.entries[-1].required


def test_repair_consumes_previous_allowance_and_changes_engagement():
    session = ContextSession(basis(), (), 'fixture')
    policy, declaration = references(session)
    first = session.frame(policy, declaration, prepared_by='runtime-fixture')
    history = CallReservations((RequestCharge(session.basis.seed.decision_id, first.request_sha256, 2),))
    repair = ContextSession(replace(session.basis, reservations=history), (first,), 'fixture')
    second_policy, second_declaration = references(repair)
    second = repair.frame(second_policy, second_declaration, prepared_by='runtime-fixture')
    assert second.request.lineage.ordinal == 2 and second.request.lineage.parent_request_sha256 == first.request_sha256
    assert second.request.planning_request.reference != first.request.planning_request.reference
    assert second.request.deadline_unix_ms == first.request.deadline_unix_ms
    assert repair.declaration(policy).remaining.slot_model_calls == 2
    assert repair.declaration(policy).remaining.campaign_model_calls == 28


@pytest.mark.parametrize('case,reason', [('accounting', 'context_previous_accounting'),
    ('foreign', 'context_previous_binding'), ('exhausted', 'context_allowance_exhausted'),
    ('undercharge', 'context_previous_call_allowance'),
    ('history', 'context_previous_history'), ('deadline', 'context_deadline')])
def test_no_invented_history_or_widened_scope(case, reason):
    session = ContextSession(basis(), (), 'fixture')
    policy, declaration = references(session)
    first = session.frame(policy, declaration, prepared_by='runtime-fixture')
    with pytest.raises(ValueError, match=reason):
        if case == 'accounting':
            ContextSession(session.basis, (first,), 'fixture')
        elif case == 'foreign':
            ContextSession(session.basis, (first,), 'different-actor')
        elif case == 'exhausted':
            first_charge = RequestCharge(session.basis.seed.decision_id, first.request_sha256, 2)
            repair = ContextSession(replace(session.basis, reservations=CallReservations((first_charge,))), (first,), 'fixture')
            second = repair.frame(*references(repair), prepared_by='runtime-fixture')
            history = CallReservations((first_charge, RequestCharge(session.basis.seed.decision_id, second.request_sha256, 2)))
            ContextSession(replace(session.basis, reservations=history), (first, second), 'fixture')
        elif case == 'undercharge':
            history = CallReservations((RequestCharge(session.basis.seed.decision_id, first.request_sha256, 1),))
            ContextSession(replace(session.basis, reservations=history), (first,), 'fixture')
        elif case == 'history':
            ContextSession(session.basis, [], 'fixture')
        else:
            replace(session.basis, deadline_unix_ms=True)


@pytest.mark.parametrize('item,field,value', [('policy', 'sha256', 'f' * 64),
    ('policy', 'size_bytes', 1), ('declaration', 'sha256', 'f' * 64),
    ('declaration', 'media_type', 'text/plain')])
def test_published_references_must_identify_exact_bytes(item, field, value):
    session = ContextSession(basis(), (), 'fixture')
    policy, declaration = references(session)
    if item == 'policy':
        policy = policy.model_copy(update={field: value})
    else:
        declaration = declaration.model_copy(update={field: value})
    with pytest.raises(ValueError, match='context_published_' + item):
        session.frame(policy, declaration, prepared_by='runtime-fixture')


def test_repair_uses_last_remaining_call_without_widening_original_limits():
    session = ContextSession(basis(calls=3), (), 'fixture')
    first = session.frame(*references(session), prepared_by='runtime-fixture')
    history = CallReservations((RequestCharge(session.basis.seed.decision_id, first.request_sha256, 2),))
    repair = ContextSession(replace(session.basis, reservations=history), (first,), 'fixture')
    second = repair.frame(*references(repair), prepared_by='runtime-fixture')
    assert first.request.planning_request.context.limits.max_attempts == 2
    assert second.request.planning_request.context.limits.max_attempts == 1
    assert second.request.planning_request.context.limits.total_tokens == first.request.planning_request.context.limits.total_tokens
