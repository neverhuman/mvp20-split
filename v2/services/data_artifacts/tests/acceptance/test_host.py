import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from amphora_data_artifacts.hosting import Host
from fastapi.testclient import TestClient


def test_executable_acceptance(artifact_database):
    env = dict(os.environ, AMPHORA_PROBE_DATABASE_URL=artifact_database.render_as_string(hide_password=False))
    result = subprocess.run([sys.executable, "-I", str(Path(__file__).with_name("installed_probe.py"))],
                            env=env, capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stdout + result.stderr


def test_startup_failure_is_sanitized(tmp_path):
    result = subprocess.run([sys.executable, "-I", "-m", "amphora_data_artifacts", "check",
                             "--config", str(tmp_path / "absent.json")], capture_output=True, text=True, timeout=15)
    assert result.returncode == 2
    assert "Traceback" not in result.stderr
    assert str(tmp_path) not in result.stderr


@pytest.mark.parametrize("role", ["artifact_service", "artifact_migrator"])
def test_host_requires_service_role(artifact_database, tmp_path, monkeypatch, role):
    source = Path(__file__).parents[2] / "config.example.json"
    config = json.loads(source.read_text())
    config["storage_root"] = str(tmp_path)
    config_path = tmp_path / "host.json"
    config_path.write_text(json.dumps(config))
    monkeypatch.setenv("AMPHORA_ARTIFACT_DATABASE_URL", artifact_database.set(username=role).render_as_string(hide_password=False))
    monkeypatch.setenv("AMPHORA_ARTIFACT_WORKER_TOKEN", "x" * 32)
    if role != "artifact_service":
        with pytest.raises(ValueError, match="service role required"):
            Host.load(config_path)
        return
    host = Host.load(config_path)
    try:
        with TestClient(host.app()) as client:
            assert client.get("/ready").json() == {"ready": True}
            assert client.get("/v1/artifacts/missing", headers={"Authorization": "Bearer " + "x" * 32}).status_code == 404
    finally:
        host.close()
