"""Stable physical-attempt slot and immutable actor/configuration/content binding."""

import hashlib
import json
from dataclasses import dataclass

from amphora_contracts_core import Identifier, Scope
from amphora_contracts_supervision import SupervisionResponse, parse_supervision_command
from pydantic import TypeAdapter

from ..context.policy import require
from ..supervision_intake.snapshot import encoded
from .capture import CaptureArtifact, CaptureOrigin


@dataclass(frozen=True)
class CaptureIdentity:
    canonical: bytes

    @classmethod
    def bind(cls, principal, origin, publisher_id):
        principal.require('record_attempts', origin.scope)
        return cls.restore(principal, origin, publisher_id)

    @classmethod
    def restore(cls, principal, origin, publisher_id):
        require(origin == CaptureOrigin.bind(origin.packet.context.snapshot, principal,
            origin.packet.preparation, origin.observation, kind=origin.kind), 'capture_origin')
        principal.require('read_attempts', origin.scope)
        TypeAdapter(Identifier).validate_python(publisher_id, strict=True)
        intake = origin.packet.context.snapshot
        require(principal.actor_id == intake.planning.document().actor_id, 'capture_actor')
        value = {'profile': 'planning-checkpoint-capture-publication.v1',
            'actor_id': principal.actor_id, 'scope': origin.scope.model_dump(mode='json'),
            'request_sha256': intake.sha256, 'attempt': origin.observation.document().attempt.model_dump(mode='json'),
            'observation_sha256': hashlib.sha256(origin.observation.canonical).hexdigest(),
            'preparation_sha256': origin.packet.preparation.sha256, 'publisher_id': publisher_id,
            'observation_kind': origin.kind}
        return cls(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode())

    @property
    def sha256(self):
        return hashlib.sha256(self.canonical).hexdigest()

    @property
    def actor_id(self):
        return json.loads(self.canonical)['actor_id']

    @property
    def scope(self):
        return Scope.model_validate(json.loads(self.canonical)['scope'])

    @property
    def publication_id(self):
        value = json.loads(self.canonical)
        slot = {key: value[key] for key in ('profile', 'actor_id', 'scope', 'request_sha256', 'attempt', 'observation_kind')}
        return 'capture-' + hashlib.sha256(json.dumps(slot, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

    def response(self, principal, origin, reference=None):
        require(self == self.restore(principal, origin, json.loads(self.canonical)['publisher_id']), 'capture_identity')
        raw = origin.observation.capture.content
        if raw:
            require(reference is not None, 'capture_reference_required')
            reference = CaptureArtifact.bind(origin).require_reference(self.scope, reference)
        else:
            require(reference is None, 'capture_empty_reference')
        intake = origin.packet.context.snapshot
        result = SupervisionResponse(response_id=self.publication_id, reference=intake.document().reference,
            request_sha256=intake.sha256, observation=origin.observation.document(), capture=reference)
        require(len(encoded(result)) <= 262144, 'capture_response_size')
        return result

    def command(self, principal, origin, reference=None):
        response = self.response(principal, origin, reference)
        return parse_supervision_command('runtime.supervision.respond', json.dumps({
            'encoding': 'amphora-command-v2', 'identity': {'scope': self.scope.model_dump(mode='json'),
            'actor_id': self.actor_id, 'command_family': 'runtime.supervision.respond',
            'command_id': self.publication_id}, 'payload': response.model_dump(mode='json')}))
