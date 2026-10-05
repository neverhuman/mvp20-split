"""Original manifest roles and mandatory-first reads, bounded independently of I/O."""

import hashlib
import json
from dataclasses import dataclass

from amphora_contracts_core import ArtifactRef

from ..context import RequestSnapshot
from ..context.policy import require


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode('utf-8')


@dataclass(frozen=True)
class PlannedArtifact:
    reference: ArtifactRef
    roles: tuple[str, ...]
    required: bool

    def document(self):
        return {'artifact': self.reference.model_dump(mode='json'), 'roles': list(self.roles), 'required': self.required}


@dataclass(frozen=True)
class ArtifactContextPlan:
    request: RequestSnapshot
    items: tuple[PlannedArtifact, ...]

    @classmethod
    def bind(cls, request):
        original = request.document()
        request = RequestSnapshot.bind(original, actor_id=original.actor_id, scope=original.reference.scope)
        require(original.purpose in {'campaign_proposal', 'supervision'}, 'campaign_artifact_context_purpose')
        context = original.context
        rows = [(context.objective, 'objective', True), (context.prompt, 'prompt', True),
                (context.policy, 'policy', True), (context.model.configuration, 'model_configuration', True)]
        rows.extend((entry.artifact, entry.role, entry.required) for entry in context.entries)
        items = {}
        for ref, role, required in rows:
            previous = items.get(ref.artifact_id)
            if previous is None:
                items[ref.artifact_id] = PlannedArtifact(ref, (role,), required)
            else:
                require(previous.reference == ref, 'campaign_artifact_context_identity')
                roles = previous.roles if role in previous.roles else (*previous.roles, role)
                items[ref.artifact_id] = PlannedArtifact(ref, roles, previous.required or required)
        # Stable ordering retains original priority within each requirement class.
        return cls(request, tuple(sorted(items.values(), key=lambda row: not row.required)))

    @property
    def canonical(self):
        return encode({'format': 'planning-campaign-artifact-plan.v1', 'request_sha256': self.request.sha256,
                       'items': [item.document() for item in self.items]})

    @property
    def sha256(self):
        return hashlib.sha256(self.canonical).hexdigest()
