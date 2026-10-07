import hashlib
import json
import os
import subprocess
import sys

import pytest
from amphora_deployment.lifecycle.jobs import ProcessJob
from amphora_deployment.profile import ProfileError
from amphora_deployment.workers.native import TURN_GATE, NativeBinding, NativeTurn


@pytest.fixture
def binding(tmp_path):
    wheel = 'amphora_campaign_runtime-0.65.0-py3-none-any.whl'
    (tmp_path / 'wheels').mkdir()
    (tmp_path / 'wheels' / wheel).write_bytes(b'fixture wheel')
    (tmp_path / 'environment/Scripts').mkdir(parents=True)
    (tmp_path / 'environment/Scripts/python.exe').write_bytes(b'fixture interpreter')
    lock, config = tmp_path / 'source.lock', tmp_path / 'worker.json'
    lock.write_bytes(b'fixture lock')
    config.write_bytes(b'{}')
    (tmp_path / 'manifest.json').write_text(json.dumps({'status': 'installed',
        'owner': 'amphora-campaign-runtime', 'packages': {'amphora-campaign-runtime': '0.65.0'},
        'wheels': {wheel: hashlib.sha256(b'fixture wheel').hexdigest()}}))
    return NativeBinding.pin('runtime-checkpoint', tmp_path, lock, config, {'AMPHORA_TEST_TOKEN': 'private'})


@pytest.mark.parametrize('filename', ['worker.json', 'source.lock', 'environment/Scripts/python.exe',
                                       'manifest.json', 'wheels/amphora_campaign_runtime-0.65.0-py3-none-any.whl'])
def test_changed_pins_reject_before_launch_or_recovery(binding, filename):
    binding.recover()
    path = binding.directory / filename
    path.write_bytes(path.read_bytes() + b' ')
    for operation in (binding.launch, binding.recover):
        with pytest.raises(ProfileError):
            operation()


def test_environment_is_immutable_private_and_scoped(binding):
    assert 'private' not in repr(binding)
    with pytest.raises(TypeError):
        binding.environment['AMPHORA_TEST_TOKEN'] = 'changed'
    with pytest.raises(ProfileError, match='worker_environment'):
        NativeBinding.pin(binding.name, binding.directory, binding.source_lock,
                          binding.configuration, {'PYTHONPATH': 'injected'})
    with pytest.raises(ProfileError, match='worker_recipe'):
        NativeBinding.pin('arbitrary', binding.directory, binding.source_lock, binding.configuration, {})


def test_pinned_binding_supplies_only_reviewed_command(binding, monkeypatch):
    calls = []
    monkeypatch.setattr(NativeTurn, 'launch', lambda command, environment: calls.append((command, environment)))
    binding.launch()
    assert calls[0][0][1:5] == ('-I', '-m', 'amphora_campaign_runtime.supervision_loop', 'run')
    assert calls[0][1]['AMPHORA_TEST_TOKEN'] == 'private'


@pytest.mark.skipif(os.name != 'nt', reason='Selected Windows profile')
def test_actual_gated_turn_completes_without_drain_signal():
    # stdlib stand-in verifies the private launcher only, not owner readiness.
    turn = NativeTurn.launch((sys.executable, '-I', '-m', 'timeit', '-n', '1', '-r', '1', 'pass'), {})
    try:
        assert turn.process.wait(timeout=10) == 0
        turn.release()
    finally:
        turn.force_stop()


@pytest.mark.skipif(os.name != 'nt', reason='Selected Windows profile')
def test_failed_job_assignment_never_enters_turn(monkeypatch):
    def fail(self, process):
        raise OSError('private diagnostics')
    monkeypatch.setattr(ProcessJob, 'attach', fail)
    with pytest.raises(ProfileError, match='worker_native_start_failed'):
        NativeTurn.launch((sys.executable, '-I', '-m', 'timeit', '-n', '1', '-r', '1', 'pass'), {})


@pytest.mark.skipif(os.name != 'nt', reason='Selected Windows profile')
def test_turn_entry_gate_eof_never_imports_owner():
    result = subprocess.run([sys.executable, '-I', '-c', TURN_GATE, 'not_an_owner'], input=b'',
        capture_output=True, timeout=10, check=False, creationflags=subprocess.CREATE_NO_WINDOW)
    assert result.returncode == 125
    assert result.stdout == result.stderr == b''


@pytest.mark.skipif(os.name != 'nt', reason='Selected Windows profile')
def test_actual_turn_release_refuses_live_work_and_waits_for_completion():
    process = subprocess.Popen([sys.executable, '-I', '-c', 'import os; os.read(0,1)'],
        stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW)
    job = ProcessJob()
    job.attach(process)
    turn = NativeTurn(process, job)
    try:
        with pytest.raises(ProfileError, match='requires_exit'):
            turn.release()
        assert turn.poll() is None
        process.stdin.write(b'X')
        process.stdin.flush()
        assert process.wait(timeout=10) == 0
        turn.release()
        turn.release()
        assert turn.poll() == 0
    finally:
        turn.force_stop()
