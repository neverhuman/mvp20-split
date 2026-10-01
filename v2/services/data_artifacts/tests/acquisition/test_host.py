import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest
from amphora_contracts_evidence import PreparedSource
from amphora_data_artifacts.acquisition.profiles import PreparedContentRule
from amphora_data_artifacts.hosting import Host
from fastapi.testclient import TestClient

pytestmark = pytest.mark.postgres


@pytest.mark.parametrize("enabled", [True, False, "true"])
def test_host_explicitly_enables_owned_ingestion(artifact_database, tmp_path, monkeypatch, enabled):
    config = json.loads((Path(__file__).parents[2] / "config.example.json").read_text(encoding="utf-8"))
    config.update(storage_root=str(tmp_path), acquisition=enabled)
    config["principals"][0]["actions"] = ["acquire", "read", "source_history"]
    path = tmp_path / "host.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    monkeypatch.setenv("AMPHORA_ARTIFACT_DATABASE_URL", artifact_database.render_as_string(hide_password=False))
    monkeypatch.setenv("AMPHORA_ARTIFACT_WORKER_TOKEN", "x" * 32)
    if type(enabled) is not bool:
        with pytest.raises(ValueError, match="flag must be boolean"):
            Host.load(path)
        return
    host = Host.load(path)
    try:
        assert (PreparedContentRule("document").identity in host.uploads.policy.allowed) is enabled
        with TestClient(host.app()) as client:
            response = client.post("/v1/acquisition/prepare", json={})
            assert response.status_code == (401 if enabled else 404)
            response = client.post("/v1/acquisition/prepare", json={}, headers={"Authorization": "Bearer " + "x" * 32})
            assert response.status_code == (422 if enabled else 404)
    finally:
        host.close()


def test_live_ingestion_receipt_survives_process_replacement(ingestion, tmp_path):
    e = ingestion
    source = e.source(b'{"value":"<0.5"}', "synthetic_lab_json")
    raw_profile = next(identity for identity in e.env.uploads.policy.allowed if identity[0] == "application/octet-stream")
    config = {"database_url_env": "AMPHORA_INGRESS_DATABASE", "storage_root": str(e.env.storage.root),
              "acquisition": True, "principals": [{"token_env": "AMPHORA_INGRESS_TOKEN", "actor_id": "worker",
              "scope": e.principal.scope.model_dump(), "actions": ["acquire", "read", "source_history"]}],
              "profiles": [dict(zip(("media_type", "schema_id", "version", "sha256"), raw_profile, strict=True))]}
    path = tmp_path / "ingress-host.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    environment = dict(os.environ, AMPHORA_INGRESS_DATABASE=e.env.engine.url.render_as_string(hide_password=False),
                       AMPHORA_INGRESS_TOKEN="p" * 32)
    original = None
    retained_request = None
    for _ in range(2):
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            port = listener.getsockname()[1]
        process = subprocess.Popen([sys.executable, "-I", "-m", "amphora_data_artifacts", "serve",
                                    "--config", str(path), "--port", str(port)], env=environment,
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))

        def request(route, body=None, *, server_port=port):
            payload = None if body is None else json.dumps(body).encode()
            query = urllib.request.Request(f"http://127.0.0.1:{server_port}" + route, data=payload,
                headers={"Authorization": "Bearer " + "p" * 32, "Content-Type": "application/json"})
            with urllib.request.urlopen(query, timeout=5) as response:
                return json.load(response)

        try:
            deadline = time.monotonic() + 15
            while True:
                assert process.poll() is None, "Ingress host exited before ready"
                try:
                    assert request("/ready")["ready"]
                    break
                except urllib.error.URLError:
                    assert time.monotonic() < deadline, "Ingress host readiness timeout"
                    time.sleep(0.05)
            prepared = request("/v1/acquisition/prepare", source.model_dump(mode="json"))
            assert prepared["disposition"] == "quarantined"
            if retained_request is None:
                parsed = PreparedSource.model_validate_json(json.dumps(prepared))
                output = e.publish(parsed.content_json_utf8.encode(), parsed.schema_ref)
                retained_request = {"wire_version": "1", "source": source.model_dump(mode="json"),
                                    "trace_id": "live-trace", "output": output.model_dump(mode="json")}
            receipt = request("/v1/acquisition/retain", retained_request)
            if original is None:
                original = receipt
            assert receipt == original
            assert request("/v1/acquisition/traces/live-trace")["disposition"] == "quarantined"
        finally:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=10)
