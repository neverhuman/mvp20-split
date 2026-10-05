"""Process-loss and replacement replay of exact campaign and predecessor outputs."""

import argparse
import hashlib
import json
import os
from pathlib import Path

from amphora_agent_planning.access import Principal
from amphora_agent_planning.budget import BudgetPolicy
from amphora_agent_planning.context import AttemptBinding, RequestSnapshot
from amphora_agent_planning.orchestration import PlanningRunner
from amphora_agent_planning.providers.port import ProviderReply
from amphora_contracts_core import Scope
from amphora_contracts_planning import ProviderUsage
from sqlalchemy import create_engine


class Provider:
    def __init__(self, raw, allowed):
        self.raw, self.allowed, self.calls = raw, allowed, 0

    def supports(self, model):
        return True

    def reply(self, binding):
        assert self.allowed, 'Replay must never call the provider'
        self.calls += 1
        return ProviderReply([self.raw], ProviderUsage(input_tokens=None, output_tokens=None,
                                                     accounting_units=None, certainty='unknown'))


def run(args):
    values = json.loads(args.fixture.read_bytes())
    engine = create_engine(os.environ['AMPHORA_TEST_PLANNING_SERVICE_URL'])
    evidence = []
    try:
        for case in values:
            original = case['request']
            scope = Scope.model_validate(original['reference']['scope'])
            principal = Principal(original['actor_id'], scope,
                                  frozenset({'record_requests', 'record_attempts', 'read_attempts'}))
            request = RequestSnapshot.from_bytes(json.dumps(original).encode(), actor_id=principal.actor_id, scope=scope)
            binding = AttemptBinding(request, 1)
            provider = Provider(case['capture_utf8'].encode(), args.stage == 'commit-crash')
            runner = PlanningRunner(engine, provider, timeout_seconds=30)
            context = request.document().context.model_dump(mode='json')
            policy = {key: context[key] for key in ('model', 'prompt', 'policy', 'output_schema', 'allowed_actions', 'limits')}
            policy.update(format='planning-budget-policy.v1', per_attempt_accounting_units=40)
            reviewed = BudgetPolicy.from_bytes(json.dumps(policy).encode())
            if args.stage == 'absent':
                assert runner.journal.read_request(principal, request.document().reference) is None
                continue
            if args.stage in {'commit-crash', 'replay'}:
                outcome = runner.run(principal, request, reviewed)
                assert outcome.stop_reason == case['status']
                stored = outcome.latest
            else:
                stored = runner.journal.read_attempt(principal, binding.reference())
            assert stored is not None and stored.binding.request == request
            observed = stored.observation
            assert observed.capture.content == case['capture_utf8'].encode()
            assert observed.document().status == case['status']
            settlement = runner.settlements.read(principal, binding.reference())
            assert settlement.charge.accounting_units == 40
            assert settlement.charge.tokens == context['limits']['max_input_tokens'] + context['limits']['max_output_tokens']
            assert provider.calls == (1 if args.stage == 'commit-crash' else 0)
            evidence.append({'name': case['name'], 'request_sha256': request.sha256,
                'capture_sha256': observed.capture.sha256,
                'observation_sha256': hashlib.sha256(observed.canonical).hexdigest(),
                'proposal_sha256': hashlib.sha256(observed.document().proposal.model_dump_json().encode()).hexdigest(),
                'settled_at': settlement.registered_at.isoformat(), 'tokens': settlement.charge.tokens,
                'units': settlement.charge.accounting_units})
        if args.stage == 'commit-crash':
            # Every journal/settlement transaction committed; discard process and acknowledgement.
            os._exit(91)
        if args.stage == 'recover':
            assert not args.expected.exists()
            args.expected.write_text(json.dumps(evidence, indent=2) + '\n', encoding='utf-8')
        elif args.stage != 'absent':
            assert evidence == json.loads(args.expected.read_bytes())
        print(json.dumps({'stage': args.stage, 'cases': len(values), 'status': 'passed'}))
    finally:
        engine.dispose()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=['absent', 'commit-crash', 'recover', 'read', 'replay'])
    parser.add_argument('--fixture', type=Path, required=True)
    parser.add_argument('--expected', type=Path, required=True)
    run(parser.parse_args())
