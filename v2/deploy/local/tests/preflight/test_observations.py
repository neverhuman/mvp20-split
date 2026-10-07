"""Observed compatibility and missing probes remain distinct from declared policy."""

import hashlib
import json
import subprocess
from types import SimpleNamespace

from amphora_deployment import DeploymentProfile
from amphora_deployment.observations import AcceleratorObservation, HostObservation, memory_bytes


def test_read_only_probe_binds_profile_and_reports_platform(monkeypatch, record, tmp_path):
    from amphora_deployment import observations as module
    record["target"]["operating_system"] = module.platform.system().lower()
    record["storage"]["artifact_root"] = str(tmp_path)
    monkeypatch.setattr(module.platform, "machine", lambda: "AMD64")
    monkeypatch.setattr(module, "memory_bytes", lambda _: 8192)
    profile = DeploymentProfile.from_bytes(json.dumps(record).encode())
    before = list(tmp_path.iterdir())
    observation = HostObservation.inspect(profile)
    assert observation.profile_sha256 == hashlib.sha256(profile.canonical_bytes()).hexdigest()
    assert observation.architecture == "x86_64" and observation.memory_bytes == 8192
    assert observation.artifact_directory_exists and observation.free_bytes > 0
    assert observation.storage_semantics == "unverified" and "provider_not_contacted" in observation.limitations
    assert list(tmp_path.iterdir()) == before


def test_foreign_platform_path_is_not_touched(monkeypatch, record):
    from amphora_deployment import observations as module
    monkeypatch.setattr(module.platform, "system", lambda: "Windows")
    monkeypatch.setattr(module.shutil, "disk_usage", lambda _: (_ for _ in ()).throw(AssertionError("path probed")))
    observation = HostObservation.inspect(DeploymentProfile.from_bytes(json.dumps(record).encode()))
    assert observation.free_bytes is None and observation.artifact_directory_exists is None
    assert "target_platform_path_not_probed" in observation.limitations


def test_accelerator_absence_failure_and_success(monkeypatch):
    from amphora_deployment import observations as module
    assert AcceleratorObservation.inspect("none").status == "not_required"
    monkeypatch.setattr(module.shutil, "which", lambda _: None)
    assert AcceleratorObservation.inspect("nvidia").status == "unavailable"
    monkeypatch.setattr(module.shutil, "which", lambda _: "nvidia-smi")
    for payload in (b"", b"unrecognized", b"x" * 4097):
        monkeypatch.setattr(module.subprocess, "run", lambda *a, **k: SimpleNamespace(returncode=0, stdout=payload))
        assert AcceleratorObservation.inspect("nvidia").status == "probe_failed"
    def timeout(*args, **kwargs):
        assert kwargs["timeout"] == 5
        raise subprocess.TimeoutExpired("nvidia-smi", 5)
    monkeypatch.setattr(module.subprocess, "run", timeout)
    assert AcceleratorObservation.inspect("nvidia").status == "probe_failed"
    monkeypatch.setattr(module.subprocess, "run", lambda *a, **k: SimpleNamespace(returncode=0, stdout=b"GPU-one\nGPU-two\n"))
    assert AcceleratorObservation.inspect("nvidia").device_count == 2


def test_unknown_memory_is_not_zero(monkeypatch):
    import os
    assert memory_bytes("unknown") is None
    monkeypatch.setattr(os, "sysconf", lambda _: 4096, raising=False)
    assert memory_bytes("linux") == 4096**2
