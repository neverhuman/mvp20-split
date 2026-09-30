"""Installed Studio authoring against real owners; no owner implementation or SQL imports."""

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

spec = importlib.util.spec_from_file_location("studio_observation_acceptance", Path(__file__).with_name("probe.py"))
OBSERVATION = importlib.util.module_from_spec(spec)
spec.loader.exec_module(OBSERVATION)
HTTP = OBSERVATION.OBSERVED.SOLVER.HTTP


class AuthoringEnvironment(OBSERVATION.BrowserEnvironment):
    def setup(self):
        super().setup()
        self.authoring = None
        self.tokens.update(studio_author=uuid.uuid4().hex, studio_cancel=uuid.uuid4().hex)
        config = json.loads(Path(self.runtime.config).read_bytes())
        config["authoring"] = True
        self.eligibility_relay = HTTP.FaultRelay(self.registry.endpoint)
        self.resources.append(self.eligibility_relay)
        config["draft_registry"] = {"endpoint": self.eligibility_relay.endpoint, "token_env": "TOKEN_RUNTIME", "actor_id": "runtime"}
        config["principals"].extend([self.principal("studio_author", ["read", "author", "validate", "admit"]),
                                     self.principal("studio_cancel", ["read", "cancel"])])
        port = self.runtime.port
        self.runtime.close()
        self.runtime = self.host("runtime", "amphora_campaign_runtime", config, "AMPHORA_RUNTIME_DATABASE_URL", port)
        registry = json.loads(Path(self.registry.config).read_bytes())
        registry["principals"].extend([self.principal("studio_author", ["read"]), self.principal("runtime", ["resolve"])])
        port = self.registry.port
        self.registry.close()
        self.registry = self.host("registry", "amphora_capability_registry", registry, "AMPHORA_REGISTRY_DATABASE_URL", port)

    def authoring_browser(self, mode, *, old=None, inputs=None, expected_reason=None):
        replacement = mode == "replacement"
        label = "replacement" if replacement else "original"
        actor = "studio_cancel" if mode == "cancel" else "studio_author"
        env = {key: value for key, value in os.environ.items() if key.upper() in {
            "SYSTEMROOT", "WINDIR", "TEMP", "TMP", "PATH", "COMSPEC", "USERPROFILE", "LOCALAPPDATA", "APPDATA"}}
        env["STUDIO_AUTHOR_TOKEN"] = self.tokens[actor]
        env["STUDIO_REGISTRY_TOKEN"] = self.tokens["studio_author"]
        output = Path(self.config["evidence"]) / self.scope["project_id"] / ("authoring-" + mode)
        result = subprocess.run([self.config["node"], "tests/integration/authoring_browser.mjs"],
            cwd=self.config["studio"][label], env=env, input=json.dumps({"endpoint": self.runtime.endpoint,
                "registry_endpoint": self.registry.endpoint, "scope": self.scope, "actor": actor,
                "run": self.active_run, "draft": "studio-draft", "mode": mode, "old": old, "inputs": inputs, "expected_reason": expected_reason, "output": str(output)}),
            text=True, capture_output=True, encoding="utf-8", timeout=180, check=False,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
        assert result.returncode == 0, "Authoring browser failed: " + result.stderr[-2500:] + result.stdout[-1000:]
        return json.loads(result.stdout)

    def execute(self):
        if self.authoring is None:
            before = self.graph()
            definition = json.loads(json.dumps(self.definitions["initial-population"]))
            definition["campaign_id"] = "studio-authoring"
            command = self.command("definition.save", {"draft_id": "studio-draft", "expected_revision": 0,
                "title": "Installed owner draft", "definition": definition}, "studio_author")
            command["encoding"] = "amphora-command-v2"
            initial = HTTP.decoded(self.runtime.endpoint, "/v1/definition-drafts/save", self.tokens["studio_author"], command)
            assert initial["outcome"]["status"] == "accepted", initial
            actual = self.authoring_browser("edit")
            record = HTTP.decoded(self.runtime.endpoint, "/v1/definition-drafts/studio-draft?revision=2", self.tokens["studio_author"])
            validation = HTTP.decoded(self.runtime.endpoint, "/v1/definition-validations/" + actual["validation"]["validation_id"], self.tokens["studio_author"])
            assert record == actual["record"] and validation == actual["validation"]
            assert validation["structurally_valid"] and validation["scientific_acceptance"] == "not_established"
            literal = next(node for node in record["definition"]["body"]["nodes"] if node["kind"] == "finish")["outputs"][-1]
            assert literal == {"port": "browser_literal", "source": {"kind": "number", "value": 1.25, "unit": "1"}}
            assert self.graph() == before, "Draft authoring changed the active execution projection"
            self.authoring = actual
            self.record("STUDIO-AUTHORING-OWNER", {"draft_revision": record["head"], "validation": validation,
                "running_graph_unchanged": True, "original_receipts": actual["receipts"], "schema_reference": actual["schema_reference"],
                "browser_owner_credentials_absent": True, "screenshot": actual["screenshots"]})
        return super().execute()

    def replace_runtime(self):
        super().replace_runtime()
        if self.authoring:
            actual = self.authoring_browser("replacement", old=self.authoring)
            assert actual["record"] == self.authoring["record"] and actual["validation"] == self.authoring["validation"]
            assert actual["receipts"] == self.authoring["receipts"]
            self.record("STUDIO-AUTHORING-REPLACEMENT", {"draft_revision": actual["record"]["head"],
                "original_receipts_preserved": True, "independent_browser_and_runtime_replaced": True})

    def activation_inputs(self):
        tool = self.stages["seed"]
        artifact = self.publish(tool, {**self.oracle["config"], "source_pins": tool.image["golden_input"]["source_pins"]})
        port = tool.descriptor["inputs"][0]
        return [{"port": "parameters", "value": {"kind": "artifact", "artifact": artifact,
                 "representation": port["representation"], "unit": port["unit"]}}]

    def activate_draft(self):
        for tool in self.tools:
            self.refresh_capacity(tool)
        inputs = self.activation_inputs()
        first = self.authoring_browser("activate", inputs=inputs)
        receipt = first["receipt"]
        assert receipt["outcome"]["status"] == "accepted", receipt
        self.active_run = receipt["outcome"]["committed"]["object_id"]
        assert self.graph()["status"] == "running"
        assert any(event["path"] == "/v1/registry/resolve" for event in self.eligibility_relay.events)
        # A separate new consumer cannot start a second campaign while this run is active.
        blocked = self.authoring_browser("activate-running", inputs=inputs, expected_reason="active_run_exists")
        assert blocked["receipt"]["outcome"]["reason_code"] == "active_run_exists"
        completed, reports = self.execute()
        assert completed["status"] == "completed" and len(reports) == 5
        before = len(self.eligibility_relay.events)
        # Exact terminal replay creates neither a new run nor fresh Registry observations.
        replay = HTTP.decoded(self.runtime.endpoint, "/v1/graph-runs/drafts", self.tokens["studio_author"], first["submission"])
        assert replay == receipt and len(self.eligibility_relay.events) == before
        self.record("STUDIO-DRAFT-ACTIVATION-OWNER", {"run": self.active_run, "receipt": receipt,
            "running_campaign_rejected": True, "executed_tool_invocations": len(reports), "original_replay_preserved": True,
            "registry_requests": self.eligibility_relay.events, "scientific_acceptance": "not_established"})
        self.activation = first

    def revoke_draft_tool(self):
        tool = self.stages["seed"]
        current = HTTP.decoded(self.registry.endpoint, "/v1/releases/" + tool.lock["descriptor_sha256"], self.tokens["studio_author"])
        revoked = self.registry_call("revoke", {"release": tool.lock, "expected_revision": current["revision"]})
        assert revoked["status"] == "accepted"
        rejected = self.authoring_browser("activate-revoked", inputs=self.activation_inputs(), expected_reason="draft_tool_ineligible")
        assert rejected["receipt"]["outcome"]["reason_code"] == "draft_tool_ineligible"
        old = self.activation
        replay = HTTP.decoded(self.runtime.endpoint, "/v1/graph-runs/drafts", self.tokens["studio_author"], old["submission"])
        assert replay == old["receipt"]
        self.record("STUDIO-DRAFT-REVOKED-TOOL", {"release": tool.lock, "rejection": rejected["receipt"],
            "prior_admission_replay_preserved": True})

    def emergency(self):
        tool = self.stages["seed"]
        artifact = self.publish(tool, {**self.oracle["config"], "source_pins": tool.image["golden_input"]["source_pins"]})
        port = tool.descriptor["inputs"][0]
        admitted = HTTP.decoded(self.runtime.endpoint, "/v1/graph-runs", self.tokens["admin"], self.command("graph.admit", {
            "plan_sha256": self.plans["initial-population"]["sha256"], "budget": {"limit": 100}, "inputs": [{"port": "parameters",
                "value": {"kind": "artifact", "artifact": artifact, "representation": port["representation"], "unit": port["unit"]}}]}))
        assert admitted["outcome"]["status"] == "accepted", admitted
        self.active_run = admitted["outcome"]["committed"]["object_id"]
        before = self.graph()
        actual = self.authoring_browser("cancel")
        after = self.graph()
        assert before["status"] == "running" and after["status"] == "cancelled"
        assert actual["receipt"]["outcome"]["committed"]["object_id"] == self.active_run
        assert actual["observed_status"] == "cancelled"
        self.record("STUDIO-EMERGENCY-OWNER", {"run": self.active_run, "receipt": actual["receipt"],
            "observed_status": after["status"], "browser_owner_credentials_absent": True,
            "limits": "No worker was claimed; cancel-vs-complete and uncertain remote effects remain B3."})


def main():
    assert importlib.util.find_spec("amphora_campaign_runtime") is None
    assert importlib.util.find_spec("sqlalchemy") is None
    config = json.loads(Path(sys.argv[1]).read_bytes())
    with tempfile.TemporaryDirectory(prefix="amphora-studio-authoring-") as directory:
        e = AuthoringEnvironment(config, Path(directory))
        try:
            e.setup()
            OBSERVATION.OBSERVED.SOLVER.scenarios(e)
            e.activate_draft()
            e.emergency()
            e.revoke_draft_tool()
            e.record("STUDIO-INDEPENDENT-BUILDS", config["studio_pins"])
            e.save("passed")
            print("Actual-owner Studio authoring passed; scope " + e.scope["project_id"], flush=True)
        except BaseException:
            e.save("failed")
            raise
        finally:
            e.close()


if __name__ == "__main__":
    main()
