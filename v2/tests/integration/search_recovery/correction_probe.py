"""Public successor correction: new evaluations/selection, immutable old rank history."""

import hashlib
import importlib.util
import json
import sys
from datetime import datetime
from pathlib import Path


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main():
    assert all(importlib.util.find_spec(name) is None for name in ("sqlalchemy", "amphora_campaign_runtime", "amphora_evolution_search", "amphora_synthetic_objectives"))
    here = Path(__file__).absolute().parent
    env = load("corrected_environment", here / "correction_environment.py")
    C = load("corrected_revision", here / "correction.py")
    execution = load("corrected_execution", env.ROOT / "services/campaign_runtime/tests/numeric_search/acceptance/execution.py")
    config = json.loads(Path(sys.argv[1]).read_bytes())
    output = Path(config["evidence"])
    output.mkdir(parents=True, exist_ok=False)
    e = env.CorrectionEnvironment(config, output)
    http = env.N.HTTP
    try:
        e.setup()
        e.admit()
        original = execution.execute(e, http)
        old_bytes = e.bytes(original["final"]["artifact"])
        previous = C.M.CheckpointEvidence.from_bytes(original["final"]["artifact"], old_bytes)
        new = previous.checkpoint.specification.model_dump(mode="json")
        new["search_id"] = "explicit-corrected-search"
        new["evaluator"]["tool"] = e.new_release["tool"]["binding"]
        spec_bytes = C.M.canonical(new)
        specification = e.publish_bytes(spec_bytes, e.releases["seed"]["tool"]["inputs"][0]["schema_ref"])
        decision = C.CorrectionRevision.prepare(previous, specification, spec_bytes).record()
        intent_bytes = C.M.canonical(decision)
        intent = e.publish_bytes(intent_bytes, e.correction_schema)
        sources = {item["source"]["port"]: item for item in original["cut"]["sources"]}
        source = sources["result"]
        carried = {"target_port": "prior_checkpoint", "source": source["source"], "expected_value_sha256": source["value_sha256"]}
        inputs = json.loads(json.dumps(e.inputs))
        next(item for item in inputs if item["port"] == "specification")["value"]["artifact"] = specification
        command = e.command("graph.admit_successor", {"plan_sha256": e.plans["numeric-search-correction-fixture"]["sha256"],
            "predecessor": original["cut"]["predecessor"], "carried": [carried], "inputs": inputs,
            "budget": {"limit": 256, "max_attempts_per_activation": 2}})
        e.admission_path = "/v1/graph-runs/successors"
        e.admission_command = command
        e.admission = http.decoded(e.runtime.endpoint, e.admission_path, e.tokens["admin"], command)
        assert e.admission["outcome"]["status"] == "accepted"
        e.active_run = e.admission["outcome"]["committed"]["object_id"]
        e.corrected = True
        e.config["evaluator"] = e.config["evaluator_corrected"]
        e.releases["evaluate"] = e.new_release
        corrected = execution.execute(e, http)
        final = corrected["final"]["result"]
        assert final["specification_sha256"] != previous.checkpoint.specification_sha256
        assert final["specification"]["evaluator"]["tool"] == e.new_release["tool"]["binding"]
        old_ids = {rank["candidate_id"] for rank in original["final"]["result"]["selection"]["ranks"]}
        new_ids = {rank["candidate_id"] for rank in final["selection"]["ranks"]}
        assert not old_ids.intersection(new_ids)
        for report in corrected["reports"]:
            if report["artifact"]["schema_ref"]["schema_id"] == "search.evaluation-observation":
                assert report["result"]["outcome"]["evaluator"] == e.new_release["tool"]["binding"]
        lineage = http.decoded(e.runtime.endpoint, "/v1/graph-runs/" + e.active_run + "/lineage", e.tokens["admin"])
        assert lineage["predecessor"] == original["cut"]["predecessor"] and lineage["carried"] == [carried]
        historical = next(item for item in corrected["cut"]["sources"] if item["source"]["port"] == "prior_checkpoint")
        assert historical["value_sha256"] == source["value_sha256"]
        e.restart_runtime(e.config["replacement_runtime"])
        assert http.decoded(e.runtime.endpoint, e.admission_path, e.tokens["admin"], command) == e.admission
        for report in original["reports"]:
            read = http.decoded(e.runtime.endpoint, "/v1/runs/" + original["graph"]["run_id"] + "/completions/" +
                report["completion"]["completion_id"], e.tokens["admin"])
            assert read == report["completion"]
        assert e.bytes(previous.artifact.model_dump(mode="json")) == old_bytes and e.bytes(intent) == intent_bytes
        handoff = {"profile": "search-correction-handoff-v1", "intent": intent, "lineage": lineage,
                   "prior": original["final"]["artifact"], "corrected": corrected["final"]["artifact"], "authority": "synthetic_engineering_only"}
        raw = C.M.canonical(handoff)
        saved = e.publish_bytes(raw, e.correction_schema)
        assert e.bytes(saved) == raw
        evidence = {"timestamp_local": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "status": "passed", "scope": e.scope,
            "packages": config["packages"], "original": original, "corrected": corrected, "decision": decision,
            "intent": intent, "handoff": saved, "lineage": lineage, "old_checkpoint_sha256": hashlib.sha256(old_bytes).hexdigest(),
            "limits": ["Release0.3 changes identity, not arithmetic; no scientific correction or gain claimed",
                       "Explicit new search from seed; prior checkpoint is historical carry, never relabeled resume",
                       "Actual Windows peers with declared fixture image pins; no Linux deployment claim"], "paid_calls": 0}
        (output / "evidence.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
        print("Corrected evaluator successor preserved prior rank history", flush=True)
    finally:
        e.close()


if __name__ == "__main__":
    main()
