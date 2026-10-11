"""Rebuildable exact lookup; called inside the existing accepted-save transaction."""

import hashlib
from dataclasses import dataclass
from typing import Literal

from amphora_contracts_core import Digest, Identifier, WireModel
from amphora_contracts_planning import CampaignOriginDraft
from sqlalchemy import text

from ..campaign_context.records import canonical
from ..campaign_dispatch.observation import CompilerObservation
from ..context.policy import require


class _Pointer(WireModel):
    format: Literal['planning-campaign-origin-pointer.v1'] = 'planning-campaign-origin-pointer.v1'
    draft: CampaignOriginDraft
    actor_id: Identifier
    selection_id: Identifier
    selection_sha256: Digest
    effect_id: Identifier
    effect_sha256: Digest
    observation_sha256: Digest


@dataclass(frozen=True)
class OriginPointer:
    canonical: bytes

    @classmethod
    def bind(cls, selection, operation):
        if operation.effect.document().kind != 'save' or operation.progress.state != 'saved':
            return None
        observed = CompilerObservation.restore(operation.progress.observation.canonical,
            selection, operation.effect, operation.request)
        require(observed.status == 'saved', 'origin_saved_required')
        readback = observed.outcome.readback
        head = readback.head
        value = _Pointer(draft=CampaignOriginDraft(scope=readback.scope, draft_id=head.draft_id,
            revision=head.revision, content_sha256=head.content_sha256), actor_id=selection.document().actor_id,
            selection_id=selection.effect_id, selection_sha256=selection.sha256,
            effect_id=operation.effect.effect_id, effect_sha256=operation.effect.sha256,
            observation_sha256=hashlib.sha256(observed.canonical).hexdigest())
        return cls.restore(canonical(value.model_dump(mode='json')))

    @classmethod
    def restore(cls, raw):
        require(type(raw) is bytes and 0 < len(raw) <= 8192, 'origin_pointer_size')
        value = _Pointer.model_validate_json(raw)
        require(canonical(value.model_dump(mode='json')) == raw, 'origin_pointer_canonical')
        return cls(raw)

    def document(self):
        return _Pointer.model_validate_json(self.canonical)

    @property
    def sha256(self):
        return hashlib.sha256(self.canonical).hexdigest()


class OriginIndex:
    KEY = 'tenant_id=:tenant AND project_id=:project AND draft_id=:draft AND revision=:revision'

    @staticmethod
    def key(draft):
        draft = CampaignOriginDraft.model_validate_json(draft.model_dump_json())
        return {'tenant': draft.scope.tenant_id, 'project': draft.scope.project_id,
                'draft': draft.draft_id, 'revision': draft.revision}

    @classmethod
    def read(cls, connection, draft):
        row = connection.execute(text('SELECT * FROM planning.campaign_origins WHERE ' + cls.KEY),
                                 cls.key(draft)).mappings().first()
        if row is None:
            return None
        pointer = OriginPointer.restore(bytes(row['pointer_bytes']))
        value = pointer.document()
        require(pointer.sha256 == row['pointer_sha256'] and value.selection_id == row['selection_id'] and
                value.effect_id == row['effect_id'] and value.draft.content_sha256 == row['content_sha256'],
                'origin_index_corrupt')
        require(value.draft == draft, 'origin_draft_mismatch')
        return pointer

    @classmethod
    def record(cls, connection, selection, operation):
        pointer = OriginPointer.bind(selection, operation)
        if pointer is None:
            return None
        value = pointer.document()
        params = cls.key(value.draft) | {'content': value.draft.content_sha256,
            'selection': value.selection_id, 'effect': value.effect_id,
            'hash': pointer.sha256, 'body': pointer.canonical}
        connection.execute(text('INSERT INTO planning.campaign_origins '
            '(tenant_id,project_id,draft_id,revision,content_sha256,selection_id,effect_id,pointer_sha256,pointer_bytes) '
            'VALUES (:tenant,:project,:draft,:revision,:content,:selection,:effect,:hash,:body) '
            'ON CONFLICT DO NOTHING'), params)
        require(cls.read(connection, value.draft) == pointer, 'origin_association_conflict')
        return pointer
