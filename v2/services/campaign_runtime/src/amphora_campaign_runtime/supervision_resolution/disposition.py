"""Attributable request-level intent; repair never grants a physical call."""

import hashlib
from dataclasses import dataclass
from typing import Literal

from amphora_contracts_core import Digest, Identifier, WireModel
from amphora_contracts_supervision import SupervisionRef

from ..supervision_requests.binding import encoded
from ..supervision_scope.observations import require


class DispositionRecord(WireModel):
    profile: Literal['runtime-supervision-disposition.v1'] = 'runtime-supervision-disposition.v1'
    reference: SupervisionRef
    request_sha256: Digest
    report_sha256: Digest
    kind: Literal['repair', 'fallback']
    reason_code: Identifier
    response_id: Identifier | None
    response_sha256: Digest | None


@dataclass(frozen=True)
class RequestDisposition:
    canonical: bytes

    @classmethod
    def bind(cls, report, kind, reason, response=None):
        source = report.document()
        if response is not None:
            report.require_response(response.bound.document())
        record = DispositionRecord(reference=source.reference, request_sha256=source.request_sha256,
            report_sha256=report.sha256, kind=kind, reason_code=reason,
            response_id=None if response is None else response.bound.document().response_id,
            response_sha256=None if response is None else response.bound.sha256)
        return cls(encoded(record))

    def document(self):
        return DispositionRecord.model_validate_json(self.canonical)

    @property
    def sha256(self):
        return hashlib.sha256(self.canonical).hexdigest()

    @classmethod
    def restore(cls, row, report, responses):
        record = DispositionRecord.model_validate_json(bytes(row['canonical_bytes']))
        response = None
        if record.response_id is not None:
            response = next((item for item in responses if item.bound.document().response_id == record.response_id), None)
            require(response is not None, 'disposition_response_missing')
        rebuilt = cls.bind(report, record.kind, record.reason_code, response)
        require(rebuilt.canonical == bytes(row['canonical_bytes']) and rebuilt.sha256 == row['disposition_sha256'],
                'stored_disposition_corrupt')
        return rebuilt
