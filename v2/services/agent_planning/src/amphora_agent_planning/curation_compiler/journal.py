"""Derived original compiler slot; job progress never grants Runtime admission."""
from dataclasses import dataclass
from amphora_contracts_campaign_curation import CurationView
from amphora_contracts_graph_runtime import DraftSelection
from ..campaign_authoring import AuthoringPlan
from ..campaign_decisions import CampaignDecisionReview
from ..campaign_dispatch.selection import CompilerSelection
from ..campaign_proposals import PreparedCampaignProposal
from ..context.policy import require
from ..curation_declaration.journal import DeclarationJournal
from ..curation_jobs.journal import CurationJobs, key_for, current
from ..curation_jobs.state import JobProgress
from ..curation_result.journal import CurationResultJournal


@dataclass(frozen=True)
class CompilerBinding:
    selection: CompilerSelection
    progress: JobProgress


class CurationCompilerJournal:
    def __init__(self, store, compiler_journal):
        require(compiler_journal.store is store, 'curation_compiler_store')
        self.store, self.compiler = store, compiler_journal
        self.engine = store.engine
        self.jobs, self.results = CurationJobs(self.engine), CurationResultJournal(self.engine)
        self.declarations = DeclarationJournal(self.engine)

    def current(self, principal, curation_id):
        principal.require('execute_curations', principal.scope)
        key = key_for(principal, curation_id)
        with self.engine.begin() as conn:
            self.jobs._lock(conn, key)
            original = self.jobs._original(conn, principal, key)
            return None if original is None else current(conn, original)

    def _guard(self, principal, lease, conn):
        progress, _ = self.jobs._owned(conn, principal, lease, key_for(principal, lease.curation_id))
        require(progress.view.receipt.phase in {'proposed', 'compiling'} and progress.view.proposal is not None
                and progress.view.proposal.outcome.kind == 'propose_campaign', 'curation_compiler_phase')

    def prepare(self, principal, lease):
        principal.require('execute_curations', principal.scope)
        outcome = self.results.read(principal, lease.curation_id)
        require(outcome is not None and outcome.disposition == ('proposed', 'provider_proposal'),
                'curation_compiler_proposal')
        identifier = CompilerSelection.identity_for(principal.actor_id, outcome.attempt.binding.reference())
        existing = self.store.read(principal, identifier)
        if existing is None:
            declaration = self.declarations.read(principal, lease.curation_id)
            require(declaration is not None and declaration.attempt.stage == 'finalized', 'curation_compiler_declaration')
            reviewed = declaration.identity.reviewed()
            require(reviewed.with_artifact(declaration.attempt.result.artifact).request == outcome.attempt.binding.request,
                    'curation_compiler_original_declaration')
            proposal = PreparedCampaignProposal.bind(outcome.frozen.preparation, outcome.attempt.binding, outcome.attempt.observation)
            review = CampaignDecisionReview.bind(proposal, reviewed.declaration, reviewed.budget)
            plan = AuthoringPlan.bind(review, reviewed.budget, owner_id=self.store.runtime_owner, actor_id=self.store.runtime_actor)
            selection = CompilerSelection.bind(principal, plan, self.store.eligibility)
            existing = self.store.register(principal, selection, guard=lambda conn: self._guard(principal, lease, conn))
        require(existing.selection.effect_id == identifier, 'curation_compiler_slot')
        progress = self._project(principal, lease, 'compiling', 'compiler_selected', None, selecting=True)
        return CompilerBinding(existing.selection, progress)

    def _project(self, principal, lease, phase, reason, draft, *, selecting=False):
        key = key_for(principal, lease.curation_id)
        with self.engine.begin() as conn:
            self.jobs._lock(conn, key)
            original = self.jobs._original(conn, principal, key)
            require(original is not None, 'curation_compiler_original')
            previous = current(conn, original)
            require(previous is not None, 'curation_compiler_progress')
            if selecting and previous.view.receipt.phase == 'compiling':
                return previous
            if (previous.view.receipt.phase, previous.view.receipt.reason_code, previous.view.validated_draft) == (phase, reason, draft):
                return previous
            self._guard(principal, lease, conn)
            previous, at = self.jobs._owned(conn, principal, lease, key)
            receipt = previous.view.receipt.model_copy(update={'phase': phase, 'reason_code': reason,
                'revision': previous.view.receipt.revision + 1, 'updated_at': at})
            view = CurationView.model_validate_json(previous.view.model_copy(update={'receipt': receipt,
                'validated_draft': draft}).model_dump_json())
            progress = JobProgress(original, view)
            self.jobs._append(conn, key, progress)
            return progress

    def observe(self, principal, lease, selected, step):
        original = self.current(principal, lease.curation_id)
        require(original is not None and original.view.provider is not None and
                selected.document().origin.attempt == original.view.provider.attempt, 'curation_compiler_attempt')
        require(step.selection_id == selected.effect_id, 'curation_compiler_step')
        if step.dispatch is None:
            return self._project(principal, lease, 'compiling', step.pause_reason or 'compiler_pending', None)
        offered = step.dispatch.operation
        retained = self.compiler.read(principal, selected.effect_id, offered.effect.effect_id)
        require(retained is not None and retained == offered, 'curation_compiler_retained_operation')
        kind, state = retained.effect.document().kind, retained.progress.state
        draft = None
        if kind == 'validate' and state == 'compiled':
            value = retained.progress.observation.outcome.readback
            draft = DraftSelection(draft_id=value.draft_id, revision=value.revision, content_sha256=value.content_sha256,
                validation_id=value.validation_id, universe_sha256=value.universe_sha256)
            phase, reason = 'ready', 'draft_validated'
        elif state == 'structural_invalid':
            phase, reason = 'failed', 'draft_structurally_invalid'
        elif state == 'rejected' and kind in {'save', 'validate'}:
            phase, reason = 'failed', 'compiler_command_rejected'
        else:
            phase, reason = 'compiling', step.pause_reason or ('draft_saved' if state == 'saved' else 'compiler_pending')
        return self._project(principal, lease, phase, reason, draft)
