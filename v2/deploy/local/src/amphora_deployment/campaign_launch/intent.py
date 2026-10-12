"""Immutable canonical identity at the authenticated launch boundary."""
import json
from dataclasses import dataclass

from amphora_contracts_campaign_launch import LaunchProfileRef, parse_launch
from amphora_contracts_commands import CanonicalCommand, CommandEncodingError
from amphora_contracts_core import Scope


class LaunchError(ValueError):
    """Safe reason code; never includes raw payloads or credentials."""


@dataclass(frozen=True, slots=True)
class LaunchIntent:
    request: CanonicalCommand
    admission: CanonicalCommand

    @classmethod
    def parse(cls, raw: bytes):
        try:
            return cls(*parse_launch(raw))
        except (CommandEncodingError, ValueError):
            raise LaunchError('launch_request_invalid') from None

    def authorize(self, actor_id: str, scope: Scope):
        if self.request.identity.actor_id != actor_id or self.request.identity.scope != scope:
            raise LaunchError('launch_scope_denied')

    @property
    def profile(self) -> LaunchProfileRef:
        return LaunchProfileRef.model_validate_json(json.dumps(json.loads(self.request.canonical_bytes)['payload']['profile']))

    @property
    def admission_route(self):
        return '/v1/graph-runs/drafts'

    @property
    def key(self) -> tuple[str, str, str, str]:
        identity = self.request.identity
        return identity.scope.tenant_id, identity.scope.project_id, identity.actor_id, identity.command_id
