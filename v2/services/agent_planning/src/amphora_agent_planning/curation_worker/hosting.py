"""Explicit process composition under the Planning serving role; no migration."""
import os
from dataclasses import dataclass

from sqlalchemy import text

from ..access import Principal
from ..capability_fulfillment.verification import FulfillmentVerifier
from ..capability_fulfillment.worker import FulfillmentWorker
from ..campaign_dispatch.dispatcher import CompilerDispatcher
from ..campaign_dispatch.journal import CompilerJournal
from ..campaign_dispatch.progression import CompilerProgression
from ..campaign_dispatch.store import CompilerStore
from ..curation_compiler.journal import CurationCompilerJournal
from ..curation_compiler.workflow import CurationCompiler
from ..curation_declaration.journal import DeclarationJournal
from ..curation_declaration.workflow import DeclarationPublisher
from ..curation_execution.executor import CurationExecutor
from ..supervision_api.hosting import serving_engine
from .configuration import ReviewedConfiguration
from .coordinator import CurationWorker
from .peers import CurationPeers
from .polling import CurationPoller

TABLES = ('curation_requests', 'curation_progress', 'curation_leases', 'curation_preparation_links',
    'curation_declarations', 'curation_declaration_events', 'compiler_selections',
    'capability_fulfillments', 'capability_verifications')


@dataclass(frozen=True)
class CurationHost:
    engine: object
    principal: Principal
    poller: CurationPoller

    def close(self):
        self.engine.dispose()

    @classmethod
    def load(cls, path, *, enable_provider=False):
        reviewed = ReviewedConfiguration.load(path)
        config = reviewed.configuration
        peers = CurationPeers.bind(reviewed)
        principal = Principal(config.actor_id, config.scope,
            frozenset({'execute_curations', 'record_requests', 'record_attempts', 'read_attempts'}))
        engine = serving_engine(os.environ[config.database_url_env])
        try:
            with engine.connect() as conn:
                for table in TABLES:
                    conn.execute(text('SELECT 1 FROM planning.' + table + ' LIMIT 0'))
            provider = config.live.provider(tuple(policy.budget() for policy in reviewed.policies)) if (
                enable_provider and config.live is not None) else None
            store = CompilerStore(engine, config.runtime_owner, config.actor_id, reviewed.eligibility())
            journal = CompilerJournal(store)
            compiler = CurationCompiler(CurationCompilerJournal(store, journal), CompilerProgression(
                CompilerDispatcher(journal, peers.refresh, peers.runtime, peers.registry)))
            publisher = DeclarationPublisher(DeclarationJournal(engine), peers.artifacts)
            worker = CurationWorker(engine, reviewed.policy_map(), peers.assembler, publisher,
                CurationExecutor(engine, peers.data, provider,
                    timeout_seconds=config.live.timeout_seconds if config.live is not None else 60), compiler)
            fulfillments = FulfillmentWorker(FulfillmentVerifier(engine, peers.acceptance))
            return cls(engine, principal, CurationPoller(worker, list(reviewed.policy_map()), config.worker_id,
                fulfillments=fulfillments))
        except BaseException:
            engine.dispose()
            raise
