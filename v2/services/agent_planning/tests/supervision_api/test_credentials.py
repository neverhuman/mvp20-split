"""Trusted configuration and HTTP caller authentication are separate inputs."""

import json

import pytest
from amphora_agent_planning.supervision_api.credentials import (
    AuthenticationError,
    Credentials,
)

from ..supervision_intake.support import principal

TOKEN = 'configuration-fixture-token-000000000000000000'


def configured():
    value = principal()
    return [{'token': TOKEN, 'actor_id': value.actor_id, 'scope': value.scope.model_dump(mode='json'),
             'actions': ['record_requests', 'read_attempts']}]


def test_explicit_configuration_is_copied_and_unknown_callers_rejected():
    records = configured()
    credentials = Credentials.from_json(json.dumps(records))
    records[0]['actions'] = []
    assert credentials.authenticate('Bearer ' + TOKEN) == principal()
    for header in (None, '', 'Basic ' + TOKEN, 'Bearer wrong', 'Bearer ' + 'x' * 513):
        with pytest.raises(AuthenticationError, match='unauthenticated'):
            credentials.authenticate(header)


@pytest.mark.parametrize('mode', ['empty', 'duplicate', 'unknown_grant', 'extra', 'short', 'object', 'nonfinite'])
def test_invalid_operator_configuration_fails_closed(mode):
    records = configured()
    if mode == 'empty':
        records = []
    elif mode == 'duplicate':
        records += records
    elif mode == 'unknown_grant':
        records[0]['actions'].append('call_any_provider')
    elif mode == 'extra':
        records[0]['extra'] = True
    elif mode == 'short':
        records[0]['token'] = 'short'
    elif mode == 'object':
        records = records[0]
    else:
        records[0]['token'] = float('nan')
    with pytest.raises(ValueError):
        Credentials.from_json(json.dumps(records))
