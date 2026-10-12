import json
from pathlib import Path
import subprocess
import sys
import time

import pytest
from sqlalchemy import text

from amphora_agent_planning.context import AttemptBinding
from amphora_agent_planning.curation_declaration.journal import DeclarationJournal
from amphora_agent_planning.curation_jobs.journal import CurationJobs
from amphora_agent_planning.curation_result.journal import CurationResultJournal
from ..curation_execution.test_executor import setup
from ..curation_jobs.test_journal import expire
from .test_configuration import files

pytestmark = pytest.mark.postgres


def test_crashed_issuance_is_recovered_by_configured_replacement_without_provider(stored, tmp_path, monkeypatch):
    principal, lease, linked, executor, provider, data = setup(stored)
    path, config, _ = files(tmp_path, monkeypatch)
    config['actor_id'] = config['eligibility']['actor_id'] = principal.actor_id
    config['scope'] = principal.scope.model_dump(mode='json')
    origin = DeclarationJournal(stored.engine).read(principal, lease.curation_id).identity
    path.write_text(json.dumps(config), encoding='utf-8')
    (tmp_path / 'policy.json').write_text(json.dumps(json.loads(origin.canonical)['policy']), encoding='utf-8')
    path.with_suffix('.probe.json').write_text(json.dumps({'bodies': {key: value.hex() for key, value in data.bodies.items()}}), encoding='utf-8')
    monkeypatch.setenv('CURATION_TEST_DATABASE', stored.engine.url.render_as_string(hide_password=False))
    CurationJobs(stored.engine).release(principal, lease)
    options = dict(capture_output=True, text=True, timeout=60, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    crashed = subprocess.run([sys.executable, '-I', str(Path(__file__).with_name('crash_worker.py').absolute()), str(path)], **options)
    assert crashed.returncode == 73, crashed.stderr
    marker = json.loads(path.with_suffix('.issued.json').read_bytes())
    assert marker['ordinal'] == 1
    binding = AttemptBinding(linked.frozen.preparation.packet.request, 1)
    assert executor.attempts.read_attempt(principal, binding.reference()).observation is None
    expire(stored, principal, lease.curation_id)  # Coordination expiry only; original dispatch deadline is untouched.
    time.sleep(max(0, marker['deadline_unix_ms'] / 1000 - time.time()) + 0.03)
    command = [sys.executable, '-m', 'amphora_agent_planning.curation_worker', 'run', '--config', str(path),
               '--seconds', '0.1', '--interval', '0.05']
    recovered = subprocess.run(command, **options)
    assert recovered.returncode == 0, recovered.stderr
    assert json.loads(recovered.stdout)['terminal'] == 1
    outcome = CurationResultJournal(stored.engine).read(principal, lease.curation_id)
    assert outcome.disposition == ('indeterminate', 'provider_outcome_unknown')
    assert outcome.settlement.charge.accounting_units == outcome.reservation.demand.accounting_units
    assert outcome.proposal is None
    replay = subprocess.run(command, **options)
    assert replay.returncode == 0 and json.loads(replay.stdout)['idle'] >= 1
    assert CurationResultJournal(stored.engine).read(principal, lease.curation_id) == outcome
    assert json.loads(path.with_suffix('.issued.json').read_bytes()) == marker and provider.calls == 0
    with stored.engine.connect() as conn:
        assert conn.execute(text('SELECT count(*) FROM planning.dispatches WHERE project_id=:project'),
            {'project': principal.scope.project_id}).scalar_one() == 1
