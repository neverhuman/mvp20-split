"""Explicit local worker composition with exact templates and disabled-by-default models."""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Literal

from amphora_contracts_core import ArtifactRef, Identifier, Scope, WireModel
from amphora_tool_protocol import ArtifactClient, HttpTransport, WorkerIdentity
from pydantic import Field, model_validator
from sqlalchemy import create_engine, text

from ..access import Principal
from ..checkpoint_openai.configuration import LiveCheckpointSettings
from ..campaign_followup.source import FollowupResearch, FollowupSeed
from ..campaign_research_access import ResearchRecordReader
from ..campaign_research_access.transport import CampaignResearchTransport
from ..context.policy import require
from ..source_access.transport import DataReader
from ..supervision_client import RuntimeClient
from ..supervision_execution.budget_template import ReviewedBudgetTemplate
from ..supervision_execution.templates import BudgetTemplates
from ..supervision_execution.worker import CheckpointWorker
from ..supervision_publication.exchange import CaptureResponseJournal
from ..supervision_publication.journal import CaptureJournal
from ..supervision_publication.workflow import CapturePublisher, CaptureResponder
from .fixture import CheckpointFixture
from .polling import PlanningCheckpointPoller


class Peer(WireModel):
    endpoint: str
    token_env: Identifier


class TemplateFile(WireModel):
    reference: ArtifactRef
    path: str


class FollowupConfiguration(WireModel):
    research: Peer
    seeds: Annotated[tuple[str, ...], Field(min_length=1, max_length=64)]


class WorkerConfiguration(WireModel):
    database_url_env: Identifier
    actor_id: Identifier
    scope: Scope
    publisher_id: Identifier
    data: Peer
    runtime: Peer
    templates: Annotated[tuple[TemplateFile, ...], Field(max_length=64)]
    provider: Literal['disabled', 'fixture_abstain', 'fixture_invalid', 'openai_checkpoint_v1'] = 'disabled'
    live: LiveCheckpointSettings | None = None
    followup: FollowupConfiguration | None = None
    timeout_seconds: Annotated[int, Field(ge=1, le=86400)] = 30

    @model_validator(mode='after')
    def selected_live_settings(self):
        require((self.provider == 'openai_checkpoint_v1') == (self.live is not None), 'checkpoint_live_configuration')
        return self


def bounded_file(path, maximum):
    with path.open('rb') as stream:
        raw = stream.read(maximum + 1)
    require(len(raw) <= maximum, 'checkpoint_configuration_size')
    return raw


@dataclass(frozen=True)
class CheckpointHost:
    engine: object
    principal: Principal
    poller: PlanningCheckpointPoller

    def close(self):
        self.engine.dispose()

    @classmethod
    def load(cls, path):
        path = Path(path)
        config = WorkerConfiguration.model_validate_json(bounded_file(path, 65536))
        principal = Principal(config.actor_id, config.scope,
            frozenset({'record_requests', 'record_attempts', 'read_attempts'}))
        entries = []
        for entry in config.templates:
            require(entry.reference.scope == config.scope, 'checkpoint_template_scope')
            template = ReviewedBudgetTemplate(bounded_file(path.parent / entry.path, 262144))
            entries.append((entry.reference, template))
        templates = BudgetTemplates(entries)
        followup = None
        if config.followup is not None:
            seeds = tuple(FollowupSeed.model_validate_json(bounded_file(path.parent / name, 262144))
                          for name in config.followup.seeds)
            for seed in seeds:
                require(seed.budget_template.scope == config.scope, 'followup_seed_scope')
                templates.require(seed.budget_template)
            peer = config.followup.research
            followup = FollowupResearch.bind(ResearchRecordReader(
                CampaignResearchTransport(peer.endpoint, os.environ[peer.token_env])), seeds)
        provider = (config.live.provider(entries) if config.live is not None else
                    None if config.provider == 'disabled' else CheckpointFixture(config.provider))
        data_token = os.environ[config.data.token_env]
        data = DataReader(config.data.endpoint, data_token)
        publisher_client = ArtifactClient(HttpTransport(config.data.endpoint, data_token),
                                         WorkerIdentity(config.actor_id, config.scope))
        runtime = RuntimeClient(config.actor_id, config.scope, config.runtime.endpoint,
                                os.environ[config.runtime.token_env])
        engine = create_engine(os.environ[config.database_url_env], pool_pre_ping=True,
                               connect_args={'options': '-c statement_timeout=5000'})
        try:
            with engine.connect() as conn:
                require(conn.execute(text('SELECT current_user')).scalar_one() == 'planning_service',
                        'checkpoint_service_role')
                for table in ('supervision_requests', 'checkpoint_execution_reports', 'capture_publications',
                              'capture_response_observations', 'campaign_preparations'):
                    conn.execute(text('SELECT 1 FROM planning.' + table + ' LIMIT 0'))
            worker = CheckpointWorker(engine, data, templates, provider, timeout_seconds=config.timeout_seconds, followup=followup)
            captures = CaptureJournal(engine, config.publisher_id)
            publisher = CapturePublisher(captures, publisher_client)
            responder = CaptureResponder(CaptureResponseJournal(captures), runtime)
            return cls(engine, principal, PlanningCheckpointPoller(engine, worker, publisher, responder))
        except BaseException:
            engine.dispose()
            raise
