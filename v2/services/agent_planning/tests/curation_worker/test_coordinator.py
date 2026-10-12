import json

import pytest
from amphora_agent_planning.curation_worker.coordinator import CurationWorker
from amphora_agent_planning.curation_worker.discovery import CurationDiscovery
from amphora_agent_planning.curation_jobs.journal import CurationJobs
from amphora_agent_planning.curation_policy import CurationPolicy
from amphora_agent_planning.curation_intake.commands import CurationCommand
from amphora_agent_planning.curation_runtime import CurationRuntimeContext
from amphora_agent_planning.curation_declaration.origin import DeclarationOrigin
from amphora_agent_planning.curation_declaration.journal import DeclarationJournal
from amphora_agent_planning.curation_declaration.workflow import DeclarationPublisher
from amphora_agent_planning.curation_execution.executor import CurationExecutor
from amphora_tool_protocol import ArtifactClient, WorkerIdentity
from ..curation_policy.test_policy import config
from ..curation_result.test_journal import setup as staged
from ..curation_execution.test_executor import Provider
from ..publication.test_workflow import DataPeer

pytestmark = pytest.mark.postgres


class NoCompiler:
    def advance(self, *args): raise AssertionError('Abstention cannot compile a graph')


def setup(stored):
    principal, lease, intent, intake, draft, assembler, run = staged(stored, freeze=False)
    value = config(); value['template'] = intent.request.document().model_dump(mode='json')
    policy = CurationPolicy.from_bytes(json.dumps(value).encode())
    incoming = CurationCommand.restore(json.dumps(json.loads(intent.canonical)['command']))
    original = CurationRuntimeContext.bind(policy.seed(incoming), draft, run)
    origin = DeclarationOrigin.bind(policy, original)
    peer = DataPeer(origin, origin.artifact())
    publisher = DeclarationPublisher(DeclarationJournal(stored.engine),
        ArtifactClient(peer, WorkerIdentity(principal.actor_id, principal.scope)))
    data = assembler.artifacts.reader.data
    data.bodies['output-1'] = origin.artifact().body
    body = json.dumps({'schema_version': '1', 'profile': 'planning.campaign-curation-draft.v1',
        'authority': 'proposal_only', 'scientific_authority': 'not_established',
        'decision_scope': origin.reviewed().declaration.sha256, 'rationale': 'Synthetic engineering boundary',
        'outcome': {'kind': 'abstain', 'reason_code': 'insufficient_evidence'}, 'unresolved': []}).encode()
    provider = Provider(body)
    executor = CurationExecutor(stored.engine, data, provider)
    worker = CurationWorker(stored.engine, {'synthetic': policy}, assembler, publisher, executor, NoCompiler())
    CurationJobs(stored.engine).release(principal, lease)
    return principal, lease.curation_id, intake, worker, provider, peer, data


def test_two_bounded_turns_prepare_then_observe_and_terminal_discovery_stops(stored):
    principal, identity, intake, worker, provider, peer, data = setup(stored)
    discovery = CurationDiscovery(stored.engine, ['synthetic'])
    assert discovery.next(principal) == identity
    first = worker.tick(principal, identity, 'worker')
    assert first.status == 'advanced' and first.phase == 'awaiting_provider' and provider.calls == 0
    worker.policies = {}  # Replacement needs retained original declaration, not mutable configuration.
    second = worker.tick(principal, identity, 'replacement')
    assert second.status == 'terminal' and second.phase == 'abstained' and provider.calls == 1
    assert discovery.next(principal) is None
    assert worker.tick(principal, identity, 'replacement').status == 'busy'
    assert provider.calls == 1 and len(peer.uploads) == 1
    assert intake.read(principal, identity).proposal.outcome.kind == 'abstain'


def test_missing_provider_keeps_original_preparation_without_reserving(stored):
    principal, identity, _, worker, provider, _, _ = setup(stored)
    worker.tick(principal, identity, 'worker')
    worker.executor.provider = None
    paused = worker.tick(principal, identity, 'worker')
    assert paused.status == 'pending' and paused.reason == 'curation_provider_unconfigured'
    assert provider.calls == 0
    worker.executor.provider = provider
    assert worker.tick(principal, identity, 'worker').phase == 'abstained' and provider.calls == 1


def test_processing_denial_after_preparation_pauses_without_new_model_call(stored):
    principal, identity, _, worker, provider, _, data = setup(stored)
    worker.tick(principal, identity, 'worker')
    data.denied = next(iter(worker.policies.values())).document().template.context.objective.artifact_id
    paused = worker.tick(principal, identity, 'worker')
    assert paused.phase == 'awaiting_provider' and paused.reason == 'curation_processing_unavailable'
    assert provider.calls == 0
    data.denied = None
    assert worker.tick(principal, identity, 'replacement').phase == 'abstained' and provider.calls == 1


def test_lost_derived_upload_resumes_original_declaration_without_new_policy(stored):
    principal, identity, _, worker, provider, peer, data = setup(stored)
    peer.lost_put = True
    paused = worker.tick(principal, identity, 'worker')
    assert paused.status == 'pending' and paused.reason == 'peer_unavailable' and provider.calls == 0
    peer.lost_put = False
    data.bodies['output-2'] = peer.artifact.body
    worker.policies = {}
    ready = worker.tick(principal, identity, 'replacement')
    assert ready.phase == 'awaiting_provider' and len(peer.uploads) == 2 and provider.calls == 0
    assert worker.tick(principal, identity, 'replacement').phase == 'abstained' and provider.calls == 1


def test_required_source_denial_stops_before_provider(stored):
    principal, identity, intake, worker, provider, _, data = setup(stored)
    data.denied = next(iter(worker.policies.values())).document().template.context.objective.artifact_id
    result = worker.tick(principal, identity, 'worker')
    assert result.phase == 'failed' and result.reason == 'curation_preparation_not_ready'
    assert provider.calls == 0 and intake.read(principal, identity).provider is None


@pytest.mark.parametrize('code,expected', [
    ('curation_predecessor_active', 'failed'), ('metadata_denied', 'failed'),
    ('metadata_unavailable', 'assembling'), ('metadata_deadline', 'assembling'),
])
def test_original_context_failures_are_bounded_per_job(stored, monkeypatch, code, expected):
    principal, identity, _, worker, provider, peer, _ = setup(stored)
    def unavailable(intent): raise ValueError(code)
    monkeypatch.setattr(worker.assembler.originals, 'read', unavailable)
    result = worker.tick(principal, identity, 'worker')
    assert result.phase == expected and result.reason == code
    assert provider.calls == 0 and len(peer.uploads) == 0


def test_unexpected_integrity_error_is_not_converted_to_a_retry(stored, monkeypatch):
    principal, identity, _, worker, provider, _, _ = setup(stored)
    def corrupt(intent): raise ValueError('curation_runtime_draft_binding')
    monkeypatch.setattr(worker.assembler.originals, 'read', corrupt)
    with pytest.raises(ValueError, match='curation_runtime_draft_binding'):
        worker.tick(principal, identity, 'worker')
    assert provider.calls == 0
    assert CurationJobs(stored.engine).claim(principal, identity, 'replacement') is not None


def test_managed_compiler_keeps_original_graph_and_reaches_ready(stored):
    from ..curation_compiler.test_workflow import setup as proposed, workflow
    principal, lease, journal, provider, graph = proposed(stored)
    compiler, lease, runtime, _, _ = workflow(stored, principal, lease, journal)
    worker = CurationWorker(stored.engine, {}, None, None, None, compiler)
    CurationJobs(stored.engine).release(principal, lease)
    first = worker.tick(principal, lease.curation_id, 'managed')
    assert first.phase == 'compiling'
    final = worker.tick(principal, lease.curation_id, 'replacement')
    assert final.phase == 'ready' and final.status == 'terminal'
    assert len(runtime.sent) == 2 and provider.calls == 1
    assert json.loads(runtime.sent[0])['payload']['definition'] == graph


@pytest.mark.parametrize('fault,code', [('revision', 'decision_future_identity'),
    ('duplicate_node', 'campaign_authored_duplicate_node')])
def test_policy_rejected_proposal_fails_without_compiler_selection(stored, fault, code):
    from types import SimpleNamespace
    from ..curation_compiler.test_workflow import setup as proposed
    from amphora_agent_planning.curation_compiler.workflow import CurationCompiler
    from amphora_agent_planning.campaign_dispatch.selection import CompilerSelection
    def duplicate(graph): graph['body']['nodes'].append(graph['body']['nodes'][0].copy())
    principal, lease, journal, provider, _ = proposed(stored, invalid_policy=fault == 'revision',
        mutate=duplicate if fault == 'duplicate_node' else None)
    compiler = CurationCompiler(journal, SimpleNamespace(journal=journal.compiler))
    worker = CurationWorker(stored.engine, {}, None, None, None, compiler)
    CurationJobs(stored.engine).release(principal, lease)
    result = worker.tick(principal, lease.curation_id, 'managed')
    assert result.phase == 'failed' and result.reason == code
    current = journal.current(principal, lease.curation_id)
    assert current.view.proposal == lease.progress.view.proposal and provider.calls == 1
    identifier = CompilerSelection.identity_for(principal.actor_id, current.view.provider.attempt)
    assert journal.store.read(principal, identifier) is None
