"""Bounded real HTTP owner process support for acquisition interruption proofs."""

import json
import os
import queue
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path


class OwnerProcess:
    def __init__(self, config, environment, fault=None, python=None):
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            self.port = listener.getsockname()[1]
        self.events = queue.Queue()
        python = python or sys.executable
        args = ([python, "-I", str(Path(__file__).with_name("fault_host.py"))] if fault else
                [python, "-I", "-m", "amphora_data_artifacts", "serve", "--config", str(config), "--port", str(self.port)])
        self.process = subprocess.Popen(args, env=environment, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, text=True, encoding="utf-8", creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))

        def output():
            for line in self.process.stdout:
                self.events.put(json.loads(line))

        self.output_thread = threading.Thread(target=output, daemon=True)
        self.output_thread.start()
        if fault:
            self.process.stdin.write(json.dumps({"config": str(config), "port": self.port, "fault": fault}) + "\n")
            self.process.stdin.flush()
        try:
            deadline = time.monotonic() + 15
            while True:
                if self.process.poll() is not None:
                    raise RuntimeError("Owner exited before readiness")
                try:
                    assert self.request("/ready")["ready"]
                    break
                except urllib.error.URLError:
                    if time.monotonic() >= deadline:
                        raise RuntimeError("Owner readiness timed out") from None
                    time.sleep(0.05)
        except BaseException:
            self.stop()
            raise

    def request(self, route, body=None):
        request = urllib.request.Request(f"http://127.0.0.1:{self.port}" + route,
            data=None if body is None else json.dumps(body).encode("utf-8"),
            headers={"Authorization": "Bearer " + "k" * 32, "Content-Type": "application/json"})
        with urllib.request.urlopen(request, timeout=15) as response:
            return json.load(response)

    def stop(self):
        if self.process.poll() is None:
            self.process.kill()
            self.process.wait(timeout=10)
        self.output_thread.join(timeout=5)
        self.process.stdin.close()
        self.process.stdout.close()


def configuration(e, tmp_path):
    profile = next(identity for identity in e.env.uploads.policy.allowed if identity[0] == "application/octet-stream")
    config = {"database_url_env": "FAULT_DATABASE", "storage_root": str(e.env.storage.root), "acquisition": True,
              "principals": [{"token_env": "FAULT_TOKEN", "actor_id": "worker", "scope": e.principal.scope.model_dump(),
                              "actions": ["read", "acquire", "source_history"]}],
              "profiles": [dict(zip(("media_type", "schema_id", "version", "sha256"), profile, strict=True))]}
    path = tmp_path / "owner.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    environment = dict(os.environ, FAULT_DATABASE=e.env.engine.url.render_as_string(hide_password=False), FAULT_TOKEN="k" * 32)
    return path, environment
