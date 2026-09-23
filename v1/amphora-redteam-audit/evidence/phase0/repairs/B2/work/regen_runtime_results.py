#!/usr/bin/env python3
"""B2 restoration: regenerate RUNTIME-shape <module>/evidence/phase0/benchmark/result.v1.json.

Faithful replay of amphora-cli/src/phase0.rs::evaluate()'s result envelope:
  execute_locked_benchmark() -> `amphora benchmark run --locked --all`
  result = {schema, module_id, bundle_sha256, first_replay, second_replay,
            replay_identical, benchmark_execution_complete,
            legacy_local_receipt_authority, scientific_outcome}
  bytes  = to_vec_pretty(canonicalize(result)) + b"\n"

A regenerated file is only written when its SHA-256 equals
`metrics.benchmark_result_sha256` inside the module's immutable, signed Phase-0
evaluation receipt. That equality is the proof the bytes are the evaluated ones.
"""
import hashlib
import json
import os
import pathlib
import subprocess
import sys

ROOT = pathlib.Path("/home/ubuntu/amphora/build/mvp20-split")
BIN = ROOT / "target/debug/amphora-tui"

DETERMINISTIC_MODULES = {
    "amphora-candidate-contract",
    "amphora-cro-protocol-packager",
    "amphora-envelope-gates",
    "amphora-evidence-intake-validator",
    "amphora-formulation-arithmetic",
    "amphora-formulation-universe",
    "amphora-model-card-authority",
    "amphora-molecule-design-gate",
    "amphora-optimizer-orchestrator",
    "amphora-redteam-audit",
    "amphora-report-packager",
    "amphora-run-provenance",
    "amphora-source-ledger",
}


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def canonical_bytes(value) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n").encode()


def run_locked_all():
    env = dict(os.environ)
    env["AMPHORA_READ_ONLY_COMMAND"] = "1"
    p = subprocess.run(
        [str(BIN), "benchmark", "run", "--locked", "--all"],
        cwd=ROOT, env=env, capture_output=True,
    )
    return p


def replay_for(proc, module_id):
    lines = [ln for ln in proc.stdout.split(b"\n")]
    hits = []
    for ln in lines:
        try:
            d = json.loads(ln)
        except Exception:
            continue
        if isinstance(d, dict) and d.get("module_id") == module_id:
            hits.append((ln, d))
    if len(hits) != 1:
        raise SystemExit(f"locked benchmark emitted {len(hits)} diagnostics for {module_id}")
    raw, diagnostic = hits[0]
    return {
        "execution_passed": proc.returncode == 0,
        "exit_code": proc.returncode,
        "scientific_passed": diagnostic.get("passed") is True,
        "diagnostic_receipt": diagnostic,
        "diagnostic_sha256": sha(raw),
        "stderr_sha256": sha(proc.stderr),
        "legacy_local_signature_authority": "NONE",
    }


def benchmark_execution_complete(module_id, replay) -> bool:
    if replay.get("execution_passed") is not True:
        return False
    if module_id in DETERMINISTIC_MODULES:
        return "diagnostic_receipt" in replay
    details = replay.get("diagnostic_receipt", {}).get("metrics", {}).get("details")
    if not isinstance(details, dict):
        return False
    status = details.get("current_benchmark_status")
    obs = details.get("observations")
    return (
        isinstance(status, str)
        and status.startswith("CHECKED_ARTIFACT_")
        and isinstance(obs, list)
        and len(obs) > 0
    )


def main(argv):
    modules = argv[1:]
    proc = run_locked_all()
    print(f"benchmark run --locked --all rc={proc.returncode} "
          f"stdout={len(proc.stdout)}B stderr_sha={sha(proc.stderr)[:12]}")
    report = []
    for m in modules:
        mod_dir = ROOT / m
        bundle = mod_dir / "evidence/phase0/bundle.v1.json"
        receipt = json.loads((mod_dir / "evidence/phase0/receipts/evaluation.v1.dsse.json").read_bytes())
        pinned = receipt["metrics"]["benchmark_result_sha256"]
        first = replay_for(proc, m)
        second = dict(first)
        complete = benchmark_execution_complete(m, first)
        if m in DETERMINISTIC_MODULES:
            outcome = "NOT_APPLICABLE"
        elif first["scientific_passed"]:
            outcome = "PASSED"
        else:
            outcome = "FAILED"
        result = {
            "schema": "amphora.module-phase0-benchmark-result.v1",
            "module_id": m,
            "bundle_sha256": sha(bundle.read_bytes()),
            "first_replay": first,
            "second_replay": second,
            "replay_identical": True,
            "benchmark_execution_complete": complete,
            "legacy_local_receipt_authority": "NONE",
            "scientific_outcome": outcome,
        }
        out = canonical_bytes(result)
        got = sha(out)
        ok = got == pinned
        target = mod_dir / "evidence/phase0/benchmark/result.v1.json"
        current = sha(target.read_bytes()) if target.is_file() else None
        if ok and current != pinned:
            target.write_bytes(out)
        report.append((m, ok, pinned[:16], got[:16], current[:16] if current else None))
    print()
    for m, ok, pinned, got, current in report:
        print(f"{m:42s} restored={ok} pinned={pinned} regenerated={got} was={current}")
    print(f"\nrestored {sum(1 for r in report if r[1])}/{len(report)}")
    return 0 if all(r[1] for r in report) else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
