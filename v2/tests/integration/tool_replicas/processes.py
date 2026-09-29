"""Owned worker subprocesses with explicit observable stage barriers."""

import json
import os
import subprocess
import time
from pathlib import Path


class Worker:
    def __init__(self, e, http, tool, actor, *, lease_seconds=30):
        self.actor, self.tool = actor, tool
        self.marker = e.root / (actor + "-barrier.json")
        if self.marker.exists():
            self.marker.unlink()
        config = e.root / (actor + "-config.json")
        config.write_text(json.dumps({"actor_id": actor, "scope": e.scope, "run_id": e.active_run,
            "image_sha256": tool.lock["tool"]["image_sha256"], "lease_seconds": lease_seconds,
            "runtime": {"endpoint": e.runtime_relay.endpoint, "token_env": "WORKER_RUNTIME_TOKEN"},
            "artifacts": {"endpoint": e.artifact_relay.endpoint, "token_env": "WORKER_ARTIFACT_TOKEN"}}), encoding="utf-8")
        env = dict(http.isolated_env(), WORKER_RUNTIME_TOKEN=e.tokens[actor], WORKER_ARTIFACT_TOKEN=e.tokens[actor])
        self.child = subprocess.Popen([tool.python, "-I", str(Path(__file__).with_name("worker_process.py")),
            tool.module, str(config), str(self.marker)], cwd=e.root, env=env,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        e.resources.append(self)

    def wait(self, stage):
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            try:
                value = json.loads(self.marker.read_bytes())
            except (FileNotFoundError, PermissionError):
                # Atomic writer replacement can briefly deny a Windows reader too.
                value = None
            if value is not None:
                if value["stage"] == stage:
                    return value["response"]
            if self.child.poll() is not None:
                _stdout, stderr = self.child.communicate(timeout=5)
                raise AssertionError("Worker exited before " + stage + ": " + stderr[-500:])
            time.sleep(0.02)
        raise AssertionError("Worker did not reach " + stage)

    def resume(self):
        self.child.stdin.write("continue\n")
        self.child.stdin.flush()

    def result(self):
        stdout, stderr = self.child.communicate(timeout=30)
        assert self.child.returncode == 0, "Worker failure: " + stderr[-500:] + stdout[-200:]
        return json.loads(stdout)

    def close(self):
        if self.child.poll() is None:
            if os.name == "nt":
                subprocess.run(["taskkill", "/PID", str(self.child.pid), "/T", "/F"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10,
                    creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                self.child.kill()
        self.child.communicate(timeout=10)
