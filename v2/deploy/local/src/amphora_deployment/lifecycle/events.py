"""Allowlisted metadata-only events; bounded files without child output ingestion."""

from datetime import datetime
import json
from pathlib import Path
import threading

from ..installation import OWNERS
from ..profile import require


class LifecycleEvents:
    def __init__(self, directory, *, limit=65536):
        require(type(limit) is int and 1024 <= limit <= 1048576, "lifecycle_log_limit")
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.limit = limit
        self.lock = threading.Lock()

    def emit(self, owner, event, *, pid=None, exit_code=None):
        require(owner in OWNERS or owner == "gateway", "lifecycle_event_owner")
        require(event in {"starting", "started", "exited", "force_stopped", "start_failed", "draining", "drained"}, "lifecycle_event_kind")
        require(pid is None or type(pid) is int and 1 <= pid <= 0xffffffff, "lifecycle_event_pid")
        require(exit_code is None or type(exit_code) is int and -(2**31) <= exit_code <= 0xffffffff, "lifecycle_event_exit")
        record = {"at": datetime.now().astimezone().isoformat(timespec="seconds"), "owner": owner,
                  "event": event, "pid": pid, "exit_code": exit_code}
        raw = (json.dumps(record, separators=(",", ":")) + "\n").encode()
        path = self.directory / "lifecycle.jsonl"
        with self.lock:
            if path.exists() and path.stat().st_size + len(raw) > self.limit:
                path.replace(self.directory / "lifecycle.previous.jsonl")
            with path.open("ab") as stream:
                stream.write(raw)
