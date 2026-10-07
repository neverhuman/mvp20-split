"""Recheck retained real-process evidence; no execution or scientific authority."""

import argparse
import hashlib
import json
import subprocess
from datetime import datetime
from pathlib import Path

from manifest import CheckpointEvidence, CheckpointTrace, canonical


def trace(run):
    return CheckpointTrace([
        CheckpointEvidence.from_bytes(report["artifact"], canonical(report["result"]))
        for report in run["reports"] if report["artifact"]["schema_ref"]["schema_id"] == "search.checkpoint"
    ])


def check_run(run, *, attempts):
    graph = run["graph"]
    assert graph["status"] == "completed" and graph["reserved"] == 0
    assert graph["spent"] == attempts <= graph["budget_limit"] == 256
    assert len(run["reports"]) == 15
    assert run["retained"] and all(item["outcome"]["status"] == "confirmed" for item in run["retained"].values())
    final = run["final"]["result"]
    assert final["stop_reason"] == "generation_budget" and final["rng"]["counter"] == 26
    assert final["progress"]["evaluations_issued"] == 6
    pin = final["specification"]["evaluator"]["tool"]
    for report in run["reports"]:
        if report["artifact"]["schema_ref"]["schema_id"] == "search.evaluation-observation":
            assert report["result"]["outcome"]["evaluator"] == pin
    return {"run_id": graph["run_id"], "attempts": attempts, "accepted": 15, "evaluations": 6, "evaluator": pin}


def verify(args):
    partial = json.loads(args.partial.read_bytes())
    correction = json.loads(args.correction.read_bytes())
    assert partial["status"] == correction["status"] == "passed"
    assert partial["paid_calls"] == correction["paid_calls"] == 0
    rebuilt = Path(__file__).with_name("rebuilt_adapter.py")
    assert hashlib.sha256(rebuilt.read_bytes()).hexdigest() == partial["adapter_sha256"]
    equivalent = trace(partial["baseline"]).equivalent(trace(partial["resumed"]))
    assert equivalent == partial["checkpoint_equivalence"]
    assert partial["resumed"]["interruption"]["original_accepted_history_unchanged"] is True
    runs = {"baseline": check_run(partial["baseline"], attempts=15),
            "resumed": check_run(partial["resumed"], attempts=16),
            "original": check_run(correction["original"], attempts=15),
            "corrected": check_run(correction["corrected"], attempts=15)}
    old, new = trace(correction["original"]), trace(correction["corrected"])
    assert old.snapshots[-1].artifact.sha256 == correction["old_checkpoint_sha256"]
    assert old.snapshots[-1].checkpoint.specification_sha256 != new.snapshots[-1].checkpoint.specification_sha256
    prior_ids = {rank.candidate_id for rank in old.snapshots[-1].checkpoint.selection.ranks}
    assert not prior_ids.intersection(rank.candidate_id for rank in new.snapshots[-1].checkpoint.selection.ranks)
    repo = Path(__file__).absolute().parents[4]
    disposition = repo / "v2/docs/Build Plans/BP-08/BP-08.01 Reuse disposition.json"
    reuse = json.loads(disposition.read_bytes())
    assert reuse["copied_sources"] == reuse["scientific_claims"] == []
    for name, digest in reuse["sources"].items():
        assert name.startswith("v1/") and ".." not in Path(name).parts
        assert hashlib.sha256((repo / name).read_bytes()).hexdigest() == digest
    probe = """import json,platform,sys,importlib.util,importlib.metadata as m
assert all(importlib.util.find_spec(n) is None for n in ('sqlalchemy','amphora_campaign_runtime','amphora_data_artifacts','numpy','torch','rdkit'))
native=importlib.util.find_spec('pydantic_core._pydantic_core')
assert native and native.origin.endswith(('.pyd','.so'))
print(json.dumps({'python':sys.version,'platform':platform.platform(),'machine':platform.machine(),'native_validation_module':native.origin,'distributions':dict(sorted((d.metadata['Name'],d.version) for d in m.distributions()))}))
"""
    profiles = {}
    for name, location in (("numeric", args.numeric), ("evaluator", args.evaluator)):
        interpreter = location / "environment/Scripts/python.exe"
        result = subprocess.run([str(interpreter.absolute()), "-I", "-c", probe], capture_output=True, check=True, timeout=30)
        profiles[name] = json.loads(result.stdout)
    report = {"timestamp_local": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "status": "passed",
        "profile": "search-recovery-consolidation-v1", "runs": runs, "equivalent_checkpoints": len(equivalent["baseline"]),
        "reuse_source_count": len(reuse["sources"]), "copied_v1_sources": [], "native_profiles": profiles,
        "inputs": {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in (args.partial, args.correction, disposition, rebuilt)},
        "limits": ["Exact recovery only on the tested Windows CPython profile", "pydantic-core is a native validation dependency; numerical kernel uses standard library",
                   "No v1 Rust execution, source extraction, cross-hardware equality or scientific efficacy claim", "Rebuilt test adapter image qualification is separate"], "paid_calls": 0}
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("Recovery, budgets, correction isolation, source hashes and native dependencies verified")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("partial", "correction", "numeric", "evaluator", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    verify(parser.parse_args())
