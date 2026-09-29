"""Public graph/worker/Artifact acceptance controlled from an isolated SDK interpreter."""

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ROOT = Path(__file__).absolute().parents[5]
BASE = load("graph_peer_environment", ROOT / "tests/integration/tool_replicas/environment.py")
OPS = load("graph_peer_operations", ROOT / "tests/integration/tool_replicas/operations.py")
DEFINITIONS = load("graph_test_definitions", Path(__file__).with_name("definitions.py"))
HTTP = BASE.HTTP


class GraphEnvironment(BASE.Environment):
    def setup(self):
        self.scope["tenant_id"] = "graph-acceptance"
        super().setup()
        artifact_config = json.loads(Path(self.artifact.config).read_bytes())
        next(principal for principal in artifact_config["principals"] if principal["actor_id"] == "runtime")["actions"].append("read")
        artifact_port = self.artifact.port
        self.artifact.close()
        self.artifact = self.host("artifact", "amphora_data_artifacts", artifact_config, "AMPHORA_ARTIFACT_DATABASE_URL", artifact_port)
        config = json.loads(Path(self.runtime.config).read_bytes())
        config.update(fixtures=[], graphs=DEFINITIONS.configure(self), projections={
            "endpoint": self.artifact.endpoint, "token_env": "TOKEN_RUNTIME"})
        next(principal for principal in config["principals"] if principal["actor_id"] == "admin")["actions"].append("maintain")
        port = self.runtime.port
        self.runtime.close()
        self.runtime = self.host("runtime", "amphora_campaign_runtime", config, "AMPHORA_RUNTIME_DATABASE_URL", port)
        self.plans = self.compile(self.config["runtime"])
        assert HTTP.decoded(self.runtime.endpoint, "/health", self.tokens["admin"])["mode"] == "configured_graphs"

    def compile(self, python):
        result = subprocess.run([python, "-I", str(Path(__file__).with_name("compile_plans.py")), self.runtime.config],
            cwd=self.root, env=HTTP.isolated_env(), capture_output=True, text=True, encoding="utf-8", timeout=30)
        assert result.returncode == 0, result.stderr[-2500:]
        return json.loads(result.stdout)

    def graph(self):
        return HTTP.decoded(self.runtime.endpoint, "/v1/graph-runs/" + self.active_run, self.tokens["admin"])

    def advance(self):
        receipt = HTTP.decoded(self.runtime.endpoint, "/v1/graph-runs/advance", self.tokens["admin"],
            self.command("graph.advance", {"run_id": self.active_run}))
        assert receipt["outcome"]["status"] == "accepted"
        return self.graph()

    def admit_graph(self, name, tool, *, items=None):
        selection = OPS.select(self, tool)
        reference = self.fixtures[tool.key + "-1"]["invocations"][0]["inputs"][0]["artifact"]
        value = {"kind": "artifact", "artifact": reference, "representation": tool.descriptor["inputs"][0]["representation"],
                 "unit": tool.descriptor["inputs"][0]["unit"]}
        inputs = [{"port": "parameters", "value": value}] if items is None else [
            {"port": "items", "value": {"kind": "collection", "items": [value] * items}}]
        command = self.command("graph.admit", {"plan_sha256": self.plans[name]["sha256"], "inputs": inputs,
                                                "budget": {"limit": 8}})
        receipt = HTTP.decoded(self.runtime.endpoint, "/v1/graph-runs", self.tokens["admin"], command)
        assert receipt["outcome"]["status"] == "accepted"
        self.active_run = receipt["outcome"]["committed"]["object_id"]
        self.admission = command, receipt
        self.advance()
        return selection

    def worker(self, tool, actor):
        return OPS.processes.Worker(self, HTTP, tool, actor)

    def finish_worker(self, worker):
        claim = worker.wait("claimed")
        worker.resume()
        publication = worker.wait("published")
        worker.resume()
        outcome = worker.result()
        assert outcome["status"] == "completion_accepted" and outcome["outcome"] == "succeeded"
        return self.report(worker, claim, publication)

    def report(self, worker, claim, publication):
        invocation = claim["outcome"]["invocation"]
        receipt = HTTP.decoded(self.runtime.endpoint, "/v1/commands/runtime.complete/complete-" + invocation["attempt_id"] +
            "?actor_id=" + worker.actor, self.tokens["admin"])
        completion = HTTP.decoded(self.runtime.endpoint, "/v1/runs/" + self.active_run + "/completions/" +
            receipt["outcome"]["committed"]["object_id"], self.tokens["admin"])
        assert completion["canonical_result"] is True and len(completion["retention_reservation_ids"]) == 1
        artifact = completion["result"]["outcome"]["outputs"][0]["artifact"]
        assert artifact == publication["artifact"]
        result = HTTP.decoded(self.artifact.endpoint, "/v1/artifacts/" + artifact["artifact_id"] + "/content", self.tokens[worker.actor])
        assert result == worker.tool.image["golden_output"]
        return {"run_id": self.active_run, "receipt": receipt, "completion": completion, "result": result}

    def complete_case(self, name, selection, reports, expected_nodes, spent):
        page = self.graph()
        if page["status"] == "running":
            page = self.advance()
        assert page["status"] == "completed" and page["node_count"] == expected_nodes
        assert (page["spent"], page["reserved"]) == (spent, 0)
        assert all(node["status"] in {"succeeded", "skipped"} for node in page["nodes"])
        replay = HTTP.decoded(self.runtime.endpoint, "/v1/graph-runs", self.tokens["admin"], self.admission[0])
        assert replay == self.admission[1]
        self.record(name, {"selection": selection, "admission": self.admission[1], "graph": page, "reports": reports})
        self.active_run = None

    def owner_command(self, action, *arguments):
        result = subprocess.run([self.runtime.python, "-I", "-m", "amphora_campaign_runtime", action,
            "--config", self.runtime.config, "--actor", "admin", "--tenant", self.scope["tenant_id"],
            "--project", self.scope["project_id"], *arguments], cwd=self.root, env=self.runtime.env,
            capture_output=True, text=True, encoding="utf-8", timeout=30)
        assert result.returncode == 0, result.stderr[-1500:]
        return json.loads(result.stdout)

    def replace_runtime(self):
        old = self.runtime
        old.close()
        self.runtime = HTTP.Service(self.config["replacements"]["amphora_campaign_runtime"], "amphora_campaign_runtime",
            old.config, old.env, self.root, old.port)
        self.resources.append(self.runtime)
        self.runtime.ready(self.tokens["admin"])
        assert self.compile(self.config["replacements"]["amphora_campaign_runtime"]) == self.plans


def scenarios(e):
    numeric, sequence = e.tools
    for plan, tool, name in (("affine", numeric, "GRAPH-NUMERIC"), ("branch-join", numeric, "GRAPH-PROJECTED-BRANCH"),
                             ("symbol-statistics", sequence, "GRAPH-SEQUENCE")):
        selection = e.admit_graph(plan, tool)
        worker = e.worker(tool, "worker1")
        report = e.finish_worker(worker)
        assert e.graph()["status"] == "running", "Worker completion cannot close the graph"
        if plan == "affine":
            report["polling"] = e.owner_command("coordinate", "--time-budget", "0.3", "--poll-interval", "0.05")
            assert report["polling"]["advanced"] >= 1 and report["polling"]["projection_unavailable"] == 0
            assert e.graph()["status"] == "completed"
        e.complete_case(name, selection, [report], 5 if plan == "branch-join" else 2, 1)

    selection = e.admit_graph("bounded-loop", numeric)
    reports = []
    for index in range(2):
        worker = e.worker(numeric, "worker1")
        reports.append(e.finish_worker(worker))
        if index == 0:
            page = e.advance()
            assert page["status"] == "running" and page["node_count"] == 6
    e.complete_case("GRAPH-TOOL-ITERATIONS", selection, reports, 6, 2)

    selection = e.admit_graph("bounded-scatter", numeric, items=0)
    page = e.graph()
    assert page["status"] == "completed" and page["node_count"] == 2 and page["spent"] == 0
    e.record("GRAPH-EMPTY-SCATTER", {"selection": selection, "graph": page, "admission": e.admission[1]})
    e.active_run = None

    selection = e.admit_graph("bounded-scatter", numeric, items=2)
    workers = [e.worker(numeric, actor) for actor in ("worker1", "worker2")]
    claims = [worker.wait("claimed") for worker in workers]
    assert len({claim["outcome"]["invocation"]["invocation_id"] for claim in claims}) == 2
    for worker in workers:
        worker.resume()
    publications = [worker.wait("published") for worker in workers]
    before = e.graph()
    e.replace_runtime()
    assert e.graph() == before
    assert HTTP.decoded(e.runtime.endpoint, "/v1/graph-runs", e.tokens["admin"], e.admission[0]) == e.admission[1]
    # Reverse completion order across a real Runtime replacement; no checkpoint/authority comes from the relay.
    e.runtime_relay.drop_path = "/v1/invocations/complete"
    reports = []
    for worker, claim, publication in reversed(list(zip(workers, claims, publications, strict=True))):
        worker.resume()
        assert worker.result()["outcome"] == "succeeded"
        reports.append(e.report(worker, claim, publication))
    e.complete_case("GRAPH-SCATTER-RUNTIME-REPLACEMENT", selection, reports, 6, 2)
    assert any(event.get("fault") == "response_dropped_after_owner_success" for event in e.runtime_relay.events)
    # Replacement must preserve completed historical graph observations, receipts and actual artifact bytes.
    for case in e.cases:
        run = case["graph"]["run_id"]
        assert HTTP.decoded(e.runtime.endpoint, "/v1/graph-runs/" + run, e.tokens["admin"]) == case["graph"]
        for report in case.get("reports", []):
            artifact = report["completion"]["result"]["outcome"]["outputs"][0]["artifact"]
            assert HTTP.decoded(e.artifact.endpoint, "/v1/artifacts/" + artifact["artifact_id"] + "/content",
                                e.tokens["worker1"]) == report["result"]
    e.record("GRAPH-RETAINED-HISTORY", {"preserved_cases": len(e.cases), "plans": e.plans})
    delivery = e.owner_command("deliver", "--limit", "100", "--time-budget", "5")
    assert delivery["acknowledged"] == 7
    e.record("GRAPH-POLLING-AND-RETENTION", {"polling": e.cases[0]["reports"][0]["polling"],
        "delivery": delivery, "actual_artifact_confirmations": 7,
        "notification_target_configured": False})


def main():
    config = json.loads(Path(sys.argv[1]).read_bytes())
    with tempfile.TemporaryDirectory(prefix="amphora-graph-peers-") as directory:
        e = GraphEnvironment(config, Path(directory))
        try:
            e.setup()
            scenarios(e)
            e.save("passed")
            print("Installed graph execution/replacement passed; scope " + e.scope["project_id"], flush=True)
        except BaseException:
            e.save("failed")
            raise
        finally:
            e.close()


if __name__ == "__main__":
    main()
