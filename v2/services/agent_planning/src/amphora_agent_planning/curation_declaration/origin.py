"""Rebuild reviewed declaration bytes from immutable original configuration."""
from dataclasses import dataclass
import hashlib
import json

from amphora_contracts_artifacts import ContentDescriptor, DerivationDeclaration, TransformationDescriptor
from ..campaign_context.records import canonical
from ..context.policy import require
from ..context.snapshot import _object, _constant
from ..curation_intake.commands import CurationCommand
from ..curation_policy import CurationPolicy
from ..curation_runtime import CurationRuntimeContext


@dataclass(frozen=True)
class DeclarationArtifact:
    body: bytes
    content: ContentDescriptor
    declaration: DerivationDeclaration


@dataclass(frozen=True)
class DeclarationOrigin:
    canonical: bytes

    @classmethod
    def bind(cls, policy, original):
        policy = CurationPolicy.from_bytes(policy.canonical)
        reviewed = policy.declare(original)
        raw = canonical({'profile': 'planning-curation-declaration.v1',
            'policy': json.loads(policy.canonical), 'runtime': json.loads(original.canonical),
            'command': json.loads(reviewed.intent.canonical)['command']})
        require(len(raw) <= 8388608, 'curation_declaration_origin_limit')
        return cls(raw)

    @classmethod
    def restore(cls, raw):
        require(type(raw) is bytes and 0 < len(raw) <= 8388608, 'curation_declaration_origin_limit')
        value = json.loads(raw.decode('utf-8'), object_pairs_hook=_object, parse_constant=_constant)
        require(type(value) is dict and set(value) == {'profile', 'policy', 'runtime', 'command'}
                and value['profile'] == 'planning-curation-declaration.v1', 'curation_declaration_origin_shape')
        policy = CurationPolicy.from_bytes(canonical(value['policy']))
        incoming = CurationCommand.restore(canonical(value['command']))
        original = CurationRuntimeContext.from_payload(policy.seed(incoming), value['runtime'])
        result = cls.bind(policy, original)
        require(result.canonical == raw, 'curation_declaration_origin_canonical')
        return result

    @property
    def sha256(self):
        return hashlib.sha256(self.canonical).hexdigest()

    def incoming(self):
        return CurationCommand.restore(canonical(json.loads(self.canonical)['command']))

    def reviewed(self):
        value = json.loads(self.canonical)
        policy = CurationPolicy.from_bytes(canonical(value['policy']))
        return policy.declare(CurationRuntimeContext.from_payload(policy.seed(self.incoming()), value['runtime']))

    def artifact(self):
        reviewed = self.reviewed()
        context = reviewed.intent.request.document().context
        roots = tuple(dict.fromkeys((context.objective, context.policy, context.model.configuration, context.prompt)))
        body = reviewed.declaration.canonical
        content = ContentDescriptor(sha256=hashlib.sha256(body).hexdigest(), size_bytes=len(body),
            media_type='text/plain', schema_ref=context.policy.schema_ref)
        derivation = DerivationDeclaration(transformation=TransformationDescriptor(
            transformation_id='planning.curation-reviewed-declaration', version='1', sha256=self.sha256), inputs=roots)
        return DeclarationArtifact(body, content, derivation)

    @property
    def scope(self):
        return self.incoming().command.identity.scope

    @property
    def actor_id(self):
        return self.incoming().command.identity.actor_id

    @property
    def publication_id(self):
        return self.incoming().curation_id
