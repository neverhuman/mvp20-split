"""Whole-suite budgets and original identities precede any physical call."""

import hashlib
import json
from pathlib import Path

import pytest
from amphora_agent_planning.access import Principal
from amphora_agent_planning.budget import BudgetPolicy
from amphora_agent_planning.context import RequestSnapshot
from amphora_agent_planning.evaluation import EvaluationProtocol
from amphora_agent_planning.evaluation_batch import EvaluationBatch
from amphora_contracts_core import Scope


def prepared(*, repetitions=2, units=40, tokens=4096, snapshot=None):
    raw = json.loads((Path(__file__).parents[1] / 'providers/fixtures/request.json').read_text()
                     if snapshot is None else snapshot.canonical)
    principal = Principal(raw['actor_id'], Scope.model_validate(raw['reference']['scope']), frozenset({'record_requests'}))
    snapshot = RequestSnapshot.from_bytes(json.dumps(raw).encode(), actor_id=principal.actor_id, scope=principal.scope)
    context = raw['context']
    policy = {key: context[key] for key in ('model', 'prompt', 'policy', 'output_schema', 'allowed_actions', 'limits')}
    policy.update(format='planning-budget-policy.v1', per_attempt_accounting_units=units)
    corpus = {'schema_version': '1', 'cases': [{'case_id': 'reference', 'category': 'fixture',
        'input_sha256': snapshot.sha256, 'allow_abstention': True, 'hard_authority': False,
        'assertions': [{'assertion_id': 'action', 'pointer': '/action', 'operation': 'equals',
                        'expected_json': '"request_evidence"'}]}]}
    corpus_bytes = json.dumps(corpus).encode()
    refs = [context['objective'], context['prompt'], context['policy'], context['model']['configuration'],
            *(item['artifact'] for item in context['entries'])]
    refs = list({json.dumps(item, sort_keys=True): item for item in refs}.values())
    manifest = {'schema_version': '1', 'suite_id': 'batch-fixture', 'mode': 'fixture', 'adapter_revision': 'fixture-1',
        'model': context['model'], 'prompt_sha256': context['prompt']['sha256'],
        'corpus_sha256': hashlib.sha256(corpus_bytes).hexdigest(), 'allowed_data': refs,
        'limits': {**context['limits'], 'total_tokens': tokens}, 'repetitions': repetitions,
        'categories': [{'category': 'fixture', 'minimum_score': 10000, 'maximum_abstention': 10000}]}
    protocol = EvaluationProtocol.load(json.dumps(manifest).encode(), corpus_bytes)
    return protocol, principal, {'reference': snapshot}, {'reference': BudgetPolicy.from_bytes(json.dumps(policy).encode())}


def test_stable_distinct_repetitions_preserve_original_context_and_policy():
    args = prepared()
    batch = EvaluationBatch.prepare(*args)
    assert batch == EvaluationBatch.prepare(*args)
    assert batch.tokens == 4096 and batch.accounting_units == 80
    assert batch.tasks[0].request.sha256 != batch.tasks[1].request.sha256
    original = args[2]['reference'].document()
    for task in batch.tasks:
        assert task.original_sha256 == args[2]['reference'].sha256
        assert task.request.document().context == original.context.model_copy(update={
            'limits': original.context.limits.model_copy(update={'max_attempts': 1})})
        assert task.binding.ordinal == 1 and task.policy == args[3]['reference']
    assert original.context.limits.max_attempts == 2


@pytest.mark.parametrize('units,repetitions,reason', [(60, 2, 'evaluation_total_accounting'),
                                                   (10, 3, 'evaluation_total_tokens')])
def test_entire_suite_must_fit_before_any_task_is_returned(units, repetitions, reason):
    with pytest.raises(ValueError, match=reason):
        EvaluationBatch.prepare(*prepared(units=units, repetitions=repetitions))


@pytest.mark.parametrize('change,reason', [('prompt', 'evaluation_model_prompt_binding'),
    ('model', 'evaluation_model_prompt_binding'), ('data', 'evaluation_data_not_allowed'),
    ('unit', 'evaluation_accounting_unit'), ('ceiling', 'evaluation_request_ceiling'),
    ('input', 'evaluation_input_digest')])
def test_frozen_authority_and_input_bindings(change, reason):
    protocol, actor, requests, policies = prepared()
    manifest = protocol.manifest.model_dump(mode='json')
    corpus = protocol.corpus.model_dump(mode='json')
    if change == 'prompt':
        manifest['prompt_sha256'] = 'f' * 64
    elif change == 'model':
        manifest['model']['model_revision'] = 'different'
    elif change == 'data':
        manifest['allowed_data'] = []
    elif change == 'unit':
        manifest['limits']['accounting_unit'] = 'other'
    elif change == 'ceiling':
        manifest['limits']['max_output_tokens'] = 1
    else:
        corpus['cases'][0]['input_sha256'] = 'f' * 64
    corpus_bytes = json.dumps(corpus).encode()
    manifest['corpus_sha256'] = hashlib.sha256(corpus_bytes).hexdigest()
    altered = EvaluationProtocol.load(json.dumps(manifest).encode(), corpus_bytes)
    with pytest.raises(ValueError, match=reason):
        EvaluationBatch.prepare(altered, actor, requests, policies)


def test_case_maps_and_principal_permissions_cannot_widen():
    protocol, actor, requests, policies = prepared()
    with pytest.raises(ValueError, match='evaluation_case_bindings'):
        EvaluationBatch.prepare(protocol, actor, {}, policies)
    with pytest.raises(PermissionError):
        EvaluationBatch.prepare(protocol, Principal(actor.actor_id, actor.scope, frozenset()), requests, policies)
