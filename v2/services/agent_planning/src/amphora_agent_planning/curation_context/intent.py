"""Byte-owned human intent is context, not instructions or processing authority."""
from dataclasses import dataclass
import json

from amphora_contracts_campaign_curation import campaign_curation_draft_schema
from ..context import RequestSnapshot
from ..context.policy import require
from ..curation_intake.commands import CurationCommand
from ..campaign_context.records import canonical


@dataclass(frozen=True)
class CurationIntent:
    request: RequestSnapshot
    canonical: bytes

    @staticmethod
    def engagement_for(incoming):
        incoming = CurationCommand.restore(incoming.command.canonical_bytes)
        return 'curation-call-' + incoming.command.sha256

    @classmethod
    def bind(cls, request, incoming):
        incoming = CurationCommand.restore(incoming.command.canonical_bytes)
        original = request.document()
        identity = incoming.command.identity
        request = RequestSnapshot.bind(original, actor_id=identity.actor_id, scope=identity.scope)
        require(original.purpose == 'campaign_proposal'
                and original.context.output_schema == campaign_curation_draft_schema(), 'curation_intent_profile')
        require(original.reference.engagement_id == cls.engagement_for(incoming), 'curation_intent_request_binding')
        selected = set(incoming.request.payload.context.artifacts)
        roots = {original.context.objective, original.context.prompt, original.context.policy,
                 original.context.model.configuration}
        require(all(item in roots or any(row.artifact == item for row in original.context.entries)
                    for item in selected), 'curation_intent_artifact_coverage')
        payload = {'format': 'planning-curation-intent.v1', 'authority': 'future_intent_only',
                   'request_sha256': request.sha256, 'command': json.loads(incoming.command.canonical_bytes)}
        return cls(request, canonical(payload))

    @classmethod
    def from_payload(cls, request, payload):
        require(type(payload) is dict and set(payload) == {'format', 'authority', 'request_sha256', 'command'},
                'curation_intent_shape')
        incoming = CurationCommand.restore(canonical(payload['command']))
        result = cls.bind(request, incoming)
        require(result.canonical == canonical(payload), 'curation_intent_payload')
        return result

    @classmethod
    def from_template(cls, template, incoming, policy_id):
        incoming = CurationCommand.restore(incoming.command.canonical_bytes)
        identity = incoming.command.identity
        value = template.document().model_dump(mode='json')
        require(incoming.request.payload.policy_id == policy_id, 'curation_policy_unavailable')
        require(not value['context']['entries'] and not value['context']['omissions'], 'curation_template_sources')
        require(value['reference']['scope'] == identity.scope.model_dump(mode='json')
                and value['actor_id'] == identity.actor_id, 'curation_template_identity')
        value['reference']['engagement_id'] = cls.engagement_for(incoming)
        # decision_scope remains the reviewed compiler declaration digest.
        # A future campaign request has no invented Runtime frontier revision.
        value['runtime_cut'] = None
        roots = {template.document().context.objective, template.document().context.prompt,
                 template.document().context.policy, template.document().context.model.configuration}
        value['context']['entries'] = [{'artifact': item.model_dump(mode='json'), 'role': 'source', 'required': False}
            for item in incoming.request.payload.context.artifacts if item not in roots]
        request = RequestSnapshot.from_bytes(canonical(value), actor_id=identity.actor_id, scope=identity.scope)
        return cls.bind(request, incoming)

    @property
    def identity(self):
        incoming = CurationCommand.restore(canonical(json.loads(self.canonical)['command']))
        return {'curation_id': incoming.curation_id, 'command_sha256': incoming.command.sha256}
