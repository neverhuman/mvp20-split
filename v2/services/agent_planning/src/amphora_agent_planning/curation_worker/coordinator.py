"""One bounded phase per claim; original history precedes fresh configuration."""
from dataclasses import dataclass
from amphora_tool_protocol import TransportLost, CommandUnresolved
from ..context.policy import require
from ..curation_jobs.journal import CurationJobs
from ..curation_preparation.link import CurationPreparationJournal
from ..curation_result.journal import CurationResultJournal
from .lease import LeaseKeeper

PENDING = frozenset({'curation_provider_unconfigured', 'curation_lease_lost',
    'curation_progress_conflict', 'curation_heartbeat_unavailable', 'compiler_lease_unavailable',
    'metadata_unavailable', 'metadata_deadline', 'curation_processing_unavailable'})
BUDGET = frozenset({'curation_group_calls_exhausted', 'curation_group_cost_exhausted',
    'provider_usage_overage', 'token_budget_exhausted', 'accounting_budget_exhausted'})
PREPARATION = frozenset({'curation_preparation_not_ready', 'curation_declaration_rejected',
    'curation_policy_unavailable', 'curation_predecessor_active', 'metadata_missing', 'metadata_denied'})


@dataclass(frozen=True)
class WorkerTurn:
    curation_id: str
    status: str
    phase: str | None
    reason: str | None


class CurationWorker:
    def __init__(self, engine, policies, assembler, publisher, executor, compiler):
        self.engine, self.policies = engine, dict(policies)
        self.assembler, self.publisher = assembler, publisher
        self.executor, self.compiler = executor, compiler
        self.jobs, self.inputs, self.results = CurationJobs(engine), CurationPreparationJournal(engine), CurationResultJournal(engine)

    def tick(self, principal, curation_id, worker_id):
        lease = self.jobs.claim(principal, curation_id, worker_id, lease_seconds=60)
        if lease is None:
            return WorkerTurn(curation_id, 'busy', None, None)
        with LeaseKeeper(self.jobs, principal, lease) as keeper:
            try:
                self._advance(principal, keeper)
            except (TransportLost, CommandUnresolved):
                return WorkerTurn(curation_id, 'pending', keeper.lease.progress.view.receipt.phase, 'peer_unavailable')
            except ValueError as error:
                code = str(error)
                if code in PENDING:
                    return WorkerTurn(curation_id, 'pending', keeper.lease.progress.view.receipt.phase, code)
                if code in BUDGET or (code in PREPARATION and keeper.current().progress.view.receipt.phase == 'assembling'):
                    self.jobs.fail(principal, keeper.current(), code)
                else:
                    raise
            current = keeper.current().progress
            return WorkerTurn(curation_id, 'terminal' if current.terminal else 'advanced',
                current.view.receipt.phase, current.view.receipt.reason_code)

    def _advance(self, principal, keeper):
        lease = keeper.current()
        phase = lease.progress.view.receipt.phase
        if phase == 'assembling':
            recovered = self.inputs.recover(principal, lease.curation_id)
            require(recovered is not None, 'curation_worker_original')
            if recovered.frozen is not None:
                self.inputs.attach(principal, keeper.current(), recovered.frozen)
                return
            declaration = self.publisher.journal.read(principal, lease.curation_id)
            if declaration is None:
                incoming = recovered.original.incoming
                policy = self.policies.get(incoming.request.payload.policy_id)
                require(policy is not None, 'curation_policy_unavailable')
                original = self.assembler.originals.read(policy.seed(incoming))
                declaration = self.publisher.publish(principal, keeper.current(), policy=policy, original=original)
            else:
                declaration = self.publisher.publish(principal, keeper.current())
            require(declaration.attempt.stage != 'rejected', 'curation_declaration_rejected')
            require(declaration.attempt.stage == 'finalized', 'curation_declaration_incomplete')
            intent = declaration.identity.reviewed().with_artifact(declaration.attempt.result.artifact)
            assembled = self.assembler.read(intent)
            self.inputs.freeze(principal, keeper.current(), assembled)
        elif phase == 'awaiting_provider':
            result = self.executor.execute(principal, lease)
            if result.observation is not None:
                self.results.record(principal, keeper.current())
        elif phase in {'proposed', 'compiling'}:
            self.compiler.advance(principal, lease)
        else:
            require(lease.progress.terminal, 'curation_worker_phase')
