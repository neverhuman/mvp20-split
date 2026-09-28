"""Installed runtime and HTTP-only worker death/reclaim; no direct database access."""

import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import ProxyHandler, Request, build_opener


def stop(child):
    if child.poll() is None:
        child.kill()
    child.communicate(timeout=10)


def main():
    tests = Path(__file__).absolute().parents[1]
    definition = json.loads((tests / "fixtures/prepared-run.json").read_text())["payload"]
    scope = {"tenant_id": "runtime-acceptance", "project_id": uuid.uuid4().hex}
    definition["invocations"][0]["timeout_seconds"] = 120
    for invocation in definition["invocations"]:
        for binding in invocation["inputs"]:
            binding["artifact"]["scope"] = scope
    env = dict(os.environ)
    principals = []
    for actor, actions in [("admin", ["admit", "cancel", "revoke", "read"]),
                           ("worker-1", ["claim", "renew"]), ("worker-2", ["claim", "renew"]),
                           ("other", ["read"])]:
        key = "AMPHORA_PROBE_" + actor.upper().replace("-", "_")
        env[key] = uuid.uuid4().hex
        principals.append({"actor_id": actor, "token_env": key, "actions": actions,
                           "scope": scope if actor != "other" else {**scope, "project_id": "other"}})
    worker_env = {k: v for k, v in os.environ.items() if k.upper() in
                  {"SYSTEMROOT", "WINDIR", "TEMP", "TMP", "PATH", "COMSPEC"}}
    with tempfile.TemporaryDirectory(prefix="amphora-runtime-acceptance-") as directory:
        root = Path(directory)
        config = root / "runtime.json"
        config.write_text(json.dumps({"database_url_env": "AMPHORA_PROBE_DATABASE_URL",
                                     "principals": principals, "fixtures": [definition]}), encoding="utf-8")
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        endpoint = f"http://127.0.0.1:{port}"
        host = subprocess.Popen([sys.executable, "-I", "-m", "amphora_campaign_runtime", "serve",
            "--config", str(config), "--port", str(port)], env=env, cwd=root,
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        opener = build_opener(ProxyHandler({}))

        def token(actor):
            return env["AMPHORA_PROBE_" + actor.upper().replace("-", "_")]

        def request(path, data=None, actor="admin", credential=None):
            try:
                with opener.open(Request(endpoint + path, data=None if data is None else json.dumps(data).encode(),
                    headers={"Authorization": "Bearer " + (credential or token(actor)),
                             "Content-Type": "application/json"}), timeout=8) as response:
                    return response.status, json.loads(response.read())
            except HTTPError as error:
                return error.code, json.loads(error.read())

        def command(family, payload, actor="admin"):
            return {"identity": {"command_family": family, "command_id": uuid.uuid4().hex,
                                 "actor_id": actor, "scope": scope}, "payload": payload}

        def worker(actor, path, cmd, stay=False):
            child = subprocess.Popen([sys.executable, "-I", str(tests / "acceptance/http_worker.py")],
                env=worker_env, cwd=root, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, text=True)
            try:
                child.stdin.write(json.dumps({"endpoint": endpoint, "token": token(actor), "path": path,
                                              "command": cmd, "stay": stay}) + "\n")
                child.stdin.flush()
                pool = ThreadPoolExecutor(max_workers=1)
                try:
                    line = pool.submit(child.stdout.readline).result(timeout=12)
                    result = json.loads(line)
                    if stay:
                        assert child.poll() is None
                    return result
                finally:
                    stop(child)
                    pool.shutdown(wait=True)
            finally:
                if child.poll() is None:
                    stop(child)

        run = None
        try:
            deadline = time.monotonic() + 30
            while True:
                try:
                    if request("/ready")[0] == 200:
                        break
                except URLError:
                    pass
                if host.poll() is not None or time.monotonic() >= deadline:
                    raise AssertionError("Installed runtime did not become ready")
                time.sleep(0.1)
            health = request("/health")[1]
            assert health["mode"] == "fixture_lifecycle" and health["execution_available"] is False
            admission = command("runtime.admit_fixture", definition)
            status, receipt = request("/v1/fixture-runs", admission)
            assert status == 200 and receipt["outcome"]["status"] == "accepted"
            run = receipt["outcome"]["committed"]["object_id"]
            assert request("/v1/fixture-runs", admission)[1] == receipt
            path = "/v1/runs/" + run
            assert request(path, actor="other")[0] == 404
            assert request(path, credential="invalid")[0] == 401
            assert request(path, actor="worker-1")[0] == 403
            tool = definition["invocations"][0]["tool"]
            first_cmd = command("runtime.claim", {"run_id": run, "worker_id": "worker-1",
                                                   "tool": tool, "lease_seconds": 2}, "worker-1")
            first = worker("worker-1", "/v1/invocations/claim", first_cmd, stay=True)
            assert first["status"] == 200 and first["body"]["outcome"]["status"] == "claimed"
            invocation = first["body"]["outcome"]["invocation"]
            expiry = datetime.fromisoformat(first["body"]["outcome"]["lease_expires_at"])
            time.sleep(max(0, (expiry - datetime.now(UTC)).total_seconds()) + 0.05)
            second_cmd = command("runtime.claim", {"run_id": run, "worker_id": "worker-2",
                                                    "tool": tool, "lease_seconds": 20}, "worker-2")
            second = worker("worker-2", "/v1/invocations/claim", second_cmd)
            assert second["status"] == 200 and second["body"]["outcome"]["status"] == "claimed"
            successor = second["body"]["outcome"]["invocation"]
            assert successor["fence"] == invocation["fence"] + 1
            assert successor["attempt_id"] != invocation["attempt_id"]
            assert request("/v1/invocations/claim", first_cmd, "worker-1")[1] == first["body"]

            def renew(inv, actor):
                attempt = {k: inv[k] for k in ("run_id", "invocation_id", "attempt_id", "fence")}
                return request("/v1/attempts/renew", command("runtime.renew",
                    {"attempt": attempt, "lease_seconds": 30}, actor), actor)[1]["outcome"]

            assert renew(invocation, "worker-1")["reason_code"] == "stale_attempt"
            assert renew(successor, "worker-2")["status"] == "accepted"
            snapshot = request(path)[1]
            assert snapshot["budget"] == {"limit": 5, "available": 3, "reserved": 1, "spent": 1}
            assert snapshot["activations"][0]["latest_attempt"]["attempt_id"] == successor["attempt_id"]
            revoke = command("runtime.revoke_worker", {"worker_id": "worker-2", "reason_code": "probe"})
            assert request("/v1/workers/revoke", revoke)[1]["outcome"]["status"] == "accepted"
            assert renew(successor, "worker-2")["status"] == "rejected"
            cancellation = command("runtime.cancel", {"run_id": run, "reason_code": "probe"})
            cancelled = request("/v1/runs/cancel", cancellation)[1]
            assert cancelled["outcome"]["status"] == "accepted"
            assert request("/v1/runs/cancel", cancellation)[1] == cancelled
            final = request(path)[1]
            assert final["status"] == "cancelled"
            assert final["budget"] == {"limit": 5, "available": 3, "reserved": 0, "spent": 2}
        finally:
            try:
                if run is not None and host.poll() is None:
                    request("/v1/runs/cancel", command("runtime.cancel", {"run_id": run, "reason_code": "cleanup"}))
            finally:
                stop(host)
    print("Installed runtime: HTTP-only worker death/reclaim, stale fencing, scoped reads, revocation and cancellation passed")


if __name__ == "__main__":
    main()
