"""Trusted authority and original-request replay, without persistence or provider I/O."""
import hashlib
import json
from dataclasses import dataclass

from amphora_contracts_campaign_curation import (
    CapabilityFulfillmentRequest, CurationRequest, parse_curation, parse_fulfillment,
)
from amphora_contracts_commands import CanonicalCommand

from ..context.policy import require


def _actor(principal, command, action):
    principal.require(action, command.identity.scope)
    if principal.actor_id != command.identity.actor_id:
        raise PermissionError('planning_access_denied')


def _unique(items, key, reason):
    keys = [key(item) for item in items]
    require(len(set(keys)) == len(keys), reason)


@dataclass(frozen=True)
class CurationCommand:
    command: CanonicalCommand
    request: CurationRequest

    @classmethod
    def bind(cls, principal, raw, policy_ids):
        value = cls.restore(raw)
        _actor(principal, value.command, 'record_curations')
        require(value.request.payload.policy_id in policy_ids, 'curation_policy_unavailable')
        return value

    @classmethod
    def restore(cls, raw):
        """Validate historical bytes without reapplying current admission configuration."""
        command = parse_curation(raw)
        request = CurationRequest.model_validate_json(command.canonical_bytes)
        context = request.payload.context
        _unique(context.knowledge, lambda item: item.snapshot.graph.graph_id, 'duplicate_curation_graph')
        _unique(context.questions, lambda item: item.question_id, 'duplicate_curation_question')
        _unique(context.needs, lambda item: item.need_id, 'duplicate_curation_need')
        _unique(context.artifacts, lambda item: item.artifact_id, 'duplicate_curation_artifact')
        return cls(command, request)

    @property
    def curation_id(self):
        # Identity, not changing payload bytes: one durable slot for the original command.
        raw = json.dumps(self.command.identity.model_dump(mode='json'), sort_keys=True,
                         separators=(',', ':')).encode()
        return 'curation-' + hashlib.sha256(raw).hexdigest()

    def reconcile(self, original_bytes):
        original = parse_curation(original_bytes)
        require(original == self.command, 'curation_command_conflict')
        return self.curation_id

    def require_read(self, principal):
        _actor(principal, self.command, 'read_curations')


@dataclass(frozen=True)
class FulfillmentCommand:
    command: CanonicalCommand
    request: CapabilityFulfillmentRequest

    @classmethod
    def bind(cls, principal, raw):
        command = parse_fulfillment(raw)
        _actor(principal, command, 'fulfill_capabilities')
        request = CapabilityFulfillmentRequest.model_validate_json(command.canonical_bytes)
        _unique(request.payload.acceptance_evidence, lambda item: item.artifact_id,
                'duplicate_fulfillment_evidence')
        return cls(command, request)

    def reconcile(self, original_bytes):
        require(parse_fulfillment(original_bytes) == self.command, 'fulfillment_command_conflict')

    def require_read(self, principal):
        _actor(principal, self.command, 'read_capabilities')
