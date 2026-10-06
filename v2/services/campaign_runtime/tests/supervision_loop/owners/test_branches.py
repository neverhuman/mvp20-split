"""Actual owner exchange while a test-only Planning provider waits at a barrier."""

import hashlib
import json
import os
import subprocess
import time
from pathlib import Path

import pytest
from amphora_campaign_runtime.supervision_journal.storage import RequestJournal
from amphora_campaign_runtime.supervision_outcomes.reports import ReportJournal
from amphora_campaign_runtime.supervision_winners import WinnerStore
from amphora_contracts_supervision import SupervisionRef, SupervisionResponse
from sqlalchemy import text

from ...supervision_checkpoints.test_coordinator import slots
from .processes import Owners

pytestmark = [pytest.mark.owner_processes, pytest.mark.skipif(
    os.environ.get('AMPHORA_TEST_OWNER_PROCESSES') != '1', reason='Explicit actual-owner process opt-in required')]


def node(graph, run, name):
    with graph.env.engine.connect() as conn:
        return conn.execute(text('SELECT status,outputs FROM runtime.graph_nodes WHERE run_id=:run AND node_id=:node'),
                            {'run': run, 'node': name}).mappings().one()


@pytest.mark.parametrize('mode', ['adjust', 'late', 'future'])
def test_independent_branch_and_late_or_future_proposal(graph_env, tmp_path, mode):
    owners = Owners(graph_env, tmp_path, 'disabled', independent=True)
    process = None
    try:
        for _ in range(3):
            owners._command(['-m', 'amphora_campaign_runtime.supervision_loop', 'run', '--config',
                             str(owners.runtime_worker), '--seconds', '0.2', '--interval', '0.05'])
        actor = graph_env.env.principal
        slot = slots(graph_env, owners.run, owners.policy)[0]
        ref = SupervisionRef(scope=actor.scope, run_id=owners.run, decision_id=slot.seed.decision_id)
        journal = RequestJournal(graph_env.env.engine, {})
        original, = journal.series(actor, owners.run, ref.decision_id)
        engagement = original.frame.request.planning_request.reference.engagement_id
        probe = Path(__file__).parents[4] / 'agent_planning/tests/supervision_execution/owner_probe.py'
        with (tmp_path / 'provider.log').open('w', encoding='utf-8') as log:
            process = subprocess.Popen([str(owners.python_for('amphora_agent_planning')), '-I', str(probe.absolute()), str(owners.planning_worker),
                engagement, mode, str(tmp_path)], env=owners.env, cwd=tmp_path, stdout=log, stderr=log,
                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            end = time.monotonic() + 30
            while not (tmp_path / 'provider-entered.json').exists():
                assert process.poll() is None, 'Planning fixture failed before its barrier; inspect provider.log'
                assert time.monotonic() < end, 'Planning fixture did not reach its barrier'
                time.sleep(0.1)
            if owners.installations is not None:
                owners.replace_hosts()
            for _ in range(4):
                assert owners.graph_round()['status'] == 'running'
                if node(graph_env, owners.run, 'independent')['status'] == 'succeeded':
                    break
            assert node(graph_env, owners.run, 'independent')['status'] == 'succeeded'
            assert node(graph_env, owners.run, 'pack')['status'] != 'succeeded'
            assert WinnerStore(graph_env.env.engine).read(actor, ref) is None
            assert process.poll() is None
            if mode != 'late':
                (tmp_path / 'provider-release').touch()
                assert process.wait(timeout=30) == 0, 'Planning fixture failed on release'
            for _ in range(10):
                page = owners.round()
                if page['status'] == 'completed':
                    break
            assert page['status'] == 'completed'
            winner = WinnerStore(graph_env.env.engine).read(actor, ref)
            report = ReportJournal(journal).read(actor, ref, original.frame.request_sha256)
            if mode == 'late':
                assert winner.document().outcome.kind == 'fallback' and winner.selection is None
                (tmp_path / 'provider-release').touch()
                assert process.wait(timeout=30) == 0, 'Late provider failed to retain its diagnostic'
                for _ in range(3):
                    assert owners.round()['status'] == 'completed'
                with graph_env.env.engine.connect() as conn:
                    raw = conn.execute(text('SELECT canonical_response FROM runtime.supervision_responses WHERE run_id=:run'),
                                       {'run': owners.run}).scalars().all()
                responses = [SupervisionResponse.model_validate_json(bytes(item)) for item in raw]
                assert {item.observation.status for item in responses} == {'unknown', 'proposed'}
                assert len(responses) == 2
            else:
                effect = winner.document().outcome.effect
                assert effect.kind == ('adjusted_materialization_fields' if mode == 'adjust' else 'future_campaign')
            expected = hashlib.sha256(b'{"a":2}' if mode == 'adjust' else b'{"a":1}').hexdigest()
            assert expected in json.dumps(node(graph_env, owners.run, 'pack')['outputs'])
            assert owners.round()['status'] == 'completed'
            assert WinnerStore(graph_env.env.engine).read(actor, ref) == winner
            assert ReportJournal(journal).read(actor, ref, original.frame.request_sha256) == report
            assert journal.series(actor, owners.run, ref.decision_id) == (original,)
            with graph_env.env.engine.connect() as conn:
                assert conn.execute(text('SELECT plan_sha256 FROM runtime.graph_runs WHERE run_id=:run'),
                                    {'run': owners.run}).scalar_one() == owners.compiled.sha256
            (tmp_path / 'evidence.json').write_text(json.dumps({'mode': mode, 'run': owners.run,
                'winner': winner.document().model_dump(mode='json'), 'independent_branch_completed_before_release': True,
                'expected_output_sha256': expected, 'original_request_sha256': original.frame.request_sha256,
                'tier': 'isolated installed replacement' if owners.installations else 'editable owners',
                'hosts': owners.host_processes,
                'installation_manifest_sha256': None if owners.installations is None else owners.installations.supervisor_manifest_sha256,
                'data_manifest_sha256': None if owners.installations is None else owners.installations.data_manifest_sha256}), encoding='utf-8')
    finally:
        if process is not None and process.poll() is None:
            process.terminate()
            process.wait(timeout=10)
        owners.close()
