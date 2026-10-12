import json
from dataclasses import replace

from amphora_agent_planning.curation_intake.journal import CurationJournal
from .test_commands import request


def environment(stored):
    principal = replace(stored.principal, actions=frozenset({'record_curations', 'read_curations'}))
    value = request()
    value['identity']['actor_id'] = principal.actor_id
    value['identity']['scope'] = principal.scope.model_dump(mode='json')
    value['payload']['context']['draft']['scope'] = principal.scope.model_dump(mode='json')
    return principal, json.dumps(value), CurationJournal(stored.engine, {'synthetic'})
