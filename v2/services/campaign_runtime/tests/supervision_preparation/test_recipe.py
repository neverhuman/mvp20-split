"""Private recipe identity and relational limits, without Artifact authority claims."""

import copy
import json
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest
from amphora_campaign_runtime.supervision_preparation import (
    RecipeRecord,
    ReviewedRecipe,
)


def document():
    fixture = Path(__file__).parent.parent / 'supervision_journal/fixtures/checkpoint-frame.json'
    data = json.loads(fixture.read_bytes())['request']['planning_request']['context']
    data.pop('schema_version')
    data.pop('output_schema')
    data['budget_policy'] = data.pop('policy')
    return data


def bind(data):
    return ReviewedRecipe.bind(RecipeRecord.model_validate_json(json.dumps(data)))


def test_recipe_is_immutable_acyclic_and_exact():
    data = document()
    recipe = bind(data)
    assert ReviewedRecipe(recipe.canonical) == recipe
    assert len(recipe.sha256) == 64
    assert 'policy' not in RecipeRecord.model_fields
    data['model']['model_revision'] = 'replacement'
    assert bind(data).sha256 != recipe.sha256
    assert recipe.document().model.model_revision == '1'
    with pytest.raises(FrozenInstanceError):
        recipe.canonical = b'{}'
    with pytest.raises(ValueError, match='noncanonical_recipe'):
        ReviewedRecipe(recipe.canonical + b' ')


@pytest.mark.parametrize('bad', [b'', b' ' * 262145, '{}'], ids=['empty', 'oversize', 'not-bytes'])
def test_recipe_size_and_bytes(bad):
    with pytest.raises(ValueError, match='recipe_size'):
        ReviewedRecipe(bad)


@pytest.mark.parametrize('case,reason', [
    ('scope', 'artifact_scope'), ('identity', 'artifact_identity'),
    ('entry', 'duplicate_entry'), ('omission', 'duplicate_omission'),
    ('included', 'included_omission'), ('action', 'duplicate_action'),
    ('window', 'context_window'), ('budget', 'attempt_budget'),
])
def test_recipe_relational_rejections(case, reason):
    data = document()
    if case == 'scope':
        data['budget_policy']['scope']['project_id'] = 'foreign'
    elif case == 'identity':
        data['prompt']['artifact_id'] = data['objective']['artifact_id']
        data['prompt']['sha256'] = 'a' * 64
    elif case == 'entry':
        data['entries'] *= 2
    elif case == 'omission':
        data['omissions'] *= 2
    elif case == 'included':
        data['omissions'][0]['artifact'] = copy.deepcopy(data['objective'])
    elif case == 'action':
        data['allowed_actions'].append(data['allowed_actions'][0])
    elif case == 'window':
        data['model']['context_window_tokens'] = 2047
    else:
        data['limits']['total_tokens'] = 2047
    with pytest.raises(ValueError, match=reason):
        bind(data)


def test_recipe_preserves_context_order_and_leaves_declaration_space():
    data = document()
    entry = copy.deepcopy(data['entries'][0])
    entry['artifact']['artifact_id'] = 'another'
    data['entries'].append(entry)
    original = bind(data)
    data['entries'].reverse()
    assert bind(data).sha256 != original.sha256
    data['entries'] = [dict(entry, artifact=dict(entry['artifact'], artifact_id=f'item-{i}')) for i in range(128)]
    with pytest.raises(ValueError):
        bind(data)


@pytest.mark.parametrize('path,value', [('profile', 'runtime-supervision-recipe.v2'), ('policy', {})])
def test_closed_private_profile(path, value):
    data = document()
    data[path] = value
    with pytest.raises(ValueError):
        bind(data)
