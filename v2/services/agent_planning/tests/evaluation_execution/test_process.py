"""Separate process replacement retains unknown primary and never repeats issuance."""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest
from amphora_agent_planning.providers import FixtureProvider

from .test_runner import setup

pytestmark = pytest.mark.postgres


def test_process_death_keeps_failed_measurement_and_reserved_charge(stored, tmp_path):
    protocol, batch, _, runner = setup(stored, FixtureProvider('abstain'), timeout=1)
    (tmp_path / 'configuration.json').write_text(json.dumps({'actor_id': stored.principal.actor_id,
        'scope': stored.principal.scope.model_dump(), 'suite_id': protocol.manifest.suite_id}), encoding='utf-8')
    env = dict(os.environ, EVALUATION_PROCESS_SQL=stored.engine.url.render_as_string(hide_password=False))
    worker = Path(__file__).with_name('process_worker.py').absolute()
    def run(mode, expected=0):
        result = subprocess.run([sys.executable, str(worker), str(tmp_path), mode], env=env,
            capture_output=True, text=True, timeout=45, check=False,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        (tmp_path / (mode + '.log')).write_text(result.stdout + result.stderr, encoding='utf-8')
        assert result.returncode == expected, 'Evaluation process failed; inspect owned probe log'
    run('crash', 73)
    time.sleep(1.1)
    run('recover')
    recovered = json.loads((tmp_path / 'recover.json').read_text())
    assert recovered['status'] == 'pending' and recovered['observations'][0]['status'] == 'unknown'
    assert (tmp_path / 'calls.txt').read_text().splitlines() == [batch.tasks[0].request.sha256]
    charge = runner.runner.settlements.read(stored.principal, batch.tasks[0].binding.reference()).charge
    assert charge.accounting_units == batch.tasks[0].demand.accounting_units
    run('complete')
    final = json.loads((tmp_path / 'complete.json').read_text())
    assert final['status'] == 'complete' and not final['passed']
    assert final['observations'][0] == recovered['observations'][0]
    assert [item['status'] for item in final['observations']] == ['unknown', 'scientific_abstention']
    assert (tmp_path / 'calls.txt').read_text().splitlines() == [task.request.sha256 for task in batch.tasks]
