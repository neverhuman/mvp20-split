"""Append-only recipe pin inside the original admission transaction."""

from sqlalchemy import text

from ..lifecycle.claims import RUN
from ..lifecycle.model import TransitionError
from .recipe import ReviewedRecipe


class RecipePins:
    @staticmethod
    def pin(conn, params, policy, recipe):
        recipe = ReviewedRecipe(recipe.canonical)
        recipe.require_policy(policy)
        conn.execute(text('INSERT INTO runtime.supervision_recipes '
            '(tenant_id,project_id,run_id,recipe_sha256,canonical_recipe) '
            'VALUES (:tenant,:project,:run,:recipe,:canonical)'),
            {**params, 'recipe': recipe.sha256, 'canonical': recipe.canonical})

    @staticmethod
    def load(conn, params, policy):
        row = conn.execute(text('SELECT recipe_sha256,canonical_recipe FROM runtime.supervision_recipes WHERE ' + RUN),
                           params).mappings().one_or_none()
        if row is None:
            raise TransitionError('stored_supervision_recipe_missing')
        recipe = ReviewedRecipe(bytes(row['canonical_recipe']))
        recipe.require_policy(policy)
        scope = recipe.document().scope
        if recipe.sha256 != row['recipe_sha256'] or scope.tenant_id != params['tenant'] or scope.project_id != params['project']:
            raise TransitionError('stored_supervision_recipe_mismatch')
        return recipe
