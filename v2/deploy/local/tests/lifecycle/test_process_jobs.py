import os
import subprocess
import sys
import time
import ctypes
from ctypes import wintypes

import pytest

from amphora_deployment.lifecycle import ProcessJob


pytestmark = pytest.mark.skipif(os.name != 'nt', reason='Selected local Windows profile')


def test_job_closure_terminates_only_its_owned_process():
    child = subprocess.Popen([sys.executable, '-I', '-c', 'import sys; sys.stdin.buffer.read(1)'],
                             stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                             creationflags=subprocess.CREATE_NO_WINDOW)
    unrelated = subprocess.Popen([sys.executable, '-I', '-c', 'import sys; sys.stdin.buffer.read(1)'],
                                 stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                 creationflags=subprocess.CREATE_NO_WINDOW)
    try:
        with ProcessJob() as job:
            job.attach(child)
            assert child.poll() is None
        child.wait(timeout=10)
        assert unrelated.poll() is None
        job.close()  # Idempotent teardown must never reopen a PID.
    finally:
        for process in (child, unrelated):
            if process.poll() is None:
                process.terminate()
            process.wait(timeout=10)
            process.stdin.close()


def test_closed_job_cannot_attach_process():
    from amphora_deployment.profile import ProfileError
    job = ProcessJob()
    job.close()
    with pytest.raises(ProfileError, match='lifecycle_job_unavailable'):
        job.attach(None)


def test_supervisor_death_closes_job_and_terminates_child(tmp_path):
    receipt = tmp_path / 'child.pid'
    code = '''
import pathlib, subprocess, sys
from amphora_deployment.lifecycle import ProcessJob
job = ProcessJob()
child = subprocess.Popen([sys.executable, '-I', '-c', 'import sys; sys.stdin.buffer.read(1)'], stdin=subprocess.PIPE,
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
job.attach(child)
pathlib.Path(sys.argv[1]).write_text(str(child.pid))
sys.stdin.buffer.read(1)
'''
    supervisor = subprocess.Popen([sys.executable, '-c', code, str(receipt)], stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
    api = ctypes.WinDLL('kernel32', use_last_error=True)
    api.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    api.OpenProcess.restype = wintypes.HANDLE
    api.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    api.WaitForSingleObject.restype = wintypes.DWORD
    api.CloseHandle.argtypes = [wintypes.HANDLE]
    api.CloseHandle.restype = wintypes.BOOL
    handle = None
    try:
        deadline = time.monotonic() + 15
        while not receipt.exists():
            assert supervisor.poll() is None
            assert time.monotonic() < deadline
            time.sleep(.05)
        handle = api.OpenProcess(0x00100000, False, int(receipt.read_text()))
        assert handle
        assert api.WaitForSingleObject(handle, 0) == 258  # WAIT_TIMEOUT: child alive.
        supervisor.terminate()
        supervisor.wait(timeout=10)
        assert api.WaitForSingleObject(handle, 10000) == 0  # Exact child HANDLE signaled.
    finally:
        if supervisor.poll() is None:
            supervisor.terminate()
        supervisor.wait(timeout=10)
        supervisor.stdin.close()
        if handle:
            api.CloseHandle(handle)
