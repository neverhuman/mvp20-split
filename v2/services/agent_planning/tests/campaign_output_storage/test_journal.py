"""Real Planning SQL journals keep campaign outputs immutable and replayable."""

import json
import time

import pytest
from amphora_agent_planning.context import AttemptBinding, RequestSnapshot
from amphora_agent_planning.orchestration import PlanningRunner
from amphora_agent_planning.providers import observe

from ..campaign_output.test_checkpoint import checkpoint_output, checkpoint_request
from ..campaign_output.test_output import output, request
from ..persistence.test_reservations import policy
from ..persistence.test_task_output import Response

pytestmark = pytest.mark.postgres


def fixture(stored, name='future'):
    raw = (checkpoint_request() if name == 'checkpoint' else request(name)).document().model_dump(mode='json')
    draft = checkpoint_output() if name == 'checkpoint' else output(name)

    def rescope(value):
        if isinstance(value, dict):
            if set(value) == {'tenant_id', 'project_id'}:
                value.update(stored.principal.scope.model_dump())
            for child in value.values():
                rescope(child)
        elif isinstance(value, list):
            for child in value:
                rescope(child)

    rescope(raw)
    rescope(draft)
    snapshot = RequestSnapshot.from_bytes(json.dumps(raw).encode(), actor_id=stored.principal.actor_id,
                                         scope=stored.principal.scope)
    return snapshot, json.dumps(draft, indent=2).encode()


@pytest.mark.parametrize('name', ['future', 'adjustment', 'evidence', 'abstain', 'checkpoint'])
def test_durable_campaign_output_replay_never_calls_provider_twice(stored, name):
    snapshot, raw = fixture(stored, name)
    provider = Response(raw)
    runner = PlanningRunner(stored.engine, provider, timeout_seconds=30)
    result = runner.run(stored.principal, snapshot, policy(snapshot))
    assert result.stop_reason == ('abstained' if name == 'abstain' else 'proposed')
    observed = result.latest.observation
    assert observed.document().schema_version == '2'
    assert observed.capture.content == raw
    assert runner.run(stored.principal, snapshot, policy(snapshot)) == result
    assert provider.calls == 1
    # A new runner reconstructs exact retained bytes and conservative usage.
    replacement = PlanningRunner(stored.engine, Response(b'forbidden second call'), timeout_seconds=30)
    assert replacement.run(stored.principal, snapshot, policy(snapshot)) == result
    assert replacement.provider.calls == 0
    charge = runner.settlements.read(stored.principal, result.latest.binding.reference()).charge
    limits = snapshot.document().context.limits
    assert charge.tokens == limits.max_input_tokens + limits.max_output_tokens


def test_late_campaign_proposal_cannot_replace_recorded_unknown(stored):
    snapshot, raw = fixture(stored)
    binding = AttemptBinding(snapshot, 1)
    runner = PlanningRunner(stored.engine, Response(raw), timeout_seconds=1)
    runner.journal.register(stored.principal, snapshot)
    runner.ledger.reserve(stored.principal, binding, policy(snapshot))
    ticket = runner.dispatch.issue(stored.principal, binding, 1)
    time.sleep(1.05)
    recovered = runner.dispatch.recover(stored.principal, binding)
    assert recovered.observation.document().schema_version == '2'
    assert recovered.observation.document().status == 'unknown'
    settled = runner.settlements.settle(stored.principal, binding)
    late = observe(binding, Response(raw))
    assert late.document().status == 'proposed'
    assert runner.dispatch.complete(stored.principal, binding, ticket, late) == recovered
    assert runner.dispatch.read_late(stored.principal, binding) == late
    assert runner.settlements.read(stored.principal, binding.reference()) == settled


def test_rejected_scope_is_retained_and_does_not_claim_a_proposal(stored):
    snapshot, raw = fixture(stored)
    value = json.loads(raw)
    value['candidate']['definition']['scope']['project_id'] = 'foreign'
    runner = PlanningRunner(stored.engine, Response(json.dumps(value).encode()), timeout_seconds=30)
    result = runner.run(stored.principal, snapshot, policy(snapshot))
    assert result.stop_reason == 'policy_rejected'
    assert result.latest.observation.document().proposal is None
    assert runner.journal.read_attempt(stored.principal, result.latest.binding.reference()) == result.latest
