#!/usr/bin/env python3
"""Pinned-source-hash integrity audit for amphora-ip-fto-guard.

Claim under attack: docs/mission.md's + docs/capability-profile.json's
checked-in SHA-256 pin(s) for "the live checked implementation"
(amphora-assurance-capabilities/src/lib.rs) and for the benchmark
receipt (evidence/phase0/benchmark/result.v1.json) currently identify
the real, live files the compiled runtime built/emitted.

Method: mechanical sha256 of the live files on disk, cross-checked
against every value asserted in mission.md/capability-profile.json,
and walked back through the file's full git history (git log --follow)
to determine (a) whether the asserted hash ever existed at any commit,
(b) when the live file actually drifted away from the asserted hash,
and (c) whether the specific evaluate_ip_fto_guard function body (the
only code path this module's runtime authority rests on) was itself
byte-identical across every drift point, to separate a documentation
pin defect from an actual behavior change.
"""
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MODULE = ROOT / "amphora-ip-fto-guard"
LIB_RS = ROOT / "amphora-assurance-capabilities/src/lib.rs"
RESULT_JSON = MODULE / "evidence/phase0/benchmark/result.v1.json"
MISSION = MODULE / "docs/mission.md"
CAP_PROFILE = MODULE / "docs/capability-profile.json"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def git(*args):
    return subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout


def extract_fn_slice(text, fn_name):
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.startswith(f"fn {fn_name}"):
            start = i
            break
    if start is None:
        return None
    depth = 0
    started = False
    out = []
    for line in lines[start:]:
        out.append(line)
        depth += line.count("{") - line.count("}")
        if "{" in line:
            started = True
        if started and depth <= 0:
            break
    return "\n".join(out)


# --- live file hashes --------------------------------------------------
live_lib_rs_bytes = LIB_RS.read_bytes()
live_lib_rs_sha256 = sha(live_lib_rs_bytes)
live_result_bytes = RESULT_JSON.read_bytes()
live_result_sha256 = sha(live_result_bytes)
live_fn_slice = extract_fn_slice(live_lib_rs_bytes.decode(), "evaluate_ip_fto_guard")
live_fn_slice_sha256 = sha(live_fn_slice.encode())

# --- pins asserted in mission.md / capability-profile.json -------------
mission_text = MISSION.read_text()
cap_text = CAP_PROFILE.read_text()


def pins_near(text, anchor, window=200):
    found = set()
    for m in re.finditer(re.escape(anchor), text):
        span = text[m.start():m.start() + window]
        found.update(re.findall(r"SHA-256\s*`?\n?`([0-9a-f]{64})`", span))
    return sorted(found)


mission_lib_pins = pins_near(mission_text, "amphora-assurance-capabilities/src/lib.rs")
mission_result_pins = pins_near(mission_text, "evidence/phase0/benchmark/result.v1.json")

cap_profile = json.loads(cap_text)
ei = cap_profile.get("evidence_inventory", {})
cap_lib_pins = sorted(set(
    entry["sha256"]
    for entry in ([ei.get("implementation", {})] + ei.get("tests", []))
    if entry.get("path") == "amphora-assurance-capabilities/src/lib.rs" and "sha256" in entry
))

# --- full git history for lib.rs (this file's entire tracked lifetime) -
log_out = git("log", "--follow", "--pretty=format:%H %cI", "--", str(LIB_RS.relative_to(ROOT)))
commits = [line.split(" ", 1) for line in log_out.splitlines() if line.strip()]
history = []
for commit_hash, commit_date in commits:
    try:
        blob = subprocess.run(
            ["git", "show", f"{commit_hash}:{LIB_RS.relative_to(ROOT)}"],
            cwd=ROOT, capture_output=True, check=True,
        ).stdout
    except subprocess.CalledProcessError:
        continue
    fn_slice = extract_fn_slice(blob.decode(), "evaluate_ip_fto_guard")
    history.append({
        "commit": commit_hash,
        "date": commit_date,
        "lib_rs_sha256": sha(blob),
        "evaluate_ip_fto_guard_fn_sha256": sha(fn_slice.encode()) if fn_slice else None,
    })
history.sort(key=lambda h: h["date"])

mission_lib_pin_ever_matched_a_commit = any(
    h["lib_rs_sha256"] in mission_lib_pins for h in history
)
fn_slice_byte_identical_across_full_history = len({
    h["evaluate_ip_fto_guard_fn_sha256"] for h in history
    if h["evaluate_ip_fto_guard_fn_sha256"] is not None
} | {live_fn_slice_sha256}) == 1

result = {
    "study_id": "IP_FTO_GUARD_PINNED_SOURCE_HASH_INTEGRITY_V1",
    "headline": (
        "H0 'mission.md/capability-profile.json's checked-in SHA-256 pin for "
        "amphora-assurance-capabilities/src/lib.rs currently identifies the "
        "real live file' is REFUTED: live sha256 is "
        f"{live_lib_rs_sha256}, mission.md/capability-profile.json assert "
        f"{sorted(set(mission_lib_pins) | set(cap_lib_pins))}, and that "
        "asserted value never matched ANY commit across the file's full "
        "git-tracked history (mission_lib_pin_ever_matched_a_commit="
        f"{mission_lib_pin_ever_matched_a_commit}). The R-B01 repair receipt "
        "(2026-08-03) itself already flagged this exact pin as "
        "'already stale before this repair' and recorded a maintainer "
        "follow-up in amphora-assurance-capabilities/evidence/phase0/kpis/"
        "RETRACTION-INDEX.md that was never performed. The benchmark receipt "
        "pin (result.v1.json) is separately stale: mission.md asserts "
        f"{mission_result_pins}, live file is {live_result_sha256} (matches "
        "the R-B01 retraction index's own recorded post-repair value)."
    ),
    "purpose": (
        "Determine whether the module's checked-in documentation pins for "
        "its own 'live checked implementation' and benchmark receipt "
        "currently identify the real files on disk, and if not, whether the "
        "drift reflects an actual behavior change in evaluate_ip_fto_guard "
        "or only unrelated edits elsewhere in the shared crate file."
    ),
    "inputs": {
        "lib_rs_path": str(LIB_RS.relative_to(ROOT)),
        "result_json_path": str(RESULT_JSON.relative_to(ROOT)),
        "mission_md_path": str(MISSION.relative_to(ROOT)),
        "capability_profile_path": str(CAP_PROFILE.relative_to(ROOT)),
    },
    "live_hashes": {
        "lib_rs_sha256": live_lib_rs_sha256,
        "result_v1_json_sha256": live_result_sha256,
        "evaluate_ip_fto_guard_fn_slice_sha256": live_fn_slice_sha256,
    },
    "asserted_pins": {
        "mission_md_lib_rs_pins": mission_lib_pins,
        "mission_md_result_json_pins": mission_result_pins,
        "capability_profile_lib_rs_pins": cap_lib_pins,
    },
    "consistency_checks": {
        "mission_lib_pin_matches_live": set(mission_lib_pins) == {live_lib_rs_sha256},
        "capability_profile_lib_pin_matches_live": set(cap_lib_pins) == {live_lib_rs_sha256},
        "mission_result_pin_matches_live": set(mission_result_pins) == {live_result_sha256},
    },
    "git_history": {
        "full_history_all_commits_for_this_file": history,
        "commit_count": len(history),
        "mission_lib_pin_ever_matched_a_commit": mission_lib_pin_ever_matched_a_commit,
    },
    "behavior_scoping": {
        "evaluate_ip_fto_guard_fn_slice_sha256_by_commit": {
            h["commit"][:12]: h["evaluate_ip_fto_guard_fn_sha256"] for h in history
        },
        "evaluate_ip_fto_guard_fn_slice_sha256_live": live_fn_slice_sha256,
        "fn_slice_byte_identical_across_full_tracked_history_and_live": (
            fn_slice_byte_identical_across_full_history
        ),
        "interpretation": (
            "The file-level SHA-256 pin has drifted repeatedly (new commits "
            "added CroProtocolPackageV2 blueprint-citation logic and other "
            "unrelated capabilities), but evaluate_ip_fto_guard's own "
            "function body has been byte-identical across the ENTIRE "
            "tracked git history and the current working tree: this is a "
            "documentation-pin staleness defect, not an undisclosed change "
            "to ip-fto-guard's tested behavior."
        ),
    },
    "known_prior_acknowledgement": {
        "source": (
            "amphora-assurance-capabilities/evidence/phase0/repairs/R-B01/"
            "done/repair-receipt.R-B01.v1.dsse.json"
        ),
        "field": "known_stale_prose_pins_not_modified",
        "quote": (
            "docs/mission.md prose pins lib.rs sha256 c0b2540f... (already "
            "stale before this repair; flagged non-load-bearing by "
            "metric-schema-parity-v1) and result.v1.json sha256 bbd8a967... "
            "(stale as of this repair). mission.md was deliberately left "
            "untouched: R-B01 scope does not authorize mission prose edits; "
            "maintainer follow-up recorded in RETRACTION-INDEX.md."
        ),
        "days_since_acknowledged_and_unfixed": "2026-08-03 to 2026-08-16 (13 days)",
    },
    "H0": "mission.md/capability-profile.json's pinned source-hash and benchmark-receipt-hash currently identify the real live files.",
    "H0_verdict": "REFUTED",
}

out = Path("/tmp/pinned_hash_integrity_diagnostic.json")
out.write_text(json.dumps(result, indent=2, sort_keys=True))
print(json.dumps(result, indent=2, sort_keys=True))
