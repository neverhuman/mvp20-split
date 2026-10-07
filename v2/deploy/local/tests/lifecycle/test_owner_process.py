import json
import os
import subprocess
import sys

import pytest
from amphora_deployment.installation import OWNERS
from amphora_deployment.lifecycle import LifecycleEvents
from amphora_deployment.lifecycle.processes import ENTRY_GATE, OwnerProcess
from amphora_deployment.profile import ProfileError

pytestmark = pytest.mark.skipif(os.name != 'nt', reason='Selected Windows profile')


def test_entry_gate_eof_never_enters_owner_module():
    result = subprocess.run([sys.executable, '-I', '-c', ENTRY_GATE, 'module_that_must_not_import'],
                            input=b'', capture_output=True, timeout=10, check=False, creationflags=subprocess.CREATE_NO_WINDOW)
    assert result.returncode == 125
    assert result.stdout == result.stderr == b''


def test_actual_owner_cli_configuration_failure_is_not_readiness(tmp_path):
    events = LifecycleEvents(tmp_path / 'logs')
    command = OWNERS['registry'].serve_command(os.environ.get('AMPHORA_TEST_REGISTRY_PYTHON', sys.executable),
                                               tmp_path / 'absent.json', 19872)
    with OwnerProcess._launch('registry', command, {}, events) as owner:
        assert owner.process.wait(timeout=15) == 2
        assert owner.status()['state'] == 'exited'
        assert owner.status()['readiness'] == 'not_assessed'
    records = [json.loads(line) for line in (tmp_path / 'logs/lifecycle.jsonl').read_text().splitlines()]
    assert [record['event'] for record in records] == ['starting', 'started', 'exited']


def test_cross_owner_and_unscoped_environment_rejected(tmp_path):
    events = LifecycleEvents(tmp_path)
    command = OWNERS['registry'].serve_command(sys.executable, 'absent.json', 19872)
    with pytest.raises(ProfileError, match='command_owner'):
        OwnerProcess._launch('runtime', command, {}, events)
    with pytest.raises(ProfileError, match='environment'):
        OwnerProcess._launch('registry', command, {'PYTHONPATH': 'arbitrary-code'}, events)
