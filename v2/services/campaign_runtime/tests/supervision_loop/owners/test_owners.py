"""Current actual Data/Runtime/Planning exchange; separate installed proof remains V1."""

import json
import os

import pytest
from amphora_campaign_runtime.supervision_journal.storage import RequestJournal
from amphora_campaign_runtime.supervision_outcomes.reports import ReportJournal
from amphora_campaign_runtime.supervision_winners import WinnerStore
from amphora_contracts_supervision import SupervisionRef
from sqlalchemy import text

from ...supervision_checkpoints.test_coordinator import slots
from .processes import Owners

pytestmark = [pytest.mark.owner_processes, pytest.mark.skipif(
    os.environ.get('AMPHORA_TEST_OWNER_PROCESSES') != '1', reason='Explicit current-owner process opt-in required')]


@pytest.mark.parametrize('variant,requests,kind', [('fixture_abstain', 1, 'model_accepted'),
                                                ('fixture_invalid', 2, 'fallback')])
def test_autonomous_checkpoint_actual_owner_loop(graph_env, tmp_path, variant, requests, kind):
    owners = Owners(graph_env, tmp_path, variant)
    try:
        page = None
        for _ in range(14):
            page = owners.round()
            if page['status'] != 'running':
                break
        assert page['status'] == 'completed', 'Bounded autonomous owner rounds did not complete; inspect worker logs'
        actor = graph_env.env.principal
        slot = slots(graph_env, owners.run, owners.policy)[0]
        reference = SupervisionRef(scope=actor.scope, run_id=owners.run, decision_id=slot.seed.decision_id)
        winner = WinnerStore(graph_env.env.engine).read(actor, reference)
        assert winner.document().outcome.kind == kind
        if kind == 'model_accepted':
            assert winner.document().outcome.effect.kind == 'abstained'
        else:
            assert winner.document().outcome.reason_code == 'checkpoint_request_allowance_exhausted'
        journal = RequestJournal(graph_env.env.engine, {})
        history = journal.series(actor, owners.run, reference.decision_id)
        assert len(history) == requests
        reports = ReportJournal(journal)
        for item in history:
            report = reports.read(actor, reference, item.frame.request_sha256).report.document()
            assert len(report.attempts) == 1
            remote = owners.planning.call('GET', '/v2/supervision/execution/' + report.engagement.engagement_id)
            assert remote == report.model_dump(mode='json')
        with graph_env.env.engine.connect() as conn:
            reserved = conn.execute(text('SELECT sum(max_attempts) FROM runtime.supervision_call_reservations '
                'WHERE run_id=:run'), {'run': owners.run}).scalar_one()
        assert reserved == requests
        assert all(item.frame.request.deadline_unix_ms <= history[0].frame.request.deadline_unix_ms for item in history)
        assert owners.round()['status'] == 'completed'
        assert WinnerStore(graph_env.env.engine).read(actor, reference) == winner
        assert journal.series(actor, owners.run, reference.decision_id) == history
        with graph_env.env.engine.connect() as conn:
            confirmations = conn.execute(text('SELECT o.status FROM runtime.outbox o '
                "JOIN runtime.audit_events a USING(event_id) WHERE a.run_id=:run AND o.target='artifact_confirm'"),
                {'run': owners.run}).scalars().all()
        assert confirmations and set(confirmations) == {'acknowledged'}
        (tmp_path / 'evidence.json').write_text(json.dumps({'run': owners.run, 'variant': variant,
            'requests': requests, 'winner': winner.document().model_dump(mode='json'), 'rounds': owners.records,
            'tier': 'actual current owner processes; editable environment; installed independence remains V1'}, indent=2), encoding='utf-8')
    finally:
        owners.close()
