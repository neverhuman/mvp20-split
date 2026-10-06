"""Reviewed admission allowlists bind exact policy/recipe bytes to configured plans."""

from amphora_contracts_core import Scope

from ..coordinator.configuration import _bytes
from ..supervision_policy import ReviewedPolicy
from ..supervision_policy.catalog import PolicyCatalog
from ..supervision_policy.records import read_policy
from ..supervision_scope.observations import require
from .catalog import RecipeCatalog
from .recipe import ReviewedRecipe


def admission_catalogs(config, root, plans):
    require(type(config) is dict and set(config) == {'policies', 'recipes'} and plans is not None,
            'supervision_admission_configuration')
    require(all(type(config[name]) is list and 1 <= len(config[name]) <= 64 for name in config),
            'supervision_admission_bounds')
    recipes = RecipeCatalog(ReviewedRecipe(_bytes(root, path, 262144)) for path in config['recipes'])
    policies = []
    for path in config['policies']:
        raw = _bytes(root, path, 262144)
        record = read_policy(raw)
        require(record.profile == 'runtime-supervision-policy.v2', 'autonomous_recipe_required')
        scope = Scope.model_validate_json(record.scope.model_dump_json())
        plan = plans.require(scope, record.plan_sha256).plan
        policy = ReviewedPolicy.from_bytes(plan, raw)
        recipes.require(policy)
        policies.append(policy)
    return PolicyCatalog(policies), recipes
