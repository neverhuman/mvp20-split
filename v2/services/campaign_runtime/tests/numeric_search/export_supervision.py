"""Compile the actual numeric fixture's invoke checkpoint; no SQL or provider access."""

import json
import os
import sys
from pathlib import Path

from amphora_campaign_runtime.compiler import (
    PinnedSchema,
    ResolvedTool,
    SchemaCatalog,
    SchemaIdentity,
    ToolCatalog,
)
from amphora_campaign_runtime.coordinator import ReviewedPlan
from amphora_campaign_runtime.supervision_policy import ReviewedPolicy
from amphora_campaign_runtime.supervision_policy.records import RecipePolicyRecord
from amphora_campaign_runtime.supervision_preparation import RecipeRecord, ReviewedRecipe
from amphora_contracts_campaigns import parse_executable_campaign
from amphora_contracts_core import SchemaRef
from amphora_contracts_tools import LockEntry, ReleaseDescriptor


def compile_fixture(output):
    assert not any('DATABASE_URL' in key or 'API_KEY' in key for key in os.environ)
    config = json.loads((output / 'runtime.json').read_bytes())
    entry, = config['graphs']
    tools = [ResolvedTool(ReleaseDescriptor.model_validate_json((output / item['descriptor']).read_bytes()),
                         LockEntry.model_validate_json(json.dumps(item['lock']))) for item in entry['releases']]
    schemas = [PinnedSchema(SchemaIdentity.from_wire(SchemaRef.model_validate(item['schema_ref'])),
                            (output / item['path']).read_bytes()) for item in entry['schemas']]
    plan = ReviewedPlan.compile(parse_executable_campaign((output / entry['definition']).read_bytes()),
                                ToolCatalog(tools), SchemaCatalog(schemas)).plan
    recipe = ReviewedRecipe.bind(RecipeRecord.model_validate_json((output / 'recipe-input.json').read_bytes()))
    rule = {'checkpoint_id': 'review-numeric-seed', 'target': {'scope_path': [], 'node_id': 'seed'},
            'kind': 'invoke', 'fields': [], 'reads': [], 'timeout_seconds': 300,
            'max_requests': 1, 'max_model_calls': 1, 'fallback': 'continue_unchanged'}
    record = {'profile': 'runtime-supervision-policy.v2', 'scope': recipe.document().scope.model_dump(mode='json'),
              'plan_sha256': plan.sha256, 'context_recipe_sha256': recipe.sha256,
              'ceilings': {'max_checkpoints': 1, 'max_requests': 1, 'max_model_calls': 1}, 'checkpoints': [rule]}
    policy = ReviewedPolicy.bind(plan, RecipePolicyRecord.model_validate_json(json.dumps(record)))
    recipe.require_policy(policy)
    (output / 'supervision-policy.json').write_bytes(policy.canonical)
    (output / 'recipe.json').write_bytes(recipe.canonical)
    (output / 'compiled.json').write_text(json.dumps({'plan_sha256': plan.sha256,
        'policy_sha256': policy.sha256}, indent=2) + '\n', encoding='utf-8')
    print('Numeric graph and invoke supervision policy compiled without SQL')


if __name__ == '__main__':
    compile_fixture(Path(sys.argv[1]))
