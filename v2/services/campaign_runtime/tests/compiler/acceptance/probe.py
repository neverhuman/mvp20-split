"""Actual installed compiler/Registry/tool public compatibility and retained-plan replacement."""

import base64
import copy
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

ROOT = Path(__file__).absolute().parents[5]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


HTTP = load("compiler_acceptance_http", ROOT / "sdk/tool_protocol/tests/acceptance/support.py")
WIRE = load("compiler_acceptance_wire", ROOT / "tests/integration/tool_replicas/wire.py")


def command(python, arguments, root, *, value=None, env=None):
    result = subprocess.run([python, "-I", *map(str, arguments)], input=None if value is None else json.dumps(value),
                            cwd=root, env=env or HTTP.isolated_env(), text=True, encoding="utf-8", capture_output=True, timeout=30)
    assert result.returncode == 0, result.stderr[-1500:]
    return json.loads(result.stdout) if result.stdout.strip() else None


def main():
    config = json.loads(Path(sys.argv[1]).read_bytes())
    images = json.loads(Path(config["images"]).read_bytes())
    scope = {"tenant_id": "compiler-installed", "project_id": uuid.uuid4().hex}
    token, records, schemas, releases = uuid.uuid4().hex, [], [], []
    destination = Path(config["evidence"]) / scope["project_id"]
    destination.mkdir(parents=True)
    with tempfile.TemporaryDirectory(prefix="amphora-compiler-peer-") as directory:
        root = Path(directory)
        for image in images["tools"]:
            module = image["module"]
            for name, digest in image["local_wheels"].items():
                assert config["packages"][name] == digest, "Published tool closure changed"
            python = config["installed"][module]
            descriptor = command(python, ["-m", module, "describe", "--image-sha256", image["descriptor"]["tool"]["binding"]["image_sha256"]], root)
            assert descriptor == image["descriptor"]
            script = ("import base64,json; from importlib.resources import files; "
                      f"print(json.dumps({{k:base64.b64encode(files('{module}').joinpath('schemas',k+'.json').read_bytes()).decode() "
                      "for k in ('input','output')}))")
            payloads = command(python, ["-c", script], root)
            for name in ("input", "output"):
                reference = descriptor["tool"][name + "s"][0]["schema_ref"]
                assert hashlib.sha256(base64.b64decode(payloads[name])).hexdigest() == reference["sha256"]
                schemas.append({**reference, "body": payloads[name]})
            tool_path = "numeric_affine" if module == "amphora_numeric_affine" else "sequence_statistics"
            golden = json.loads((ROOT / "tools" / tool_path / "tests/fixtures/golden.json").read_bytes())
            assert command(python, ["-m", module, "compute"], root, value=golden["input"]) == golden["output"]
            releases.append({"descriptor": descriptor, "lock": WIRE.release_lock(descriptor)})
        registry_config = root / "registry.json"
        registry_config.write_text(json.dumps({"database_url_env": "DATABASE_URL", "principals": [
            {"actor_id": "compiler", "scope": scope, "token_env": "TOKEN", "actions": ["register", "activate", "read", "resolve", "drain"]}],
            "resources": {"architecture": "x86_64", "operating_system": "linux", "cpu_millicores": 4000,
                          "memory_mib": 1024, "gpu_count": 0, "timeout_seconds": 300, "max_parallel_invocations": 8, "max_batch_size": 128}}), encoding="utf-8")
        registry_env = dict(HTTP.isolated_env(), DATABASE_URL=os.environ["AMPHORA_REGISTRY_DATABASE_URL"], TOKEN=token)
        migrate_env = dict(HTTP.isolated_env(), AMPHORA_REGISTRY_MIGRATION_URL=os.environ["AMPHORA_REGISTRY_MIGRATION_URL"])
        command(config["installed"]["amphora_capability_registry"], ["-m", "amphora_capability_registry.persistence.migrate"], root, env=migrate_env)
        host = None
        try:
            def start(python):
                service = HTTP.Service(python, "amphora_capability_registry", registry_config, registry_env, root, HTTP.free_port())
                try:
                    service.ready(token, "/v1/releases")
                except BaseException:
                    service.close()
                    raise
                return service

            host = start(config["installed"]["amphora_capability_registry"])

            def operation(action, payload):
                return {"identity": {"scope": scope, "actor_id": "compiler", "command_family": "registry." + action,
                                     "command_id": uuid.uuid4().hex}, "payload": payload}

            def call(value):
                action = value["identity"]["command_family"].removeprefix("registry.")
                return HTTP.decoded(host.endpoint, "/v1/registry/" + action, token, value)

            receipts, snapshots, registrations = [], [], []
            for release in releases:
                register = operation("register", {"scope": scope, "descriptor": release["descriptor"], "expected_lock": release["lock"]})
                receipt = call(register)
                assert receipt["reason_code"] == "registered"
                active = call(operation("activate", {"release": release["lock"], "expected_revision": 1}))
                assert active["release"]["status"] == "active"
                tool = release["descriptor"]["tool"]
                decision = call(operation("resolve", {"release": release["lock"], "context": "synthetic-tests",
                                                       "inputs": tool["inputs"], "outputs": tool["outputs"]}))
                assert decision["reason_code"] == "no_eligible_capacity"
                observed = decision["decision"]["observations"]
                assert observed["structural"]["status"] == "valid" and observed["scientific"]["status"] == "eligible"
                assert observed["capacity"]["status"] == "unavailable"
                receipts.append(receipt)
                registrations.append(register)
                snapshots.append(active["release"])
            cases = json.loads((ROOT / "contracts/fixtures/v2/executable_cases.json").read_bytes())
            definitions = [copy.deepcopy(case["payload"]) for case in cases if case["model"] == "campaigns.definition" and case["valid"]]
            for value in definitions:
                value["scope"] = scope
            # Compose the second installed capability through its published ports, with no scientific adapter import.
            sequence = next(item["descriptor"]["tool"] for item in releases if item["lock"]["tool"]["capability_id"] == "synthetic.sequence-statistics")
            extra = copy.deepcopy(definitions[0])
            extra["campaign_id"] = "sequence"
            for direction in ("inputs", "outputs"):
                port = sequence[direction][0]
                extra["body"][direction][0]["value_type"].update(schema_ref=port["schema_ref"], representation=port["representation"], unit=port["unit"])
            invoke = extra["body"]["nodes"][0]
            invoke["tool"] = sequence["binding"]
            invoke["inputs"][0]["port"] = sequence["inputs"][0]["name"]
            extra["body"]["nodes"][1]["outputs"][0]["source"]["port"] = sequence["outputs"][0]["name"]
            definitions.append(extra)
            request = {"scope": scope, "endpoint": host.endpoint, "token": token, "schemas": schemas,
                       "releases": [item["lock"]["descriptor_sha256"] for item in releases], "definitions": definitions}
            client = Path(__file__).with_name("client.py")
            plans = command(config["installed"]["amphora_campaign_runtime"], [client], root, value=request)
            retained = json.dumps(plans, sort_keys=True, separators=(",", ":")).encode()
            (destination / "plans.json").write_bytes(retained)
            records.append({"stage": "original", "observed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "plans": [plan["sha256"] for plan in plans], "no_live_capacity": True})
            host.close()
            host = None
            command(config["replacements"]["amphora_capability_registry"], ["-m", "amphora_capability_registry.persistence.migrate"], root, env=migrate_env)
            host = start(config["replacements"]["amphora_capability_registry"])
            for register, receipt, snapshot in zip(registrations, receipts, snapshots, strict=True):
                assert call(register) == receipt
                assert HTTP.decoded(host.endpoint, "/v1/releases/" + snapshot["lock"]["descriptor_sha256"], token) == snapshot
            request.update(endpoint=host.endpoint, retained=plans)
            assert command(config["replacements"]["amphora_campaign_runtime"], [client], root, value=request) == plans
            assert (destination / "plans.json").read_bytes() == retained
            records.append({"stage": "fresh_replacement", "observed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "original_receipts_and_plans_preserved": True})
            for release in releases:
                assert call(operation("drain", {"release": release["lock"], "expected_revision": 2}))["release"]["status"] == "draining"
            assert command(config["replacements"]["amphora_campaign_runtime"], [client], root, value=request) == plans
            records.append({"stage": "drained_exact_history", "observed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "plan_identity_preserved_without_dispatch_authority": True})
        finally:
            if host is not None:
                host.close()
    evidence = {"scenario": "installed-compiler-public-peers-v1", "status": "passed", "scope": scope, "observations": records,
                "packages": config["packages"], "tool_locks": [item["lock"] for item in releases],
                "retained_plans_sha256": hashlib.sha256(retained).hexdigest()}
    body = json.dumps(evidence, indent=2, sort_keys=True).encode() + b"\n"
    (destination / "acceptance.json").write_bytes(body)
    (destination / "acceptance.sha256").write_text(hashlib.sha256(body).hexdigest() + "\n", encoding="ascii")
    print("Installed compiler: five plans, two actual tools, public Registry/no-capacity observation, fresh replacement and retained drain history passed; scope " + scope["project_id"])


if __name__ == "__main__":
    main()
