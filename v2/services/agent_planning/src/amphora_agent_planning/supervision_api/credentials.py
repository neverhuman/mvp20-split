"""Operator-selected principals; never deserialize permissions from HTTP callers."""

import hmac
import json

from amphora_contracts_core import Scope

from ..access import Principal
from ..context.policy import require
from ..context.snapshot import _constant, _object


class AuthenticationError(PermissionError):
    pass


class Credentials:
    def __init__(self, entries):
        self._entries = tuple(entries)
        require(1 <= len(self._entries) <= 64, 'credential_count')
        require(all(type(token) is str and 32 <= len(token) <= 512 and
                    all(33 <= ord(char) <= 126 for char in token) and isinstance(principal, Principal)
                    for token, principal in self._entries), 'invalid_configured_credential')
        require(len({token for token, _ in self._entries}) == len(self._entries), 'duplicate_configured_credential')

    @classmethod
    def from_json(cls, raw):
        require(type(raw) is str and len(raw.encode('utf-8')) <= 65536, 'credential_configuration_size')
        records = json.loads(raw, object_pairs_hook=_object, parse_constant=_constant)
        require(type(records) is list, 'credential_configuration_shape')
        entries = []
        for record in records:
            require(type(record) is dict and set(record) == {'token', 'actor_id', 'scope', 'actions'} and
                    type(record['actions']) is list, 'credential_configuration_shape')
            principal = Principal(record['actor_id'], Scope.model_validate_json(json.dumps(record['scope'])),
                                  frozenset(record['actions']))
            entries.append((record['token'], principal))
        return cls(entries)

    def authenticate(self, authorization):
        if type(authorization) is str and authorization.startswith('Bearer ') and len(authorization) <= 519:
            supplied = authorization[7:].encode('utf-8')
            for token, principal in self._entries:
                if hmac.compare_digest(supplied, token.encode('ascii')):
                    return principal
        raise AuthenticationError('unauthenticated')
