"""Actual installed Data/Runtime HTTP retention with lost response and replacement.

Synthetic protocol proof only. Uses a new labeled PostgreSQL fixture and removes
its container in finally; no demo state, scientific tools or provider calls.
"""

import argparse
import hashlib
import http.client
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import threading
import time
import uuid
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from sqlalchemy import URL
from amphora_contracts_tools import ReleaseDescriptor


ROOT = Path(__file__).absolute().parents[1]


def write(path, value):
    path.write_text(json.dumps(value, indent=2), encoding="utf-8")


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def request(port, path, body=None, *, method=None):
    raw = None if body is None else json.dumps(body).encode()
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=20)
    try:
        connection.request(method or ("GET" if body is None else "POST"), path, raw,
            {"Authorization": "Bearer " + "q" * 32, "Content-Type": "application/json"})
        response = connection.getresponse()
        return response.status, json.loads(response.read())
    finally:
        connection.close()


def verify(output, data_python, runtime_python, population_python=None, *, population_only=False, population_slice=False, population_method=None, inspect_inputs=False, population_collect=False, collection_case="normal", population_fitness=False, population_select=False, population_propose=False, successor_tight=False, successor_consume=False, successor_fitness=False, successor_failure=False, successor_select=False):
    if successor_select:
        successor_fitness = True
    if successor_failure:
        successor_fitness = True
    if successor_fitness:
        successor_consume = True
    if successor_consume:
        assert collection_case == "normal" and not successor_tight
        population_propose = True
    if population_propose:
        population_select = True
    if population_select:
        population_fitness = True
    if population_fitness:
        population_collect = True
    if population_collect:
        population_method = population_method or "evaluate-squares"
    if population_method is not None:
        population_slice = True
    if (population_only or population_slice) and population_python is None:
        raise ValueError("Population-only probe requires its isolated interpreter")
    output = output.absolute()
    output.mkdir(parents=True, exist_ok=False)
    os.environ["AMPHORA_TEST_POSTGRES_STATE"] = str(output / "postgres-fixture.json")
    import postgres_fixture as fixture
    processes, streams = {}, []
    proxy = proxy_thread = None
    scope = {"tenant_id": "retention-qualification", "project_id": uuid.uuid4().hex}
    data_port, runtime_port, proxy_port = (free_port() for _ in range(3))
    actor = "runtime"

    def command(family, payload):
        return {"identity": {"command_family": family, "command_id": uuid.uuid4().hex,
            "actor_id": actor, "scope": scope}, "payload": payload}

    def call(port, path, body=None):
        status, value = request(port, path, body)
        assert status == 200, (path, status, value)
        return value

    def stop(owner):
        process = processes.pop(owner, None)
        if process is not None and process.poll() is None:
            process.terminate()
            process.wait(timeout=30)

    def start(owner, python, port, environment):
        stream = (output / (owner + "-" + uuid.uuid4().hex[:6] + ".log")).open("wb")
        streams.append(stream)
        ready = output / (owner + "-ready.json")
        if ready.exists():
            ready.unlink()
        process = subprocess.Popen([str(python), "-I", str(ROOT / "dev/retention_owner_process.py"),
            owner, str(output / (owner + ".json")), str(port), str(ready)], env=environment,
            stdout=stream, stderr=stream, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        processes[owner] = process
        deadline = time.monotonic() + 180
        while time.monotonic() < deadline:
            assert process.poll() is None, f"{owner} exited; inspect owner log"
            try:
                if request(port, "/ready")[0] == 200:
                    return json.loads(ready.read_bytes())
            except (OSError, ValueError):
                pass
            time.sleep(.25)
        raise RuntimeError(owner + " readiness timeout")

    try:
        fixture.start()
        fixture.verify()
        state = fixture.owned_state()
        host, port = state["endpoint"].split(":")
        environment = {k: v for k, v in os.environ.items() if not k.startswith("AMPHORA_")}
        environment["QUAL_TOKEN"] = "q" * 32
        environment["QUAL_DATA_PYTHON"] = str(data_python)
        environment["QUAL_RUNTIME_PYTHON"] = str(runtime_python)
        for owner, python, role, migration in (
            ("data", data_python, "artifact", "amphora_data_artifacts.persistence.migrate"),
            ("runtime", runtime_python, "runtime", "amphora_campaign_runtime.persistence.migrate")):
            url = URL.create("postgresql+psycopg", username=role + "_migrator", password=state["password"],
                             host=host, port=int(port), database=state["database"])
            env = dict(environment)
            env["AMPHORA_" + ("ARTIFACT" if owner == "data" else "RUNTIME") + "_MIGRATION_URL"] = url.render_as_string(hide_password=False)
            result = subprocess.run([str(python), "-I", "-m", migration], env=env,
                capture_output=True, timeout=180)
            (output / (owner + "-migration.log")).write_bytes(result.stdout + result.stderr)
            assert result.returncode == 0, "Owner migration failed"
            environment["QUAL_" + owner.upper() + "_URL"] = url.set(username=role + "_service").render_as_string(hide_password=False)

        cases = json.loads((ROOT / "contracts/fixtures/v2/executable_cases.json").read_bytes())
        definition = next(c["payload"] for c in cases if c["model"] == "campaigns.definition" and c["valid"])
        definition["scope"] = scope
        definition["body"]["nodes"][0]["timeout_seconds"] = 300
        lock = next(c["payload"] for c in cases if c["model"] == "campaigns.execution-plan" and c["valid"])["document"]["lock"]["tools"][0]
        write(output / "graph.json", definition)
        materials = ROOT / "services/campaign_runtime/tests/fixtures/compiler"
        # Explicit synthetic restart fixture variant; retain a matching descriptor lock.
        descriptor = json.loads((materials / "numeric-release.json").read_bytes())
        descriptor["resources"]["timeout_seconds"] = 300
        descriptor = ReleaseDescriptor.model_validate_json(json.dumps(descriptor)).model_dump(mode="json")
        lock["descriptor_sha256"] = hashlib.sha256(json.dumps(
            {"profile": "amphora-tool-release-v1", "descriptor": descriptor},
            sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode()).hexdigest()
        write(output / "release.json", descriptor)
        profiles, schemas = [], []
        for kind in ("input", "output"):
            ref = lock[kind + "_schemas"][0]["schema_ref"]
            shutil.copyfile(materials / (kind + ".json"), output / (kind + ".json"))
            profiles.append({"media_type": "application/json", **ref, "schema_path": kind + ".json"})
            schemas.append({"schema_ref": ref, "path": kind + ".json"})
        principal = {"actor_id": actor, "scope": scope, "token_env": "QUAL_TOKEN"}
        (output / "bytes").mkdir()
        write(output / "data.json", {"database_url_env": "QUAL_DATA_URL", "storage_root": str(output / "bytes"),
            "principals": [{**principal, "actions": ["upload", "finalize", "retention", "read"]}], "profiles": profiles,
            "runtime": {"owner": actor, "endpoint": f"http://127.0.0.1:{runtime_port}/v1/completion-intents/outcome", "token_env": "QUAL_TOKEN"}})

        loss = {"enabled": True, "receipts": []}
        class Proxy(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def relay(self):
                body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
                connection = http.client.HTTPConnection("127.0.0.1", data_port, timeout=20)
                try:
                    connection.request(self.command, self.path, body,
                        {"Authorization": "Bearer " + "q" * 32, "Content-Type": "application/json"})
                    response = connection.getresponse()
                    raw, status = response.read(), response.status
                finally:
                    connection.close()
                if self.command == "POST" and status == 200:
                    loss["receipts"].append(json.loads(raw))
                    if loss["enabled"]:
                        loss["enabled"] = False
                        status, raw = 503, b'{"reason_code":"simulated_lost_response"}'
                self.send_response(status)
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

            do_GET = do_POST = relay

        proxy = ThreadingHTTPServer(("127.0.0.1", proxy_port), Proxy)
        proxy_thread = threading.Thread(target=proxy.serve_forever, daemon=True)
        proxy_thread.start()
        write(output / "runtime.json", {"database_url_env": "QUAL_RUNTIME_URL", "fixtures": [],
            "principals": [{**principal, "actions": ["admit", "claim", "complete", "cancel", "read", "outcome", "maintain"]}],
            "graphs": [{"definition": "graph.json", "releases": [{"descriptor": "release.json", "lock": lock}], "schemas": schemas}],
            "artifacts": {"runtime_owner": actor, "reserve_endpoint": f"http://127.0.0.1:{data_port}/v1/reservations",
                "token_env": "QUAL_TOKEN", "retention_profile": "derived-closure-retention-v1",
                "closure_reserve_endpoint": f"http://127.0.0.1:{proxy_port}/v1/retention-closures/reserve"}})
        if population_only:
            from population_seed_fixture import verify as verify_seed
            loss["enabled"] = False
            verify_seed(output, population_python, (data_port, runtime_port), environment, scope,
                        call, command, start, stop, with_slice=population_slice, method_operation=population_method, inspect_inputs=inspect_inputs, with_collection=population_collect, collection_case=collection_case, with_fitness=population_fitness, with_selection=population_select, with_successor=population_propose, successor_tight=successor_tight, successor_consume=successor_consume, successor_fitness=successor_fitness, successor_failure=successor_failure, successor_select=successor_select)
            return
        start("data", data_python, data_port, environment)
        runtime = start("runtime", runtime_python, runtime_port, environment)

        def publish(value, kind="output", parents=()):
            raw = json.dumps(value).encode()
            content = {"sha256": hashlib.sha256(raw).hexdigest(), "size_bytes": len(raw),
                       "media_type": "application/json", "schema_ref": lock[kind + "_schemas"][0]["schema_ref"]}
            payload = {"content": content}
            if parents:
                payload["declaration"] = {"transformation": {"transformation_id": "synthetic.retention", "version": "1", "sha256": "e" * 64}, "inputs": list(parents)}
            begin = call(data_port, "/v1/derived-uploads" if parents else "/v1/uploads",
                command("artifacts.begin_derived_upload" if parents else "artifacts.begin_upload", payload))
            upload = begin["upload"] if parents else begin
            connection = http.client.HTTPConnection("127.0.0.1", data_port, timeout=20)
            try:
                connection.request("PUT", "/v1/uploads/" + upload["upload_id"] + "/content", raw,
                    {"Authorization": "Bearer " + "q" * 32})
                response = connection.getresponse()
                assert response.status == 200, response.read()
                response.read()
            finally:
                connection.close()
            return call(data_port, "/v1/artifacts/finalize", command("artifacts.finalize",
                {"upload_id": upload["upload_id"], "content": upload["content"]}))["artifact"]

        source = publish({"a": 1, "b": 0, "values": [1]}, "input")
        leaf = publish({"values": [1]})
        left = publish({"values": [2]}, parents=(leaf,))
        right = publish({"values": [3]}, parents=(leaf,))
        root = publish({"values": [4]}, parents=(left, right))

        def admission():
            value_type = definition["body"]["inputs"][0]["value_type"]
            result = call(runtime_port, "/v1/graph-runs", command("graph.admit", {
                "plan_sha256": runtime["plan_sha256"], "inputs": [{"port": "parameters", "value": {
                    "kind": "artifact", "representation": value_type["representation"], "unit": "1", "artifact": source}}],
                "budget": {"limit": 2}}))
            run = result["outcome"]["committed"]["object_id"]
            claimed = call(runtime_port, "/v1/invocations/claim", command("runtime.claim", {
                "run_id": run, "worker_id": actor, "tool": lock["tool"], "lease_seconds": 300}))["outcome"]["invocation"]
            complete = command("runtime.complete", {"run_id": run, "completion": {
                "schema_version": "1", "invocation_id": claimed["invocation_id"], "attempt_id": claimed["attempt_id"],
                "fence": claimed["fence"], "outcome": {"status": "succeeded", "outputs": [{"port": "result", "artifact": root}]}}})
            return run, complete

        run, complete = admission()
        assert call(runtime_port, "/v1/invocations/complete", complete)["outcome"]["status"] == "pending"
        reserved = loss["receipts"][-1]
        assert reserved["artifact_count"] == 4
        binding = reserved["reservation"]["outcome"]["binding"]
        assert call(runtime_port, "/v1/completion-intents/outcome", binding)["proof"]["status"] == "prepared"
        stop("runtime")
        stop("data")
        start("data", data_python, data_port, environment)
        start("runtime", runtime_python, runtime_port, environment)
        accepted = call(runtime_port, "/v1/invocations/complete", complete)
        assert accepted["outcome"]["status"] == "accepted"
        assert loss["receipts"][-1] == reserved
        reservation_id = binding["reservation_id"]
        confirmed = call(data_port, "/v1/reservations/confirm", command("artifacts.confirm", {
            "reservation_id": reservation_id, "intent_id": binding["intent"]["intent_id"],
            "runtime_receipt_id": accepted["outcome"]["committed"]["object_id"]}))
        assert confirmed["outcome"]["status"] == "confirmed"
        readback = call(data_port, "/v1/retention-closures/" + reservation_id)
        assert readback["members_sha256"] == reserved["members_sha256"] and readback["artifact_count"] == 4
        assert readback["reservation"]["outcome"]["status"] == "confirmed"
        call(runtime_port, "/v1/graph-runs/advance", command("graph.advance", {"run_id": run, "max_transitions": 10}))
        loss["enabled"] = True
        second_run, second = admission()
        assert call(runtime_port, "/v1/invocations/complete", second)["outcome"]["status"] == "pending"
        second_binding = loss["receipts"][-1]["reservation"]["outcome"]["binding"]
        call(runtime_port, "/v1/runs/cancel", command("runtime.cancel", {"run_id": second_run, "reason_code": "qualification_cancel"}))
        released = call(data_port, "/v1/reservations/reconcile", command("artifacts.reconcile", {"reservation_id": second_binding["reservation_id"]}))
        assert released["outcome"]["status"] == "released"
        assert call(data_port, "/v1/retention-closures/" + reservation_id)["reservation"]["outcome"]["status"] == "confirmed"
        if population_python is not None:
            from population_seed_fixture import verify as verify_seed
            verify_seed(output, population_python, (data_port, runtime_port), environment, scope,
                        call, command, start, stop, with_slice=population_slice, method_operation=population_method, inspect_inputs=inspect_inputs, with_collection=population_collect, collection_case=collection_case, with_fitness=population_fitness, with_selection=population_select, with_successor=population_propose, successor_tight=successor_tight, successor_consume=successor_consume, successor_fitness=successor_fitness, successor_failure=successor_failure, successor_select=successor_select)
        write(output / "evidence.json", {"status": "passed", "timestamp_local": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "scope": "Synthetic actual installed owner HTTP/restart, not population scientific execution",
            "members": 4, "lost_responses": 2, "restarted_owners": ["data", "runtime"], "committed_group": "confirmed",
            "aborted_group": "released", "independent_confirmed_group_preserved": True, "provider_calls": 0})
        print("Installed Data/Runtime closure HTTP, lost response, restart and cancellation passed.", flush=True)
    finally:
        for owner in tuple(processes):
            stop(owner)
        if proxy is not None:
            proxy.shutdown()
            proxy.server_close()
            proxy_thread.join(timeout=5)
        for stream in streams:
            stream.close()
        if fixture.STATE.exists():
            state = fixture.owned_state()
            fixture.docker("rm", "--force", state["container"])
            print("Owned test container removed; labeled volume retained.", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--data-python", type=Path, required=True)
    parser.add_argument("--runtime-python", type=Path, required=True)
    parser.add_argument("--population-python", type=Path)
    parser.add_argument("--population-only", action="store_true")
    parser.add_argument("--population-slice", action="store_true")
    parser.add_argument("--collection-case", choices=["normal","failed-required","conditional-not-taken"], default="normal")
    parser.add_argument("--population-propose", action="store_true")
    parser.add_argument("--successor-tight", action="store_true")
    parser.add_argument("--successor-consume", action="store_true")
    parser.add_argument("--successor-fitness", action="store_true")
    parser.add_argument("--successor-failure", action="store_true")
    parser.add_argument("--successor-select", action="store_true")
    parser.add_argument("--population-select", action="store_true")
    parser.add_argument("--population-fitness", action="store_true")
    parser.add_argument("--population-collect", action="store_true")
    parser.add_argument("--inspect-inputs", action="store_true")
    parser.add_argument("--population-method", choices=["evaluate-squares", "evaluate-negative-sum"])
    args = parser.parse_args()
    verify(args.output, args.data_python.absolute(), args.runtime_python.absolute(),
           None if args.population_python is None else args.population_python.absolute(),
           population_only=args.population_only, population_slice=args.population_slice, population_method=args.population_method, inspect_inputs=args.inspect_inputs, population_collect=args.population_collect, collection_case=args.collection_case, population_fitness=args.population_fitness, population_select=args.population_select, population_propose=args.population_propose, successor_tight=args.successor_tight, successor_consume=args.successor_consume, successor_fitness=args.successor_fitness, successor_failure=args.successor_failure, successor_select=args.successor_select)
