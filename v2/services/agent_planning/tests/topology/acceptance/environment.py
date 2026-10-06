"""Independent owner configuration and immutable synthetic release registration."""

import base64
import json
import os
import subprocess
from hashlib import sha256
from pathlib import Path

import common


class Environment(common.Peers):
    def setup(self):
        self.descriptors, self.locks = {}, {}
        self.images = {"numeric-old": "c" * 64, "numeric-new": "d" * 64}
        schemas, profiles, releases = [], [], []
        for owner in self.images:
            descriptor = json.loads(self.cli(owner, "amphora_numeric_affine", "describe", "--image-sha256", self.images[owner]))
            self.descriptors[owner] = descriptor
            lock = self.locks[owner] = common.WIRE.release_lock(descriptor)
            filename = owner + "-release.json"
            (self.root / filename).write_bytes(common.encoded(descriptor))
            releases.append({"descriptor": filename, "lock": lock})
        assert self.locks["numeric-old"]["tool"]["release"] == "0.2.0"
        assert self.locks["numeric-new"]["tool"]["release"] == "0.3.0"
        script = "import base64,json; from importlib.resources import files; print(json.dumps({k:base64.b64encode(files('amphora_numeric_affine').joinpath('schemas',k+'.json').read_bytes()).decode() for k in ('input','output')}))"
        result = subprocess.run([self.config["numeric-old"], "-I", "-c", script], env=common.HTTP.isolated_env(), capture_output=True, check=True)
        documents = json.loads(result.stdout)
        for kind, ports in (("input", "inputs"), ("output", "outputs")):
            raw = base64.b64decode(documents[kind])
            reference = self.descriptors["numeric-old"]["tool"][ports][0]["schema_ref"]
            assert sha256(raw).hexdigest() == reference["sha256"]
            assert self.descriptors["numeric-new"]["tool"][ports][0]["schema_ref"] == reference
            filename = "numeric-" + kind + ".json"
            (self.root / filename).write_bytes(raw)
            schemas.append({"schema_ref": reference, "path": filename})
            profiles.append({**reference, "media_type": "application/json", "schema_path": filename})
        self.evidence_schemas = {}
        for name in ("benchmark", "handoff"):
            identity = "fixture.topology-" + name
            raw = common.encoded({"$schema": "https://json-schema.org/draft/2020-12/schema",
                                  "$id": f"urn:amphora:{identity}:1:validation", "type": "object"}) + b"\n"
            reference = {"schema_id": identity, "version": "1", "sha256": sha256(raw).hexdigest()}
            self.evidence_schemas[name] = reference
            filename = name + "-schema.json"
            (self.root / filename).write_bytes(raw)
            profiles.append({**reference, "media_type": "application/json", "schema_path": filename})
        self.host("registry", "amphora_capability_registry", {
            "database_url_env": "DATABASE_URL", "principals": [
                self.principal("admin", ["register", "activate", "deploy", "resolve", "read"]),
                self.principal("worker", ["heartbeat"]), self.principal("planning", ["read"])],
            "resources": {"architecture": "x86_64", "operating_system": "linux", "cpu_millicores": 4000,
                          "memory_mib": 4096, "gpu_count": 0, "timeout_seconds": 300, "max_parallel_invocations": 8, "max_batch_size": 128}})
        self.registry_records = []
        self.revisions = {}
        for owner, descriptor in self.descriptors.items():
            lock = self.locks[owner]
            registered = self.registry_command("register", {"scope": self.scope, "descriptor": descriptor, "expected_lock": lock})
            active = self.registry_command("activate", {"release": lock, "expected_revision": 1})
            deployment = self.registry_command("deploy", {"deployment_id": owner, "release": lock,
                "architecture": "x86_64", "operating_system": "linux", "workers": ["worker"]})
            assert registered["status"] == active["status"] == deployment["status"] == "accepted"
            self.registry_records.append({"registered": registered, "activated": active, "deployed": deployment})
            self.revisions[owner] = 0
            self.heartbeat(owner)

        runtime_port = common.HTTP.free_port()
        (self.root / "storage").mkdir()
        self.host("artifact", "amphora_data_artifacts", {"database_url_env": "DATABASE_URL",
            "storage_root": str(self.root / "storage"), "profiles": profiles,
            "principals": [self.principal("admin", ["upload", "finalize", "read"]),
                self.principal("worker", ["upload", "finalize", "read"]), self.principal("runtime", ["upload", "finalize", "read", "retention"])],
            "runtime": {"owner": "runtime", "endpoint": f"http://127.0.0.1:{runtime_port}/v1/completion-intents/outcome", "token_env": "TOKEN_ARTIFACT"}})
        ports = self.descriptors["numeric-old"]["tool"]
        def value_type(port):
            return {"kind": "artifact", "media_type": "application/json", **{k: port[k] for k in ("schema_ref", "representation", "unit")}}
        self.parameter_type = value_type(ports["inputs"][0])
        result_type = value_type(ports["outputs"][0])
        self.definition = {"schema_version": "4", "profile": "deterministic-v3", "campaign_id": "topology-affine", "revision": 1,
            "scope": self.scope, "context": [], "body": {
                "inputs": [{"name": "parameters", "value_type": self.parameter_type}],
                "outputs": [{"name": "parameters", "value_type": self.parameter_type}, {"name": "result", "value_type": result_type}],
                "nodes": [{"kind": "invoke", "node_id": "evaluate", "tool": self.locks["numeric-old"]["tool"],
                           "inputs": [{"port": "parameters", "source": {"kind": "input", "name": "parameters"}}], "checkpoint": None, "timeout_seconds": 30},
                          {"kind": "finish", "node_id": "done", "outputs": [
                              {"port": "parameters", "source": {"kind": "input", "name": "parameters"}},
                              {"port": "result", "source": {"kind": "output", "node_id": "evaluate", "port": "result"}}]}],
                "edges": [{"source": "evaluate", "target": "done", "route": "next"}]}}
        (self.root / "graph.json").write_bytes(common.encoded(self.definition))
        self.host("runtime", "amphora_campaign_runtime", {
            "database_url_env": "DATABASE_URL", "fixtures": [], "graphs": [{"definition": "graph.json", "releases": releases, "schemas": schemas}],
            "authoring": True, "draft_registry": {"endpoint": self.registry.endpoint, "token_env": "TOKEN_ADMIN", "actor_id": "admin"},
            "principals": [self.principal("admin", ["admit", "cancel", "read", "inspect_receipts", "deliver", "maintain", "author", "validate"]),
                self.principal("worker", ["claim", "renew", "complete", "read"]), self.principal("artifact", ["outcome"]), self.principal("planning", ["read"])],
            "tools": [d["tool"] for d in self.descriptors.values()],
            "artifacts": {"runtime_owner": "runtime", "reserve_endpoint": self.artifact.endpoint + "/v1/reservations", "token_env": "TOKEN_RUNTIME"},
            "bindings": {"endpoint": self.artifact.endpoint, "token_env": "TOKEN_RUNTIME"},
            "inspection": {"cursor_key_env": "CURSOR_KEY"}}, port=runtime_port)
        result = subprocess.run([self.config["runtime"], "-I", str(common.ROOT / "services/campaign_runtime/tests/scheduling/acceptance/compile_plans.py"), self.runtime.config],
                                env=common.HTTP.isolated_env(), cwd=self.root, capture_output=True, check=True)
        self.plan = json.loads(result.stdout)["topology-affine"]
        self.parameters = self.publish(common.encoded({"values": [-1, 0, 1], "a": -2, "b": 3}), ports["inputs"][0]["schema_ref"])

    def heartbeat(self, owner):
        receipt = self.registry_command("heartbeat", {"deployment_id": owner, "replica_id": owner + "-worker",
            "expected_revision": self.revisions[owner], "free_slots": 1, "ttl_seconds": 60}, "worker")
        assert receipt["status"] == "accepted"
        self.revisions[owner] = receipt["heartbeat"]["revision"]

    def planning_host(self, policy):
        from amphora_contracts_topology_search import TopologyPolicy
        self.policy = TopologyPolicy.model_validate_json(common.encoded(policy)).model_dump(mode="json")
        self.policy_reference = {"schema_id": "planning.topology-policy", "version": "1",
                                 "sha256": common.digest({"profile": "planning-topology-policy-v1", "policy": self.policy})}
        path = self.root / "topology.json"
        path.write_bytes(common.encoded({"profiles": [{"policy": self.policy, "plan": self.plan}],
            "runtime": {"endpoint": self.runtime.endpoint, "token_env": "TOKEN_PLANNING"},
            "registry": {"endpoint": self.registry.endpoint, "token_env": "TOKEN_PLANNING"}}))
        env = dict(common.HTTP.isolated_env(), AMPHORA_PLANNING_DATABASE_URL=os.environ["AMPHORA_PLANNING_DATABASE_URL"],
            AMPHORA_PLANNING_TOPOLOGY_CONFIG=str(path), TOKEN_PLANNING=self.tokens["planning"],
            AMPHORA_PLANNING_SUPERVISION_CREDENTIALS=json.dumps([{"token": self.tokens["admin"], "actor_id": "admin", "scope": self.scope,
                                                               "actions": ["propose_topology", "read_topology"]}]))
        self.planning = common.Service(self.config["planning"], "amphora_agent_planning.supervision_api", path, env, self.root, common.HTTP.free_port())
        self.services.append(self.planning)
        self.planning.ready(self.tokens["admin"])
