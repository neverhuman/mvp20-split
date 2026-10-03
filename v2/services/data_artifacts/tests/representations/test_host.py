"""Representation host opt-in and readiness without hidden registrations/migrations."""

import json
from pathlib import Path

import pytest
from amphora_data_artifacts.hosting import Host
from amphora_data_artifacts.representations.bindings.content_rule import VectorContentRule
from fastapi.testclient import TestClient
from sqlalchemy import text

pytestmark = pytest.mark.postgres


@pytest.mark.parametrize("enabled", [True, False, "true", 1])
def test_host_explicit_representation_boundary(artifact_database, tmp_path, monkeypatch, enabled):
    config = json.loads((Path(__file__).parents[2] / "config.example.json").read_text(encoding="utf-8"))
    config.update(storage_root=str(tmp_path), representations=enabled)
    config["principals"][0]["actions"] = [
        "representation_read",
        "representation_manage",
        "representation_encode",
        "read",
        "source_history",
        "upload",
        "finalize",
    ]
    path = tmp_path / "host.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    monkeypatch.setenv(
        "AMPHORA_ARTIFACT_DATABASE_URL", artifact_database.render_as_string(hide_password=False)
    )
    monkeypatch.setenv("AMPHORA_ARTIFACT_WORKER_TOKEN", "x" * 32)
    if type(enabled) is not bool:
        with pytest.raises(ValueError, match="Representations flag must be boolean"):
            Host.load(path)
        return
    host = Host.load(path)
    try:
        assert host.representations_enabled is enabled
        assert (VectorContentRule().identity in host.uploads.policy.allowed) is enabled
        with host.uploads.commands.engine.connect() as c:
            before = c.execute(text("SELECT count(*) FROM artifacts.encoding_profiles")).scalar_one()
        with TestClient(host.app()) as client:
            route = "/v1/representations/available-profiles"
            assert client.get(route).status_code == (401 if enabled else 404)
            response = client.get(route, headers={"Authorization": "Bearer " + "x" * 32})
            assert response.status_code == (200 if enabled else 404)
        with host.uploads.commands.engine.connect() as c:
            assert c.execute(text("SELECT count(*) FROM artifacts.encoding_profiles")).scalar_one() == before
    finally:
        host.close()
