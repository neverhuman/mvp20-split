"""Configured client construction has no implicit credential or database discovery."""

import json

import pytest
from amphora_tool_protocol import PureToolWorker, WorkerConfig, run_worker
from pydantic import ValidationError


def configuration():
    return {"actor_id": "worker", "scope": {"tenant_id": "fixture", "project_id": "config"},
        "run_id": "admitted-run", "image_sha256": "a" * 64,
        "runtime": {"endpoint": "http://127.0.0.1:8080", "token_env": "TEST_RUNTIME_TOKEN"},
        "artifacts": {"endpoint": "http://127.0.0.1:8081", "token_env": "TEST_ARTIFACT_TOKEN"}}


@pytest.mark.parametrize("change", [{"lease_seconds": 0}, {"lease_seconds": True},
    {"max_clock_skew_seconds": -1}, {"max_clock_skew_seconds": 6}, {"max_clock_skew_seconds": float("nan")},
    {"database_url": "must-not-be-used"}, {"image_sha256": "not-an-image"},
    {"runtime": {"endpoint": "http://127.0.0.1", "token": "inline-secret-forbidden"}}])
def test_invalid_launch_configuration_fails_before_any_io(change):
    with pytest.raises(ValidationError):
        WorkerConfig.model_validate_json(json.dumps({**configuration(), **change}))


def test_explicit_public_clients_are_constructed_from_named_credentials(tmp_path, monkeypatch):
    import amphora_tool_protocol.worker as module
    config = configuration()
    path = tmp_path / "worker.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    monkeypatch.setenv("TEST_RUNTIME_TOKEN", "a" * 32)
    monkeypatch.setenv("TEST_ARTIFACT_TOKEN", "b" * 32)
    seen = []
    def factory(runtime, artifacts, descriptor, compute, **kwargs):
        assert runtime.identity == artifacts.identity
        assert runtime.identity.actor_id == "worker"
        assert descriptor == "selected-descriptor"
        assert kwargs == {"lease_seconds": 30, "skew_seconds": 1.0}
        seen.append((runtime.transport.endpoint, artifacts.transport.endpoint))
        class Worker:
            def run_once(self, run_id):
                assert run_id == "admitted-run"
                return {"status": "no_eligible_work"}
        return Worker()
    monkeypatch.setattr(module, "PureToolWorker", factory)
    assert run_worker(path, lambda digest: "selected-descriptor" if digest == "a" * 64 else None,
                      lambda _body: b"{}") == {"status": "no_eligible_work"}
    assert seen == [("http://127.0.0.1:8080", "http://127.0.0.1:8081")]
    assert PureToolWorker is not factory  # The public class is not replaced outside this test.
