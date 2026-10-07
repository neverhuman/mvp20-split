"""Bounded local observations; never installs, writes storage or contacts a provider."""

import ctypes
import hashlib
import os
import platform
import shutil
import socket
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path


def memory_bytes(system):
    if system == "windows":
        class MemoryStatus(ctypes.Structure):
            _fields_ = [("length", ctypes.c_ulong), ("load", ctypes.c_ulong)] + [
                (name, ctypes.c_ulonglong) for name in ("total", "available", "page_total", "page_available", "virtual_total", "virtual_available", "extended")]
        record = MemoryStatus()
        record.length = ctypes.sizeof(record)
        try:
            return record.total if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(record)) else None
        except (AttributeError, OSError):
            return None
    if system == "linux":
        try:
            result = os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")
            return result if result > 0 else None
        except (AttributeError, OSError, ValueError):
            return None
    return None


@dataclass(frozen=True)
class AcceleratorObservation:
    status: str
    device_count: int | None

    @classmethod
    def inspect(cls, required):
        if required == "none":
            return cls("not_required", None)
        executable = shutil.which("nvidia-smi")
        if executable is None:
            return cls("unavailable", None)
        try:
            result = subprocess.run([executable, "--query-gpu=uuid", "--format=csv,noheader"],
                                    capture_output=True, timeout=5, check=False)
        except (OSError, subprocess.TimeoutExpired):
            return cls("probe_failed", None)
        if result.returncode != 0 or len(result.stdout) > 4096:
            return cls("probe_failed", None)
        identities = result.stdout.splitlines()
        if not identities or any(not value.startswith(b"GPU-") for value in identities):
            return cls("probe_failed", None)
        return cls("observed", len(identities))


@dataclass(frozen=True)
class HostObservation:
    profile_sha256: str
    observed_at: str
    hostname: str
    operating_system: str
    architecture: str
    python: str
    cpu_count: int | None
    memory_bytes: int | None
    artifact_directory_exists: bool | None
    free_bytes: int | None
    storage_semantics: str
    accelerator: AcceleratorObservation
    limitations: tuple[str, ...]

    @classmethod
    def inspect(cls, profile):
        system = platform.system().lower()
        machine = platform.machine().lower()
        architecture = {"amd64": "x86_64", "arm64": "aarch64"}.get(machine, machine)
        directory, available = None, None
        limitations = ["read_only_observation", "durability_not_tested", "network_exposure_not_tested", "provider_not_contacted"]
        if system == profile.target.operating_system:
            try:
                path = Path(profile.storage.artifact_root)
                directory = path.is_dir()
                if directory:
                    available = shutil.disk_usage(path).free
            except OSError:
                limitations.append("storage_probe_failed")
        else:
            limitations.append("target_platform_path_not_probed")
        return cls(hashlib.sha256(profile.canonical_bytes()).hexdigest(), datetime.now().astimezone().isoformat(timespec="seconds"),
                   socket.gethostname(), system, architecture, ".".join(platform.python_version_tuple()[:2]),
                   os.cpu_count(), memory_bytes(system), directory, available, "unverified",
                   AcceleratorObservation.inspect(profile.target.accelerator), tuple(limitations))

    def to_record(self):
        return asdict(self)
