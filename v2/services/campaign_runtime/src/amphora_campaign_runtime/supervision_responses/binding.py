"""Provenance of a response; current policy, budgets and acceptance are separate."""

import hashlib
from dataclasses import dataclass

from amphora_contracts_supervision import SupervisionResponse

from ..supervision_requests.binding import encoded
from ..supervision_requests.profiles import request_binding
from ..supervision_scope.observations import require
from .capture import proposal_from_capture


@dataclass(frozen=True)
class SupervisionResponseBinding:
    canonical: bytes

    @classmethod
    def bind(cls, origin, footprint, response, *, actor_id, capture_bytes):
        request = origin.document()
        checked = request_binding(request).bind(request, footprint, actor_id=actor_id)
        require(checked == origin, 'original_supervision_bytes_mismatch')
        record = SupervisionResponse.model_validate_json(response.model_dump_json())
        require(record.reference == request.reference and record.request_sha256 == origin.sha256,
                'response_request_mismatch')
        original, observation = request.planning_request, record.observation
        require(observation.attempt.engagement == original.reference and
                observation.attempt.request_sha256 == request.planning_request_sha256,
                'response_attempt_mismatch')
        require(observation.attempt.ordinal <= original.context.limits.max_attempts, 'response_attempt_limit')
        usage = observation.usage
        require(usage.certainty != 'reported' or None not in
                (usage.input_tokens, usage.output_tokens, usage.accounting_units), 'incomplete_reported_usage')
        require(capture_bytes is None or type(capture_bytes) is bytes, 'capture_bytes_required')
        raw = b'' if capture_bytes is None else capture_bytes
        require(len(raw) <= 65536 and len(raw) == observation.captured_bytes and
                hashlib.sha256(raw).hexdigest() == observation.output_sha256, 'capture_content_mismatch')
        if record.capture is None:
            require(not raw and observation.status not in {'proposed', 'abstained'}, 'capture_artifact_missing')
        else:
            require(capture_bytes is not None, 'capture_unavailable')
            require(record.capture.scope == original.reference.scope and record.capture.size_bytes == len(raw) and
                    record.capture.sha256 == observation.output_sha256, 'capture_artifact_mismatch')
        if observation.status in {'proposed', 'abstained'}:
            proposal_from_capture(original, observation, raw)
        else:
            require(observation.proposal is None, 'diagnostic_has_proposal')
        canonical = encoded(record)
        require(len(canonical) <= 262144, 'supervision_response_limit')
        return cls(canonical)

    @property
    def sha256(self):
        return hashlib.sha256(self.canonical).hexdigest()

    def document(self):
        return SupervisionResponse.model_validate_json(self.canonical)
