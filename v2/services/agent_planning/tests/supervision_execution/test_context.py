"""Public Runtime claims bind to original intake; no Runtime private code imported."""

import hashlib
import json

import pytest
from amphora_agent_planning.supervision_execution import BudgetTemplates
from amphora_agent_planning.supervision_execution.context import (
    CheckpointContextBinding,
)
from amphora_agent_planning.supervision_intake.snapshot import CheckpointIntakeSnapshot
from amphora_contracts_core import ArtifactRef
from amphora_contracts_supervision import (
    CheckpointContext,
    CheckpointRequest,
    checkpoint_context_content_schema,
)

from ..supervision_intake.support import principal
from ..supervision_intake.test_checkpoints import request
from .test_budget_template import documents, reference, reviewed


def encoded(data):
    return json.dumps(data, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()


def prepared(*, change=None, unicode_value=False, actor=None, configure=None, deadline=None, per_attempt_units=None):
    actor = principal() if actor is None else actor
    original, template_data = documents(actor)
    if configure:
        configure(original)
        for key in ('model', 'prompt', 'output_schema', 'allowed_actions', 'limits'):
            template_data[key] = original['context'][key]
    if per_attempt_units is not None:
        template_data['per_attempt_accounting_units'] = per_attempt_units
    template = reviewed(template_data)
    budget = reference(template, original)
    wrapper = request(actor).model_dump(mode='json')
    if deadline is not None:
        wrapper['deadline_unix_ms'] = deadline
    wrapper['policy'] = original['context']['policy']
    wrapper['planning_request'] = original
    checkpoint = wrapper['snapshot']['checkpoints'][0]
    target = next(item['node']['path'] for item in wrapper['snapshot']['reads']
                  if item['node']['activation_id'] == checkpoint['activation_id'])
    value = {'kind': 'string', 'value': 'μmol'} if unicode_value else {'kind': 'integer', 'value': 1, 'unit': '1'}
    scalar = json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()
    data = {'reference': wrapper['reference'], 'engagement': original['reference'], 'lineage': wrapper['lineage'],
        'checkpoint_id': wrapper['checkpoint_id'], 'checkpoint_seed_sha256': 'a' * 64, 'recipe_sha256': 'b' * 64,
        'objective': original['context']['objective'], 'policy': wrapper['policy'], 'budget_policy': budget.model_dump(mode='json'),
        'snapshot': wrapper['snapshot'], 'target': target,
        'fields': [{'name': name, 'value_type': {'kind': 'scalar', 'scalar': value['kind']},
            'original_value': value, 'original_value_sha256': hashlib.sha256(scalar).hexdigest(),
            'constraint': {'kind': 'choices', 'values': [value]}} for name in sorted(checkpoint['fields'])],
        'remaining': {'slot_requests': 2, 'slot_model_calls': 4, 'campaign_requests': 20, 'campaign_model_calls': 30},
        'deadline_unix_ms': wrapper['deadline_unix_ms'], 'allowed_actions': original['context']['allowed_actions']}
    if change:
        change(data)
    context = CheckpointContext.model_validate_json(json.dumps(data))
    raw = encoded(context.model_dump(mode='json'))
    ref = ArtifactRef.model_validate_json(json.dumps(dict(original['context']['policy'], artifact_id='checkpoint-context',
        sha256=hashlib.sha256(raw).hexdigest(), size_bytes=len(raw), media_type='application/json',
        schema_ref=checkpoint_context_content_schema().model_dump(mode='json'))))
    original['context']['entries'].append({'artifact': ref.model_dump(mode='json'), 'role': 'constraint', 'required': True})
    original['decision_scope'] = ref.sha256
    original_record = CheckpointRequest.model_validate_json(json.dumps(wrapper)).planning_request
    wrapper['planning_request_sha256'] = hashlib.sha256(encoded(original_record.model_dump(mode='json'))).hexdigest()
    intake = CheckpointIntakeSnapshot.bind(CheckpointRequest.model_validate_json(json.dumps(wrapper)), actor)
    return actor, intake, ref, raw, BudgetTemplates([(budget, template)])


@pytest.mark.parametrize('unicode_value', [False, True])
def test_exact_original_context_and_ascii_scalar_fingerprint(unicode_value):
    actor, intake, ref, raw, templates = prepared(unicode_value=unicode_value)
    bound = CheckpointContextBinding.bind(intake, actor, ref, raw)
    assert bound.canonical == raw and bound.snapshot == intake
    assert bound.document().fields[0].original_value.value == ('μmol' if unicode_value else 1)
    assert bound.budget_policy(templates).document().policy == intake.document().policy


@pytest.mark.parametrize('case,reason', [('engagement', 'execution_context_request'),
    ('objective', 'execution_context_roots'), ('deadline', 'execution_context_cut_deadline'),
    ('actions', 'execution_context_actions'), ('target', 'execution_context_target'),
    ('fields', 'execution_context_fields'), ('digest', 'execution_context_scalar_digest'),
    ('allowance', 'execution_context_allowance')])
def test_false_runtime_claims_do_not_become_local_authority(case, reason):
    def change(data):
        if case == 'engagement':
            data['engagement'] = dict(data['engagement'], engagement_id='different')
        elif case == 'objective':
            data['objective'] = dict(data['objective'], artifact_id='different')
        elif case == 'deadline':
            data['deadline_unix_ms'] -= 1
        elif case == 'actions':
            data['allowed_actions'] = ['abstain']
        elif case == 'target':
            data['target'] = dict(data['target'], node_id='different')
        elif case == 'fields':
            data['fields'] *= 2
        elif case == 'digest':
            data['fields'][0]['original_value_sha256'] = 'f' * 64
        else:
            data['remaining']['slot_model_calls'] = 0

    actor, intake, ref, raw, _ = prepared(change=change)
    with pytest.raises(ValueError, match=reason):
        CheckpointContextBinding.bind(intake, actor, ref, raw)


def test_bytes_and_artifact_identity_cannot_be_substituted():
    actor, intake, ref, raw, _ = prepared()
    with pytest.raises(ValueError, match='execution_context_artifact'):
        CheckpointContextBinding.bind(intake, actor, ref, raw + b' ')
    with pytest.raises(ValueError, match='execution_context_entry'):
        CheckpointContextBinding.bind(intake, actor, ref.model_copy(update={'artifact_id': 'other'}), raw)
    with pytest.raises(ValueError, match='execution_context_size'):
        CheckpointContextBinding.bind(intake, actor, ref, b'')
