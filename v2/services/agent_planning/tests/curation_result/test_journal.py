import json
import hashlib
from dataclasses import replace
from uuid import uuid4

import pytest
from amphora_agent_planning.access import Principal
from amphora_agent_planning.context import RequestSnapshot
from amphora_agent_planning.curation_context import CurationIntent
from amphora_agent_planning.curation_intake.commands import CurationCommand
from amphora_agent_planning.curation_intake.journal import CurationJournal
from amphora_agent_planning.curation_jobs.journal import CurationJobs
from amphora_agent_planning.curation_preparation.link import CurationPreparationJournal
from amphora_agent_planning.curation_runtime import CurationRuntimeReader
from amphora_agent_planning.curation_runtime.context import draft_digest
from amphora_agent_planning.curation_result.journal import CurationResultJournal
from amphora_agent_planning.orchestration import PlanningRunner
from ..curation_preparation.test_assembly import assembly
from ..curation_openai.test_adapter import source as provider_source
from ..curation_runtime.test_context import case, Peer
from ..curation_jobs.test_journal import expire
from ..persistence.test_reservations import policy
from ..providers.test_task_output import Response

pytestmark = pytest.mark.postgres


def setup(stored):
    assembler, original, *_ = assembly()
    _, _, draft, run = case()
    scope = stored.principal.scope
    def scoped(value):
        if isinstance(value, dict):
            if set(value) == {'tenant_id', 'project_id'}: value.update(scope.model_dump())
            for child in value.values(): scoped(child)
        elif isinstance(value, list):
            for child in value: scoped(child)
        return value
    draft = type(draft).model_validate_json(json.dumps(scoped(draft.model_dump(mode='json'))))
    draft = draft.model_copy(update={'head': draft.head.model_copy(update={'content_sha256': draft_digest(draft)})})
    run = type(run).model_validate_json(json.dumps(scoped(run.model_dump(mode='json'))))
    raw = scoped(json.loads(original.canonical)['command'])
    raw['identity']['command_id'] = uuid4().hex
    raw['payload']['context']['draft']['content_sha256'] = draft.head.content_sha256
    incoming = CurationCommand.restore(json.dumps(raw))
    request_value = scoped(original.request.document().model_dump(mode='json'))
    request_value['context']['limits'] = provider_source().request.document().context.limits.model_dump(mode='json')
    request = RequestSnapshot.from_bytes(json.dumps(request_value).encode(),
        actor_id=incoming.command.identity.actor_id, scope=scope)
    intent = CurationIntent.from_template(request, incoming, 'synthetic')
    assembler.originals = CurationRuntimeReader(Peer(draft, run))
    for reader in (assembler.registry, assembler.runtime):
        peer = reader.transport
        peer.responses = [type(value).model_validate_json(json.dumps(scoped(value.model_dump(mode='json')))) for value in peer.responses]
    universe = assembler.runtime.transport.responses[0]
    def canonical(value): return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()
    profile = {'profile': 'amphora-authoring-universe-v1', 'compiler': 'amphora-deterministic-compiler-v3',
        'scope': scope.model_dump(mode='json'), 'tools': sorted((row.model_dump(mode='json') for row in universe.reviewed_tools), key=canonical),
        'schemas': sorted((row.model_dump(mode='json') for row in universe.schemas), key=canonical)}
    assembler.runtime.transport.responses[0] = universe.model_copy(update={'universe_sha256': hashlib.sha256(canonical(profile)).hexdigest()})
    principal = Principal(incoming.command.identity.actor_id, scope, frozenset({
        'execute_curations', 'record_curations', 'read_curations', 'record_requests', 'record_attempts', 'read_attempts'}))
    intake = CurationJournal(stored.engine, {'synthetic'})
    intake.receive(principal, incoming.command.canonical_bytes)
    jobs = CurationJobs(stored.engine)
    lease = jobs.claim(principal, incoming.curation_id, 'worker', lease_seconds=60)
    linked = CurationPreparationJournal(stored.engine).freeze(principal, lease, assembler.read(intent))
    return principal, replace(lease, progress=linked.progress), linked, intake, draft


def output(linked, draft, kind):
    outcome = {'kind': 'abstain', 'reason_code': 'insufficient_evidence'}
    if kind == 'propose_campaign':
        outcome = {'kind': kind, 'candidate': {'kind': 'future_campaign', 'title': 'Future', 'definition': draft.definition.model_dump(mode='json'), 'expected_evidence': []}, 'gaps': []}
    if kind == 'request_capabilities':
        outcome = {'kind': kind, 'gaps': [{'gap_key': 'heat', 'purpose': 'Heat mixture', 'inputs': [], 'outputs': [{'name': 'mixture', 'representation': 'mixture', 'schema_ref': None, 'description': 'Changed material', 'unit': None}],
            'applicability': ['synthetic'], 'evidence_need': 'Thermal history',
            'acceptance_criteria': ['Retain input identity'], 'graph_gap': 'After mixing'}]}
    return json.dumps({'schema_version': '1', 'profile': 'planning.campaign-curation-draft.v1',
        'authority': 'proposal_only', 'scientific_authority': 'not_established',
        'decision_scope': linked.frozen.preparation.packet.request.document().decision_scope,
        'rationale': 'Future iteration', 'outcome': outcome, 'unresolved': []}).encode()


@pytest.mark.parametrize('kind,phase', [('abstain','abstained'), ('request_capabilities','proposed'),
                                       ('propose_campaign','proposed'), ('invalid','failed')])
def test_original_outcome_accounting_and_replacement_readback(stored, kind, phase):
    principal, lease, linked, intake, draft = setup(stored)
    request = linked.frozen.preparation.packet.request
    provider = Response(b'invalid' if kind == 'invalid' else output(linked, draft, kind))
    runner = PlanningRunner(stored.engine, provider, timeout_seconds=30)
    runner.run(principal, request, policy(request, units=250000000))
    journal = CurationResultJournal(stored.engine)
    result = journal.record(principal, lease)
    assert result.view.receipt.phase == phase and result.view.receipt.revision == 3
    assert result.view.provider.envelope_sha256 == linked.frozen.envelope.sha256
    if kind != 'invalid': assert result.view.proposal.outcome.kind == kind
    assert CurationResultJournal(stored.engine).record(principal, lease) == result
    assert intake.read(principal, lease.curation_id).receipt == result.view.receipt
    assert provider.calls == 1


def test_pending_and_expired_worker_cannot_advance(stored):
    principal, lease, linked, intake, draft = setup(stored)
    journal = CurationResultJournal(stored.engine)
    with pytest.raises(ValueError, match='curation_result_pending'): journal.record(principal, lease)
    request = linked.frozen.preparation.packet.request
    PlanningRunner(stored.engine, Response(output(linked, draft, 'abstain')), timeout_seconds=30).run(
        principal, request, policy(request, units=250000000))
    expire(stored, principal, lease.curation_id)
    with pytest.raises(ValueError, match='curation_lease_lost'): journal.record(principal, lease)
    assert intake.read(principal, lease.curation_id).receipt.phase == 'awaiting_provider'
    replacement = CurationJobs(stored.engine).claim(principal, lease.curation_id, 'replacement', lease_seconds=60)
    assert journal.record(principal, replacement).view.receipt.phase == 'abstained'


@pytest.mark.parametrize('fault,phase', [('unknown','indeterminate'), ('overage','failed')])
def test_uncertain_or_over_budget_results_never_become_compiler_ready(stored, fault, phase):
    from amphora_contracts_planning import ProviderUsage
    from amphora_agent_planning.providers.port import ProviderReply
    principal, lease, linked, _, draft = setup(stored)
    request = linked.frozen.preparation.packet.request
    class Provider(Response):
        def reply(self, binding):
            self.calls += 1
            if fault == 'unknown': raise RuntimeError('private diagnostic')
            return ProviderReply([self.raw], ProviderUsage(input_tokens=10, output_tokens=10,
                accounting_units=250000001, certainty='reported'))
    provider = Provider(output(linked, draft, 'propose_campaign'))
    PlanningRunner(stored.engine, provider, timeout_seconds=30).run(principal, request, policy(request, units=250000000))
    result = CurationResultJournal(stored.engine).record(principal, lease)
    assert result.view.receipt.phase == phase and result.view.validated_draft is None
    assert result.view.receipt.reason_code == ('provider_outcome_unknown' if fault == 'unknown' else 'provider_usage_overage')
    assert 'private diagnostic' not in result.view.model_dump_json() and provider.calls == 1


def test_unsettled_observation_waits_for_original_accounting(stored, monkeypatch):
    from amphora_agent_planning.context import AttemptBinding
    from amphora_agent_planning.persistence.settlement import SettlementJournal
    principal, lease, linked, intake, draft = setup(stored)
    request = linked.frozen.preparation.packet.request
    runner = PlanningRunner(stored.engine, Response(output(linked, draft, 'abstain')), timeout_seconds=30)
    def crash(*args): raise RuntimeError('after observation')
    monkeypatch.setattr(runner.settlements, 'settle', crash)
    with pytest.raises(RuntimeError): runner.run(principal, request, policy(request, units=250000000))
    journal = CurationResultJournal(stored.engine)
    with pytest.raises(ValueError, match='curation_result_settlement'): journal.record(principal, lease)
    assert intake.read(principal, lease.curation_id).receipt.phase == 'awaiting_provider'
    SettlementJournal(stored.engine).settle(principal, AttemptBinding(request, 1))
    append = journal.jobs._append
    def rollback(*args):
        append(*args)
        raise RuntimeError('before commit')
    monkeypatch.setattr(journal.jobs, '_append', rollback)
    with pytest.raises(RuntimeError): journal.record(principal, lease)
    assert intake.read(principal, lease.curation_id).receipt.phase == 'awaiting_provider'
    assert CurationResultJournal(stored.engine).record(principal, lease).view.receipt.phase == 'abstained'
