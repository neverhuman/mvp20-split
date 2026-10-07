"""Two reviewed graph versions and evaluator releases; prior rank is history only."""

import copy
import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).absolute().parents[3]
spec = importlib.util.spec_from_file_location("correction_numeric_environment", ROOT / "services/campaign_runtime/tests/numeric_search/acceptance/environment.py")
N = importlib.util.module_from_spec(spec)
spec.loader.exec_module(N)


class CorrectionEnvironment(N.NumericEnvironment):
    corrected = False

    def new_cli(self, action, *arguments):
        result = subprocess.run([self.config["evaluator_corrected"], "-I", "-m", "amphora_synthetic_objectives", action, *arguments],
            cwd=self.root, env=N.HTTP.isolated_env(), capture_output=True, timeout=30)
        assert result.returncode == 0
        return result.stdout

    def image(self, stage):
        return "d" * 64 if self.corrected and stage == "evaluate" else super().image(stage)

    def host(self, owner, module, config, *args, **kwargs):
        if owner == "artifact":
            raw = b'{"$id":"urn:amphora:fixture.search-correction:1:validation","$schema":"https://json-schema.org/draft/2020-12/schema","type":"object"}\n'
            self.correction_schema = {"schema_id": "fixture.search-correction", "version": "1", "sha256": hashlib.sha256(raw).hexdigest()}
            (self.root / "correction-schema.json").write_bytes(raw)
            config["profiles"].append({**self.correction_schema, "media_type": "application/json", "schema_path": "correction-schema.json"})
        if owner == "runtime":
            self.new_release = json.loads(self.new_cli("describe", "--image-sha256", "d" * 64))
            assert self.releases["evaluate"]["tool"]["binding"]["release"] == "0.2.0"
            assert self.new_release["tool"]["binding"]["release"] == "0.3.0"
            for kind in ("input", "output", "policy"):
                assert self.new_cli("schema", "--kind", kind) == self.tool_cli("evaluate", "schema", "--kind", kind)
            assert self.new_cli("policy") == self.tool_cli("evaluate", "policy")
            (self.root / "corrected-evaluator.json").write_text(json.dumps(self.new_release), encoding="utf-8")
            releases = dict(self.releases, evaluate=self.new_release)
            definition = N.DEFINITION.campaign(self.scope, releases, 2)
            definition.update(campaign_id="numeric-search-correction-fixture", revision=2)
            body = definition["body"]
            historical = copy.deepcopy(body["outputs"][0])
            historical["name"] = "prior_checkpoint"
            body["inputs"].append(historical)
            body["outputs"].append(copy.deepcopy(historical))
            body["nodes"][-1]["outputs"].append({"port": "prior_checkpoint", "source": {"kind": "input", "name": "prior_checkpoint"}})
            self.corrected_definition = definition
            (self.root / "corrected-graph.json").write_text(json.dumps(definition), encoding="utf-8")
            graph = copy.deepcopy(config["graphs"][0])
            graph["definition"] = "corrected-graph.json"
            graph["releases"] = [entry for entry in graph["releases"] if entry["descriptor"] != "evaluate-descriptor.json"]
            graph["releases"].append({"descriptor": "corrected-evaluator.json", "lock": N.GRAPH.BASE.WIRE.release_lock(self.new_release)})
            config["graphs"].append(graph)
            config["tools"].append(self.new_release["tool"])
        return super().host(owner, module, config, *args, **kwargs)
