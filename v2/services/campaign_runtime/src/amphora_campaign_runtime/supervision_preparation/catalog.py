"""Exact scoped immutable recipes, with no latest-configuration fallback."""

from types import MappingProxyType

from ..lifecycle.model import TransitionError
from .recipe import ReviewedRecipe


class RecipeCatalog:
    def __init__(self, recipes):
        entries = {}
        for item in recipes:
            recipe = ReviewedRecipe(item.canonical)
            scope = recipe.document().scope
            key = (scope.tenant_id, scope.project_id, recipe.sha256)
            if key in entries:
                raise TransitionError('duplicate_reviewed_recipe')
            entries[key] = recipe
        self._entries = MappingProxyType(entries)

    def require(self, policy):
        record = policy.document()
        recipe = self._entries.get((record.scope.tenant_id, record.scope.project_id, record.context_recipe_sha256))
        if recipe is None:
            raise TransitionError('supervision_recipe_unavailable')
        try:
            recipe.require_policy(policy)
        except ValueError as error:
            raise TransitionError(str(error)) from error
        return recipe
