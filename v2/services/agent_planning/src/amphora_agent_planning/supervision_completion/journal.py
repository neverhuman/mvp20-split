"""Reload actual issued and settled history under the original request lock."""

from dataclasses import dataclass
from datetime import datetime

from amphora_contracts_core import Identifier
from amphora_contracts_supervision import CheckpointExecutionReport
from pydantic import TypeAdapter
from sqlalchemy import text

from ..context.policy import require
from ..orchestration import RunOutcome
from ..persistence.family_state import lock_request
from ..persistence.journal import KEY, PlanningJournal
from ..persistence.settlement import SettlementJournal
from ..supervision_execution.completion import ExecutionCompletion
from ..supervision_intake.snapshot import CheckpointIntakeSnapshot
from ..supervision_intake.storage import SupervisionIntake


@dataclass(frozen=True)
class StoredCompletion:
    report: ExecutionCompletion
    outcome: RunOutcome
    registered_at: datetime


class CompletionJournal:
    def __init__(self, engine):
        self.engine = engine
        self.attempts = PlanningJournal(engine)
        self.settlements = SettlementJournal(engine)

    @staticmethod
    def key(principal, engagement_id):
        TypeAdapter(Identifier).validate_python(engagement_id, strict=True)
        return {'tenant': principal.scope.tenant_id, 'project': principal.scope.project_id, 'engagement': engagement_id}

    def _history(self, conn, key, intake):
        rows = conn.execute(text('SELECT a.ordinal,d.ordinal AS issued,o.ordinal AS observed '
            'FROM planning.attempts a LEFT JOIN planning.dispatches d USING(tenant_id,project_id,engagement_id,ordinal) '
            'LEFT JOIN planning.observations o USING(tenant_id,project_id,engagement_id,ordinal) '
            'WHERE a.tenant_id=:tenant AND a.project_id=:project AND a.engagement_id=:engagement ORDER BY a.ordinal'),
            key).mappings().all()
        history = []
        for row in rows:
            if row['issued'] is None:
                require(row['observed'] is None, 'completion_unissued_observation')
                continue  # Unissued reservation remains held; never invent a physical attempt.
            selected = {**key, 'ordinal': row['ordinal']}
            attempt = self.attempts._attempt(conn, selected, intake.planning)
            require(attempt.observation is not None, 'completion_attempt_pending')
            charge = self.settlements._charge(conn, selected, attempt.binding)
            require(self.settlements._read(conn, selected, charge) is not None, 'completion_settlement_missing')
            history.append(attempt)
        return tuple(history)

    def _read(self, conn, key, principal):
        intake = SupervisionIntake._wrapper(conn, key, principal)
        row = conn.execute(text('SELECT * FROM planning.checkpoint_execution_reports WHERE ' + KEY), key).mappings().first()
        if row is None:
            return None
        require(isinstance(intake, CheckpointIntakeSnapshot), 'completion_intake_missing')
        require(row['actor_id'] == principal.actor_id and row['request_sha256'] == intake.sha256,
                'stored_completion_identity')
        wire = CheckpointExecutionReport.model_validate_json(bytes(row['canonical_bytes']))
        outcome = RunOutcome(self._history(conn, key, intake), wire.stop_reason)
        report = ExecutionCompletion.bind(intake, principal, outcome)
        require(report.canonical == bytes(row['canonical_bytes']) and report.sha256 == row['report_sha256'],
                'stored_completion_corrupt')
        return StoredCompletion(report, outcome, row['registered_at'])

    def read(self, principal, engagement_id):
        principal.require('read_attempts', principal.scope)
        key = self.key(principal, engagement_id)
        with self.engine.connect() as conn:
            return self._read(conn, key, principal)

    def finish(self, principal, engagement_id, *, stop_reason):
        principal.require('record_attempts', principal.scope)
        key = self.key(principal, engagement_id)
        with self.engine.begin() as conn:
            lock_request(conn, key)
            previous = self._read(conn, key, principal)
            if previous is not None:
                return previous  # Original completion wins before caller configuration/reason.
            intake = SupervisionIntake._wrapper(conn, key, principal)
            require(isinstance(intake, CheckpointIntakeSnapshot), 'completion_intake_missing')
            outcome = RunOutcome(self._history(conn, key, intake), stop_reason)
            report = ExecutionCompletion.bind(intake, principal, outcome)
            conn.execute(text('INSERT INTO planning.checkpoint_execution_reports '
                '(tenant_id,project_id,engagement_id,actor_id,request_sha256,report_sha256,canonical_bytes) '
                'VALUES (:tenant,:project,:engagement,:actor,:request,:digest,:canonical)'),
                {**key, 'actor': principal.actor_id, 'request': intake.sha256,
                 'digest': report.sha256, 'canonical': report.canonical})
            return self._read(conn, key, principal)
