"""Public test observations shared by bounded replica scenarios, with independent oracles."""

import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("replica_operations_processes", Path(__file__).with_name("processes.py"))
processes = importlib.util.module_from_spec(spec)
spec.loader.exec_module(processes)


class Campaign:
    def __init__(self, e, http, tool):
        self.e, self.http, self.tool = e, http, tool
        fixture = e.fixtures[tool.key + "-1"]
        admitted = http.decoded(e.runtime.endpoint, "/v1/fixture-runs", e.tokens["admin"], e.command("runtime.admit_fixture", fixture))
        assert admitted["outcome"]["status"] == "accepted"
        self.run_id = e.active_run = admitted["outcome"]["committed"]["object_id"]

    def snapshot(self):
        return self.http.decoded(self.e.runtime.endpoint, "/v1/runs/" + self.run_id, self.e.tokens["admin"])

    def worker(self, actor, **kwargs):
        assert self.e.active_run == self.run_id
        return processes.Worker(self.e, self.http, self.tool, actor, **kwargs)

    def finish(self, worker):
        claim = worker.wait("claimed")
        worker.resume()
        published = worker.wait("published")
        worker.resume()
        assert worker.result()["outcome"] == "succeeded"
        record = self.report(claim["outcome"]["invocation"]["attempt_id"], worker.actor)
        assert record["completion"]["result"]["outcome"]["outputs"][0]["artifact"] == published["artifact"]
        assert record["result"] == self.tool.image["golden_output"]
        assert self.snapshot()["status"] == "completed"
        self.e.active_run = None
        return record

    def report(self, attempt, actor):
        e, http = self.e, self.http
        receipt = http.decoded(e.runtime.endpoint, "/v1/commands/runtime.complete/complete-" + attempt + "?actor_id=" + actor,
            e.tokens["admin"])
        report = http.decoded(e.runtime.endpoint, "/v1/runs/" + self.run_id + "/completions/" + receipt["outcome"]["committed"]["object_id"],
            e.tokens["admin"])
        assert report["canonical_result"] is True
        artifact = report["result"]["outcome"]["outputs"][0]["artifact"]
        result = http.decoded(e.artifact.endpoint, "/v1/artifacts/" + artifact["artifact_id"] + "/content", e.tokens[actor])
        return {"run_id": self.run_id, "receipt": receipt, "completion": report, "result": result}


def select(e, tool):
    e.refresh_capacity(tool)
    result = e.registry_call("resolve", {"release": tool.lock, "context": "synthetic-tests",
        "inputs": tool.descriptor["inputs"], "outputs": tool.descriptor["outputs"]})
    assert result["decision"]["status"] == "candidate"
    return result
