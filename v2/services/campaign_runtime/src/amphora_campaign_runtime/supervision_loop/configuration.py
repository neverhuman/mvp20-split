"""Explicit scoped worker wiring; credentials are environment references, never JSON values."""

import os
from dataclasses import dataclass
from pathlib import Path

from amphora_contracts_core import Identifier, Scope, WireModel
from sqlalchemy import create_engine, text

from ..artifact_bindings.publication import ArtifactPublisher
from ..lifecycle.access import RuntimePrincipal
from ..supervision_client import CheckpointPlanningClient
from ..supervision_context.preparation import ContextPreparer
from ..supervision_delivery import RequestDispatcher
from ..supervision_journal.delivery import DeliveryJournal
from ..supervision_outcomes.collection import ReportCollector
from ..supervision_outcomes.reports import ReportJournal
from ..supervision_resolution import OutcomeResolver
from ..supervision_scope.observations import require
from .driver import CheckpointLoop
from .polling import CheckpointPoller


class Peer(WireModel):
    endpoint: str
    token_env: Identifier
    actor_id: Identifier


class WorkerConfiguration(WireModel):
    database_url_env: Identifier
    actor_id: Identifier
    scope: Scope
    planning: Peer
    data: Peer


@dataclass(frozen=True)
class CheckpointHost:
    engine: object
    principal: RuntimePrincipal
    poller: CheckpointPoller

    def close(self):
        self.engine.dispose()

    @classmethod
    def load(cls, path):
        with Path(path).open('rb') as stream:
            raw = stream.read(65537)
        require(len(raw) <= 65536, 'checkpoint_configuration_size')
        config = WorkerConfiguration.model_validate_json(raw)
        principal = RuntimePrincipal(config.actor_id, config.scope,
            frozenset({'read', 'supervise_prepare', 'supervise_dispatch', 'supervise_accept'}))
        planning = CheckpointPlanningClient(config.planning.actor_id, config.scope,
            config.planning.endpoint, os.environ[config.planning.token_env])
        artifacts = ArtifactPublisher(config.data.endpoint, os.environ[config.data.token_env], config.data.actor_id)
        engine = create_engine(os.environ[config.database_url_env], pool_pre_ping=True,
                               connect_args={'options': '-c statement_timeout=5000'})
        try:
            with engine.connect() as conn:
                require(conn.execute(text('SELECT current_user')).scalar_one() == 'runtime_service',
                        'checkpoint_service_role')
                for table in ('supervision_recipes', 'supervision_winners', 'supervision_call_reservations',
                              'supervision_execution_reports', 'supervision_request_dispositions'):
                    conn.execute(text('SELECT 1 FROM runtime.' + table + ' LIMIT 0'))
            delegation = {(config.scope.tenant_id, config.scope.project_id, config.actor_id): config.planning.actor_id}
            preparer = ContextPreparer(engine, delegation, artifacts)
            reports = ReportJournal(preparer.journal)
            loop = CheckpointLoop(preparer, RequestDispatcher(DeliveryJournal(preparer.journal), planning),
                                  ReportCollector(reports, planning), OutcomeResolver(reports))
            return cls(engine, principal, CheckpointPoller(engine, loop))
        except BaseException:
            engine.dispose()
            raise
