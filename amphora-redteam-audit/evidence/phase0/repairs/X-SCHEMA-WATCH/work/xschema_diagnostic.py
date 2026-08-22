#!/usr/bin/env python3
"""Stateless diagnostic snapshot for X-SCHEMA-WATCH two-replay gate.
Deterministic function of repo HEAD + worktree only: no RNG, no wall clock
embedded in the body (run twice, bytes must match)."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")


def sh(*args):
    return subprocess.run(args, cwd=ROOT, capture_output=True, text=True, check=True).stdout


def head_shape(path):
    try:
        content = sh("git", "show", f"HEAD:{path}")
    except subprocess.CalledProcessError:
        return None
    return "RUNTIME" if "execution_passed" in content else "MODULE-HARNESS"


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


files = sorted(f for f in sh("git", "ls-files", "*/evidence/phase0/benchmark/result.v1.json").splitlines() if f)
shapes = {f: head_shape(f) for f in files}
runtime_n = sum(1 for s in shapes.values() if s == "RUNTIME")
harness_n = sum(1 for s in shapes.values() if s == "MODULE-HARNESS")

unbound = []
for f in files:
    module = f.split("/")[0]
    receipt_path = ROOT / module / "evidence/phase0/receipts/evaluation.v1.dsse.json"
    if not receipt_path.is_file():
        continue
    try:
        receipt = json.loads(receipt_path.read_text())
        pinned = receipt["metrics"]["benchmark_result_sha256"]
    except Exception:
        continue
    if sha256_of(ROOT / f) != pinned:
        unbound.append(module)
unbound.sort()

guard_log = ROOT / "logs" / "autocommit-guard.log"
guard_lines = guard_log.read_text().splitlines() if guard_log.exists() else []

out = {
    "counts": {"RUNTIME": runtime_n, "MODULE-HARNESS": harness_n, "total": len(files)},
    "shapes": shapes,
    "unbound_modules": unbound,
    "unbound_count": len(unbound),
    "guard_log_line_count": len(guard_lines),
    "guard_log_lines": guard_lines,
}
sys.stdout.write(json.dumps(out, indent=2, sort_keys=True))
