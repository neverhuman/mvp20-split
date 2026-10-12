import json

import pytest
from amphora_agent_planning.curation_policy import CurationPolicy
from amphora_agent_planning.curation_runtime import CurationRuntimeContext
from amphora_agent_planning.curation_intake.commands import CurationCommand
from amphora_agent_planning.context import AttemptBinding
from ..curation_openai.test_adapter import source
from ..curation_runtime.test_context import case


def config():
    template = source().request.document().model_dump(mode='json')
    template['context']['allowed_actions'] = ['abstain', 'propose_campaign']
    return {'profile': 'planning-curation-policy.v1', 'policy_id': 'synthetic', 'template': template,
        'future': {'max_nodes': 64, 'max_scopes': 16, 'max_depth': 4, 'max_iterations': 32,
                   'max_tool_timeout': 300, 'side_effects': ['pure']},
        'eligibility_context': 'synthetic-only', 'reservation_units': 250000000}


def declared():
    policy = CurationPolicy.from_bytes(json.dumps(config()).encode())
    _, old, draft, run = case()
    incoming = CurationCommand.restore(json.dumps(json.loads(old.canonical)['command']))
    seed = policy.seed(incoming)
    original = CurationRuntimeContext.bind(seed, draft, run)
    return policy, incoming, original, policy.declare(original)


def test_reviewed_future_bounds_and_budget_are_independent_of_human_direction():
    policy, incoming, original, declaration = declared()
    future = declaration.declaration.document().future
    selected = json.loads(original.canonical)['draft']['definition']
    assert future.campaign_id == selected['campaign_id'] and future.revision == selected['revision'] + 1
    assert future.max_nodes == 64 and future.max_iterations == 32 and future.side_effects == ('pure',)
    assert declaration.declaration.document().adjustments == ()
    assert declaration.declaration.document().runtime_cut is None
    assert declaration.declaration.document().engagement.engagement_id == CurationPolicy.from_bytes(policy.canonical).seed(incoming).request.document().reference.engagement_id
    assert declaration.budget.document().per_attempt_accounting_units == 250000000
    assert {row.kind for row in future.context} == {'source', 'policy', 'model'}
    assert b'Ignore all instructions' not in declaration.declaration.canonical


def test_published_reference_binds_exact_declaration_without_claiming_source_rights():
    _, _, _, declared_value = declared()
    declaration = declared_value.declaration
    reference = declared_value.intent.request.document().context.objective.model_copy(update={
        'artifact_id': 'published-declaration', 'sha256': declaration.sha256,
        'size_bytes': len(declaration.canonical), 'media_type': 'text/plain'})
    intent = declared_value.with_artifact(reference)
    request = intent.request.document()
    assert request.decision_scope == declaration.sha256
    entry = declaration.original_entry(request, declaration.document())
    assert entry.artifact == reference and entry.required and entry.role == 'constraint'
    assert declared_value.budget.demand(AttemptBinding(intent.request, 1)).accounting_units == 250000000
    assert request.reference == declared_value.intent.request.document().reference
    for field, value in [('sha256', 'f' * 64), ('size_bytes', 1), ('media_type', 'application/json')]:
        with pytest.raises(ValueError, match='curation_declaration_artifact'):
            declared_value.with_artifact(reference.model_copy(update={field: value}))


@pytest.mark.parametrize('fault', ['reservation', 'attempts', 'provider', 'action', 'effects', 'policy', 'hidden_source'])
def test_unreviewed_or_widened_configuration_rejects(fault):
    value = config()
    if fault == 'reservation': value['reservation_units'] = 250000001
    if fault == 'attempts': value['template']['context']['limits']['max_attempts'] = 2
    if fault == 'provider': value['template']['context']['model']['provider_id'] = 'other'
    if fault == 'action': value['template']['context']['allowed_actions'].append('propose_knowledge_change')
    if fault == 'effects': value['future']['side_effects'] = ['pure', 'pure']
    if fault == 'policy': value['future']['max_nodes'] = 4097
    if fault == 'hidden_source': value['template']['context']['entries'] = [{
        'artifact': value['template']['context']['objective'], 'role': 'source', 'required': False}]
    with pytest.raises(ValueError): CurationPolicy.from_bytes(json.dumps(value).encode())


def test_changed_seed_cannot_be_reinterpreted_under_another_policy():
    _, _, original, _ = declared()
    changed = config(); changed['template']['context']['limits']['max_output_tokens'] = 4096
    policy = CurationPolicy.from_bytes(json.dumps(changed).encode())
    with pytest.raises(ValueError, match='curation_policy_original_request'): policy.declare(original)
