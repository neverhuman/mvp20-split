"""Actual independently installed SDK/tools and owner services over public HTTP."""

import base64
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path
from types import SimpleNamespace

spec = importlib.util.spec_from_file_location("worker_acceptance_support", Path(__file__).with_name("support.py"))
support = importlib.util.module_from_spec(spec)
spec.loader.exec_module(support)


def save_evidence(context, status):
    output = Path(context.config["evidence"]) / context.scope["project_id"]
    output.mkdir(parents=True, exist_ok=True)
    evidence = {"schema_version": "1", "status": status, "scope": context.scope, "packages": context.packages,
        "image_digests": {tool.module: tool.image["image_manifest_digest"] for tool in context.tools},
        "worker_install_profile": "independent Windows wheels; identical internal wheels to separately tested Linux images",
        "cases": context.cases}
    if status == "failed":
        evidence["interrupted_run"] = context.active_run
        evidence["last_runtime_requests"] = context.runtime_relay.events
        evidence["last_artifact_requests"] = context.artifact_relay.events
    encoded = (json.dumps(evidence, sort_keys=True, indent=2) + "\n").encode()
    (output / "manifest.json").write_bytes(encoded)
    (output / "manifest.sha256").write_text(hashlib.sha256(encoded).hexdigest() + "\n", encoding="utf-8")


def main(config_path):
    config = json.loads(Path(config_path).read_bytes())
    images = json.loads(Path(config["images"]).read_bytes())
    packages = config["packages"]
    scope = {"tenant_id": "sdk-acceptance", "project_id": uuid.uuid4().hex}
    tokens = {actor: uuid.uuid4().hex for actor in ("admin", "worker", "runtime", "artifact")}

    def principal(actor, actions):
        return {"actor_id": actor, "scope": scope, "token_env": "TOKEN_" + actor.upper(), "actions": actions}

    def command(family, payload, actor="admin", key=None):
        return {"identity": {"command_family": family, "command_id": key or uuid.uuid4().hex,
            "actor_id": actor, "scope": scope}, "payload": payload}

    with tempfile.TemporaryDirectory(prefix="amphora-sdk-peers-") as directory:
        root = Path(directory)
        storage = root / "bytes"
        storage.mkdir()
        profiles, tools = [], []
        for image in images["tools"]:
            module = image["module"]
            python = config["tools"][module]
            for name, digest in image["local_wheels"].items():
                assert packages[name] == digest, "Installed internal wheel differs from the actual image"
            # Read public schema resources from the independently installed tool, never its checkout.
            script = ("import base64,json; from importlib.resources import files; "
                f"print(json.dumps({{k:base64.b64encode(files('{module}').joinpath('schemas',k+'.json').read_bytes()).decode() "
                "for k in ('input','output')}))")
            result = subprocess.run([python, "-I", "-c", script], cwd=root, env=support.isolated_env(),
                capture_output=True, text=True, timeout=20)
            assert result.returncode == 0, "Installed tool schema resources missing"
            documents = json.loads(result.stdout)
            descriptor = image["descriptor"]["tool"]
            for kind, port in (("input", descriptor["inputs"][0]), ("output", descriptor["outputs"][0])):
                schema = base64.b64decode(documents[kind])
                assert hashlib.sha256(schema).hexdigest() == port["schema_ref"]["sha256"]
                path = root / (module + "-" + kind + ".json")
                path.write_bytes(schema)
                profiles.append({"media_type": "application/json", **port["schema_ref"], "schema_path": path.name})
            tools.append(SimpleNamespace(image=image, module=module, python=python, descriptor=descriptor))
        runtime_port = support.free_port()
        runtime_endpoint = f"http://127.0.0.1:{runtime_port}"
        artifact_config = root / "artifacts.json"
        artifact_config.write_text(json.dumps({"database_url_env": "DATABASE_URL", "storage_root": str(storage),
            "principals": [principal("worker", ["upload", "finalize", "read"]), principal("runtime", ["retention"])],
            "profiles": profiles, "runtime": {"owner": "runtime", "endpoint": runtime_endpoint + "/v1/completion-intents/outcome",
                "token_env": "TOKEN_ARTIFACT"}}), encoding="utf-8")
        artifact_env = dict(support.isolated_env(), DATABASE_URL=os.environ["AMPHORA_ARTIFACT_DATABASE_URL"],
            TOKEN_WORKER=tokens["worker"], TOKEN_RUNTIME=tokens["runtime"], TOKEN_ARTIFACT=tokens["artifact"])
        runtime_env = dict(support.isolated_env(), DATABASE_URL=os.environ["AMPHORA_RUNTIME_DATABASE_URL"],
            CURSOR_KEY=uuid.uuid4().hex, **{"TOKEN_" + actor.upper(): token for actor, token in tokens.items()})
        artifact = support.Service(config["artifact"], "amphora_data_artifacts", artifact_config, artifact_env,
                                   root, support.free_port())
        runtime = artifact_relay = runtime_relay = None
        context = None
        try:
            artifact.ready(tokens["worker"])
            def publish(tool, payload):
                body = json.dumps(payload).encode()
                content = {"sha256": hashlib.sha256(body).hexdigest(), "size_bytes": len(body), "media_type": "application/json",
                           "schema_ref": tool.descriptor["inputs"][0]["schema_ref"]}
                upload = support.decoded(artifact.endpoint, "/v1/uploads", tokens["worker"],
                    command("artifacts.begin_upload", {"content": content}, "worker"))
                assert support.request(artifact.endpoint, "/v1/uploads/" + upload["upload_id"] + "/content",
                    tokens["worker"], body, "PUT")[0] == 200
                return support.decoded(artifact.endpoint, "/v1/artifacts/finalize", tokens["worker"],
                    command("artifacts.finalize", {"upload_id": upload["upload_id"], "content": content}, "worker"))["artifact"]

            fixtures = {}
            for tool in tools:
                payloads = [("golden", tool.image["golden_input"])]
                if tool.module == "amphora_sequence_statistics":
                    payloads.append(("invalid-symbol", {"sequence": "AX", "alphabet": "ACGT"}))
                for variant, payload in payloads:
                    reference = publish(tool, payload)
                    key = tool.module + "-" + variant
                    definition = {"fixture_id": key, "plan_sha256": hashlib.sha256(key.encode()).hexdigest(),
                        "invocations": [{"node_id": "tool", "activation_id": "activation", "invocation_id": "invocation",
                            "tool": tool.descriptor["binding"], "inputs": [{"port": tool.descriptor["inputs"][0]["name"],
                                "artifact": reference}], "timeout_seconds": 60}],
                        "budget": {"limit": 2, "max_attempts_per_activation": 2}}
                    fixtures[key] = definition
            runtime_config = root / "runtime.json"
            runtime_config.write_text(json.dumps({"database_url_env": "DATABASE_URL", "fixtures": list(fixtures.values()),
                "principals": [principal("admin", ["admit", "cancel", "read", "inspect_receipts", "deliver"]),
                    principal("worker", ["claim", "renew", "complete", "read"]), principal("artifact", ["outcome"])],
                "tools": [tool.descriptor for tool in tools],
                "artifacts": {"runtime_owner": "runtime", "reserve_endpoint": artifact.endpoint + "/v1/reservations",
                    "token_env": "TOKEN_RUNTIME"}, "inspection": {"cursor_key_env": "CURSOR_KEY"}}), encoding="utf-8")
            runtime = support.Service(config["runtime"], "amphora_campaign_runtime", runtime_config, runtime_env, root, runtime_port)
            runtime.ready(tokens["admin"])
            artifact_relay, runtime_relay = support.FaultRelay(artifact.endpoint), support.FaultRelay(runtime.endpoint)
            context = SimpleNamespace(root=root, tools=tools, fixtures=fixtures, scope=scope, tokens=tokens, command=command,
                artifact=artifact, runtime=runtime, artifact_relay=artifact_relay, runtime_relay=runtime_relay,
                config=config, packages=packages, active_run=None, cases=[])
            context.save_evidence = lambda status: save_evidence(context, status)
            cases_spec = importlib.util.spec_from_file_location("worker_acceptance_cases", Path(__file__).with_name("scenarios.py"))
            cases = importlib.util.module_from_spec(cases_spec)
            cases_spec.loader.exec_module(cases)
            try:
                cases.run(context, support)
            except BaseException:
                save_evidence(context, "failed")
                raise
            save_evidence(context, "passed")
            print("Actual independent tool/SDK owner proof passed; scope " + scope["project_id"], flush=True)
        finally:
            if context is not None and context.active_run is not None and runtime.child.poll() is None:
                snapshot = support.decoded(runtime.endpoint, "/v1/runs/" + context.active_run, tokens["admin"])
                if snapshot["status"] == "running":
                    support.request(runtime.endpoint, "/v1/runs/cancel", tokens["admin"], command("runtime.cancel",
                        {"run_id": context.active_run, "reason_code": "acceptance_cleanup"}))
            for resource in (runtime_relay, artifact_relay, runtime, artifact):
                if resource is not None:
                    resource.close()


if __name__ == "__main__":
    main(sys.argv[1])
