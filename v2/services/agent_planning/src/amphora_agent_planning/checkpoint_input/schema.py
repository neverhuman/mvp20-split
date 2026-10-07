"""Versioned schema guidance; remove annotations only at JSON Schema positions."""

from copy import deepcopy

from amphora_contracts_planning import CheckpointDraft

from ..context.policy import require


def without_titles(schema):
    if not isinstance(schema, dict):
        return deepcopy(schema)
    result = {key: deepcopy(value) for key, value in schema.items() if key != 'title'}
    for key in ('$defs', 'definitions', 'properties', 'patternProperties', 'dependentSchemas'):
        if key in result:
            result[key] = {name: without_titles(value) for name, value in result[key].items()}
    for key in ('allOf', 'anyOf', 'oneOf', 'prefixItems'):
        if key in result:
            result[key] = [without_titles(value) for value in result[key]]
    for key in ('additionalProperties', 'unevaluatedProperties', 'propertyNames', 'contains', 'items',
                'unevaluatedItems', 'not', 'if', 'then', 'else', 'contentSchema'):
        if key in result:
            result[key] = without_titles(result[key])
    return result


def guidance(version):
    require(version in {'1', '2'}, 'checkpoint_input_profile')
    original = CheckpointDraft.model_json_schema(mode='validation')
    return original if version == '1' else without_titles(original)
