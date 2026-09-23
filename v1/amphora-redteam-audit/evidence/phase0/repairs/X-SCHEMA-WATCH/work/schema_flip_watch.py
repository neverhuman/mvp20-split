#!/usr/bin/env python3
"""X-SCHEMA-WATCH surfacing check.

Directive AMPHORA-DIRECTIVE-2026-08-05 A.3 / X-SCHEMA-WATCH: the autocommit
guard (/home/ubuntu/amphora-autocommit-guard.sh) restores a benchmark result
that flips RUNTIME -> MODULE-HARNESS shape in the working tree before commit,
and logs RESTORED_SCHEMA_FLIP to logs/autocommit-guard.log. That log has one
line in it (2026-08-04T06:46:57+00:00, amphora-solvency-score) and nobody
reads it. This script gives the condition three independent, run-every-time
surfacing paths instead of one passive log file:

  1. GUARD ACTIVITY  - any new RESTORED_SCHEMA_FLIP line since the last run
     (so a real future firing is reported, not left for a human to stumble on).
  2. HEAD SHAPE CENSUS - every */evidence/phase0/benchmark/result.v1.json,
     classified RUNTIME vs MODULE-HARNESS, diffed against the last run's
     census. A RUNTIME -> MODULE-HARNESS transition at HEAD with no matching
     new guard-log line is something the guard did not catch (guard down,
     lock timeout, direct commit) -- SILENT_SCHEMA_FLIP_UNGUARDED.
  3. RECEIPT HASH BINDING - for every module with a signed
     evidence/phase0/receipts/evaluation.v1.dsse.json, replicate the
     amphora-cli regression test
     `shipped_benchmark_results_stay_bound_to_signed_evaluation_receipts`:
     compare the receipt's pinned metrics.benchmark_result_sha256 against the
     on-disk file's live sha256. A mismatch is a flip that was ALREADY
     silently committed -- this is how B2 (2026-08-04) first found the 9
     UNBOUND_BENCHMARK_RESULTS modules, and it is the one check of the three
     the guard's git-diff heuristic cannot replace, because it binds to the
     cryptographically signed claim rather than to whatever happens to be in
     HEAD. This script runs it unconditionally, every invocation, instead of
     only when a human happens to run `cargo test -p amphora-cli`.

Exit codes: 0 = quiet. 1 = guard fired since last check (healthy, still
surfaced). 2 = SILENT_SCHEMA_FLIP_UNGUARDED found (guard failed to catch a
live transition). 3 = one or more modules with a signed evaluation receipt
have on-disk bytes that no longer match the pinned hash (flip already
committed, undetected by the guard by construction since it predates or
bypasses it).
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
GUARD_LOG = REPO / "logs" / "autocommit-guard.log"
STATE_PATH = Path(sys.argv[2]) if len(sys.argv) > 2 else REPO / "schema_watch_state.json"


def sh(*args):
    return subprocess.run(args, cwd=REPO, capture_output=True, text=True, check=True).stdout


def head_shape(path):
    try:
        content = sh("git", "show", f"HEAD:{path}")
    except subprocess.CalledProcessError:
        return None
    return "RUNTIME" if "execution_passed" in content else "MODULE-HARNESS"


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    files = sorted(
        f for f in sh("git", "ls-files", "*/evidence/phase0/benchmark/result.v1.json").splitlines() if f
    )
    current_shapes = {f: head_shape(f) for f in files}

    log_lines = GUARD_LOG.read_text().splitlines() if GUARD_LOG.exists() else []
    log_count = len(log_lines)

    state = {}
    if STATE_PATH.exists():
        state = json.loads(STATE_PATH.read_text())
    prior_shapes = state.get("module_shapes", {})
    prior_log_count = state.get("last_log_line_count", 0)
    prior_unbound = set(state.get("unbound_modules", []))

    new_log_lines = log_lines[prior_log_count:]
    restored_this_run = {line.split()[-1] for line in new_log_lines if "RESTORED_SCHEMA_FLIP" in line}

    runtime_n = sum(1 for s in current_shapes.values() if s == "RUNTIME")
    harness_n = sum(1 for s in current_shapes.values() if s == "MODULE-HARNESS")
    print(f"1) HEAD shape census: {runtime_n} RUNTIME, {harness_n} MODULE-HARNESS, "
          f"{len(current_shapes)} total")

    exit_code = 0
    if new_log_lines:
        print(f"2) guard log advanced by {len(new_log_lines)} line(s) since last check:")
        for line in new_log_lines:
            print(f"   {line}")
        exit_code = 1
    else:
        print("2) guard log: no new lines since last check")

    silent = [
        f for f, shape in current_shapes.items()
        if prior_shapes.get(f) == "RUNTIME" and shape == "MODULE-HARNESS" and f not in restored_this_run
    ]
    if silent:
        print("   ALERT SILENT_SCHEMA_FLIP_UNGUARDED: RUNTIME -> MODULE-HARNESS at HEAD with "
              "no matching guard-log restore:")
        for f in silent:
            print(f"     {f}")
        exit_code = 2

    unbound = []
    for f in files:
        module = f.split("/")[0]
        receipt_path = REPO / module / "evidence/phase0/receipts/evaluation.v1.dsse.json"
        if not receipt_path.is_file():
            continue
        try:
            receipt = json.loads(receipt_path.read_text())
            pinned = receipt["metrics"]["benchmark_result_sha256"]
        except Exception:
            continue
        on_disk = sha256_of(REPO / f)
        if on_disk != pinned:
            unbound.append(module)
    unbound.sort()
    print(f"3) receipt hash binding: {len(unbound)} module(s) with a signed evaluation receipt "
          f"whose on-disk benchmark result no longer matches the pinned hash "
          f"(flip already silently committed):")
    for m in unbound:
        new_marker = "" if m in prior_unbound else "  <- new since last check"
        print(f"   UNBOUND {m}{new_marker}")
    if unbound:
        exit_code = max(exit_code, 3)

    STATE_PATH.write_text(json.dumps({
        "last_log_line_count": log_count,
        "module_shapes": current_shapes,
        "unbound_modules": unbound,
    }, indent=2, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
