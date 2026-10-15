"""Separate Runtime processes reload immutable capacity and original receipts."""

import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request

from .test_bounded_admission import bounded
from ..lifecycle.test_claims import command, run_row


def test_restart_preserves_capacity_and_owner_preflight(graph_env, monkeypatch, tmp_path):
    e = graph_env.env
    _, _, receipt, _ = bounded(graph_env, monkeypatch)
    run = receipt.outcome.committed.object_id
    payload = {"run_id": run, "worker_id": e.principal.actor_id,
               "tool": graph_env.raw["body"]["nodes"][0]["tool"], "lease_seconds": 120}
    original = command(e, "runtime.claim", payload, "before-restart")
    no_work = command(e, "runtime.claim", payload, "capacity-receipt")
    fresh = command(e, "runtime.claim", payload, "after-restart")
    config = tmp_path / "runtime.json"
    config.write_text(json.dumps({"database_url_env": "AMPHORA_TEST_RUNTIME_DATABASE", "fixtures": [e.raw["payload"]],
        "principals": [{"token_env": "AMPHORA_TEST_RUNTIME_TOKEN", "actor_id": e.principal.actor_id,
                        "scope": e.principal.scope.model_dump(), "actions": sorted(e.principal.actions)}]}))
    environment = dict(os.environ, AMPHORA_TEST_RUNTIME_DATABASE=e.engine.url.render_as_string(hide_password=False),
                       AMPHORA_TEST_RUNTIME_TOKEN="x" * 32)
    cli = [sys.executable, "-I", "-m", "amphora_campaign_runtime"]
    flags = {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}
    for target, expected in (("0.68.0", 0), ("0.67.0", 2)):
        result = subprocess.run([*cli, "resource-preflight", "--config", str(config), "--target-release", target],
            env=environment, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=45, **flags)
        assert result.returncode == expected

    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    observed = []
    for generation in range(2):
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            port = listener.getsockname()[1]
        endpoint = f"http://127.0.0.1:{port}"
        process = subprocess.Popen([*cli, "serve", "--config", str(config), "--port", str(port)],
            env=environment, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **flags)
        try:
            deadline = time.monotonic() + 45
            while True:
                assert process.poll() is None, "Runtime exited before readiness"
                try:
                    with opener.open(endpoint + "/health", timeout=1) as response:
                        assert response.status == 200
                    break
                except (OSError, urllib.error.URLError):
                    assert time.monotonic() < deadline, "Runtime readiness deadline"
                    time.sleep(.1)

            def claim(request):
                http = urllib.request.Request(endpoint + "/v1/invocations/claim", request.canonical_bytes,
                    {"Authorization": "Bearer " + "x" * 32, "Content-Type": "application/json"}, method="POST")
                with opener.open(http, timeout=10) as response:
                    return json.loads(response.read())

            first = claim(original)
            capped = claim(no_work)
            assert first["outcome"]["status"] == "claimed"
            assert capped["outcome"]["status"] == "no_eligible_work"
            if generation:
                assert (first, capped) == observed[0]
                assert claim(fresh)["outcome"]["status"] == "no_eligible_work"
            observed.append((first, capped))
        finally:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=10)
    assert (run_row(e, run)["reserved"], run_row(e, run)["spent"]) == (1, 0)
