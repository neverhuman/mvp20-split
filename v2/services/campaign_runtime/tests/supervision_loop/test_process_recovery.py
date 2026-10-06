"""Separate Runtime processes die after request/response commits, before effects."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from amphora_campaign_runtime.lifecycle.access import RuntimePrincipal
from amphora_campaign_runtime.lifecycle.authority import AuthorityCommands
from amphora_contracts_core import Scope
from amphora_contracts_runtime import parse_command
from sqlalchemy import text


@pytest.fixture
def probe_cleanup(graph_env, tmp_path):
    yield
    path = tmp_path / 'barrier.json'
    if path.exists():
        metadata = json.loads(path.read_bytes())
        actor = RuntimePrincipal(metadata['actor'], Scope.model_validate(metadata['reference']['scope']),
                                 frozenset(metadata['actions']))
        command = parse_command('runtime.cancel', json.dumps({'identity': {
            'scope': actor.scope.model_dump(mode='json'), 'actor_id': actor.actor_id,
            'command_family': 'runtime.cancel', 'command_id': 'crash-probe-cleanup'},
            'payload': {'run_id': metadata['reference']['run_id'], 'reason_code': 'probe_cleanup'}}))
        assert AuthorityCommands(graph_env.env.engine).cancel(actor, command).outcome.status == 'accepted'


@pytest.mark.parametrize('mode', ['request', 'response'])
def test_runtime_checkpoint_process_replacement(graph_env, tmp_path, mode, probe_cleanup):
    path = tmp_path / 'barrier.json'
    probe = Path(__file__).with_name('process_probe.py').absolute()
    config = Path(__file__).parents[4] / 'dev/pyproject.toml'
    env = dict(os.environ, PYTHONUTF8='1', AMPHORA_RUNTIME_PROBE_STATE=str(path.absolute()))

    def run(stage):
        result = subprocess.run([sys.executable, '-m', 'pytest', '-c', str(config.absolute()), str(probe),
                               '-p', 'no:cacheprovider', '-q', '--tb=short'],
                              env=dict(env, AMPHORA_RUNTIME_PROBE_MODE=stage),
                              capture_output=True, text=True, timeout=45, check=False)
        (tmp_path / (stage + '.log')).write_text(result.stdout + result.stderr, encoding='utf-8')
        return result

    crashed = run(mode)
    assert crashed.returncode == 73, 'Runtime process did not reach its durable barrier'
    metadata = json.loads(path.read_bytes())
    params = {'run': metadata['reference']['run_id']}
    with graph_env.env.engine.connect() as conn:
        assert conn.execute(text('SELECT count(*) FROM runtime.supervision_winners WHERE run_id=:run'), params).scalar_one() == 0
    replacement = run('recover')
    assert replacement.returncode == 0, 'Runtime replacement probe failed'
    assert json.loads(path.with_suffix('.recovered.json').read_bytes())['pid'] != metadata['pid']
    with graph_env.env.engine.connect() as conn:
        assert conn.execute(text('SELECT count(*) FROM runtime.supervision_call_reservations WHERE run_id=:run'), params).scalar_one() == 1
        assert conn.execute(text('SELECT count(*) FROM runtime.supervision_winners WHERE run_id=:run'), params).scalar_one() == (mode == 'response')
