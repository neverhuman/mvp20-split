"""Owner-local no-SQL compilation of a reviewed synthetic checkpoint scenario."""

import hashlib
import json
import os
import sys
from pathlib import Path

from amphora_campaign_runtime.compiler import (
    PinnedSchema,
    SchemaCatalog,
    SchemaIdentity,
    ToolCatalog,
    compile_campaign,
)
from amphora_campaign_runtime.supervision_policy import ReviewedPolicy
from amphora_campaign_runtime.supervision_policy.records import RecipePolicyRecord
from amphora_campaign_runtime.supervision_preparation import RecipeRecord, ReviewedRecipe
from amphora_contracts_campaigns import parse_executable_campaign
from amphora_contracts_core import SchemaRef
from amphora_contracts_supervision import (
    checkpoint_context_content_schema,
    checkpoint_context_content_schema_bytes,
    checkpoint_repair_context_content_schema,
    checkpoint_repair_context_content_schema_bytes,
)

SCALAR = b'{"additionalProperties":false,"properties":{"a":{"type":"integer"}},"required":["a"],"type":"object"}'


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()


def reference(name, body):
    return {'schema_id': name, 'version': '1', 'sha256': hashlib.sha256(body).hexdigest()}


def main():
    assert not any('DATABASE_URL' in key or 'API_KEY' in key for key in os.environ)
    output = Path(sys.argv[2])
    schema = reference('demo.checkpoint.scalar', SCALAR)
    if sys.argv[1] == 'profiles':
        policy_schema = canonical(RecipePolicyRecord.model_json_schema(mode='validation'))
        definitions = [('policy', reference('runtime.supervision-policy.v2', policy_schema), policy_schema),
            ('context', checkpoint_context_content_schema().model_dump(mode='json'), checkpoint_context_content_schema_bytes()),
            ('repair', checkpoint_repair_context_content_schema().model_dump(mode='json'), checkpoint_repair_context_content_schema_bytes()),
            ('scalar', schema, SCALAR), ('template', reference('demo.budget-template', b'{"type":"object"}'), b'{"type":"object"}')]
        profiles = []
        for name, ref, body in definitions:
            path = name + '-schema.json'
            (output / path).write_bytes(body)
            profiles.append(dict(ref, media_type='application/json', schema_path=path))
        profiles += [dict(reference('demo.text', b'{"type":"string"}'), media_type='text/plain'),
            dict(reference('planning.supervision-capture', b'{"type":"string","contentEncoding":"base64"}'), media_type='application/octet-stream')]
        (output / 'profiles.json').write_bytes(canonical(profiles))
        return
    recipe = ReviewedRecipe.bind(RecipeRecord.model_validate_json((output / 'recipe-input.json').read_bytes()))
    scope = recipe.document().scope.model_dump(mode='json')
    shape = {'kind': 'artifact', 'schema_ref': schema, 'representation': 'demo.parameters', 'unit': '1', 'media_type': 'application/json'}
    definition = {'schema_version': '4', 'profile': 'deterministic-v3', 'campaign_id': 'local-model-checkpoint', 'revision': 1,
        'scope': scope, 'body': {'inputs': [], 'outputs': [{'name': 'result', 'value_type': shape}], 'nodes': [
            {'kind': 'artifact_materialize', 'node_id': 'pack', 'fields': [{'name': 'a', 'mode': 'inline', 'source': {'kind': 'integer', 'value': 1}}],
             'output': {'name': 'result', 'value_type': shape}},
            {'kind': 'finish', 'node_id': 'finish', 'outputs': [{'port': 'result', 'source': {'kind': 'output', 'node_id': 'pack', 'port': 'result'}}]}],
            'edges': [{'source': 'pack', 'target': 'finish'}]}}
    plan = compile_campaign(parse_executable_campaign(json.dumps(definition)), ToolCatalog([]),
        SchemaCatalog([PinnedSchema(SchemaIdentity.from_wire(SchemaRef.model_validate(schema)), SCALAR)]))
    record = {'profile': 'runtime-supervision-policy.v2', 'scope': scope, 'plan_sha256': plan.sha256,
        'context_recipe_sha256': recipe.sha256, 'ceilings': {'max_checkpoints': 1, 'max_requests': 1, 'max_model_calls': 1},
        'checkpoints': [{'checkpoint_id': 'choose-synthetic-parameter', 'target': {'scope_path': [], 'node_id': 'pack'},
            'kind': 'artifact_materialize', 'fields': [{'name': 'a', 'value_type': {'kind': 'scalar', 'scalar': 'integer'},
                'constraint': {'kind': 'range', 'minimum': {'kind': 'number', 'value': '0'}, 'maximum': {'kind': 'number', 'value': '10'}}}],
            'reads': [], 'timeout_seconds': 300, 'max_requests': 1, 'max_model_calls': 1, 'fallback': 'continue_unchanged'}]}
    policy = ReviewedPolicy.bind(plan, RecipePolicyRecord.model_validate_json(json.dumps(record)))
    recipe.require_policy(policy)
    (output / 'graph.json').write_bytes(canonical(definition))
    (output / 'policy.json').write_bytes(policy.canonical)
    (output / 'recipe.json').write_bytes(recipe.canonical)
    graph = {'definition': 'graph.json', 'releases': [], 'schemas': [{'schema_ref': schema, 'path': 'scalar-schema.json'}]}
    (output / 'compiled.json').write_bytes(canonical({'plan_sha256': plan.sha256, 'policy_sha256': policy.sha256, 'graph': graph}))
    print(json.dumps({'compiled': True, 'plan_sha256': plan.sha256, 'policy_sha256': policy.sha256}))


if __name__ == '__main__':
    main()
