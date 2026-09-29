"""Installed external wait protocol with a real HTTP issuer and Artifact owner, no private SQL."""

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
GRAPH = load("installed_graph_helpers", ROOT / "services/campaign_runtime/tests/scheduling/acceptance/probe.py")
HTTP = GRAPH.HTTP


class WaitEnvironment(GRAPH.GraphEnvironment):
    def setup(self):
        self.scope["tenant_id"] = "wait-acceptance"
        GRAPH.BASE.Environment.setup(self)
        raw = json.loads((ROOT / "contracts/fixtures/v3/await_cases.json").read_bytes())[0]["payload"]
        raw["scope"] = self.scope
        raw["body"]["nodes"][0].update(issuer_id="worker1", timeout_seconds=120)
        path = self.root / "await.json"
        path.write_text(json.dumps(raw), encoding="utf-8")
        schemas = [{"schema_ref": self.tools[0].descriptor[ports][0]["schema_ref"],
            "path": self.tools[0].module + "-" + kind + ".json"} for ports, kind in (("inputs", "input"), ("outputs", "output"))]
        config = json.loads(Path(self.runtime.config).read_bytes())
        config.update(fixtures=[], graphs=[{"definition": path.name, "releases": [], "schemas": schemas}])
        for principal in config["principals"]:
            if principal["actor_id"] == "admin":
                principal["actions"].append("maintain")
            if principal["actor_id"] == "worker1":
                principal["actions"].append("submit_receipt")
        port = self.runtime.port
        self.runtime.close()
        self.runtime = self.host("runtime", "amphora_campaign_runtime", config, "AMPHORA_RUNTIME_DATABASE_URL", port)
        self.plans = self.compile(self.config["runtime"])

    def compile(self, python):
        result = subprocess.run([python, "-I", str(Path(__file__).with_name("compile_plan.py")), self.runtime.config],
            cwd=self.root, env=HTTP.isolated_env(), capture_output=True, text=True, encoding="utf-8", timeout=30)
        assert result.returncode == 0, result.stderr[-2500:]
        return json.loads(result.stdout)

    def graph(self):
        return HTTP.decoded(self.runtime.endpoint, "/v2/graph-runs/" + self.active_run, self.tokens["admin"])

    def wait(self):
        activation = next(node["activation_id"] for node in self.graph()["nodes"] if node["kind"] == "await")
        self.wait_path = "/v1/graph-runs/" + self.active_run + "/waits/" + activation
        return HTTP.decoded(self.runtime.endpoint, self.wait_path, self.tokens["worker1"])

    def issuer(self, status="accepted", **options):
        job = self.root / "issuer-job.json"
        job.write_text(json.dumps({"scope": self.scope, "runtime": self.runtime.endpoint, "artifact": self.artifact.endpoint,
            "wait_path": self.wait_path, "status": status, "output": self.tools[0].image["golden_output"], **options}), encoding="utf-8")
        result = subprocess.run([self.config["runtime"], "-I", str(Path(__file__).with_name("issuer.py")), str(job)],
            cwd=self.root, env={**HTTP.isolated_env(), "ISSUER_TOKEN": self.tokens["worker1"]},
            capture_output=True, text=True, encoding="utf-8", timeout=40)
        assert result.returncode == 0, result.stderr[-2500:]
        return json.loads(result.stdout)


def scenarios(e):
    e.admit_graph("synthetic-external-evidence", e.tools[0])
    opened = e.wait()
    assert opened["closure"] is None
    e.replace_runtime()
    assert e.wait() == opened
    e.record("WAIT-OPEN-REPLACEMENT", {"wait": opened, "admission": e.admission[1]})
    wrong = e.issuer("abstained", purpose="wrong-purpose")
    assert wrong["reply"]["outcome"]["reason_code"] == "wait_receipt_purpose_mismatch"
    superseded = e.issuer("superseded")
    assert superseded["reply"]["outcome"]["reason_code"] == "wait_receipt_superseded"
    assert e.wait() == opened
    e.record("WAIT-INELIGIBLE-ISSUER-EVIDENCE", {"wrong_purpose": wrong, "superseded": superseded})
    accepted = e.issuer()
    assert accepted["reply"]["outcome"]["status"] == "accepted"
    closed = e.wait()
    assert closed["closure"]["outcome"]["status"] == "accepted"
    assert closed["closure"]["outcome"]["receipt"] == accepted["command"]["payload"]["receipt"]
    page = e.advance()
    assert page["status"] == "completed" and (page["spent"], page["reserved"]) == (0, 0)
    delivery = e.owner_command("deliver", "--limit", "100", "--time-budget", "5")
    assert delivery["acknowledged"] == 1
    e.record("WAIT-ACTUAL-ISSUER-ARTIFACT", {"issuer": accepted, "wait": closed, "graph": page, "delivery": delivery})
    e.replace_runtime()
    assert e.wait() == closed and e.graph() == page
    assert HTTP.decoded(e.runtime.endpoint, "/v1/graph-receipts", e.tokens["worker1"], accepted["command"]) == accepted["reply"]
    assert HTTP.decoded(e.artifact.endpoint, "/v1/artifacts/" + accepted["artifact"]["artifact_id"] + "/content",
        e.tokens["worker1"]) == e.tools[0].image["golden_output"]
    e.record("WAIT-CLOSED-REPLACEMENT-REPLAY", {"original_receipt": accepted["reply"], "wait": closed, "graph": page})
    e.active_run = None
    e.admit_graph("synthetic-external-evidence", e.tools[0])
    e.wait()
    abstained = e.issuer("abstained")
    assert abstained["reply"]["outcome"]["status"] == "accepted"
    assert e.wait()["closure"]["outcome"]["status"] == "abstained"
    assert e.advance()["status"] == "blocked"
    e.record("WAIT-SCIENTIFIC-ABSTENTION", {"issuer": abstained, "wait": e.wait(), "graph": e.graph()})
    e.active_run = None


def main():
    config = json.loads(Path(sys.argv[1]).read_bytes())
    with tempfile.TemporaryDirectory(prefix="amphora-wait-peers-") as directory:
        e = WaitEnvironment(config, Path(directory))
        try:
            e.setup()
            scenarios(e)
            e.save("passed")
            print("Installed wait issuer/Artifact/replacement passed; scope " + e.scope["project_id"], flush=True)
        except BaseException:
            e.save("failed")
            raise
        finally:
            e.close()


if __name__ == "__main__":
    main()
