"""Public literal supervisor fixtures, with no private Runtime imports."""

import hashlib
import json
from pathlib import Path

from amphora_agent_planning.access import Principal
from amphora_agent_planning.supervision_intake.snapshot import encoded
from amphora_contracts_supervision import SupervisionRequest, parse_supervision_command

FIXTURES = Path(__file__).absolute().parents[4] / 'contracts/supervision/tests/fixtures'


def request(principal=None, change=None):
    data = json.loads((FIXTURES / 'request.json').read_bytes())
    def scoped(value):
        if isinstance(value, dict):
            if set(value) == {'tenant_id', 'project_id'}:
                value.update(principal.scope.model_dump(mode='json'))
            else:
                for item in value.values():
                    scoped(item)
        elif isinstance(value, list):
            for item in value:
                scoped(item)
    if principal is not None:
        scoped(data)
        data['planning_request']['actor_id'] = principal.actor_id
    if change:
        change(data)
    result = SupervisionRequest.model_validate_json(json.dumps(data))
    return result.model_copy(update={'planning_request_sha256': hashlib.sha256(encoded(result.planning_request)).hexdigest()})


def principal():
    value = request()
    return Principal(value.planning_request.actor_id, value.reference.scope,
                     frozenset({'record_requests', 'read_attempts'}))


def command(value, key='command-1'):
    return parse_supervision_command('planning.supervision.request', json.dumps({
        'encoding': 'amphora-command-v2', 'identity': {'scope': value.reference.scope.model_dump(mode='json'),
        'actor_id': value.planning_request.actor_id, 'command_family': 'planning.supervision.request',
        'command_id': key}, 'payload': value.model_dump(mode='json')}))
