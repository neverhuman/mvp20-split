"""Receipt-first publication via the existing public Artifact transport."""

import hashlib
import uuid
from dataclasses import dataclass

from amphora_contracts_core import SchemaRef
from amphora_contracts_supervision import (
    SupervisionRef,
    checkpoint_context_content_schema,
)

from ..compiler.catalog import canonical
from ..supervision_scope.observations import digest


@dataclass(frozen=True)
class ContextPublicationAddress:
    reference: SupervisionRef
    content_sha256: str

    def __post_init__(self):
        object.__setattr__(self, 'reference', SupervisionRef.model_validate_json(self.reference.model_dump_json()))
        digest(self.content_sha256)

    @property
    def scope(self):
        return self.reference.scope

    def operation(self, family, slot):
        identity = {'profile': 'checkpoint-context-publication.v1', 'reference': self.reference.model_dump(mode='json'),
                    'content_sha256': self.content_sha256, 'family': family, 'slot': slot}
        return uuid.uuid5(uuid.NAMESPACE_URL, canonical(identity).decode()).hex


class ContextPublisher:
    def __init__(self, artifacts):
        self.artifacts = artifacts

    def prepare(self, session, *, prepared_by, guard):
        policy = session.basis.seed.policy
        schema = type(policy.document()).model_json_schema(mode='validation')
        schema_ref = SchemaRef(schema_id='runtime.supervision-policy.v2', version='1',
                               sha256=hashlib.sha256(canonical(schema)).hexdigest())
        policy_ref = self.artifacts.publish(ContextPublicationAddress(session.basis.reference, policy.sha256),
            'policy', policy.canonical, schema_ref, guard)
        body = session.declaration_bytes(policy_ref)
        declaration = self.artifacts.publish(ContextPublicationAddress(session.basis.reference, hashlib.sha256(body).hexdigest()),
            'declaration', body, checkpoint_context_content_schema(), guard)
        guard()
        return session.frame(policy_ref, declaration, prepared_by=prepared_by)
