"""Actual independently installed peers; only authenticated public observations."""

import hashlib

# -I excludes the checkout: explicitly load this test-owned stdlib harness only.
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace

spec = importlib.util.spec_from_file_location("paired_support", Path(__file__).with_name("paired_support.py"))
support = importlib.util.module_from_spec(spec)
spec.loader.exec_module(support)


def main():
    scope = {"tenant_id": "integrated-acceptance", "project_id": uuid.uuid4().hex}
    tokens = {actor: uuid.uuid4().hex for actor in ("admin", "worker", "worker2", "runtime", "artifact", "other")}
    schema = {"schema_id": "fixture.object", "version": "1",
              "sha256": hashlib.sha256(b'{"type":"object"}').hexdigest()}
    tests = Path(__file__).absolute().parents[1]

    def principal(actor, actions, project=None):
        return {"actor_id": actor, "scope": scope if project is None else {**scope, "project_id": project},
                "token_env": "TOKEN_" + actor.upper(), "actions": actions}

    def command(family, payload, actor="admin"):
        return {"identity": {"command_family": family, "command_id": uuid.uuid4().hex,
                             "actor_id": actor, "scope": scope}, "payload": payload}

    with tempfile.TemporaryDirectory(prefix="amphora-paired-") as directory:
        root = Path(directory)
        storage = root / "bytes"
        storage.mkdir()
        runtime_port = support.free_port()
        endpoint = f"http://127.0.0.1:{runtime_port}"
        artifact_env = dict(support.isolated_env(), DATABASE_URL=os.environ["AMPHORA_ARTIFACT_DATABASE_URL"],
                            **{"TOKEN_" + a.upper(): tokens[a] for a in ("worker", "runtime", "artifact", "other")})
        runtime_env = dict(support.isolated_env(), DATABASE_URL=os.environ["AMPHORA_RUNTIME_DATABASE_URL"],
                           CURSOR_KEY=uuid.uuid4().hex, **{"TOKEN_" + a.upper(): t for a, t in tokens.items()})
        artifact_config = root / "artifact.json"
        artifact_config.write_text(json.dumps({"database_url_env": "DATABASE_URL", "storage_root": str(storage),
            "principals": [principal("worker", ["upload", "finalize", "read"]), principal("runtime", ["retention"]),
                           principal("other", ["retention"], "other")],
            "profiles": [{"media_type": "application/json", **schema}],
            "runtime": {"owner": "runtime", "endpoint": endpoint + "/v1/completion-intents/outcome",
                        "token_env": "TOKEN_ARTIFACT"}}), encoding="utf-8")
        artifact = support.Process(sys.argv[1], "amphora_data_artifacts", artifact_config, artifact_env,
                                   root, support.free_port())
        runtime = proxy = None
        active_run = None
        try:
            artifact.ready(tokens["worker"])

            def art(path, payload=None, actor="worker"):
                return support.decoded(artifact.endpoint, path, tokens[actor], payload)

            def publish(value):
                body = json.dumps({"value": value}).encode()
                content = {"sha256": hashlib.sha256(body).hexdigest(), "size_bytes": len(body),
                           "media_type": "application/json", "schema_ref": schema}
                upload = art("/v1/uploads", command("artifacts.begin_upload", {"content": content}, "worker"))
                assert support.request(artifact.endpoint, "/v1/uploads/" + upload["upload_id"] + "/content",
                                       tokens["worker"], body, "PUT")[0] == 200
                ref = art("/v1/artifacts/finalize", command("artifacts.finalize",
                          {"upload_id": upload["upload_id"], "content": content}, "worker"))["artifact"]
                assert support.request(artifact.endpoint, "/v1/artifacts/" + ref["artifact_id"] + "/content",
                                       tokens["worker"]) == (200, body)
                return ref

            input_ref, output_ref = publish(1), publish(2)
            definition = json.loads((tests / "fixtures/prepared-run.json").read_text())["payload"]
            invocation = definition["invocations"][0]
            invocation["timeout_seconds"] = 120
            invocation["inputs"][0]["artifact"] = input_ref
            port = {"name": "value", "schema_ref": schema, "representation": "synthetic", "unit": "1"}
            descriptor = {"schema_version": "1", "binding": invocation["tool"], "purpose": "Synthetic paired acceptance",
                          "applicability": ["test"], "inputs": [port], "outputs": [port], "side_effects": "pure",
                          "checkpoint_schema": schema}
            branches = json.loads(json.dumps(definition))
            branches["fixture_id"] = "synthetic-branches"
            second = json.loads(json.dumps(invocation))
            second.update(node_id="n2", activation_id="iteration-1.n2", invocation_id="i2")
            branches["invocations"].append(second)
            proxy = support.ReservationProxy(artifact.endpoint)
            config = root / "runtime.json"
            config.write_text(json.dumps({"database_url_env": "DATABASE_URL", "fixtures": [definition, branches],
                "principals": [principal("admin", ["admit", "cancel", "read", "inspect_receipts", "maintain", "deliver"]),
                               principal("worker", ["claim", "renew", "complete", "read"]),
                               principal("worker2", ["claim", "renew", "complete", "read"]), principal("artifact", ["outcome"])],
                "tools": [descriptor], "artifacts": {"runtime_owner": "runtime", "reserve_endpoint": proxy.endpoint + "/v1/reservations",
                "token_env": "TOKEN_RUNTIME"}, "delivery": {"lease_seconds": 2},
                "inspection": {"cursor_key_env": "CURSOR_KEY"}}), encoding="utf-8")
            runtime = support.Process(sys.executable, "amphora_campaign_runtime", config, runtime_env, root, runtime_port)
            runtime.ready(tokens["admin"])

            def rt(path, payload=None, actor="admin"):
                return support.decoded(endpoint, path, tokens[actor], payload)

            def worker(path, cmd):
                result = subprocess.run([sys.executable, "-I", str(tests / "acceptance/http_worker.py")],
                    input=json.dumps({"endpoint": endpoint, "token": tokens[cmd["identity"]["actor_id"]], "path": path, "command": cmd}) + "\n",
                    env=support.isolated_env(), cwd=root, text=True, capture_output=True, timeout=15)
                assert result.returncode == 0, "HTTP-only worker failed"
                reply = json.loads(result.stdout)
                assert reply["status"] == 200, reply
                return reply["body"]

            def start(fixture=None):
                nonlocal active_run
                admitted = rt("/v1/fixture-runs", command("runtime.admit_fixture", fixture or definition))
                run = admitted["outcome"]["committed"]["object_id"]
                active_run = run
                claimed = worker("/v1/invocations/claim", command("runtime.claim", {
                    "run_id": run, "worker_id": "worker", "tool": invocation["tool"], "lease_seconds": 60}, "worker"))
                work = claimed["outcome"]["invocation"]
                completion = {k: work[k] for k in ("invocation_id", "attempt_id", "fence")}
                completion.update(schema_version="1", outcome={"status": "succeeded", "outputs": [
                    {"port": "value", "artifact": output_ref}], "checkpoint": output_ref})
                return run, command("runtime.complete", {"run_id": run, "completion": completion,
                                                        "expected_checkpoint_revision": 0}, "worker")

            def delivery_process():
                return subprocess.Popen([sys.executable, "-I", "-m", "amphora_campaign_runtime", "deliver",
                    "--config", str(config), "--actor", "admin", "--tenant", scope["tenant_id"], "--project", scope["project_id"],
                    "--limit", "100", "--time-budget", "20"], env=runtime_env, cwd=root,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            def deliver():
                child = delivery_process()
                try:
                    stdout, _ = child.communicate(timeout=30)
                    assert child.returncode == 0, "Installed delivery process failed"
                    return json.loads(stdout)
                finally:
                    if child.poll() is None:
                        child.kill()
                        child.communicate(timeout=10)

            if len(sys.argv) > 2:
                case_spec = importlib.util.spec_from_file_location("recovery_cases", Path(__file__).with_name("recovery_cases.py"))
                cases = importlib.util.module_from_spec(case_spec)
                case_spec.loader.exec_module(cases)
                cases.exercise(SimpleNamespace(scope=scope, tokens=tokens, schema=schema, command=command,
                    artifact=artifact, runtime=runtime, proxy=proxy, art=art, rt=rt, start=start, deliver=deliver,
                    worker=worker, output_ref=output_ref, support=support, fault_script=Path(sys.argv[2]),
                    definition=definition, branches=branches, delivery_process=delivery_process,
                    http_worker=tests / "acceptance/http_worker.py",
                    evidence_dir=Path(sys.argv[3]), packages=json.loads(os.environ["AMPHORA_TESTED_PACKAGES"])))
                return

            active_run, complete = start()
            receipt = worker("/v1/invocations/complete", complete)
            assert receipt["outcome"]["status"] == "accepted", receipt
            assert worker("/v1/invocations/complete", complete) == receipt
            cmd_id = complete["identity"]["command_id"]
            assert rt("/v1/commands/runtime.complete/" + cmd_id + "?actor_id=worker") == receipt
            report_id = receipt["outcome"]["committed"]["object_id"]
            report = rt(f"/v1/runs/{active_run}/completions/{report_id}")
            assert report["canonical_result"] is True
            reservations = report["retention_reservation_ids"]
            assert len(reservations) == 2
            for reservation in reservations:
                path = "/v1/reservations/" + reservation
                assert art(path, actor="runtime")["outcome"]["status"] == "reserved"
                assert support.request(artifact.endpoint, path, tokens["other"])[0] == 404
            assert deliver()["acknowledged"] >= 2
            for reservation in reservations:
                retained = art("/v1/reservations/" + reservation, actor="runtime")["outcome"]
                assert retained["status"] == "confirmed"
                proof = rt("/v1/completion-intents/outcome", retained["binding"], "artifact")
                assert proof["proof"]["status"] == "committed"
            snapshot = rt("/v1/runs/" + active_run)
            assert snapshot["status"] == "completed" and snapshot["budget"]["reserved"] == 0
            assert snapshot["budget"]["spent"] == 1
            assert rt(f"/v1/runs/{active_run}/audit?limit=2")["next_cursor"] is not None

            active_run, complete = start()
            offset = len(proxy.receipts)
            proxy.hold_next = True
            with ThreadPoolExecutor(max_workers=1) as pool:
                pending = pool.submit(worker, "/v1/invocations/complete", complete)
                try:
                    assert proxy.arrived.wait(timeout=10), "Reservation barrier not reached"
                    cancelled = rt("/v1/runs/cancel", command("runtime.cancel", {"run_id": active_run, "reason_code": "probe"}))
                    assert cancelled["outcome"]["status"] == "accepted"
                    held = proxy.receipts[offset]["outcome"]["binding"]
                    released = art("/v1/reservations/reconcile", command("artifacts.reconcile",
                        {"reservation_id": held["reservation_id"]}, "runtime"), "runtime")
                    assert released["outcome"]["status"] == "released"
                finally:
                    proxy.release.set()
                rejected = pending.result(timeout=15)
            assert rejected["outcome"]["status"] == "rejected", rejected
            assert worker("/v1/invocations/complete", complete) == rejected
            deliver()
            for acquired in proxy.receipts[offset:]:
                reservation = acquired["outcome"]["binding"]["reservation_id"]
                assert art("/v1/reservations/" + reservation, actor="runtime")["outcome"]["status"] == "released"
            snapshot = rt("/v1/runs/" + active_run)
            assert snapshot["status"] == "cancelled" and snapshot["budget"]["reserved"] == 0
            assert snapshot["budget"]["spent"] == 1
        finally:
            if proxy is not None:
                proxy.release.set()
            if runtime is not None:
                try:
                    if active_run is not None and runtime.child.poll() is None:
                        support.request(endpoint, "/v1/runs/cancel", tokens["admin"],
                            command("runtime.cancel", {"run_id": active_run, "reason_code": "cleanup"}))
                finally:
                    runtime.close()
            if proxy is not None:
                proxy.close()
            artifact.close()
    print("Installed paired services: acceptance/confirmation, cancellation/release race, original replay and isolated HTTP workers passed")


if __name__ == "__main__":
    main()
