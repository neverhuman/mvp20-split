"""Independent public HTTP peers for numeric graphs; no owner imports or SQL."""

import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ROOT = Path(__file__).absolute().parents[5]
GRAPH = load("numeric_graph_hosts", ROOT / "services/campaign_runtime/tests/scheduling/acceptance/probe.py")
RELAY = load("numeric_artifact_relay", ROOT / "services/campaign_runtime/tests/bindings/acceptance/relay.py")
DEFINITION = load("numeric_definition", Path(__file__).parents[1] / "definition.py")
SPECIFICATION = load("numeric_specification", Path(__file__).parents[1] / "specification.py")
HTTP = GRAPH.HTTP
IMAGE = "c" * 64  # Declared test identity; image builds remain a separate acceptance tier.


class NumericEnvironment(GRAPH.GraphEnvironment):
    def tool_cli(self, stage, action, *arguments):
        numeric = stage != "evaluate"
        module = "amphora_evolution_search" if numeric else "amphora_synthetic_objectives"
        selector = ["--operation", stage] if numeric else []
        process = subprocess.run([self.config["numeric" if numeric else "evaluator"], "-I", "-m", module,
            action, *selector, *arguments], cwd=self.root, env=HTTP.isolated_env(), capture_output=True, check=False, timeout=30)
        assert process.returncode == 0, process.stderr.decode()[-1500:]
        return process.stdout

    def setup(self):
        self.scope["tenant_id"] = "numeric-http"
        releases, schemas, profiles = [], {}, []
        self.releases = {}
        for stage in ("seed", "requests", "collect", "vary", "evaluate"):
            release = json.loads(self.tool_cli(stage, "describe", "--image-sha256", IMAGE))
            self.releases[stage] = release
            filename = stage + "-descriptor.json"
            (self.root / filename).write_text(json.dumps(release), encoding="utf-8")
            releases.append({"descriptor": filename, "lock": GRAPH.BASE.WIRE.release_lock(release)})
            for kind in (("input", "output", "policy") if stage == "evaluate" else ("input", "output")):
                body = self.tool_cli(stage, "schema", "--kind" if stage == "evaluate" else "--direction", kind)
                ports = release["tool"]["outputs" if kind == "output" else "inputs"]
                port = next(port for port in ports if (port["name"] == "policy") == (kind == "policy"))
                reference = port["schema_ref"]
                assert hashlib.sha256(body).hexdigest() == reference["sha256"]
                key = json.dumps(reference, sort_keys=True)
                if key in schemas:
                    assert (self.root / schemas[key]["path"]).read_bytes() == body
                    continue
                filename = stage + "-" + kind + ".json"
                (self.root / filename).write_bytes(body)
                schemas[key] = {"schema_ref": reference, "path": filename}
                profiles.append({**reference, "media_type": "application/json", "schema_path": filename})
        self.definition = DEFINITION.campaign(self.scope, self.releases, 2)
        (self.root / "graph.json").write_text(json.dumps(self.definition), encoding="utf-8")
        graph = {"definition": "graph.json", "releases": releases, "schemas": list(schemas.values())}
        runtime_port = HTTP.free_port()
        (self.root / "storage").mkdir()
        self.artifact = self.host("artifact", "amphora_data_artifacts", {
            "database_url_env": "DATABASE_URL", "storage_root": str(self.root / "storage"), "profiles": profiles,
            "principals": [self.principal(actor, ["upload", "finalize", "read"]) for actor in ("worker1", "worker2")]
                + [self.principal("runtime", ["upload", "finalize", "read", "retention"])],
            "runtime": {"owner": "runtime", "endpoint": f"http://127.0.0.1:{runtime_port}/v1/completion-intents/outcome",
                        "token_env": "TOKEN_ARTIFACT"}}, "AMPHORA_ARTIFACT_DATABASE_URL")
        self.artifact_relay = RELAY.ArtifactRelay(HTTP, self.artifact.endpoint)
        self.resources.append(self.artifact_relay)
        endpoint = self.artifact_relay.endpoint
        self.runtime = self.host("runtime", "amphora_campaign_runtime", {
            "database_url_env": "DATABASE_URL", "fixtures": [], "graphs": [graph],
            "tools": [release["tool"] for release in self.releases.values()],
            "principals": [self.principal("admin", ["admit", "cancel", "read", "inspect_receipts", "deliver", "maintain"]),
                self.principal("artifact", ["outcome"])] +
                [self.principal(actor, ["claim", "renew", "complete", "read"]) for actor in ("worker1", "worker2")],
            "artifacts": {"runtime_owner": "runtime", "reserve_endpoint": endpoint + "/v1/reservations", "token_env": "TOKEN_RUNTIME"},
            "bindings": {"endpoint": endpoint, "token_env": "TOKEN_RUNTIME"},
            "projections": {"endpoint": endpoint, "token_env": "TOKEN_RUNTIME"},
            "inspection": {"cursor_key_env": "CURSOR_KEY"}}, "AMPHORA_RUNTIME_DATABASE_URL", runtime_port)
        self.runtime_relay = HTTP.FaultRelay(self.runtime.endpoint)
        self.resources.append(self.runtime_relay)
        self.plans = self.compile(self.config["runtime"])

    def publish_bytes(self, body, schema):
        content = {"sha256": hashlib.sha256(body).hexdigest(), "size_bytes": len(body),
                   "media_type": "application/json", "schema_ref": schema}
        token = self.tokens["worker1"]
        upload = HTTP.decoded(self.artifact.endpoint, "/v1/uploads", token,
            self.command("artifacts.begin_upload", {"content": content}, "worker1"))
        assert HTTP.request(self.artifact.endpoint, "/v1/uploads/" + upload["upload_id"] + "/content", token, body, "PUT")[0] == 200
        return HTTP.decoded(self.artifact.endpoint, "/v1/artifacts/finalize", token,
            self.command("artifacts.finalize", {"upload_id": upload["upload_id"], "content": content}, "worker1"))["artifact"]

    def bytes(self, artifact):
        status, body = HTTP.request(self.artifact.endpoint, "/v1/artifacts/" + artifact["artifact_id"] + "/content", self.tokens["worker1"])
        assert status == 200 and len(body) == artifact["size_bytes"] and hashlib.sha256(body).hexdigest() == artifact["sha256"]
        return body

    def graph(self):
        return HTTP.decoded(self.runtime.endpoint, "/v3/graph-runs/" + self.active_run, self.tokens["admin"])

    def admit(self, *, reuse=False):
        if not reuse:
            self.prepare_inputs()
        self.admission_command = self.command("graph.admit", {"plan_sha256": self.plans["numeric-search-fixture"]["sha256"],
            "inputs": self.inputs, "budget": {"limit": 256, "max_attempts_per_activation": 2}})
        self.admission = HTTP.decoded(self.runtime.endpoint, "/v1/graph-runs", self.tokens["admin"], self.admission_command)
        assert self.admission["outcome"]["status"] == "accepted"
        self.active_run = self.admission["outcome"]["committed"]["object_id"]

    def prepare_inputs(self):
        self.policy = self.publish_bytes(self.tool_cli("evaluate", "policy"), self.releases["evaluate"]["tool"]["inputs"][1]["schema_ref"])
        self.specification = SPECIFICATION.specification(self.scope, self.releases, self.policy)
        spec = self.publish_bytes(json.dumps(self.specification, sort_keys=True, separators=(",", ":")).encode(),
                                  self.releases["seed"]["tool"]["inputs"][0]["schema_ref"])
        refs = {"specification": spec, "policy": self.policy}
        self.inputs = [{"port": port["name"], "value": {"kind": "artifact", "artifact": refs[port["name"]],
            "representation": port["value_type"]["representation"], "unit": port["value_type"]["unit"]}}
            for port in self.definition["body"]["inputs"]]

    def restart_runtime(self):
        old = self.runtime
        before = self.graph()
        old.close()
        self.runtime = HTTP.Service(old.python, "amphora_campaign_runtime", old.config, old.env, self.root, old.port)
        self.resources.append(self.runtime)
        self.runtime.ready(self.tokens["admin"])
        assert self.graph() == before
        assert self.compile(old.python) == self.plans
        return before
