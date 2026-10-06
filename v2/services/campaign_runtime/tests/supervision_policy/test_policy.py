"""Policy identity and concrete occurrence selection against actual compiled graphs."""

import json
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest
from amphora_campaign_runtime.supervision_policy import PolicyRecord, ReviewedPolicy
from amphora_campaign_runtime.supervision_policy.policy import normalized
from amphora_contracts_campaigns import ActivationPath, parse_execution_plan

from .support import plan, policy


def test_exact_reviewed_policy_roundtrip_and_no_caller_mutation():
    graph = plan()
    record = policy(graph)
    original = ReviewedPolicy.bind(graph, record)
    assert ReviewedPolicy.from_bytes(graph, original.canonical) == original
    assert len(original.sha256) == 64
    data = record.model_dump(mode='json')
    data['checkpoints'][0]['fallback'] = 'block_target'
    changed = ReviewedPolicy.bind(graph, PolicyRecord.model_validate_json(json.dumps(data)))
    assert original.sha256 != changed.sha256
    assert original.document().checkpoints[0].fallback == 'continue_unchanged'
    with pytest.raises(FrozenInstanceError):
        original.canonical = b'{}'
    with pytest.raises(ValueError, match='noncanonical_policy'):
        ReviewedPolicy.from_bytes(graph, original.canonical + b' ')


def test_actual_loop_occurrences_and_ancestor_reads_are_deterministic():
    graph = plan(nested=True)
    data = policy(graph, nested=True).model_dump(mode='json')
    data['checkpoints'][0]['reads'] = [{'scope_path': [], 'node_id': 'loop'}]
    reviewed = ReviewedPolicy.bind(graph, PolicyRecord.model_validate_json(json.dumps(data)))
    for index in (0, 1):
        path = ActivationPath.model_validate({'schema_version': '2', 'node_id': 'pack',
            'occurrences': ({'kind': 'loop', 'node_id': 'loop', 'index': index},)})
        selected = reviewed.read_paths(path)
        assert selected[0] == path and selected[1].node_id == 'loop' and selected[1].occurrences == ()
        assert reviewed.rule_for(path).checkpoint_id == 'before-parameters'
    unrelated = ActivationPath(schema_version='2', node_id='finish', occurrences=())
    assert reviewed.rule_for(unrelated) is None
    with pytest.raises(ValueError, match='policy_checkpoint_missing'):
        reviewed.read_paths(unrelated)


def test_sibling_occurrence_selection_is_not_an_implicit_wildcard():
    graph = plan(nested=True, sibling=True)
    data = policy(graph, nested=True).model_dump(mode='json')
    data['checkpoints'][0]['reads'] = [{'scope_path': ['other'], 'node_id': 'pack'}]
    with pytest.raises(ValueError, match='policy_read_occurrence_ambiguous'):
        ReviewedPolicy.bind(graph, PolicyRecord.model_validate_json(json.dumps(data)))


@pytest.mark.parametrize('change,reason', [
    ('missing_node', 'policy_node_missing'), ('missing_scope', 'policy_scope_missing'),
    ('kind', 'policy_target_kind'), ('no_fields', 'policy_fields_for_kind'),
    ('missing_field', 'policy_field_missing'), ('wrong_unit', 'policy_field_type_mismatch'),
    ('wrong_type', 'policy_field_type_mismatch'), ('duplicate_field', 'policy_duplicate_field'),
    ('duplicate_checkpoint', 'policy_duplicate_checkpoint'), ('duplicate_read', 'policy_duplicate_read'),
    ('ceiling', 'policy_slot_ceiling'), ('plan', 'policy_plan_binding'),
])
def test_ineligible_policy_rejects_at_review(change, reason):
    graph = plan()
    data = policy(graph).model_dump(mode='json')
    rule = data['checkpoints'][0]
    if change == 'missing_node':
        rule['target']['node_id'] = 'absent'
    elif change == 'missing_scope':
        rule['target']['scope_path'] = ['absent']
    elif change == 'kind':
        rule['kind'] = 'invoke'
    elif change == 'no_fields':
        rule['fields'] = []
    elif change == 'missing_field':
        rule['fields'][0]['name'] = 'unknown'
    elif change == 'wrong_unit':
        rule['fields'][0]['value_type']['unit'] = 'kg'
    elif change == 'wrong_type':
        rule['fields'][0]['value_type']['scalar'] = 'number'
    elif change == 'duplicate_field':
        rule['fields'] *= 2
    elif change == 'duplicate_checkpoint':
        data['checkpoints'] *= 2
    elif change == 'duplicate_read':
        rule['reads'] = [rule['target']]
    elif change == 'ceiling':
        data['ceilings']['max_requests'] = 1
    else:
        data['plan_sha256'] = 'b' * 64
    with pytest.raises(ValueError, match=reason):
        ReviewedPolicy.bind(graph, PolicyRecord.model_validate_json(json.dumps(data)))


def test_forged_plan_hash_and_unbounded_bytes_reject():
    graph = plan()
    with pytest.raises(ValueError, match='policy_plan_digest'):
        ReviewedPolicy.bind(graph.model_copy(update={'sha256': 'b' * 64}), policy(graph))
    with pytest.raises(ValueError, match='policy_size'):
        ReviewedPolicy.from_bytes(graph, b' ' * 262145)


def test_review_only_invoke_policy_preserves_no_adjustable_fields():
    root = Path(__file__).absolute().parents[4]
    cases = json.loads((root / 'contracts/fixtures/v2/executable_cases.json').read_bytes())
    raw = next(case['payload'] for case in cases if case['model'] == 'campaigns.execution-plan' and case['valid'])
    graph = parse_execution_plan(json.dumps(raw))
    node = next(node for node in graph.document.definition.body.nodes if node.kind == 'invoke')
    data = policy(plan()).model_dump(mode='json')
    data.update(scope=graph.document.definition.scope.model_dump(mode='json'), plan_sha256=graph.sha256)
    rule = data['checkpoints'][0]
    rule.update(target={'scope_path': [], 'node_id': node.node_id}, kind='invoke', fields=[])
    reviewed = ReviewedPolicy.bind(graph, PolicyRecord.model_validate_json(json.dumps(data)))
    path = ActivationPath(schema_version='2', node_id=node.node_id, occurrences=())
    assert reviewed.rule_for(path).fields == ()
    rule['fields'] = policy(plan()).model_dump(mode='json')['checkpoints'][0]['fields']
    with pytest.raises(ValueError, match='policy_fields_for_kind'):
        ReviewedPolicy.bind(graph, PolicyRecord.model_validate_json(json.dumps(data)))


def test_finite_choice_order_does_not_change_canonical_identity():
    data = policy(plan()).model_dump(mode='json')
    field = data['checkpoints'][0]['fields'][0]
    field['value_type']['scalar'] = 'string'
    field['constraint'] = {'kind': 'choices', 'values': [
        {'kind': 'string', 'value': 'water'}, {'kind': 'string', 'value': 'ethanol'}]}
    first = normalized(PolicyRecord.model_validate_json(json.dumps(data)))
    field['constraint']['values'].reverse()
    assert first == normalized(PolicyRecord.model_validate_json(json.dumps(data)))
