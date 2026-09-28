"""Owned ephemeral setup through public APIs; no private owner imports or SQL."""

import base64
import copy
import hashlib
import importlib.util
import json
import os
import subprocess
import uuid
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


HTTP = load("replica_http", Path(__file__).parents[3] / "sdk/tool_protocol/tests/acceptance/support.py")
WIRE = load("replica_wire", Path(__file__).with_name("wire.py"))


class Environment:
    def __init__(self, config, root):
        self.config, self.root = config, root
        self.scope = {"tenant_id": "tool-replicas", "project_id": uuid.uuid4().hex}
        self.tokens = {actor: uuid.uuid4().hex for actor in ("admin", "worker1", "worker2", "runtime", "artifact")}
        self.resources, self.cases, self.tools, self.fixtures = [], [], [], {}
        self.active_run = None
        self.registry = self.runtime = self.artifact = None

    def command(self, family, payload, actor="admin", key=None):
        return {"identity": {"scope": self.scope, "actor_id": actor, "command_family": family,
            "command_id": key or uuid.uuid4().hex}, "payload": payload}

    def principal(self, actor, actions):
        return {"actor_id": actor, "scope": self.scope, "token_env": "TOKEN_" + actor.upper(), "actions": actions}

    def host(self, name, module, config, database_env, port=None):
        path = self.root / (name + ".json")
        path.write_text(json.dumps(config), encoding="utf-8")
        env = dict(HTTP.isolated_env(), DATABASE_URL=os.environ[database_env])
        # Host receives only the token names declared by its own configuration.
        actors = {principal["actor_id"] for principal in config["principals"]}
        if name == "runtime":
            actors.add("runtime")
            env["CURSOR_KEY"] = uuid.uuid4().hex
        if name == "artifact":
            actors.add("artifact")
        env.update({"TOKEN_" + actor.upper(): self.tokens[actor] for actor in actors})
        host = HTTP.Service(self.config[name], module, path, env, self.root, port or HTTP.free_port())
        self.resources.append(host)
        host.ready(self.tokens["admin"] if name == "registry" else self.tokens[config["principals"][0]["actor_id"]],
            "/v1/releases" if name == "registry" else "/ready")
        return host

    def registry_call(self, action, payload, actor="admin"):
        return HTTP.decoded(self.registry.endpoint, "/v1/registry/" + action, self.tokens[actor],
            self.command("registry." + action, payload, actor))

    def setup(self):
        images = json.loads(Path(self.config["images"]).read_bytes())
        selected_images = [(image, False) for image in images["tools"]]
        if self.config.get("previous_images"):
            old = json.loads(Path(self.config["previous_images"]).read_bytes())
            selected_images.extend((image, True) for image in old["tools"] if image["module"] in self.config["previous_tools"])
        profiles = []
        for image, previous in selected_images:
            module = image["module"]
            for name, digest in image["local_wheels"].items():
                assert self.config["packages"][name] == digest, "Internal wheel differs from image evidence"
            python = self.config["previous_tools" if previous else "tools"][module]
            script = ("import base64,json; from importlib.resources import files; "
                f"print(json.dumps({{k:base64.b64encode(files('{module}').joinpath('schemas',k+'.json').read_bytes()).decode() "
                "for k in ('input','output')}))")
            result = subprocess.run([python, "-I", "-c", script], cwd=self.root, env=HTTP.isolated_env(),
                text=True, capture_output=True, timeout=20)
            assert result.returncode == 0
            tool = SimpleNamespace(image=image, module=module, python=python, descriptor=image["descriptor"]["tool"],
                lock=WIRE.release_lock(image["descriptor"]), previous=previous,
                pending_replacement=bool(self.config.get("previous_images")) and not previous and module == "amphora_sequence_statistics")
            tool.key = module + "-" + tool.lock["tool"]["release"]
            schemas = json.loads(result.stdout)
            for kind, port in (("input", tool.descriptor["inputs"][0]), ("output", tool.descriptor["outputs"][0])):
                body = base64.b64decode(schemas[kind])
                assert hashlib.sha256(body).hexdigest() == port["schema_ref"]["sha256"]
                path = self.root / (module + "-" + kind + ".json")
                path.write_bytes(body)
                profile = {**port["schema_ref"], "media_type": "application/json", "schema_path": path.name}
                if profile not in profiles:
                    profiles.append(profile)
            self.tools.append(tool)
        self.registry = self.host("registry", "amphora_capability_registry", {
            "database_url_env": "DATABASE_URL", "principals": [self.principal("admin", ["register", "activate", "deploy", "read", "resolve", "drain", "revoke"]),
                self.principal("worker1", ["heartbeat"]), self.principal("worker2", ["heartbeat"])],
            "resources": {"architecture": "x86_64", "operating_system": "linux", "cpu_millicores": 4000,
                "memory_mib": 4096, "gpu_count": 0, "timeout_seconds": 300, "max_parallel_invocations": 8, "max_batch_size": 128}},
            "AMPHORA_REGISTRY_DATABASE_URL")
        for index, tool in enumerate(self.tools):
            registered = self.registry_call("register", {"scope": self.scope, "descriptor": tool.image["descriptor"], "expected_lock": tool.lock})
            assert registered["reason_code"] == "registered" and registered["release"]["lock"] == tool.lock
            tool.deployment = "deployment-" + str(index)
            tool.heartbeats = []
            tool.registration = registered
            if not tool.pending_replacement:
                self.activate(tool)
        port = HTTP.free_port()
        (self.root / "storage").mkdir()
        self.artifact = self.host("artifact", "amphora_data_artifacts", {"database_url_env": "DATABASE_URL",
            "storage_root": str(self.root / "storage"), "profiles": profiles,
            "principals": [self.principal(worker, ["upload", "finalize", "read"]) for worker in ("worker1", "worker2")]
                + [self.principal("runtime", ["retention"])],
            "runtime": {"owner": "runtime", "endpoint": f"http://127.0.0.1:{port}/v1/completion-intents/outcome", "token_env": "TOKEN_ARTIFACT"}},
            "AMPHORA_ARTIFACT_DATABASE_URL")
        for tool in self.tools:
            reference = self.publish(tool, tool.image["golden_input"])
            for count in (1, 2):
                key = tool.key + "-" + str(count)
                self.fixtures[key] = {"fixture_id": key, "plan_sha256": hashlib.sha256(key.encode()).hexdigest(),
                    "invocations": [{"node_id": "node-" + str(i), "activation_id": "activation-" + str(i), "invocation_id": "invocation-" + str(i),
                        "tool": tool.lock["tool"], "inputs": [{"port": "parameters", "artifact": reference}], "timeout_seconds": 60}
                        for i in range(count)], "budget": {"limit": count * 2, "max_attempts_per_activation": 2}}
            limited = copy.deepcopy(self.fixtures[tool.key + "-1"])
            limited["fixture_id"] = tool.key + "-budget-one"
            limited["plan_sha256"] = hashlib.sha256(limited["fixture_id"].encode()).hexdigest()
            limited["budget"]["limit"] = 1
            self.fixtures[limited["fixture_id"]] = limited
        self.runtime = self.host("runtime", "amphora_campaign_runtime", {"database_url_env": "DATABASE_URL",
            "fixtures": list(self.fixtures.values()), "tools": [tool.descriptor for tool in self.tools],
            "principals": [self.principal("admin", ["admit", "cancel", "read", "inspect_receipts", "deliver"]),
                self.principal("artifact", ["outcome"])] + [self.principal(worker, ["claim", "renew", "complete", "read"]) for worker in ("worker1", "worker2")],
            "artifacts": {"runtime_owner": "runtime", "reserve_endpoint": self.artifact.endpoint + "/v1/reservations", "token_env": "TOKEN_RUNTIME"},
            "inspection": {"cursor_key_env": "CURSOR_KEY"}}, "AMPHORA_RUNTIME_DATABASE_URL", port)
        self.runtime_relay, self.artifact_relay = HTTP.FaultRelay(self.runtime.endpoint), HTTP.FaultRelay(self.artifact.endpoint)
        self.resources.extend((self.runtime_relay, self.artifact_relay))

    def activate(self, tool):
        activated = self.registry_call("activate", {"release": tool.lock, "expected_revision": 1})
        assert activated["release"]["status"] == "active"
        deployed = self.registry_call("deploy", {"deployment_id": tool.deployment, "release": tool.lock,
            "architecture": "x86_64", "operating_system": "linux", "workers": ["worker1", "worker2"]})
        assert deployed["status"] == "accepted"
        for actor in ("worker1", "worker2"):
            tool.heartbeats.append(self.registry_call("heartbeat", {"deployment_id": tool.deployment,
                "replica_id": actor + "-" + tool.deployment, "expected_revision": 0, "free_slots": 1, "ttl_seconds": 60}, actor))
            assert tool.heartbeats[-1]["status"] == "accepted"

    def refresh_capacity(self, tool):
        refreshed = []
        for receipt in tool.heartbeats:
            old = receipt["heartbeat"]
            refreshed.append(self.registry_call("heartbeat", {"deployment_id": tool.deployment,
                "replica_id": old["replica_id"], "expected_revision": old["revision"], "free_slots": 1, "ttl_seconds": 60}, old["worker_id"]))
            assert refreshed[-1]["status"] == "accepted"
        tool.heartbeats = refreshed

    def publish(self, tool, payload):
        body = json.dumps(payload).encode()
        content = {"sha256": hashlib.sha256(body).hexdigest(), "size_bytes": len(body), "media_type": "application/json",
            "schema_ref": tool.descriptor["inputs"][0]["schema_ref"]}
        token = self.tokens["worker1"]
        upload = HTTP.decoded(self.artifact.endpoint, "/v1/uploads", token,
            self.command("artifacts.begin_upload", {"content": content}, "worker1"))
        assert HTTP.request(self.artifact.endpoint, "/v1/uploads/" + upload["upload_id"] + "/content", token, body, "PUT")[0] == 200
        return HTTP.decoded(self.artifact.endpoint, "/v1/artifacts/finalize", token,
            self.command("artifacts.finalize", {"upload_id": upload["upload_id"], "content": content}, "worker1"))["artifact"]

    def record(self, case, facts):
        self.cases.append({"case": case, "observed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), **facts})
        self.save("running")
        print(case + " passed", flush=True)

    def save(self, status):
        value = {"schema_version": "1", "status": status, "scope": self.scope, "cases": self.cases,
            "packages": self.config["packages"], "image_digests": {tool.key: tool.image["image_manifest_digest"] for tool in self.tools},
            "execution_profile": "Windows independent wheel processes; advertised Linux image profile separately verified",
            "active_run": self.active_run}
        if hasattr(self, "runtime_relay"):
            value.update(runtime_requests=self.runtime_relay.events, artifact_requests=self.artifact_relay.events)
        output = Path(self.config["evidence"]) / self.scope["project_id"]
        output.mkdir(parents=True, exist_ok=True)
        body = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()
        (output / "manifest.json").write_bytes(body)
        (output / "manifest.sha256").write_text(hashlib.sha256(body).hexdigest() + "\n", encoding="utf-8")

    def close(self):
        try:
            if self.active_run and self.runtime:
                state = HTTP.decoded(self.runtime.endpoint, "/v1/runs/" + self.active_run, self.tokens["admin"])
                if state["status"] == "running":
                    HTTP.decoded(self.runtime.endpoint, "/v1/runs/cancel", self.tokens["admin"],
                        self.command("runtime.cancel", {"run_id": self.active_run, "reason_code": "replica_acceptance_cleanup"}))
        finally:
            for resource in reversed(self.resources):
                resource.close()
