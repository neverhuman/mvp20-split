"""Independently authored small conversion graphs for policy eligibility tests."""

import copy
import hashlib
import json

from amphora_campaign_runtime.compiler import (
    PinnedSchema,
    SchemaCatalog,
    SchemaIdentity,
    ToolCatalog,
    compile_campaign,
)
from amphora_campaign_runtime.supervision_policy import PolicyRecord
from amphora_contracts_campaigns import parse_executable_campaign
from amphora_contracts_core import SchemaRef

SCOPE = {'tenant_id': 'policy-test', 'project_id': 'isolated'}


def plan(*, nested=False, sibling=False, scope=None):
    schema = b'{"additionalProperties":false,"properties":{"a":{"type":"integer"}},"required":["a"],"type":"object"}'
    reference = SchemaRef(schema_id='fixture.policy', version='1', sha256=hashlib.sha256(schema).hexdigest())
    shape = {'kind': 'artifact', 'schema_ref': reference.model_dump(mode='json'),
             'representation': 'fixture.parameters', 'unit': '1', 'media_type': 'application/json'}
    pack = {'kind': 'artifact_materialize', 'node_id': 'pack', 'fields': [
        {'name': 'a', 'mode': 'inline', 'source': {'kind': 'integer', 'value': 1}}],
        'output': {'name': 'result', 'value_type': shape}}
    body = {'inputs': [], 'outputs': [{'name': 'result', 'value_type': shape}], 'nodes': [pack,
        {'kind': 'finish', 'node_id': 'finish', 'outputs': [{'port': 'result',
            'source': {'kind': 'output', 'node_id': 'pack', 'port': 'result'}}]}],
        'edges': [{'source': 'pack', 'target': 'finish'}]}
    if nested:
        scalar = {'kind': 'scalar', 'scalar': 'integer', 'unit': '1'}
        body['inputs'] = body['outputs'] = [{'name': 'n', 'value_type': scalar}]
        body['nodes'][1]['outputs'] = [{'port': 'n', 'source': {'kind': 'input', 'name': 'n'}}]
        loop = {'kind': 'iterate', 'node_id': 'loop', 'state': [{'name': 'n', 'value_type': scalar,
            'initial': {'kind': 'integer', 'value': 0}, 'feedback_port': 'n'}], 'body': body,
            'until': {'kind': 'constant', 'value': False}, 'max_iterations': 2, 'on_limit': 'finish'}
        finish = {'kind': 'finish', 'node_id': 'finish', 'outputs': [{'port': 'n',
            'source': {'kind': 'output', 'node_id': 'loop', 'port': 'n'}}]}
        body = {'inputs': [], 'outputs': [{'name': 'n', 'value_type': scalar}], 'nodes': [loop, finish],
                'edges': [{'source': 'loop', 'target': 'finish'}]}
        if sibling:
            other = copy.deepcopy(loop)
            other['node_id'] = 'other'
            body['nodes'].insert(1, other)
            body['edges'] = [{'source': 'loop', 'target': 'other'}, {'source': 'other', 'target': 'finish'}]
    raw = {'schema_version': '4', 'profile': 'deterministic-v3', 'campaign_id': 'policy-fixture',
           'revision': 1, 'scope': scope or SCOPE, 'body': body}
    return compile_campaign(parse_executable_campaign(json.dumps(raw)), ToolCatalog([]),
        SchemaCatalog([PinnedSchema(SchemaIdentity.from_wire(reference), schema)]))


def policy(plan, *, nested=False):
    return PolicyRecord.model_validate_json(json.dumps({'scope': plan.document.definition.scope.model_dump(mode='json'), 'plan_sha256': plan.sha256,
        'ceilings': {'max_checkpoints': 10, 'max_requests': 20, 'max_model_calls': 30},
        'checkpoints': [{'checkpoint_id': 'before-parameters', 'target': {
            'scope_path': ('loop',) if nested else (), 'node_id': 'pack'}, 'kind': 'artifact_materialize',
            'fields': [{'name': 'a', 'value_type': {'kind': 'scalar', 'scalar': 'integer'}, 'constraint': {
                'kind': 'range', 'minimum': {'kind': 'number', 'value': '0'},
                'maximum': {'kind': 'number', 'value': '10'}}}],
            'reads': [], 'timeout_seconds': 30, 'max_requests': 2, 'max_model_calls': 4,
            'fallback': 'continue_unchanged'}]}))
