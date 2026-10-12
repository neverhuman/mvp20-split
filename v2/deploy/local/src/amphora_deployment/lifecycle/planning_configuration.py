"""Map reviewed Planning host settings without importing the owner implementation."""
import json
import re

from ..profile import require


def planning_environment(settings, grants):
    require(type(settings) is dict and set(settings) <= {
        'principals', 'topology_configuration', 'curation_policies'} and 'principals' in settings,
        'lifecycle_planning_config')
    require(type(settings['principals']) is list, 'lifecycle_planning_principals')
    principals = []
    for principal in settings['principals']:
        require(type(principal) is dict and set(principal) == {'token_env', 'actor_id', 'scope', 'actions'},
                'lifecycle_planning_principal')
        require(type(principal['token_env']) is str and principal['token_env'] in grants,
                'lifecycle_planning_principal_grant')
        principals.append({key: value for key, value in principal.items() if key != 'token_env'} |
                          {'token': grants[principal['token_env']]})
    result = {'AMPHORA_PLANNING_SUPERVISION_CREDENTIALS': json.dumps(principals)}
    if 'topology_configuration' in settings:
        result['AMPHORA_PLANNING_TOPOLOGY_CONFIG'] = settings['topology_configuration']
    if 'curation_policies' in settings:
        policies = settings['curation_policies']
        require(type(policies) is list and len(policies) <= 32, 'lifecycle_planning_curation_policies')
        # Public core Identifier spelling; no private Planning parser dependency.
        require(all(type(value) is str and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:-]{0,127}', value)
                    for value in policies), 'lifecycle_planning_curation_policy_id')
        require(len(policies) == len(set(policies)), 'lifecycle_planning_curation_policy_duplicate')
        result['AMPHORA_PLANNING_CURATION_POLICIES'] = json.dumps(policies)
    return result
