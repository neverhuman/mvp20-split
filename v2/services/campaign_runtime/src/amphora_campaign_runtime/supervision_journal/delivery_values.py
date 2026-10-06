"""Private delivery evidence and lease identity, separate from dispatch authority."""

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Annotated, Literal

from amphora_contracts_core import Digest, Identifier, WireModel
from amphora_contracts_supervision import (
    CheckpointRequest,
    SupervisionCommandReceipt,
    SupervisionRef,
    SupervisionRequest,
)
from pydantic import Field, TypeAdapter

from ..supervision_requests.binding import encoded
from ..supervision_scope.observations import require


def identifier(value):
    return TypeAdapter(Identifier).validate_python(value)


class DeliveryEvidence(WireModel):
    profile: Literal['runtime-supervision-delivery.v1'] = 'runtime-supervision-delivery.v1'
    submission_sha256: Digest
    holder: Identifier
    fence: Annotated[int, Field(ge=0, le=9007199254740991)]
    expires_at: datetime | None
    reason: Identifier | None = None
    receipt: SupervisionCommandReceipt | None = None
    readback: SupervisionRequest | None = None


class CheckpointDeliveryEvidence(DeliveryEvidence):
    profile: Literal['runtime-supervision-delivery.v2'] = 'runtime-supervision-delivery.v2'
    readback: CheckpointRequest | None = None


def evidence_type(request):
    return CheckpointDeliveryEvidence if request.schema_version == '2' else DeliveryEvidence


@dataclass(frozen=True)
class DeliveryLease:
    reference: SupervisionRef
    request_sha256: str
    holder: str
    fence: int
    expires_at: datetime

    @property
    def record(self):
        return {'reference': self.reference.model_dump(mode='json'), 'request_sha256': self.request_sha256,
                'holder': self.holder, 'fence': self.fence, 'expires_at': self.expires_at.isoformat()}


@dataclass(frozen=True)
class DeliveryEvent:
    event_id: str
    sequence: int
    kind: str
    evidence: DeliveryEvidence
    created_at: datetime

    @classmethod
    def from_row(cls, row):
        raw = bytes(row['evidence'])
        document = json.loads(raw)
        require(type(document) is dict, 'delivery_evidence_profile')
        model = {'runtime-supervision-delivery.v1': DeliveryEvidence,
                 'runtime-supervision-delivery.v2': CheckpointDeliveryEvidence}.get(document.get('profile'))
        require(model is not None, 'delivery_evidence_profile')
        evidence = model.model_validate_json(raw)
        require(encoded(evidence) == raw and evidence.fence == row['fence'], 'delivery_evidence_mismatch')
        return cls(row['event_id'], row['sequence'], row['kind'], evidence, row['created_at'])

    def replay(self, submission):
        require(self.evidence.submission_sha256 == submission, 'delivery_event_conflict')
        return self

    def lease(self, reference, request_sha256):
        if self.kind != 'claim':
            return None
        require(self.evidence.expires_at is not None and self.evidence.fence > 0, 'invalid_stored_lease')
        return DeliveryLease(reference, request_sha256, self.evidence.holder,
                             self.evidence.fence, self.evidence.expires_at)


def fingerprint(record):
    from ..compiler.catalog import canonical
    return hashlib.sha256(canonical(record)).hexdigest()
