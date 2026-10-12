import json
from dataclasses import replace
from concurrent.futures import ThreadPoolExecutor
from threading import Event

import pytest
from amphora_agent_planning.curation_execution.executor import CurationExecutor
from amphora_agent_planning.curation_declaration.journal import DeclarationJournal
from amphora_agent_planning.curation_declaration.origin import DeclarationOrigin
from amphora_agent_planning.curation_declaration.workflow import DeclarationPublisher
from amphora_agent_planning.curation_policy import CurationPolicy
from amphora_agent_planning.curation_runtime import CurationRuntimeContext
from amphora_agent_planning.curation_intake.commands import CurationCommand
from amphora_agent_planning.curation_jobs.journal import CurationJobs
from amphora_agent_planning.curation_result.journal import CurationResultJournal
from amphora_tool_protocol import ArtifactClient, WorkerIdentity
from ..curation_policy.test_policy import config
from ..curation_result.test_journal import setup as inputs, output
from ..curation_jobs.test_journal import expire
from ..publication.test_workflow import DataPeer
from ..providers.test_task_output import Response

pytestmark = pytest.mark.postgres


class Provider(Response):
    def validate_policy(self, policy):
        from amphora_agent_planning.curation_budget import CurationAllowance
        CurationAllowance.validate_policy(policy)

    def reply(self, binding, packet, *, deadline_unix_ms):
        assert deadline_unix_ms > 0 and json.loads(packet)['format']
        self.packet, self.deadline = packet, deadline_unix_ms
        return super().reply(binding)


def setup(stored):
    selected = {}
    def before(assembler, intent, draft, run, principal, lease):
        raw = config(); raw['template'] = intent.request.document().model_dump(mode='json')
        policy = CurationPolicy.from_bytes(json.dumps(raw).encode())
        incoming = CurationCommand.restore(json.dumps(json.loads(intent.canonical)['command']))
        original = CurationRuntimeContext.bind(policy.seed(incoming), draft, run)
        origin = DeclarationOrigin.bind(policy, original)
        peer = DataPeer(origin, origin.artifact())
        client = ArtifactClient(peer, WorkerIdentity(principal.actor_id, principal.scope))
        state = DeclarationPublisher(DeclarationJournal(stored.engine), client).publish(
            principal, lease, policy=policy, original=original)
        data = assembler.artifacts.reader.data
        data.bodies[state.attempt.result.artifact.artifact_id] = origin.artifact().body
        selected['data'] = data
        return origin.reviewed().with_artifact(state.attempt.result.artifact)
    principal, lease, linked, intake, draft = inputs(stored, before)
    provider = Provider(output(linked, draft, 'abstain'))
    executor = CurationExecutor(stored.engine, selected['data'], provider)
    return principal, lease, linked, executor, provider, selected['data']


def test_exact_once_and_replacement_ignores_changed_configuration_and_denied_data(stored):
    principal, lease, linked, executor, provider, data = setup(stored)
    result = executor.execute(principal, lease)
    assert result.observation.document().status == 'abstained' and provider.calls == 1
    assert provider.packet == linked.frozen.preparation.packet.canonical
    calls = list(data.calls)
    replacement = CurationExecutor(stored.engine, None, None)
    assert replacement.execute(principal, lease) == result and data.calls == calls
    assert CurationResultJournal(stored.engine).record(principal, lease).view.receipt.phase == 'abstained'


def test_denial_before_reservation_makes_no_call_or_hold(stored):
    principal, lease, linked, executor, provider, data = setup(stored)
    data.denied = linked.frozen.preparation.packet.request.document().context.objective.artifact_id
    with pytest.raises(ValueError, match='curation_processing_unavailable'): executor.execute(principal, lease)
    from amphora_agent_planning.context import AttemptBinding
    ref = AttemptBinding(linked.frozen.preparation.packet.request, 1).reference()
    assert executor.budgets.read(principal, ref) is None and provider.calls == 0


def test_expired_job_cannot_reserve_or_issue(stored):
    principal, lease, _, executor, provider, _ = setup(stored)
    expire(stored, principal, lease.curation_id)
    with pytest.raises(ValueError, match='curation_lease_lost'): executor.execute(principal, lease)
    assert provider.calls == 0


def test_concurrent_replacement_waits_for_original_physical_call(stored):
    principal, lease, linked, executor, provider, _ = setup(stored)
    entered, release = Event(), Event()
    reply = provider.reply
    def blocked(*args, **kwargs):
        entered.set()
        assert release.wait(20)
        return reply(*args, **kwargs)
    provider.reply = blocked
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(executor.execute, principal, lease)
        try:
            assert entered.wait(20)
            expire(stored, principal, lease.curation_id)
            replacement = CurationJobs(stored.engine).claim(principal, lease.curation_id, 'replacement', lease_seconds=60)
            pending = CurationExecutor(stored.engine, None, None).execute(principal, replacement)
            assert pending.observation is None
        finally:
            release.set()
        first = future.result(timeout=20)
    assert first.observation.document().status == 'abstained' and provider.calls == 1
    assert CurationResultJournal(stored.engine).record(principal, replacement).view.receipt.phase == 'abstained'


def test_process_death_after_issuance_recovers_unknown_without_second_call(stored):
    import time
    principal, lease, linked, executor, provider, data = setup(stored)
    executor.timeout = 1
    def die(*args, **kwargs):
        provider.calls += 1
        raise SystemExit('owned crash probe')
    provider.reply = die
    with pytest.raises(SystemExit): executor.execute(principal, lease)
    time.sleep(1.1)
    result = CurationExecutor(stored.engine, None, None).execute(principal, lease)
    assert result.observation.document().status == 'unknown' and provider.calls == 1
    assert CurationResultJournal(stored.engine).record(principal, lease).view.receipt.phase == 'indeterminate'


@pytest.mark.parametrize('failing_guard,held', [(3,False), (5,True)])
def test_final_transaction_fence_rolls_back_new_reservation_or_issuance(stored, monkeypatch, failing_guard, held):
    from amphora_agent_planning.context import AttemptBinding
    principal, lease, linked, executor, provider, _ = setup(stored)
    original = executor._guard
    calls = []
    def fail(principal, lease, conn):
        calls.append(1)
        original(principal, lease, conn)
        if len(calls) == failing_guard: raise ValueError('injected_final_fence')
    monkeypatch.setattr(executor, '_guard', fail)
    with pytest.raises(ValueError, match='injected_final_fence'): executor.execute(principal, lease)
    ref = AttemptBinding(linked.frozen.preparation.packet.request, 1).reference()
    assert (executor.budgets.read(principal, ref) is not None) == held
    key = {**executor.attempts._key(ref.engagement), 'ordinal': 1}
    with stored.engine.connect() as conn: assert executor.dispatch._issued(conn, key) is None
    assert provider.calls == 0


def test_revocation_after_issuance_records_unknown_without_sending(stored, monkeypatch):
    principal, lease, linked, executor, provider, data = setup(stored)
    original = executor.dispatch.issue
    def revoke(*args, **kwargs):
        result = original(*args, **kwargs)
        data.denied = linked.frozen.preparation.packet.request.document().context.objective.artifact_id
        return result
    monkeypatch.setattr(executor.dispatch, 'issue', revoke)
    result = executor.execute(principal, lease)
    assert result.observation.document().status == 'unknown' and provider.calls == 0
    assert CurationExecutor(stored.engine, None, None).execute(principal, lease) == result
