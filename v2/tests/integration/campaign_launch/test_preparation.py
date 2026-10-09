import copy
import pytest
from campaign_launch_demo.preparation import pinned_definition


def fixture():
    scope = {'tenant_id': 'internal', 'project_id': 'demo'}
    value = {'kind': 'artifact', 'artifact': {'scope': scope, 'artifact_id': 'retained'}, 'unit': '1', 'representation': 'fixture'}
    definition = {'scope': scope, 'revision': 2, 'body': {'inputs': [{'name': 'input'}], 'nodes': [
        {'kind': 'invoke', 'node_id': 'science', 'inputs': [{'port': 'parameters', 'source': {'kind': 'input', 'name': 'input'}}]},
        {'kind': 'finish', 'node_id': 'done', 'outputs': [{'port': 'result', 'source': {'kind': 'output', 'node_id': 'science', 'port': 'result'}}]}],
        'edges': [{'source': 'science', 'target': 'done', 'route': 'next'}]}}
    return definition, {'payload': {'inputs': [{'port': 'input', 'value': value}]}}


def test_pinned_demo_preserves_structure_and_artifacts_without_mutating_original():
    definition, admission = fixture(); original = copy.deepcopy(definition)
    result = pinned_definition(definition, admission)
    assert definition == original and result['revision'] == 3 and result['body']['inputs'] == []
    assert result['body']['edges'] == definition['body']['edges']
    assert result['body']['nodes'][1] == definition['body']['nodes'][1]
    assert result['body']['nodes'][0]['inputs'][0]['source'] == admission['payload']['inputs'][0]['value']


def test_missing_foreign_or_nested_inputs_never_become_empty_bindings():
    definition, admission = fixture()
    with pytest.raises(AssertionError): pinned_definition(definition, {'payload': {'inputs': []}})
    admission['payload']['inputs'][0]['value']['artifact']['scope'] = {'tenant_id': 'other', 'project_id': 'demo'}
    with pytest.raises(AssertionError): pinned_definition(definition, admission)
    definition['body']['nodes'][0]['kind'] = 'scatter'
    with pytest.raises(AssertionError): pinned_definition(definition, admission)
