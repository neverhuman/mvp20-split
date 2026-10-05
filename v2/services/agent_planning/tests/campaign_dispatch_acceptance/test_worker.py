"""Installed public-owner compilation and test-controlled abrupt worker boundaries."""

import json
import os
import time
from pathlib import Path

import pytest
from amphora_agent_planning.campaign_authoring import AuthoringPlan
from amphora_agent_planning.campaign_dispatch import CompilerSelection
from amphora_agent_planning.campaign_dispatch.progression import CompilerProgression
from amphora_agent_planning.campaign_exchanges import CompilerWindow, ExchangeAbsent
from amphora_agent_planning.campaign_packet import prepare
from amphora_agent_planning.campaign_preparations.journal import (
    CampaignPreparationJournal,
)
from amphora_agent_planning.persistence.budget import BudgetLedger
from amphora_agent_planning.persistence.journal import PlanningJournal
from amphora_agent_planning.persistence.settlement import SettlementJournal
from sqlalchemy import create_engine

from .original import original
from .support import components

pytestmark = pytest.mark.skipif('DISPATCH_CASE' not in os.environ, reason='Installed owner/crash fixture opt-in')


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


def test_installed_worker(monkeypatch):
    case = json.loads(Path(os.environ['DISPATCH_CASE']).read_bytes())
    engine = create_engine(os.environ['DISPATCH_DB'], connect_args={'options': '-c statement_timeout=5000'})
    try:
        principal, store, journal, dispatcher, registry, runtime = components(case, engine, denied=case.get('denied', False))
        if case['stage'] == 'seed':
            review, budget, selected = original(case, os.environ['DISPATCH_DATA'], os.environ['CTX_TOKEN'], registry, runtime)
            proposal = review.composition.evidence.proposal
            attempts = PlanningJournal(engine)
            attempts.register(principal, proposal.attempt.request)
            CampaignPreparationJournal(engine).register(principal, selected, prepare(selected).packet)
            BudgetLedger(engine).reserve(principal, proposal.attempt, budget)
            attempts.record(principal, proposal.attempt, proposal.observation)
            SettlementJournal(engine).settle(principal, proposal.attempt)
            authoring = AuthoringPlan.bind(review, budget, owner_id='fixture-runtime', actor_id='fixture')
            selection = CompilerSelection.bind(principal, authoring, store.eligibility)
            retained = store.register(principal, selection)
            write(os.environ['DISPATCH_RESULT'], {'selection_id': retained.selection.effect_id,
                'selection_sha256': retained.selection.sha256, 'request_sha256': proposal.attempt.request.sha256,
                'declaration_sha256': review.declaration.sha256})
            return
        selected = journal.selected(principal, case['selection_id'])
        assert selected is not None and selected.selection.sha256 == case['selection_sha256']
        if case['stage'] == 'assert-absent':
            authoring = journal.context(principal, selected.selection).history.authoring
            with pytest.raises(ExchangeAbsent):
                dispatcher.runtime.receipt(authoring.save(), CompilerWindow('runtime'))
            write(os.environ['DISPATCH_RESULT'], {'state': 'absent'})
            return
        if case['stage'] in {'peer-history', 'saved-history'}:
            operations = journal.context(principal, selected.selection)
            authoring = operations.history.authoring
            runtime_client = dispatcher.runtime
            saved = runtime_client.readback(runtime_client.receipt(authoring.save(), CompilerWindow('runtime')),
                                            CompilerWindow('runtime'))
            if case['stage'] == 'saved-history':
                effect, _ = operations.save()
                stored = journal.read(principal, selected.selection.effect_id, effect.effect_id)
                assert stored.progress.observation.outcome == saved
                write(os.environ['DISPATCH_RESULT'], {'state': 'saved_history_exact'})
                return
            compiled = runtime_client.readback(runtime_client.receipt(authoring.validate(saved), CompilerWindow('runtime')),
                                               CompilerWindow('runtime'))
            for outcome, expected in ((saved, case['saved_observation']), (compiled, case['compiled_observation'])):
                assert outcome.receipt.model_dump(mode='json') == expected['receipt']
                assert outcome.readback.model_dump(mode='json') == expected['readback']
            write(os.environ['DISPATCH_RESULT'], {'state': 'peer_history_exact'})
            return
        if case['stage'].startswith('crash-'):
            acquire = store.acquire
            def short_lease(actor, identity, seconds=300):
                # Existing public lease option, test-only; production remains300s.
                return acquire(actor, identity, seconds=20)
            monkeypatch.setattr(store, 'acquire', short_lease)
            append = journal.append
            def boundary(actor, lease, effect_id, position, event):
                action = json.loads(event.canonical)['action']
                operation = journal.read(actor, lease.selection.effect_id, effect_id)
                crash = operation.effect.document().kind == 'save'
                if action == 'observed' and crash and case['stage'] == 'crash-after-commit':
                    hold(lease, effect_id)
                result = append(actor, lease, effect_id, position, event)
                if action == 'dispatch' and crash and case['stage'] == 'crash-before-post':
                    hold(lease, effect_id)
                return result
            def hold(lease, effect_id):
                write(os.environ['DISPATCH_MARKER'], {'pid': os.getpid(), 'parent_pid': os.getppid(), 'effect_id': effect_id,
                    'fence': lease.fence, 'expires_at': lease.expires_at.isoformat(), 'stage': case['stage']})
                time.sleep(45)
                raise AssertionError('Owned harness must terminate worker at marker')
            monkeypatch.setattr(journal, 'append', boundary)
        result = CompilerProgression(dispatcher).advance(principal, case['selection_id'])
        operation = None if result.dispatch is None else result.dispatch.operation
        write(os.environ['DISPATCH_RESULT'], {'stage': result.stage, 'terminal': result.terminal,
            'pause_reason': result.pause_reason, 'state': None if operation is None else operation.progress.state,
            'effect_id': None if operation is None else operation.effect.effect_id,
            'dispatches': None if operation is None else operation.progress.dispatches,
            'command_sha256': None if operation is None else operation.effect.command().sha256,
            'observation': None if operation is None or operation.progress.observation is None else
                json.loads(operation.progress.observation.canonical),
            'round': None if result.round is None else result.round.check_id})
    finally:
        engine.dispose()
