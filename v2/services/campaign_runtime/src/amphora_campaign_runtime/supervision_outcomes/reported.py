"""Bind public owner reports to original retained requests without peer-private code."""

import hashlib
from dataclasses import dataclass

from amphora_contracts_supervision import (
    CheckpointExecutionReport,
    CheckpointRequest,
    SupervisionResponse,
)

from ..supervision_requests.binding import encoded
from ..supervision_scope.observations import require

SUCCESS = frozenset({'proposed', 'abstained', 'policy_rejected'})


@dataclass(frozen=True)
class ReportedExecution:
    canonical: bytes

    @classmethod
    def bind(cls, request, report):
        request = CheckpointRequest.model_validate_json(request.model_dump_json())
        report = CheckpointExecutionReport.model_validate_json(report.model_dump_json())
        original = request.planning_request
        require(report.reference == request.reference and
                report.request_sha256 == hashlib.sha256(encoded(request)).hexdigest(), 'execution_report_request')
        require(report.engagement == original.reference and
                report.planning_request_sha256 == request.planning_request_sha256 ==
                hashlib.sha256(encoded(original)).hexdigest(), 'execution_report_planning')
        require(len(report.attempts) <= original.context.limits.max_attempts, 'execution_report_attempt_limit')
        for ordinal, result in enumerate(report.attempts, 1):
            require(result.attempt.engagement == original.reference and
                    result.attempt.request_sha256 == request.planning_request_sha256 and
                    result.attempt.ordinal == ordinal, 'execution_report_attempt_identity')
            require(ordinal == len(report.attempts) or result.status not in SUCCESS, 'execution_report_after_stop')
        latest = report.attempts[-1] if report.attempts else None
        if report.stop_reason in SUCCESS:
            require(latest is not None and latest.status == report.stop_reason, 'execution_report_status')
        else:
            require(latest is None or latest.status not in SUCCESS, 'execution_report_status')
            if report.stop_reason == 'attempt_limit':
                require(len(report.attempts) == original.context.limits.max_attempts, 'execution_report_not_exhausted')
        canonical = encoded(report)
        require(len(canonical) <= 32768, 'execution_report_size')
        return cls(canonical)

    def document(self):
        return CheckpointExecutionReport.model_validate_json(self.canonical)

    @property
    def sha256(self):
        return hashlib.sha256(self.canonical).hexdigest()

    def require_response(self, response):
        """Match an independently validated response, not merely its attempt ordinal."""
        response = SupervisionResponse.model_validate_json(response.model_dump_json())
        report = self.document()
        require(response.reference == report.reference and response.request_sha256 == report.request_sha256,
                'execution_response_request')
        observation = response.observation
        result = next((item for item in report.attempts if item.attempt == observation.attempt), None)
        require(result is not None and result.status == observation.status and
                result.observation_sha256 == hashlib.sha256(encoded(observation)).hexdigest(),
                'execution_response_observation')
        return result
