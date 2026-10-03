"""Explicit optional retrieval host; no backend connection, migration or registration."""

import json
from pathlib import Path

import pytest
from amphora_data_artifacts.hosting import Host
from fastapi.testclient import TestClient
from sqlalchemy import text

pytestmark = pytest.mark.postgres


@pytest.mark.parametrize(
    "setting",
    [
        None,
        {"endpoint": "http://127.0.0.1:1", "token_env": "QUERY_KEY"},
        False,
        {},
        {"endpoint": "http://127.0.0.1:1", "token_env": "bad-name"},
        {"endpoint": "http://127.0.0.1:1", "token_env": "QUERY_KEY", "namespace": "caller"},
    ],
)
def test_optional_retrieval_configuration_is_explicit_without_backend_dependency(
    artifact_database, tmp_path, monkeypatch, setting
):
    config = json.loads((Path(__file__).parents[2] / "config.example.json").read_text(encoding="utf-8"))
    config.update(storage_root=str(tmp_path))
    config["principals"][0]["actions"] = ["representation_read", "read"]
    if setting is not None:
        config["retrieval"] = setting
    path = tmp_path / "host.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    monkeypatch.setenv(
        "AMPHORA_ARTIFACT_DATABASE_URL", artifact_database.render_as_string(hide_password=False)
    )
    monkeypatch.setenv("AMPHORA_ARTIFACT_WORKER_TOKEN", "x" * 32)
    monkeypatch.setenv("QUERY_KEY", "q" * 32)
    valid = setting is None or (
        type(setting) is dict
        and set(setting) == {"endpoint", "token_env"}
        and setting["token_env"] == "QUERY_KEY"
    )
    if not valid:
        with pytest.raises(ValueError):
            Host.load(path)
        return
    host = Host.load(path)
    try:
        assert (host.retrieval_configuration is None) == (setting is None)
        assert host.representations_enabled is False
        with host.uploads.commands.engine.connect() as c:
            before = c.execute(text("SELECT count(*) FROM artifacts.index_generations")).scalar_one()
        with TestClient(host.app()) as client:
            response = client.get(
                "/v1/retrieval/queries/absent", headers={"Authorization": "Bearer " + "x" * 32}
            )
            assert response.status_code == 404
            if setting is not None:
                assert response.json()["detail"] == "retrieval_query_missing"
        with host.uploads.commands.engine.connect() as c:
            assert c.execute(text("SELECT count(*) FROM artifacts.index_generations")).scalar_one() == before
    finally:
        host.close()
