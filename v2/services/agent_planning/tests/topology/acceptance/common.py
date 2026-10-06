"""Public-only controller support and owned process lifecycle."""

import importlib.util
import json
import os
import subprocess
import time
import uuid
from hashlib import sha256
from pathlib import Path
from urllib.error import URLError

ROOT = Path(__file__).absolute().parents[5]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


HTTP = load("topology_http", ROOT / "services/campaign_runtime/tests/acceptance/paired_support.py")
WIRE = load("topology_wire", ROOT / "tests/integration/tool_replicas/wire.py")


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode()


def digest(value):
    return sha256(encoded(value)).hexdigest()


class Service(HTTP.Process):
    def close(self):
        if self.child.poll() is None:
            self.child.terminate()
        try:
            _, stderr = self.child.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            self.child.kill()
            _, stderr = self.child.communicate(timeout=10)
        if stderr:
            with (self.cwd / (self.module + ".log")).open("ab") as stream:
                stream.write(stderr.encode() if isinstance(stderr, str) else stderr)

    def start(self, *args, **kwargs):
        if self.module != "amphora_agent_planning.supervision_api":
            return super().start(*args, **kwargs)
        self.child = subprocess.Popen([self.python, "-I", "-m", self.module, "--port", str(self.port)],
                                     cwd=self.cwd, env=self.env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

    def ready(self, token, route="/ready"):
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline and self.child.poll() is None:
            try:
                if HTTP.request(self.endpoint, route, token)[0] == 200:
                    return
            except (URLError, TimeoutError):
                pass
            time.sleep(0.1)
        raise RuntimeError("topology_owner_not_ready:" + self.module)


class Peers:
    def __init__(self, config, root):
        self.config, self.root = config, root
        self.scope = {"tenant_id": "topology-handoff", "project_id": uuid.uuid4().hex}
        self.tokens = {actor: uuid.uuid4().hex + uuid.uuid4().hex for actor in ("admin", "worker", "runtime", "artifact", "planning")}
        self.services = []

    def principal(self, actor, actions):
        return {"actor_id": actor, "scope": self.scope, "actions": actions, "token_env": "TOKEN_" + actor.upper()}

    def command(self, family, payload, actor="admin", key=None):
        return {"identity": {"scope": self.scope, "actor_id": actor, "command_family": family,
                             "command_id": key or uuid.uuid4().hex}, "payload": payload}

    def cli(self, owner, module, *args, payload=None):
        result = subprocess.run([self.config[owner], "-I", "-m", module, *args], input=payload,
                                env=HTTP.isolated_env(), cwd=self.root, capture_output=True, timeout=60)
        if result.returncode:
            raise RuntimeError("topology_tool_cli_failed:" + owner)
        return result.stdout

    def host(self, owner, module, config, *, port=None):
        path = self.root / (owner + ".json")
        path.write_bytes(encoded(config))
        env = dict(HTTP.isolated_env(), DATABASE_URL=os.environ["AMPHORA_" + owner.upper() + "_DATABASE_URL"])
        actors = {p["actor_id"] for p in config["principals"]}
        if owner == "runtime":
            actors.update(("runtime", "planning"))
            env["CURSOR_KEY"] = uuid.uuid4().hex
        if owner == "artifact": actors.add("artifact")
        env.update({"TOKEN_" + actor.upper(): self.tokens[actor] for actor in actors})
        process = Service(self.config[owner], module, path, env, self.root, port or HTTP.free_port())
        self.services.append(process)
        process.ready(self.tokens["admin"], "/v1/releases" if owner == "registry" else "/ready")
        setattr(self, owner, process)
        return process

    def call(self, owner, path, payload=None, actor="admin"):
        return HTTP.decoded(getattr(self, owner).endpoint, path, self.tokens[actor], payload)

    def registry_command(self, action, payload, actor="admin"):
        return self.call("registry", "/v1/registry/" + action, self.command("registry." + action, payload, actor), actor)

    def publish(self, data, schema):
        content = {"sha256": sha256(data).hexdigest(), "size_bytes": len(data), "media_type": "application/json", "schema_ref": schema}
        upload = self.call("artifact", "/v1/uploads", self.command("artifacts.begin_upload", {"content": content}))
        assert HTTP.request(self.artifact.endpoint, "/v1/uploads/" + upload["upload_id"] + "/content",
                            self.tokens["admin"], data, "PUT")[0] == 200
        return self.call("artifact", "/v1/artifacts/finalize", self.command("artifacts.finalize", {"upload_id": upload["upload_id"], "content": content}))["artifact"]

    def read_bytes(self, artifact):
        status, raw = HTTP.request(self.artifact.endpoint, "/v1/artifacts/" + artifact["artifact_id"] + "/content", self.tokens["admin"])
        assert status == 200 and sha256(raw).hexdigest() == artifact["sha256"] and len(raw) == artifact["size_bytes"]
        return raw

    def close(self):
        if hasattr(self, "active_run") and self.active_run:
            try:
                self.call("runtime", "/v1/runs/cancel", self.command("runtime.cancel", {"run_id": self.active_run, "reason_code": "acceptance_cleanup"}))
            except Exception:
                pass
        for service in reversed(self.services):
            service.close()
