"""New explicit profile; fixed predecessor recipe bytes came from cf15a0b7."""

import json
import pytest
from amphora_campaign_runtime.supervision_preparation import FollowupRecipeRecord, RecipeRecord, ReviewedRecipe
from amphora_contracts_planning import checkpoint_draft_schema, checkpoint_followup_draft_schema

from ..supervision_preparation.test_recipe import bind, document


def test_fixed_predecessor_recipe_and_new_profile_remain_distinct():
    old = bind(document())
    assert old.sha256 == '8e53ac98b6a79bacb9a3107026c591ade9b941a2d08bfb90b8a95212066faa7a'
    assert len(old.canonical) == 2786 and old.output_schema == checkpoint_draft_schema()
    value = dict(document(), output_schema=checkpoint_followup_draft_schema().model_dump(mode='json'))
    new = ReviewedRecipe.bind(FollowupRecipeRecord.model_validate_json(json.dumps(value)))
    assert new.sha256 != old.sha256 and new.output_schema == checkpoint_followup_draft_schema()
    assert ReviewedRecipe(new.canonical) == new and ReviewedRecipe(old.canonical) == old
    with pytest.raises(ValueError):
        RecipeRecord.model_validate_json(new.canonical)
    value['output_schema'] = checkpoint_draft_schema().model_dump(mode='json')
    with pytest.raises(ValueError, match='recipe_followup_profile'):
        ReviewedRecipe.bind(FollowupRecipeRecord.model_validate_json(json.dumps(value)))
