"""Test-only marker sharing conflicts must be bounded and must not lose a real peer response."""

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

spec = importlib.util.spec_from_file_location("replica_barrier_probe", Path(__file__).with_name("worker_process.py"))
barrier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(barrier)
reader_spec = importlib.util.spec_from_file_location("replica_barrier_reader", Path(__file__).with_name("processes.py"))
reader = importlib.util.module_from_spec(reader_spec)
reader_spec.loader.exec_module(reader)


def pending_worker(marker):
    worker = reader.Worker.__new__(reader.Worker)
    worker.marker = marker
    worker.child = SimpleNamespace(poll=lambda: None)
    return worker


def test_reader_retries_sharing_conflict_and_returns_original_packet(tmp_path, monkeypatch):
    marker = tmp_path / "barrier.json"
    marker.write_text('{"stage":"published","response":{"artifact_id":"original"}}', encoding="utf-8")
    original, attempts = Path.read_bytes, []

    def read(path):
        attempts.append(path)
        if len(attempts) == 1:
            raise PermissionError("sharing_conflict")
        return original(path)

    monkeypatch.setattr(Path, "read_bytes", read)
    assert pending_worker(marker).wait("published") == {"artifact_id": "original"}
    assert len(attempts) == 2


def test_reader_permanent_sharing_failure_remains_bounded(tmp_path, monkeypatch):
    clock = iter((0, 1, 21))
    monkeypatch.setattr(reader.time, "monotonic", lambda: next(clock))
    monkeypatch.setattr(reader.time, "sleep", lambda _seconds: None)

    def denied(path):
        raise PermissionError("permanent_conflict")

    monkeypatch.setattr(Path, "read_bytes", denied)
    with pytest.raises(AssertionError, match="Worker did not reach published"):
        pending_worker(tmp_path / "barrier.json").wait("published")


def test_reader_does_not_hide_malformed_marker(tmp_path):
    marker = tmp_path / "barrier.json"
    marker.write_text("malformed", encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        pending_worker(marker).wait("published")


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
