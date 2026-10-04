"""Bounded hidden fault process and actual CLI replacement using the same HTTP client."""

import json
import os
import queue
import socket
import subprocess
import threading
import time
import urllib.error
from pathlib import Path

from ...representations.http_support import HttpOwner


class FaultOwner(HttpOwner):
    def __init__(self, python, config, environment, stage):
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            self.port = listener.getsockname()[1]
        self.token = "k" * 32
        self.events = queue.Queue()
        self.process = subprocess.Popen(
            [python, "-I", str(Path(__file__).absolute().with_name("fault_host.py"))],
            env=environment,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )

        def output():
            for line in self.process.stdout:
                self.events.put(json.loads(line))

        self.reader = threading.Thread(target=output, daemon=True)
        self.reader.start()
        self.process.stdin.write(
            json.dumps({"config": str(config), "port": self.port, "stage": stage}) + "\n"
        )
        self.process.stdin.flush()
        try:
            deadline = time.monotonic() + 60
            while time.monotonic() < deadline:
                if self.process.poll() is not None:
                    raise RuntimeError("Retrieval fault owner exited before readiness")
                try:
                    if self.call("GET", "/ready").status == 200:
                        break
                except urllib.error.URLError:
                    pass
                time.sleep(0.05)
            else:
                raise RuntimeError("Retrieval fault owner readiness deadline")
        except BaseException:
            self.kill()
            raise

    def release(self):
        self.process.stdin.write("release\n")
        self.process.stdin.flush()

    def kill(self):
        if self.process.poll() is None:
            self.process.kill()
            self.process.wait(timeout=10)
        self.reader.join(timeout=5)
        self.process.stdin.close()
        self.process.stdout.close()


def configuration(e, state, tmp_path):
    profile = next(
        item for item in e.ingestion.env.uploads.policy.allowed if item[0] == "application/octet-stream"
    )
    body = {
        "database_url_env": "FAULT_DATABASE",
        "storage_root": str(e.ingestion.env.storage.root),
        "profiles": [dict(zip(("media_type", "schema_id", "version", "sha256"), profile, strict=True))],
        "retrieval": {"endpoint": state["endpoint"], "token_env": "FAULT_QDRANT"},
        "principals": [
            {
                "token_env": "FAULT_TOKEN",
                "actor_id": e.p.actor_id,
                "scope": e.p.scope.model_dump(mode="json"),
                "actions": sorted(e.p.actions),
            }
        ],
    }
    path = tmp_path / "owner.json"
    path.write_text(json.dumps(body), encoding="utf-8")
    environment = {
        name: os.environ[name] for name in ("PATH", "SYSTEMROOT", "TEMP", "TMP") if name in os.environ
    }
    environment.update(
        PYTHONUTF8="1",
        FAULT_DATABASE=e.engine.url.render_as_string(hide_password=False),
        FAULT_TOKEN="k" * 32,
        FAULT_QDRANT=state["api_key"],
    )
    return path, environment
