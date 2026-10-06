"""Explicit role-checked worker processes restart from owned SQL without peer side effects."""

import json
import subprocess
import sys

import pytest
from amphora_campaign_runtime.supervision_loop.configuration import CheckpointHost
from sqlalchemy import text

from .support import fixture


def configuration(graph, tmp_path, monkeypatch):
    monkeypatch.setenv('TEST_CHECKPOINT_DB', graph.env.engine.url.render_as_string(hide_password=False))
    monkeypatch.setenv('TEST_CHECKPOINT_TOKEN', 'synthetic-checkpoint-token-000000000000')
    peer = {'endpoint': 'http://127.0.0.1:1', 'token_env': 'TEST_CHECKPOINT_TOKEN', 'actor_id': 'fixture'}
    raw = {'database_url_env': 'TEST_CHECKPOINT_DB', 'actor_id': graph.env.principal.actor_id,
        'scope': graph.env.principal.scope.model_dump(mode='json'), 'planning': peer, 'data': peer}
    path = tmp_path / 'checkpoint-worker.json'
    path.write_text(json.dumps(raw), encoding='utf-8')
    return path, raw


def process(path, action):
    return subprocess.run([sys.executable, '-m', 'amphora_campaign_runtime.supervision_loop', action,
        '--config', str(path), '--seconds', '0.05', '--interval', '0.05'], capture_output=True,
        text=True, check=False, timeout=60, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))


def test_process_check_cancellation_and_replacement_without_peers(graph_env, tmp_path, monkeypatch):
    actor, ref, _, loop, _, _ = fixture(graph_env)
    path, _ = configuration(graph_env, tmp_path, monkeypatch)
    checked = process(path, 'check')
    assert checked.returncode == 0 and json.loads(checked.stdout)['mode'] == 'checkpoint_worker'
    with graph_env.env.engine.begin() as conn:
        conn.execute(text("UPDATE runtime.runs SET status='cancelled' WHERE run_id=:run"), {'run': ref.run_id})
    first = process(path, 'run')
    assert first.returncode == 0 and json.loads(first.stdout)['decided'] == 1
    winner = loop.resolver.winners.read(actor, ref)
    assert winner.document().outcome.kind == 'cancelled'
    second = process(path, 'run')
    assert second.returncode == 0 and json.loads(second.stdout)['idle'] >= 1
    assert loop.resolver.winners.read(actor, ref) == winner


@pytest.mark.parametrize('change', ['unknown', 'missing_secret', 'role', 'oversized'])
def test_bad_configuration_cannot_start_or_disclose_credentials(graph_env, tmp_path, monkeypatch, change):
    path, raw = configuration(graph_env, tmp_path, monkeypatch)
    if change == 'unknown':
        raw['executable_adapter'] = 'arbitrary.py'
    elif change == 'missing_secret':
        monkeypatch.delenv('TEST_CHECKPOINT_TOKEN')
    elif change == 'role':
        monkeypatch.setenv('TEST_CHECKPOINT_DB', graph_env.env.engine.url.set(username='runtime_migrator').render_as_string(hide_password=False))
    if change == 'oversized':
        path.write_bytes(b' ' * 65537)
    else:
        path.write_text(json.dumps(raw), encoding='utf-8')
    result = process(path, 'check')
    assert result.returncode == 2
    assert result.stdout == '' and 'durable state remains authoritative' in result.stderr
    assert 'synthetic-checkpoint-token' not in result.stderr and 'postgresql' not in result.stderr


def test_host_load_has_no_implicit_tick(graph_env, tmp_path, monkeypatch):
    actor, ref, _, loop, _, _ = fixture(graph_env)
    path, _ = configuration(graph_env, tmp_path, monkeypatch)
    host = CheckpointHost.load(path)
    try:
        assert host.principal.actor_id == actor.actor_id and host.principal.scope == actor.scope
        assert loop.preparer.journal.series(actor, ref.run_id, ref.decision_id) == ()
        assert loop.resolver.winners.read(actor, ref) is None
    finally:
        host.close()
