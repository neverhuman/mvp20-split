"""Planning-owned packet, history-first recovery and bounded checkpoint execution."""

from datetime import datetime, timezone

from sqlalchemy import text

from ..campaign_artifact_context import CampaignArtifactContextReader
from ..campaign_packet import prepare
from ..campaign_preparations.journal import CampaignPreparationJournal
from ..campaign_preparations.record import CampaignPreparation
from ..campaign_slice_plan import CampaignSlicePlan
from ..context import AttemptBinding
from ..context.policy import require
from ..orchestration import PlanningRunner, RunOutcome
from ..orchestration.runner import BUDGET_STOPS
from ..persistence.dispatch import DispatchJournal
from ..persistence.journal import KEY, PlanningJournal
from ..persistence.settlement import SettlementJournal
from ..supervision_intake import SupervisionIntake
from ..supervision_intake.snapshot import CheckpointIntakeSnapshot
from .packet import CheckpointPacket, CheckpointProvider

STOPS = BUDGET_STOPS | {'checkpoint_deadline', 'execution_processing_unavailable',
    'required_artifact_unavailable', 'required_packet_size', 'required_input_limit'}


class CheckpointWorker:
    def __init__(self, engine, data, templates, provider, *, timeout_seconds):
        require(type(timeout_seconds) is int and 1 <= timeout_seconds <= 86400, 'dispatch_timeout')
        self.engine, self.data, self.templates, self.provider = engine, data, templates, provider
        self.timeout_seconds = timeout_seconds
        self.intake = SupervisionIntake(engine)
        self.preparations = CampaignPreparationJournal(engine)
        self.journal = PlanningJournal(engine)
        self.dispatch = DispatchJournal(engine)
        self.settlements = SettlementJournal(engine)

    def _deadline(self, intake):
        with self.engine.connect() as conn:
            timely = conn.execute(text('SELECT extract(epoch FROM clock_timestamp())*1000 < :deadline'),
                {'deadline': intake.document().deadline_unix_ms}).scalar_one()
        require(timely, 'checkpoint_deadline')

    def _issued(self, principal, binding):
        reference = binding.reference()
        key = {**self.journal._key(reference.engagement), 'ordinal': reference.ordinal}
        with self.engine.connect() as conn:
            return conn.execute(text('SELECT 1 FROM planning.dispatches WHERE ' + KEY +
                ' AND ordinal=:ordinal'), key).first() is not None

    def _provider_deadline(self, intake, packet, binding):
        self._deadline(intake)
        packet.authorize(self.data)
        key = {**self.journal._key(binding.reference().engagement), 'ordinal': binding.ordinal}
        with self.engine.connect() as conn:
            issued = self.dispatch._issued(conn, key)
            require(issued is not None and not issued['expired'], 'checkpoint_deadline')
        delta = issued['deadline'] - datetime(1970, 1, 1, tzinfo=timezone.utc)
        milliseconds = delta.days * 86400000 + delta.seconds * 1000 + delta.microseconds // 1000
        return min(milliseconds, intake.document().deadline_unix_ms)

    def _history(self, principal, binding):
        current = self.journal.read_attempt(principal, binding.reference())
        if current is None or (current.observation is None and not self._issued(principal, binding)):
            return None
        require(self.preparations.read(principal, binding.reference().engagement) is not None,
                'execution_preparation_missing')
        if current.observation is None:
            try:
                current = self.dispatch.recover(principal, binding)
            except ValueError as exc:
                if str(exc) != 'attempt_not_expired':
                    raise
        if current.observation is not None:
            self.settlements.settle(principal, binding)
        return current

    def _packet(self, principal, intake):
        stored = self.preparations.read(principal, intake.planning.document().reference)
        if stored is None:
            projection = CampaignArtifactContextReader(self.data).read(intake.planning).projection
            plan = CampaignSlicePlan.from_artifacts(projection)
            result = prepare(plan)
            require(result.packet is not None, result.failure)
            # Validate checkpoint/configuration before retaining or issuing the packet.
            candidate = CheckpointPacket.bind(intake, principal, CampaignPreparation.bind(plan, result.packet))
            candidate.context.budget_policy(self.templates)
            self._deadline(intake)
            stored = self.preparations.register(principal, plan, result.packet)
        return CheckpointPacket.bind(intake, principal, stored.record)

    def run(self, principal, engagement_id):
        principal.require('record_attempts', principal.scope)
        intake = self.intake.request(principal, engagement_id)
        require(isinstance(intake, CheckpointIntakeSnapshot), 'execution_checkpoint_intake')
        attempts = []
        for ordinal in range(1, intake.planning.document().context.limits.max_attempts + 1):
            binding = AttemptBinding(intake.planning, ordinal)
            current = self._history(principal, binding)
            if current is None:
                try:
                    self._deadline(intake)
                    packet = self._packet(principal, intake)
                    policy = packet.context.budget_policy(self.templates)
                    packet.authorize(self.data)
                    self._deadline(intake)
                    provider = CheckpointProvider(self.provider, packet,
                        lambda bound, retained=packet: self._provider_deadline(intake, retained, bound))
                    current = PlanningRunner(self.engine, provider, timeout_seconds=self.timeout_seconds).execute(
                        principal, binding, policy)
                except ValueError as exc:
                    if str(exc) not in STOPS:
                        raise
                    return RunOutcome(tuple(attempts), str(exc))
            attempts.append(current)
            if current.observation is None:
                return RunOutcome(tuple(attempts), 'attempt_pending')
            status = current.observation.document().status
            if status in {'proposed', 'abstained', 'policy_rejected'}:
                return RunOutcome(tuple(attempts), status)
        return RunOutcome(tuple(attempts), 'attempt_limit')
