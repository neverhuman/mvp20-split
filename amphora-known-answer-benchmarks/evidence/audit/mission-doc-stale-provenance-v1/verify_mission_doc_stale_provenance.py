#!/usr/bin/env python3
"""Independent re-derivation audit: does docs/mission.md's 'Current benchmark
result' section (the module's own standing description of its live Phase-0
evidence) still match the live on-disk implementation and artifacts?

Attack: recompute SHA-256 of every artifact mission.md pins by exact hash
citation, compare byte-for-byte against the live file, and trace any
mismatch to its actual source in the repo (git history / superseded tree).
AUDIT_ONLY. Read-only: writes only its own report JSON.
"""
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-known-answer-benchmarks"
MISSION = MOD / "docs/mission.md"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def sha_file(p):
    return sha(p.read_bytes()) if p.exists() else None


mission_text = MISSION.read_text()

# --- Extract the three pinned claims from mission.md verbatim -------------
lib_rs_claim = re.search(
    r"native Rust at `([^`]+)` with SHA-256 `([0-9a-f]{64})`", mission_text
)
result_claim = re.search(
    r"canonical receipt at\s*`([^`]+)`\s*\(SHA-256\s*`([0-9a-f]{64})`\)", mission_text
)
kpi_claim = re.search(
    r"Phase-0 KPI receipt lives at\s*`([^`]+)`", mission_text
)

assert lib_rs_claim and result_claim and kpi_claim, "failed to extract mission.md claims -- mission.md prose changed, re-derive regex"

lib_rs_path_rel, lib_rs_pinned_sha = lib_rs_claim.group(1), lib_rs_claim.group(2)
result_path_rel, result_pinned_sha = result_claim.group(1), result_claim.group(2)
kpi_path_rel = kpi_claim.group(1)

# --- Live recompute ---------------------------------------------------------
lib_rs_path = ROOT / lib_rs_path_rel
result_path = MOD / "evidence/phase0/benchmark/result.v1.json"
kpi_path = MOD / "evidence/phase0/kpis/known-answer-benchmarks-audit-kpi.v1.json"

lib_rs_live_sha = sha_file(lib_rs_path)
result_live_sha = sha_file(result_path)
kpi_exists_live = kpi_path.exists()

lib_rs_match = (lib_rs_live_sha == lib_rs_pinned_sha)
result_match = (result_live_sha == result_pinned_sha)

# --- Trace the pinned result hash to its actual source ---------------------
superseded_kpi_glob = list(MOD.glob("evidence/superseded/*/phase0/kpis/known-answer-benchmarks-audit-kpi.v1.json"))
traced_to_superseded = None
supersession_reason = None
superseded_unsigned = None
for cand in superseded_kpi_glob:
    body = cand.read_text()
    m = re.search(r'"benchmark_result_sha256":\s*"([0-9a-f]{64})"', body)
    if m and m.group(1) == result_pinned_sha:
        traced_to_superseded = str(cand.relative_to(ROOT))
        supersession_dir = cand.parent.parent
        supersession_json = supersession_dir / "supersession.v1.json"
        if supersession_json.exists():
            sj = json.loads(supersession_json.read_text())
            supersession_reason = sj.get("reason")
            superseded_unsigned = sj.get("unsigned_preparation_only")
        # also check the archived KPI file's own unsigned flag if present
        break

# --- Grep-wide search: does the pinned lib.rs hash exist anywhere live? ----
grep_lib = subprocess.run(
    ["grep", "-rl", lib_rs_pinned_sha, str(ROOT)],
    capture_output=True, text=True
)
lib_rs_hash_found_anywhere = sorted(
    l for l in grep_lib.stdout.splitlines()
    if "/.git/" not in l and "mission-doc-stale-provenance-v1" not in l
)

# --- git history check for lib.rs (does any tracked revision match?) -------
git_log = subprocess.run(
    ["git", "-C", str(ROOT), "log", "--oneline", "--all", "--", lib_rs_path_rel],
    capture_output=True, text=True
).stdout.strip().splitlines()
git_revisions_checked = []
for line in git_log:
    commit = line.split()[0]
    show = subprocess.run(
        ["git", "-C", str(ROOT), "show", f"{commit}:{lib_rs_path_rel}"],
        capture_output=True
    )
    if show.returncode == 0:
        git_revisions_checked.append({"commit": commit, "sha256": sha(show.stdout)})

lib_rs_matches_any_tracked_revision = any(
    r["sha256"] == lib_rs_pinned_sha for r in git_revisions_checked
)

# --- also check: does the ATTACKED control_by_control_receipt.v1.json (the
# other hash-pinned artifact in the same mission.md section) still match? ---
control_receipt_claim = re.search(
    r"compile-time-embedded\s*\n?`control_by_control_receipt\.v1\.json` \(SHA-256\s*\n?`([0-9a-f]{64})`\)",
    mission_text,
)
control_receipt_pinned = control_receipt_claim.group(1) if control_receipt_claim else None
control_receipt_path = MOD / "reference/mvp20/out/control_by_control_receipt.v1.json"
control_receipt_live_sha = sha_file(control_receipt_path)
control_receipt_match = (control_receipt_live_sha == control_receipt_pinned)

report = {
    "schema": "amphora.known-answer-benchmarks.mission-doc-stale-provenance-report.v1",
    "module": "amphora-known-answer-benchmarks",
    "mission_md_sha256": sha_file(MISSION),
    "claims_extracted": {
        "lib_rs_path": lib_rs_path_rel,
        "lib_rs_pinned_sha256": lib_rs_pinned_sha,
        "result_path_claimed": result_path_rel,
        "result_pinned_sha256": result_pinned_sha,
        "kpi_path_claimed": kpi_path_rel,
        "control_receipt_pinned_sha256": control_receipt_pinned,
    },
    "live_recompute": {
        "lib_rs_live_sha256": lib_rs_live_sha,
        "lib_rs_match": lib_rs_match,
        "result_v1_live_sha256": result_live_sha,
        "result_v1_match": result_match,
        "kpi_file_exists_at_claimed_live_path": kpi_exists_live,
        "control_receipt_live_sha256": control_receipt_live_sha,
        "control_receipt_match": control_receipt_match,
    },
    "root_cause_trace": {
        "result_hash_traced_to_superseded_file": traced_to_superseded,
        "supersession_reason": supersession_reason,
        "superseded_kpi_was_unsigned_preparation_only": superseded_unsigned,
    },
    "lib_rs_provenance_search": {
        "pinned_hash_found_anywhere_in_live_tree": lib_rs_hash_found_anywhere,
        "git_tracked_revisions_checked": git_revisions_checked,
        "matches_any_tracked_git_revision": lib_rs_matches_any_tracked_revision,
    },
    "verdict": {
        "lib_rs_identity_pin": "STALE" if not lib_rs_match else "CURRENT",
        "benchmark_result_pin": "STALE_POINTS_TO_SUPERSEDED_UNSIGNED_ARTIFACT" if (not result_match and traced_to_superseded) else ("STALE" if not result_match else "CURRENT"),
        "kpi_receipt_path_claim": "FALSE_FILE_ABSENT_AT_LIVE_PATH" if not kpi_exists_live else "TRUE",
        "control_receipt_pin": "CURRENT" if control_receipt_match else "STALE",
        "overall": "REFUTED" if (not lib_rs_match or not result_match or not kpi_exists_live) else "SURVIVED",
    },
}

out = Path("/tmp/mission_doc_stale_provenance_report.v1.json")
out.write_text(json.dumps(report, indent=2, sort_keys=True))
print(json.dumps(report["verdict"], indent=2))
print("wrote", out)
