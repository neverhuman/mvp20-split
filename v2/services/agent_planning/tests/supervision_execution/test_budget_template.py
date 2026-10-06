"""Exact configuration construction preserves the existing ledger policy format."""

import copy
import json
from dataclasses import FrozenInstanceError

import pytest
from amphora_agent_planning.budget import BudgetPolicy
from amphora_agent_planning.context import AttemptBinding, RequestSnapshot
from amphora_agent_planning.supervision_execution import (
    BudgetTemplates,
    ReviewedBudgetTemplate,
)
from amphora_contracts_core import ArtifactRef
from amphora_contracts_planning import checkpoint_draft_schema

from ..supervision_intake.support import principal
from ..supervision_intake.test_checkpoints import request


def documents():
    original = request(principal()).planning_request.model_dump(mode='json')
    original['context']['output_schema'] = checkpoint_draft_schema().model_dump(mode='json')
    context = original['context']
    record = {name: copy.deepcopy(context[name]) for name in
              ('model', 'prompt', 'output_schema', 'allowed_actions', 'limits')}
    record.update(scope=original['reference']['scope'], per_attempt_accounting_units=60)
    return original, record


def snapshot(data):
    actor = principal()
    return RequestSnapshot.from_bytes(json.dumps(data).encode(), actor_id=actor.actor_id, scope=actor.scope)


def reviewed(record):
    return ReviewedBudgetTemplate.from_bytes(json.dumps(record).encode())


def reference(template, original):
    data = copy.deepcopy(original['context']['policy'])
    data.update(artifact_id='reviewed-budget-template', sha256=template.sha256,
                size_bytes=len(template.canonical), media_type='application/json')
    return ArtifactRef.model_validate_json(json.dumps(data))


def test_acyclic_template_derives_exact_existing_policy_bytes_and_demand():
    original, data = documents()
    template = reviewed(data)
    context = original['context']
    previous = {name: context[name] for name in ('model', 'prompt', 'policy', 'output_schema', 'allowed_actions', 'limits')}
    previous.update(format='planning-budget-policy.v1', per_attempt_accounting_units=60)
    expected = BudgetPolicy.from_bytes(json.dumps(previous).encode())
    actual = template.bind(snapshot(original))
    assert actual.canonical == expected.canonical and actual.sha256 == expected.sha256
    attempt = AttemptBinding(snapshot(original), 1)
    assert actual.demand(attempt) == expected.demand(attempt)
    assert 'policy' not in template.document().model_dump()
    assert ReviewedBudgetTemplate(template.canonical) == template
    with pytest.raises(FrozenInstanceError):
        template.canonical = b'{}'
    with pytest.raises(ValueError, match='noncanonical_budget_template'):
        ReviewedBudgetTemplate(template.canonical + b' ')


def test_original_request_supplies_only_dynamic_policy_binding():
    original, data = documents()
    template = reviewed(data)
    first = template.bind(snapshot(original))
    original['context']['policy']['sha256'] = 'f' * 64
    second = template.bind(snapshot(original))
    assert first.sha256 != second.sha256
    assert first.document().model == second.document().model
    assert first.document().limits == second.document().limits
    assert template == reviewed(data)


@pytest.mark.parametrize('field,value,reason', [('max_attempts', 3, 'budget_ceiling_exceeded'),
    ('max_input_tokens', 1025, 'budget_ceiling_exceeded'), ('accounting_unit', 'other', 'budget_unit_mismatch')])
def test_request_cannot_widen_original_template(field, value, reason):
    original, data = documents()
    template = reviewed(data)
    original['context']['limits'][field] = value
    with pytest.raises(ValueError, match=reason):
        template.bind(snapshot(original))


def test_narrowed_request_keeps_original_policy_ceiling_and_charge():
    original, data = documents()
    template = reviewed(data)
    original['context']['limits'].update(max_attempts=1, max_input_tokens=512, max_output_tokens=512)
    policy = template.bind(snapshot(original))
    demand = policy.demand(AttemptBinding(snapshot(original), 1))
    assert demand.tokens == 1024 and demand.accounting_units == 60
    assert policy.document().limits.max_attempts == 2


@pytest.mark.parametrize('case,reason', [('scope', 'budget_template_scope'), ('profile', 'budget_template_output_profile'),
    ('actions', 'budget_template_actions'), ('tokens', 'budget_template_tokens'), ('cost', 'budget_template_accounting')])
def test_template_relations_are_owner_validated(case, reason):
    _, data = documents()
    if case == 'scope':
        data['scope'] = dict(data['scope'], project_id='foreign')
    elif case == 'profile':
        data['output_schema']['sha256'] = 'f' * 64
    elif case == 'actions':
        data['allowed_actions'].append(data['allowed_actions'][0])
    elif case == 'tokens':
        data['limits']['total_tokens'] = 1
    else:
        data['per_attempt_accounting_units'] = 101
    with pytest.raises(ValueError, match=reason):
        reviewed(data)


def test_exact_catalog_never_selects_latest_or_changed_artifact_identity():
    original, data = documents()
    template = reviewed(data)
    ref = reference(template, original)
    catalog = BudgetTemplates([(ref, template)])
    assert catalog.require(ref) == template
    with pytest.raises(ValueError, match='duplicate_budget_template'):
        BudgetTemplates([(ref, template), (ref, template)])
    for changed in [ref.model_copy(update={'sha256': 'f' * 64}), ref.model_copy(update={'artifact_id': 'other'})]:
        with pytest.raises(ValueError, match='budget_template_unavailable'):
            catalog.require(changed)
    with pytest.raises(ValueError, match='budget_template_artifact'):
        BudgetTemplates([(ref.model_copy(update={'size_bytes': 1}), template)])


@pytest.mark.parametrize('raw', [b'', b'x' * 16385, b'{"scope":{},"scope":{}}'], ids=['empty', 'oversize', 'duplicate-key'])
def test_bounded_strict_template_input(raw):
    with pytest.raises(ValueError):
        ReviewedBudgetTemplate.from_bytes(raw)
