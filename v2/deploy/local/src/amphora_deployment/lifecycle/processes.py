"""Reviewed owner CLI launch, gated on containment; process state is not readiness."""

import os
from pathlib import Path
import subprocess

from ..installation import OWNERS
from ..installation.inventory import sha256, WheelIdentity
from ..profile import require, ProfileError
from .jobs import ProcessJob


# The child cannot enter the owner module before the parent has assigned its job.
ENTRY_GATE = "import sys,runpy; gate=sys.stdin.buffer.read(1); module=sys.argv.pop(1); sys.argv[0]=module; sys.exit(125) if gate!=b'G' else runpy.run_module(module,run_name='__main__')"
BASE_ENVIRONMENT = {"SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP", "COMSPEC", "USERPROFILE", "LOCALAPPDATA", "APPDATA"}


class OwnerProcess:
    def __init__(self, owner, process, job, events):
        self.owner, self.process, self.job, self.events = owner, process, job, events

    @classmethod
    def start(cls, installation, directory, configuration, port, environment, events):
        owner = installation.owner
        require(owner in OWNERS, "lifecycle_owner")
        root = Path(directory)
        python = root / "environment/Scripts/python.exe"
        require(sha256(python) == installation.interpreter_sha256 and
                sha256(root / "manifest.json") == installation.installation_manifest_sha256,
                "lifecycle_installation_changed")
        for wheel in installation.wheels:
            WheelIdentity.verified(root, wheel.filename, wheel.sha256)
        return cls._launch(owner, OWNERS[owner].serve_command(python, configuration, port), environment, events)

    @classmethod
    def _launch(cls, owner, command, environment, events):
        # Internal primitive: callers use start() to verify the immutable owner inventory.
        require(owner in OWNERS and tuple(command[1:3]) == ("-I", "-m"), "lifecycle_command")
        expected = OWNERS[owner].module + (".supervision_api" if owner == "planning" else "")
        require(command[3] == expected, "lifecycle_command_owner")
        require(type(environment) is dict and all(type(k) is str and k.startswith("AMPHORA_") and
                type(v) is str and "\x00" not in v for k, v in environment.items()), "lifecycle_environment")
        values = {key:value for key,value in os.environ.items() if key.upper() in BASE_ENVIRONMENT}
        values.update(environment)
        job, process = ProcessJob(), None
        try:
            events.emit(owner, "starting")
            process = subprocess.Popen([command[0], "-I", "-c", ENTRY_GATE, *command[3:]],
                env=values, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW, close_fds=True)
            job.attach(process)
            process.stdin.write(b"G")
            process.stdin.flush()
            process.stdin.close()
            events.emit(owner, "started", pid=process.pid)
            return cls(owner, process, job, events)
        except Exception:
            job.close()
            if process is not None:
                if process.poll() is None:
                    process.terminate()
                process.wait(timeout=10)
                if not process.stdin.closed:
                    process.stdin.close()
            raise ProfileError("lifecycle_owner_start_failed") from None

    def status(self):
        code = self.process.poll()
        return {"owner": self.owner, "pid": self.process.pid,
                "state": "running" if code is None else "exited", "exit_code": code,
                "readiness": "not_assessed"}

    def force_stop(self):
        running = self.process.poll() is None
        self.job.close()
        code = self.process.wait(timeout=10)
        self.events.emit(self.owner, "force_stopped" if running else "exited", pid=self.process.pid, exit_code=code)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.force_stop()
