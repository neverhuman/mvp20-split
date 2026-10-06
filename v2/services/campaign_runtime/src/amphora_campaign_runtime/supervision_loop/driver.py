"""One bounded checkpoint stage per tick; scheduling and peer work remain separate."""

from dataclasses import dataclass

from ..coordinator.projections import ProjectionUnavailable
from ..supervision_client import ExchangeAbsent, ExchangeUnavailable
from ..supervision_delivery.progress import DeliveryProgress
from ..supervision_resolution.disposition import RequestDisposition
from .fallback import PREPARATION_FAILURES, PinnedFallback

REFRESH = frozenset({'selected_observation_changed', 'context_repair_evidence_changed',
    'context_terminal_winner', 'context_checkpoint_expired', 'context_checkpoint_ineligible',
    'run_not_running', 'delivery_winner_committed', 'delivery_lease_lost', 'resolution_request_superseded'})


@dataclass(frozen=True)
class LoopStep:
    stage: str
    request_sha256: str | None = None
    winner: object | None = None
    reason: str | None = None

    @property
    def terminal(self):
        return self.winner is not None


class CheckpointLoop:
    def __init__(self, preparer, dispatcher, collector, resolver):
        self.preparer, self.dispatcher = preparer, dispatcher
        self.collector, self.resolver = collector, resolver
        self.fallback = PinnedFallback(preparer.journal)

    def tick(self, principal, reference):
        winner = self.resolver.winners.resolve(principal, reference)
        if winner is not None:
            return LoopStep('decided', winner=winner)
        try:
            return self._advance(principal, reference)
        except ValueError as error:
            if str(error) not in REFRESH:
                raise
            return LoopStep('pending', reason=str(error))

    def _prepare(self, principal, reference, parent=None):
        try:
            original = self.preparer.prepare(principal, reference, parent_request_sha256=parent)
        except ProjectionUnavailable:
            return LoopStep('pending', parent, reason='context_publication_uncertain')
        except ValueError as error:
            if str(error) not in PREPARATION_FAILURES:
                raise
            winner = self.fallback.resolve(principal, reference, parent=parent, preparation_reason=str(error))
            return LoopStep('decided' if winner else 'pending', parent, winner, str(error))
        return LoopStep('prepared', original.frame.request_sha256)

    def _advance(self, principal, reference):
        series = self.preparer.journal.series(principal, reference.run_id, reference.decision_id)
        if not series:
            return self._prepare(principal, reference)
        sha = series[-1].frame.request_sha256
        progress = DeliveryProgress.load(self.dispatcher.journal, principal, reference, sha)
        if not progress.terminal:
            self.dispatcher.run(principal, reference, sha)
            return LoopStep('delivery', sha)
        if progress.events[-1].kind != 'recorded':
            winner = self.fallback.resolve(principal, reference, delivery_request=sha)
            return LoopStep('decided' if winner else 'pending', sha, winner)
        if self.collector.journal.read(principal, reference, sha) is None:
            try:
                self.collector.run(principal, reference, sha)
            except (ExchangeAbsent, ExchangeUnavailable):
                return LoopStep('pending', sha, reason='execution_report_unresolved')
            return LoopStep('report_recorded', sha)
        result = self.resolver.resolve(principal, reference, sha)
        if isinstance(result, RequestDisposition):
            return self._prepare(principal, reference, sha)
        return LoopStep('decided' if result else 'pending', sha, result)
