"""Test-only marker sharing conflicts must be bounded and must not lose a real peer response."""

import importlib.util
import json
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location("replica_barrier_probe", Path(__file__).with_name("worker_process.py"))
barrier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(barrier)


def test_marker_retries_transient_sharing_conflict_without_losing_response(tmp_path, monkeypatch):
    marker = tmp_path / "worker.json"
    marker.write_text('{"stage":"claimed"}', encoding="utf-8")
    original = Path.replace
    attempts = []

    def replace(path, target):
        attempts.append(path)
        if len(attempts) == 1:
            raise PermissionError("sharing_conflict")
        return original(path, target)

    monkeypatch.setattr(Path, "replace", replace)
    packet = {"stage": "published", "response": {"artifact_id": "actual-response"}}
    barrier.publish_marker(marker, packet)
    assert len(attempts) == 2 and json.loads(marker.read_bytes()) == packet
    assert not marker.with_suffix(".tmp").exists()


def test_permanent_marker_failure_exits_at_bound(tmp_path, monkeypatch):
    clock = iter((0, 0.1, 2.1))
    monkeypatch.setattr(barrier.time, "monotonic", lambda: next(clock))
    monkeypatch.setattr(barrier.time, "sleep", lambda _seconds: None)

    def denied(_path, _target):
        raise PermissionError("permanent_conflict")

    monkeypatch.setattr(Path, "replace", denied)
    with pytest.raises(PermissionError, match="permanent_conflict"):
        barrier.publish_marker(tmp_path / "worker.json", {"stage": "published"})
