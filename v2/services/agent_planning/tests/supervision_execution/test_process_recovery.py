"""Actual checkpoint process death preserves issuance and conservative charge."""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest
from amphora_agent_planning.context import AttemptBinding
from sqlalchemy import text

from .test_worker import setup

pytestmark = pytest.mark.postgres


def test_issued_checkpoint_survives_process_death_without_second_call(stored, tmp_path):
    worker, data, _, intake = setup(stored, attempts=1)
    engagement = intake.planning.document().reference.engagement_id
    config = {'actor': stored.principal.actor_id, 'scope': stored.principal.scope.model_dump(mode='json'),
              'engagement': engagement, 'bodies': {key: value.hex() for key, value in data.bodies.items()},
              'templates': [{'reference': ref.model_dump(mode='json'), 'canonical': template.canonical.decode()}
                            for ref, template in worker.templates._entries.values()]}
    path = tmp_path / 'checkpoint.json'
    path.write_text(json.dumps(config), encoding='utf-8')
    env = dict(os.environ, PYTHONUTF8='1', AMPHORA_CHECKPOINT_PROBE_SQL=stored.engine.url.render_as_string(hide_password=False))
    probe = Path(__file__).with_name('crash_worker.py').absolute()

    def run(phase):
        return subprocess.run([sys.executable, '-I', str(probe), phase, str(path.absolute())],
                              env=env, capture_output=True, text=True, timeout=30, check=False)

    crashed = run('crash')
    assert crashed.returncode == 73, 'Probe did not reach committed issuance barrier'
    marker = json.loads(path.with_suffix('.issued.json').read_bytes())
    assert marker['ordinal'] == 1
    binding = AttemptBinding(intake.planning, 1)
    assert worker.journal.read_attempt(stored.principal, binding.reference()).observation is None
    assert worker.completions.read(stored.principal, engagement) is None
    with stored.engine.connect() as conn:
        remaining = conn.execute(text('SELECT extract(epoch FROM deadline-clock_timestamp()) FROM planning.dispatches '
                                      'WHERE project_id=:project AND engagement_id=:engagement'),
                                 {'project': stored.principal.scope.project_id, 'engagement': engagement}).scalar_one()
    time.sleep(max(0, float(remaining)) + 0.03)
    recovered = run('recover')
    assert recovered.returncode == 0, 'Replacement process failed'
    result = json.loads(recovered.stdout)
    assert result['pid'] != marker['pid']
    assert result['stop_reason'] == 'attempt_limit' and result['statuses'] == ['unknown']
    report = worker.completions.read(stored.principal, engagement)
    charge = worker.settlements.read(stored.principal, binding.reference()).charge
    limits = intake.planning.document().context.limits
    assert charge.input_tokens == limits.max_input_tokens and charge.output_tokens == limits.max_output_tokens
    assert charge.accounting_units > 0 and not charge.overage
    replay = run('recover')
    assert replay.returncode == 0 and json.loads(replay.stdout)['statuses'] == ['unknown']
    assert worker.completions.read(stored.principal, engagement) == report
    assert worker.settlements.read(stored.principal, binding.reference()).charge == charge
    with stored.engine.connect() as conn:
        assert conn.execute(text('SELECT count(*) FROM planning.dispatches WHERE project_id=:project'),
                            {'project': stored.principal.scope.project_id}).scalar_one() == 1
    assert json.loads(path.with_suffix('.issued.json').read_bytes()) == marker
