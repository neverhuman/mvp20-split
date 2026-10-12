import json
from dataclasses import replace

import pytest
from amphora_agent_planning.curation_compiler.journal import CurationCompilerJournal
from amphora_agent_planning.curation_compiler.workflow import CurationCompiler
from amphora_agent_planning.curation_declaration.journal import DeclarationJournal
from amphora_agent_planning.curation_result.journal import CurationResultJournal
from amphora_agent_planning.curation_jobs.journal import CurationJobs
from amphora_agent_planning.campaign_dispatch.store import CompilerStore
from amphora_agent_planning.campaign_dispatch.journal import CompilerJournal
from amphora_agent_planning.campaign_dispatch.dispatcher import CompilerDispatcher
from amphora_agent_planning.campaign_dispatch.progression import CompilerProgression
from amphora_agent_planning.campaign_eligibility import EligibilityConfiguration
from ..curation_execution.test_executor import setup as execute_setup
from ..curation_jobs.test_journal import expire
from ..campaign_dispatch_coordinator.support import Refresh, Runtime, Registry

pytestmark = pytest.mark.postgres


def setup(stored, *, invalid_policy=False):
    principal, lease, linked, executor, provider, data = execute_setup(stored)
    declared = DeclarationJournal(stored.engine).read(principal, lease.curation_id).identity.reviewed()
    context = next(row['payload'] for row in linked.frozen.preparation.packet.context()['slices'] if row['lane'] == 'curation_runtime')
    graph = context['draft']['definition']
    future = declared.declaration.document().future
    graph['revision'] = future.revision + (1 if invalid_policy else 0)
    graph['context'] = [row.model_dump(mode='json') for row in future.context]
    raw = json.loads(provider.raw)
    raw['outcome'] = {'kind': 'propose_campaign', 'candidate': {'kind': 'future_campaign', 'title': 'Future',
        'definition': graph, 'expected_evidence': []}, 'gaps': []}
    provider.raw = json.dumps(raw).encode()
    executor.execute(principal, lease)
    progress = CurationResultJournal(stored.engine).record(principal, lease)
    assert progress.view.receipt.phase == 'proposed'
    lease = replace(lease, progress=progress)
    eligibility = EligibilityConfiguration.bind(owner_id='registry-fixture', actor_id='planning-agent', policy_sha256='c' * 64)
    store = CompilerStore(stored.engine, 'runtime', 'planning-agent', eligibility)
    compiler = CompilerJournal(store)
    journal = CurationCompilerJournal(store, compiler)
    return principal, lease, journal, provider, graph


def workflow(stored, principal, lease, journal):
    selected = journal.prepare(principal, lease)
    lease = replace(lease, progress=selected.progress)
    context = journal.compiler.context(principal, selected.selection)
    runtime = Runtime(stored, journal.compiler, None, context.history.authoring)
    registry = Registry(journal.compiler, principal, None)
    refresh = Refresh()
    dispatcher = CompilerDispatcher(journal.compiler, refresh, runtime, registry)
    CurationJobs(stored.engine).heartbeat(principal, lease, lease_seconds=60)
    return CurationCompiler(journal, CompilerProgression(dispatcher)), lease, runtime, refresh, selected


@pytest.mark.parametrize('valid', [True, False])
def test_exact_model_graph_save_validate_and_terminal_replay(stored, valid):
    principal, lease, journal, provider, graph = setup(stored)
    worker, lease, runtime, _, selected = workflow(stored, principal, lease, journal)
    runtime.valid = valid
    first = worker.advance(principal, lease)
    assert first.view.receipt.phase == 'compiling' and first.view.receipt.reason_code == 'draft_saved'
    next_lease = replace(lease, progress=first)
    CurationJobs(stored.engine).heartbeat(principal, next_lease, lease_seconds=60)
    final = worker.advance(principal, next_lease)
    assert final.view.receipt.phase == ('ready' if valid else 'failed')
    assert (final.view.validated_draft is not None) == valid
    assert len(runtime.sent) == 2 and provider.calls == 1
    command = json.loads(runtime.sent[0])
    assert command['payload']['definition'] == graph
    assert worker.advance(principal, lease) == final and len(runtime.sent) == 2
    assert final.view.proposal == lease.progress.view.proposal


def test_lost_save_reply_reconciles_original_command_after_job_replacement(stored):
    principal, lease, journal, provider, _ = setup(stored)
    worker, lease, runtime, refresh, selected = workflow(stored, principal, lease, journal)
    runtime.lose_reply = True
    first = worker.advance(principal, lease)
    assert first.view.receipt.phase == 'compiling' and len(runtime.sent) == 1
    expire(stored, principal, lease.curation_id)
    replacement = CurationJobs(stored.engine).claim(principal, lease.curation_id, 'replacement', lease_seconds=60)
    runtime.lose_reply = False
    refresh.denied = True
    recovered = worker.advance(principal, replacement)
    assert recovered.view.receipt.reason_code == 'draft_saved' and len(runtime.sent) == 1
    refresh.denied = False
    final = worker.advance(principal, replace(replacement, progress=recovered))
    assert final.view.receipt.phase == 'ready' and len(runtime.sent) == 2 and provider.calls == 1


def test_model_cannot_widen_reviewed_campaign_revision(stored):
    principal, lease, journal, provider, _ = setup(stored, invalid_policy=True)
    with pytest.raises(ValueError, match='decision_future_identity'): journal.prepare(principal, lease)
    assert journal.current(principal, lease.curation_id).view.receipt.phase == 'proposed'
    assert provider.calls == 1


def test_selection_recovery_after_lost_progress_write(stored, monkeypatch):
    principal, lease, journal, _, _ = setup(stored)
    project = journal._project
    def crash(*args, **kwargs): raise RuntimeError('after selection commit')
    monkeypatch.setattr(journal, '_project', crash)
    with pytest.raises(RuntimeError): journal.prepare(principal, lease)
    monkeypatch.setattr(journal, '_project', project)
    expire(stored, principal, lease.curation_id)
    replacement = CurationJobs(stored.engine).claim(principal, lease.curation_id, 'replacement', lease_seconds=60)
    recovered = journal.prepare(principal, replacement)
    assert recovered.progress.view.receipt.phase == 'compiling'
    assert recovered.selection == journal.prepare(principal, replace(replacement, progress=recovered.progress)).selection


def test_runtime_validation_survives_job_expiry_and_replacement(stored):
    principal, lease, journal, provider, _ = setup(stored)
    worker, lease, runtime, _, selected = workflow(stored, principal, lease, journal)
    first = worker.advance(principal, lease)
    next_lease = replace(lease, progress=first)
    CurationJobs(stored.engine).heartbeat(principal, next_lease, lease_seconds=60)
    runtime.before_send = lambda: expire(stored, principal, lease.curation_id)
    with pytest.raises(ValueError, match='curation_lease_lost'): worker.advance(principal, next_lease)
    assert len(runtime.sent) == 2
    runtime.before_send = None
    replacement = CurationJobs(stored.engine).claim(principal, lease.curation_id, 'replacement', lease_seconds=60)
    final = worker.advance(principal, replacement)
    assert final.view.receipt.phase == 'ready' and len(runtime.sent) == 2 and provider.calls == 1


def test_expired_job_cannot_register_original_selection(stored):
    from amphora_agent_planning.campaign_dispatch.selection import CompilerSelection
    principal, lease, journal, _, _ = setup(stored)
    expire(stored, principal, lease.curation_id)
    with pytest.raises(ValueError, match='curation_lease_lost'): journal.prepare(principal, lease)
    identifier = CompilerSelection.identity_for(principal.actor_id, lease.progress.view.provider.attempt)
    assert journal.store.read(principal, identifier) is None


def test_constructed_lease_cannot_substitute_another_provider_attempt(stored):
    from types import SimpleNamespace
    from amphora_agent_planning.campaign_dispatch.selection import CompilerSelection
    from amphora_agent_planning.campaign_context.records import canonical
    principal, lease, journal, _, _ = setup(stored)
    selected = journal.prepare(principal, lease)
    foreign = selected.progress.view.provider.attempt.model_copy(update={'ordinal': 2})
    raw = json.loads(selected.selection.canonical)
    raw['origin']['attempt'] = foreign.model_dump(mode='json')
    forged_selection = CompilerSelection(canonical(raw))
    provider = selected.progress.view.provider.model_copy(update={'attempt': foreign})
    progress = replace(selected.progress, view=selected.progress.view.model_copy(update={'provider': provider}))
    forged_lease = replace(lease, progress=progress)
    step = SimpleNamespace(selection_id=forged_selection.effect_id, dispatch=None, pause_reason='forged')
    with pytest.raises(ValueError, match='curation_compiler_attempt'):
        journal.observe(principal, forged_lease, forged_selection, step)
    assert journal.current(principal, lease.curation_id) == selected.progress
