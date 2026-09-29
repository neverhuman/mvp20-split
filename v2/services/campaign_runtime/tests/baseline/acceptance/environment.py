"""Public installed solver peers; controller imports no owner implementation or SQL."""

import hashlib
import importlib.util
import json
from pathlib import Path


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ROOT = Path(__file__).absolute().parents[5]
BINDING = load("solver_binding_environment", ROOT / "services/campaign_runtime/tests/bindings/acceptance/probe.py")
DEFINITION = load("solver_definition", Path(__file__).parents[1] / "definition.py")
HTTP = BINDING.HTTP


class SolverEnvironment(BINDING.BindingEnvironment):
    def setup(self):
        self.scope["tenant_id"] = "solver-acceptance"
        BINDING.GRAPH.BASE.Environment.setup(self)
        self.stages = {tool.module.removeprefix("amphora_solver_"): tool for tool in self.tools}
        artifact = json.loads(Path(self.artifact.config).read_bytes())
        next(p for p in artifact["principals"] if p["actor_id"] == "runtime")["actions"].extend(["upload", "finalize", "read"])
        port = self.artifact.port
        self.artifact.close()
        self.artifact = self.host("artifact", "amphora_data_artifacts", artifact, "AMPHORA_ARTIFACT_DATABASE_URL", port)
        self.binding_relay = BINDING.RELAY.ArtifactRelay(HTTP, self.artifact.endpoint)
        self.resources.append(self.binding_relay)
        config = json.loads(Path(self.runtime.config).read_bytes())
        config.update(fixtures=[], graphs=self.configure(), bindings={"endpoint": self.binding_relay.endpoint, "token_env": "TOKEN_RUNTIME"})
        config["artifacts"]["reserve_endpoint"] = self.binding_relay.endpoint + "/v1/reservations"
        next(p for p in config["principals"] if p["actor_id"] == "admin")["actions"].append("maintain")
        port = self.runtime.port
        self.runtime.close()
        self.runtime = self.host("runtime", "amphora_campaign_runtime", config, "AMPHORA_RUNTIME_DATABASE_URL", port)
        self.plans = self.compile(self.config["runtime"])
        oracles = json.loads((Path(__file__).parents[2] / "fixtures/v1_solver/expected_traces.json").read_bytes())
        self.oracle = next(case for case in oracles["cases"] if case["name"] == "two_generations")

    def configure(self):
        releases, schemas = [], {}
        for tool in self.tools:
            path = self.root / (tool.key + "-release.json")
            path.write_text(json.dumps(tool.image["descriptor"]), encoding="utf-8")
            releases.append({"descriptor": path.name, "lock": tool.lock})
            for kind, ports in (("input", tool.descriptor["inputs"]), ("output", tool.descriptor["outputs"])):
                reference = ports[0]["schema_ref"]
                schemas.setdefault(json.dumps(reference, sort_keys=True), {"schema_ref": reference, "path": tool.module + "-" + kind + ".json"})
        descriptors = {stage: tool.image["descriptor"] for stage, tool in self.stages.items()}
        entries = []
        self.definitions = {}
        for name, generations, continuation in (("initial-population", 0, False), ("continued-generations", 2, True)):
            raw = DEFINITION.campaign(self.scope, descriptors, generations, continuation=continuation)
            raw["campaign_id"] = name
            self.definitions[name] = raw
            path = self.root / (name + ".json")
            path.write_text(json.dumps(raw), encoding="utf-8")
            entries.append({"definition": path.name, "releases": releases, "schemas": list(schemas.values())})
        return entries

    def report(self, worker, claim, publication):
        invocation = claim["outcome"]["invocation"]
        receipt = HTTP.decoded(self.runtime.endpoint, "/v1/commands/runtime.complete/complete-" + invocation["attempt_id"] +
            "?actor_id=" + worker.actor, self.tokens["admin"])
        completion = HTTP.decoded(self.runtime.endpoint, "/v1/runs/" + self.active_run + "/completions/" +
            receipt["outcome"]["committed"]["object_id"], self.tokens["admin"])
        artifact = completion["result"]["outcome"]["outputs"][0]["artifact"]
        assert completion["canonical_result"] and len(completion["retention_reservation_ids"]) == 1
        assert artifact == publication["artifact"]
        source = json.loads(self.bytes(invocation["inputs"][0]["artifact"]))
        result = json.loads(self.bytes(artifact))
        stage = worker.tool.module.removeprefix("amphora_solver_")
        if stage == "score":
            assert result["candidate"] == source["candidate"]
            assert not result["ranked"] and result["eligible_objectives"] == 0
            assert all(module["authority"] == "NO_AUTHORITY" for module in result["modules"])
        if stage == "retain":
            expected = self.oracle["generations"][result["generation"]]
            assert [item["candidate"]["candidate_id"] for item in result["current"]] == expected["current"]
            assert [item["candidate"]["candidate_id"] for item in result["cumulative"]] == expected["cumulative"]
        return {"stage": stage, "invocation": invocation, "receipt": receipt, "completion": completion, "input": source, "result": result}

    def execute(self):
        reports = []
        for _ in range(100):
            page = self.advance()
            if page["status"] != "running":
                break
            pending = [node for node in page["nodes"] if node["kind"] == "invoke" and node["status"] == "issued"]
            for stage in dict.fromkeys(node["path"]["node_id"] for node in pending):
                tool = self.stages[stage]
                count = sum(node["path"]["node_id"] == stage for node in pending)
                BINDING.GRAPH.OPS.select(self, tool)
                # Two independent worker processes exercise concurrent public claims.
                workers = [self.worker(tool, actor) for actor in ("worker1", "worker2")[:min(count, 2)]]
                try:
                    claimed = [(worker, worker.wait("claimed")) for worker in workers]
                    if stage == "score":
                        claimed.sort(key=lambda pair: json.loads(self.bytes(pair[1]["outcome"]["invocation"]["inputs"][0]["artifact"]))["candidate"]["proposal_index"], reverse=True)
                    for worker, _ in claimed:
                        reports.append(self.finish_worker(worker))
                finally:
                    for worker in workers:
                        worker.close()
        assert page["status"] == "completed" and page["reserved"] == 0, page
        assert page["spent"] == len(reports)
        return page, reports

    def export(self, run, report):
        cut = HTTP.decoded(self.runtime.endpoint, "/v1/graph-runs/" + run + "/carry-sources", self.tokens["admin"])
        artifact = report["completion"]["result"]["outcome"]["outputs"][0]["artifact"]
        port = self.stages["retain"].descriptor["outputs"][0]
        value = {"kind": "artifact", "artifact": artifact, "representation": port["representation"], "unit": port["unit"]}
        expected = hashlib.sha256(json.dumps({"profile": "amphora-carried-value-v1", "value": value},
            sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()
        assert cut["predecessor_ready"] and cut["sources"] == [{"source": {"kind": "run_output", "port": "result"}, "value_sha256": expected}]
        return cut, artifact
