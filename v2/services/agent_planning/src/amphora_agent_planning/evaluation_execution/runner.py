"""One bounded progress step, original durable issuance, no hidden measured retries."""

from dataclasses import dataclass

from sqlalchemy import text

from ..context.policy import require
from ..evaluation import EvaluationScorer
from ..evaluation.scoring import EvaluationScore
from ..evaluation_batch.storage import EvaluationJournal
from ..orchestration import PlanningRunner
from .projection import MeasuredObservation


@dataclass(frozen=True)
class EvaluationRun:
    score: EvaluationScore
    observations: tuple[MeasuredObservation, ...]
    status: str

    @property
    def passed(self):
        return self.status == 'complete' and self.score.passed


class EvaluationRunner:
    def __init__(self, engine, provider, *, adapter_revision, timeout_seconds):
        self.engine, self.adapter_revision = engine, adapter_revision
        self.suites = EvaluationJournal(engine)
        self.runner = PlanningRunner(engine, provider, timeout_seconds=timeout_seconds)

    def _suite(self, principal, suite_id):
        stored = self.suites.read(principal, suite_id)
        require(stored is not None, 'evaluation_suite_unavailable')
        return stored

    def _attempts(self, principal, batch):
        return tuple(self.runner.journal.read_attempt(principal, task.binding.reference()) for task in batch.tasks)

    def _overage(self, principal, batch):
        principal.require('read_attempts', principal.scope)
        identities = [task.request.document().reference.engagement_id for task in batch.tasks]
        with self.engine.connect() as conn:
            return conn.execute(text('SELECT EXISTS ('
                'SELECT 1 FROM planning.settlements WHERE tenant_id=:tenant AND project_id=:project '
                'AND engagement_id=ANY(:ids) AND overage UNION ALL '
                'SELECT 1 FROM planning.late_observations WHERE tenant_id=:tenant AND project_id=:project '
                'AND engagement_id=ANY(:ids) AND overage)'),
                {'tenant': principal.scope.tenant_id, 'project': principal.scope.project_id, 'ids': identities}).scalar_one()

    def read(self, principal, suite_id):
        protocol, batch = self._suite(principal, suite_id)
        attempts = self._attempts(principal, batch)
        measured = tuple(MeasuredObservation.from_attempt(protocol, task, attempt)
            for task, attempt in zip(batch.tasks, attempts, strict=True)
            if attempt is not None and attempt.observation is not None)
        overage = self._overage(principal, batch)
        # Completion requires original settlements, not merely observed provider text.
        settled = all(attempt is not None and attempt.observation is not None and
            self.runner.settlements.read(principal, task.binding.reference()) is not None
            for task, attempt in zip(batch.tasks, attempts, strict=True))
        status = 'budget_overage' if overage else 'complete' if settled else 'pending'
        score = EvaluationScorer(protocol).score([item.observation for item in measured])
        return EvaluationRun(score, measured, status)

    def step(self, principal, suite_id):
        principal.require('record_requests', principal.scope)
        principal.require('record_attempts', principal.scope)
        protocol, batch = self._suite(principal, suite_id)
        require(protocol.manifest.mode == 'fixture', 'evaluation_live_adapter_unconfigured')
        require(protocol.manifest.adapter_revision == self.adapter_revision, 'evaluation_adapter_revision')
        attempts = self._attempts(principal, batch)
        pending = None
        for task, attempt in zip(batch.tasks, attempts, strict=True):
            if attempt is not None and attempt.observation is not None:
                self.runner.settlements.settle(principal, task.binding)
            elif pending is None:
                pending = task, attempt
        if pending is None:
            return self.read(principal, suite_id)
        task, previous = pending
        if self._overage(principal, batch):
            # Already issued history can recover; overage never authorizes fresh issuance.
            if previous is not None:
                try:
                    recovered = self.runner.dispatch.recover(principal, task.binding)
                    if recovered.observation is not None:
                        self.runner.settlements.settle(principal, task.binding)
                except ValueError as error:
                    if str(error) not in {'dispatch_unknown', 'attempt_not_expired'}:
                        raise
            return self.read(principal, suite_id)
        self.runner.execute(principal, task.binding, task.policy)
        return self.read(principal, suite_id)
