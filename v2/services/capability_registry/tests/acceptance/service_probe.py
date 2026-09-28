"""Actual independently installed original/replacement registry over public HTTP."""

import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import uuid
from datetime import datetime
from pathlib import Path

spec = importlib.util.spec_from_file_location("registry_http_support", Path(__file__).with_name("http_support.py"))
support = importlib.util.module_from_spec(spec)
spec.loader.exec_module(support)


def main():
    replacement_python, fixture_path, evidence_dir = sys.argv[1:]
    fixture = json.loads(Path(fixture_path).read_text())[0]
    scope = {"tenant_id": "registry-installed", "project_id": uuid.uuid4().hex}
    tokens = {name: uuid.uuid4().hex for name in ("admin", "worker", "other")}
    records = []

    def command(action, payload, actor="admin"):
        return {"identity": {"scope": scope, "actor_id": actor, "command_id": uuid.uuid4().hex,
                             "command_family": "registry."+action}, "payload": payload}

    def migrate(executable):
        env = dict(support.isolated_env(), AMPHORA_REGISTRY_MIGRATION_URL=os.environ["AMPHORA_REGISTRY_MIGRATION_URL"])
        result = subprocess.run([str(executable), "-I", "-m", "amphora_capability_registry.persistence.migrate"],
            env=env, text=True, capture_output=True, timeout=20)
        assert result.returncode == 0, "Installed owner migration failed"

    with tempfile.TemporaryDirectory(prefix="amphora-registry-host-") as directory:
        root = Path(directory)
        config = root/"registry.json"
        config.write_text(json.dumps({"database_url_env": "DATABASE_URL", "principals": [
            {"actor_id": actor, "scope": scope if actor != "other" else {**scope, "project_id": "other"},
             "token_env": "TOKEN_"+actor.upper(), "actions": ["heartbeat"] if actor == "worker" else
             ["register", "activate", "deploy", "read", "resolve", "drain", "revoke"]} for actor in tokens],
            "resources": {"architecture": "x86_64", "operating_system": "windows", "cpu_millicores": 2000,
                "memory_mib": 1024, "gpu_count": 0, "timeout_seconds": 300, "max_parallel_invocations": 8, "max_batch_size": 128}}), encoding="utf-8")
        env = dict(support.isolated_env(), DATABASE_URL=os.environ["AMPHORA_REGISTRY_DATABASE_URL"],
                   **{"TOKEN_"+name.upper(): token for name, token in tokens.items()})
        migrate(sys.executable)
        host = support.Process(sys.executable, config, env, root)
        try:
            host.ready()

            def call(cmd):
                actor = cmd["identity"]["actor_id"]
                action = cmd["identity"]["command_family"].removeprefix("registry.")
                status, result = support.request(host.endpoint, "/v1/registry/"+action, tokens[actor], cmd)
                assert status == 200, result
                return result

            register = command("register", {"scope": scope, "descriptor": fixture["descriptor"], "expected_lock": fixture["lock"]})
            original_receipt = call(register)
            assert original_receipt["reason_code"] == "registered"
            lock = original_receipt["release"]["lock"]
            active = call(command("activate", {"release": lock, "expected_revision": 1}))["release"]
            deployed = call(command("deploy", {"deployment_id": "d1", "release": lock, "architecture": "x86_64",
                "operating_system": "windows", "workers": ["worker"]}))["deployment"]
            heartbeat = command("heartbeat", {"deployment_id": "d1", "replica_id": "r1", "expected_revision": 0,
                "free_slots": 1, "ttl_seconds": 60}, "worker")
            observed = call(heartbeat)
            tool = fixture["descriptor"]["tool"]
            need = {"release": lock, "context": "synthetic-tests", "inputs": tool["inputs"], "outputs": tool["outputs"]}
            resolve = command("resolve", need)
            selected = call(resolve)
            assert selected["decision"]["status"] == "candidate"
            catalog = support.request(host.endpoint, "/v1/releases?capability_id=synthetic.numeric-affine&release=0.1.0", tokens["admin"])
            assert catalog[0] == 200 and catalog[1]["items"] == [active]
            records.append({"stage": "original", "observed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "operation_id": original_receipt["operation_id"], "descriptor_sha256": lock["descriptor_sha256"]})
            host.close()
            migrate(replacement_python)
            migrate(replacement_python)
            host = support.Process(replacement_python, config, env, root)
            host.ready()
            assert call(register) == original_receipt
            assert call(heartbeat) == observed
            assert call(resolve) == selected
            assert support.request(host.endpoint, "/v1/releases/"+lock["descriptor_sha256"], tokens["admin"]) == (200, active)
            assert support.request(host.endpoint, "/v1/deployments/d1", tokens["admin"]) == (200, deployed)
            assert support.request(host.endpoint, "/v1/releases?capability_id=synthetic.numeric-affine&release=0.1.0", tokens["admin"]) == catalog
            assert support.request(host.endpoint, "/v1/releases/"+lock["descriptor_sha256"], tokens["other"])[0] == 404
            report = {**heartbeat["payload"], "expected_revision": 1}
            assert call(command("heartbeat", report, "worker"))["heartbeat"]["revision"] == 2
            assert call(command("resolve", need))["decision"]["status"] == "candidate"
            drained = call(command("drain", {"release": lock, "expected_revision": 2}))
            assert drained["release"]["lock"] == lock and drained["release"]["revision"] == 3
            assert call(command("resolve", need))["reason_code"] == "release_not_active"
            assert call(register) == original_receipt
            records.append({"stage": "replacement", "observed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "operation_id": drained["operation_id"], "original_receipts_preserved": True,
                            "release_revision": 3, "replica_revision": 2})
        finally:
            host.close()
    value = {"scenario": "registry-retained-replacement-v1", "scope": scope, "status": "passed", "observations": records,
             "packages": json.loads(os.environ["AMPHORA_TESTED_PACKAGES"])}
    body = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    destination = Path(evidence_dir)/scope["project_id"]
    destination.mkdir(parents=True, exist_ok=True)
    (destination/"replacement.json").write_text(json.dumps({"sha256": hashlib.sha256(body).hexdigest(), "evidence": value}, indent=2)+"\n", encoding="utf-8")
    print("Installed registry HTTP replacement: immutable release/deployment, original receipts, heartbeat and lifecycle preserved; scope "+scope["project_id"])


if __name__ == "__main__":
    main()
