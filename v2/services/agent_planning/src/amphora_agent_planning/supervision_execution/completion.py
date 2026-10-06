"""Pure owner projection; durable finalization must reload owned settled history."""

import hashlib
from dataclasses import dataclass
from typing import get_args

from amphora_contracts_supervision import (
    CheckpointAttemptResult,
    CheckpointExecutionReport,
    CheckpointStopReason,
)

from ..context import AttemptBinding
from ..context.policy import require
from ..persistence.records import verified_observation
from ..supervision_intake.snapshot import CheckpointIntakeSnapshot, encoded

SUCCESS = frozenset({'proposed', 'abstained', 'policy_rejected'})
STOP_REASONS = frozenset(get_args(CheckpointStopReason))


@dataclass(frozen=True)
class ExecutionCompletion:
    canonical: bytes

    @classmethod
    def bind(cls, intake, principal, outcome):
        require(isinstance(intake, CheckpointIntakeSnapshot), 'completion_checkpoint_required')
        intake = CheckpointIntakeSnapshot.from_bytes(intake.canonical, principal)
        reason, attempts = outcome.stop_reason, outcome.attempts
        require(reason in STOP_REASONS, 'completion_stop_reason')
        maximum = intake.planning.document().context.limits.max_attempts
        require(len(attempts) <= maximum, 'completion_attempt_limit')
        records = []
        for ordinal, stored in enumerate(attempts, 1):
            expected = AttemptBinding(intake.planning, ordinal)
            require(stored.binding == expected, 'completion_attempt_identity')
            require(stored.observation is not None, 'completion_attempt_pending')
            observation = verified_observation(expected, stored.observation)
            wire = observation.document()
            require(ordinal == len(attempts) or wire.status not in SUCCESS, 'completion_after_stop')
            records.append(CheckpointAttemptResult(attempt=expected.reference(),
                observation_sha256=hashlib.sha256(encoded(wire)).hexdigest(), status=wire.status))
        if reason in SUCCESS:
            require(bool(records) and records[-1].status == reason, 'completion_status_mismatch')
        else:
            require(not records or records[-1].status not in SUCCESS, 'completion_status_mismatch')
            if reason == 'attempt_limit':
                require(len(records) == maximum, 'completion_not_exhausted')
        original = intake.document()
        report = CheckpointExecutionReport(reference=original.reference, request_sha256=intake.sha256,
            engagement=original.planning_request.reference, planning_request_sha256=intake.planning.sha256,
            stop_reason=reason, attempts=tuple(records))
        return cls(encoded(report))

    def document(self):
        return CheckpointExecutionReport.model_validate_json(self.canonical)

    @property
    def sha256(self):
        return hashlib.sha256(self.canonical).hexdigest()
