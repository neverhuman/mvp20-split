"""Installed Runtime-only follow-up recipe and scalar graph compiler; no SQL or provider."""

import hashlib
import json
import os
import sys
from pathlib import Path

from amphora_campaign_runtime.compiler import PinnedSchema, SchemaCatalog, SchemaIdentity, ToolCatalog, compile_campaign
from amphora_campaign_runtime.supervision_policy import ReviewedPolicy
from amphora_campaign_runtime.supervision_policy.records import RecipePolicyRecord
from amphora_campaign_runtime.supervision_preparation.recipe import FollowupRecipeRecord, ReviewedRecipe
from amphora_contracts_campaigns import parse_executable_campaign
from amphora_contracts_core import SchemaRef


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()


def main(root):
    assert not any('DATABASE_URL' in key or 'API_KEY' in key for key in os.environ)
    recipe = ReviewedRecipe.bind(FollowupRecipeRecord.model_validate_json((root / 'recipe-input.json').read_bytes()))
    scope = recipe.document().scope.model_dump(mode='json')
    raw = (root / 'scalar-schema.json').read_bytes()
    schema = {'schema_id': 'demo.checkpoint.scalar', 'version': '1', 'sha256': hashlib.sha256(raw).hexdigest()}
    shape = {'kind': 'artifact', 'schema_ref': schema, 'representation': 'demo.parameters', 'unit': '1', 'media_type': 'application/json'}
    definition = {'schema_version': '4', 'profile': 'deterministic-v3', 'campaign_id': 'followup-original', 'revision': 1,
        'scope': scope, 'body': {'inputs': [], 'outputs': [{'name': 'result', 'value_type': shape}], 'nodes': [
            {'kind': 'artifact_materialize', 'node_id': 'pack', 'fields': [{'name': 'a', 'mode': 'inline', 'source': {'kind': 'integer', 'value': 1}}],
             'output': {'name': 'result', 'value_type': shape}},
            {'kind': 'finish', 'node_id': 'finish', 'outputs': [{'port': 'result', 'source': {'kind': 'output', 'node_id': 'pack', 'port': 'result'}}]}],
            'edges': [{'source': 'pack', 'target': 'finish'}]}}
    catalog = SchemaCatalog([PinnedSchema(SchemaIdentity.from_wire(SchemaRef.model_validate(schema)), raw)])
    plan = compile_campaign(parse_executable_campaign(json.dumps(definition)), ToolCatalog([]), catalog)
    record = {'profile': 'runtime-supervision-policy.v2', 'scope': scope, 'plan_sha256': plan.sha256,
        'context_recipe_sha256': recipe.sha256, 'ceilings': {'max_checkpoints': 1, 'max_requests': 1, 'max_model_calls': 1},
        'checkpoints': [{'checkpoint_id': 'retain-followup-intent', 'target': {'scope_path': [], 'node_id': 'pack'},
            'kind': 'artifact_materialize', 'fields': [{'name': 'a', 'value_type': {'kind': 'scalar', 'scalar': 'integer'},
                'constraint': {'kind': 'range', 'minimum': {'kind': 'number', 'value': '0'}, 'maximum': {'kind': 'number', 'value': '10'}}}],
            'reads': [], 'timeout_seconds': 300, 'max_requests': 1, 'max_model_calls': 1, 'fallback': 'continue_unchanged'}]}
    policy = ReviewedPolicy.bind(plan, RecipePolicyRecord.model_validate_json(json.dumps(record)))
    recipe.require_policy(policy)
    (root / 'graph.json').write_bytes(canonical(definition))
    (root / 'recipe.json').write_bytes(recipe.canonical)
    (root / 'policy.json').write_bytes(policy.canonical)
    definition['campaign_id'] = 'followup-successor'
    definition['body']['inputs'] = [{'name': 'previous_result', 'value_type': shape}]
    definition['body']['outputs'].append({'name': 'previous_result', 'value_type': shape})
    definition['body']['nodes'][0]['fields'][0]['source']['value'] = 2
    definition['body']['nodes'][1]['outputs'].append({'port': 'previous_result', 'source': {'kind': 'input', 'name': 'previous_result'}})
    candidate = parse_executable_campaign(json.dumps(definition))
    compile_campaign(candidate, ToolCatalog([]), catalog)
    (root / 'candidate.json').write_bytes(canonical(definition))
    (root / 'compiled.json').write_bytes(canonical({'plan_sha256': plan.sha256, 'policy_sha256': policy.sha256,
        'graph': {'definition': 'graph.json', 'releases': [], 'schemas': [{'schema_ref': schema, 'path': 'scalar-schema.json'}]}}))
    print('Follow-up recipe and both synthetic graph shapes compiled')


if __name__ == '__main__':
    main(Path(sys.argv[1]))
