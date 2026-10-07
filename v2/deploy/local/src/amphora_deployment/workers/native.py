"""Pinned installed-owner turns in Windows jobs, without interrupt-based drain."""

import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType

from ..installation.inventory import OwnerInstallation
from ..lifecycle.jobs import ProcessJob
from ..lifecycle.processes import BASE_ENVIRONMENT
from ..profile import ProfileError, require
from .configuration import ConfigurationPins
from .recipes import NATIVE_RECIPES, WorkerScope

TURN_GATE = """import os,runpy,sys
if os.read(sys.stdin.fileno(),1)!=b'G': sys.exit(125)
module=sys.argv.pop(1)
sys.argv[0]=module
runpy.run_module(module,run_name='__main__')
"""


@dataclass(frozen=True)
class NativeBinding:
    name: str
    directory: Path
    source_lock: Path
    configuration: Path
    installation: OwnerInstallation
    configuration_pins: ConfigurationPins
    environment: object = field(repr=False)
    scope: WorkerScope | None = None

    @classmethod
    def pin(cls, name, directory, source_lock, configuration, environment, scope=None):
        require(name in NATIVE_RECIPES, "worker_recipe")
        directory, source_lock, configuration = map(Path, (directory, source_lock, configuration))
        require(all(path.is_absolute() for path in (directory, source_lock, configuration)), "worker_absolute_paths")
        require(type(environment) is dict and all(type(key) is str and key.startswith("AMPHORA_") and
                type(value) is str and "\x00" not in value for key, value in environment.items()), "worker_environment")
        recipe = NATIVE_RECIPES[name]
        recipe.command(directory / "environment/Scripts/python.exe", configuration, scope)
        return cls(name, directory, source_lock, configuration,
                   OwnerInstallation.from_directory(recipe.owner, directory, source_lock), ConfigurationPins.bind(name, configuration),
                   MappingProxyType(dict(environment)), scope)

    def _verify(self):
        require(OwnerInstallation.from_directory(NATIVE_RECIPES[self.name].owner, self.directory,
                self.source_lock) == self.installation, "worker_installation_changed")
        self.configuration_pins.verify()

    def recover(self):
        self._verify()

    def launch(self):
        self._verify()
        command = NATIVE_RECIPES[self.name].command(
            self.directory / "environment/Scripts/python.exe", self.configuration, self.scope)
        return NativeTurn.launch(command, self.environment)


class NativeTurn:
    def __init__(self, process, job):
        self.process, self.job = process, job
        self.released = False

    @classmethod
    def launch(cls, command, environment):
        # Private process primitive; production callers must use NativeBinding.
        values = {key: value for key, value in os.environ.items() if key.upper() in BASE_ENVIRONMENT}
        values.update(environment)
        job, process = ProcessJob(), None
        try:
            process = subprocess.Popen([command[0], "-I", "-c", TURN_GATE, *command[3:]],
                env=values, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW, close_fds=True)
            job.attach(process)
            process.stdin.write(b"G")
            process.stdin.flush()
            return cls(process, job)
        except Exception:  # noqa: BLE001 - release owned handles without leaking child diagnostics.
            job.close()
            if process is not None:
                if process.poll() is None:
                    process.terminate()
                process.wait(timeout=10)
                process.stdin.close()
            raise ProfileError("worker_native_start_failed") from None

    def poll(self):
        return self.process.poll()

    def release(self):
        require(self.poll() is not None, "worker_release_requires_exit")
        if not self.released:
            self.job.close()
            self.process.stdin.close()
            self.released = True

    def force_stop(self):
        self.job.close()
        self.process.wait(timeout=10)
        self.release()
