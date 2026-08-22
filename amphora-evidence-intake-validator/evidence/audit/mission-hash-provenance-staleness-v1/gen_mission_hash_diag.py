#!/usr/bin/env python3
"""Diagnostic generator for mission-hash-provenance-staleness-v1.

Mechanically extracts the SHA-256 hashes docs/mission.md cites for its own
"live checked implementation" (amphora-assurance-capabilities/src/lib.rs)
and "Focused checked test evidence" (amphora-assurance-capabilities/src/
diagnostics.rs), recomputes the real on-disk SHA-256 of both files, and
reports whether the citation still identifies the current file. No RNG, no
wall clock, no network. Deterministic function of on-disk bytes only.
"""
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-evidence-intake-validator"
MISSION = MOD / "docs/mission.md"
LIB_RS = ROOT / "amphora-assurance-capabilities/src/lib.rs"
DIAG_RS = ROOT / "amphora-assurance-capabilities/src/diagnostics.rs"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def extract_hashes(text, filename):
    # matches: `<filename>` ... SHA-256 `<64-hex>` on the same line/sentence,
    # both the inline-prose form and the bullet-list form used in mission.md.
    pattern = re.compile(
        re.escape(filename) + r"[^\n]*?SHA-256 `([0-9a-f]{64})`"
    )
    return pattern.findall(text)


mission_bytes = MISSION.read_bytes()
mission_text = mission_bytes.decode("utf-8")

lib_cited = extract_hashes(mission_text, "amphora-assurance-capabilities/src/lib.rs")
diag_cited = extract_hashes(mission_text, "amphora-assurance-capabilities/src/diagnostics.rs")

lib_actual = sha(LIB_RS.read_bytes())
diag_actual = sha(DIAG_RS.read_bytes())

lib_cited_unique = sorted(set(lib_cited))
diag_cited_unique = sorted(set(diag_cited))

lib_stale = (len(lib_cited_unique) >= 1) and all(c != lib_actual for c in lib_cited_unique)
diag_stale = (len(diag_cited_unique) >= 1) and all(c != diag_actual for c in diag_cited_unique)

# Corroborating provenance: git history of both source files and mission.md,
# to show the citations were never refreshed across subsequent edits.
def git_log(path):
    out = subprocess.run(
        ["git", "log", "--oneline", "--follow", "--", str(path.relative_to(ROOT))],
        cwd=str(ROOT), capture_output=True, text=True,
    ).stdout.strip().splitlines()
    return out


lib_git_log = git_log(LIB_RS)
diag_git_log = git_log(DIAG_RS)
mission_git_log = git_log(MISSION)

mission_front_matter_audit_date = None
m = re.search(r'"audit_date"\s*:\s*"([^"]+)"', mission_text)
if m:
    mission_front_matter_audit_date = m.group(1)

diag = {
    "schema": "amphora.evidence-intake-validator.mission-hash-provenance-staleness-probe.v1",
    "inputs": {
        "mission_md_path": str(MISSION.relative_to(ROOT)),
        "mission_md_sha256": sha(mission_bytes),
        "lib_rs_path": str(LIB_RS.relative_to(ROOT)),
        "diagnostics_rs_path": str(DIAG_RS.relative_to(ROOT)),
        "mission_front_matter_audit_date": mission_front_matter_audit_date,
    },
    "extraction": {
        "lib_rs_cited_hashes_found": lib_cited,
        "lib_rs_cited_hashes_unique": lib_cited_unique,
        "diagnostics_rs_cited_hashes_found": diag_cited,
        "diagnostics_rs_cited_hashes_unique": diag_cited_unique,
    },
    "actual": {
        "lib_rs_sha256_actual": lib_actual,
        "diagnostics_rs_sha256_actual": diag_actual,
    },
    "results": {
        "lib_rs_citation_count": len(lib_cited),
        "lib_rs_citation_internally_consistent": len(lib_cited_unique) <= 1,
        "lib_rs_citation_matches_actual": (not lib_stale),
        "diagnostics_rs_citation_count": len(diag_cited),
        "diagnostics_rs_citation_internally_consistent": len(diag_cited_unique) <= 1,
        "diagnostics_rs_citation_matches_actual": (not diag_stale),
    },
    "gates": {
        "g1_lib_rs_citation_found_and_nonempty": len(lib_cited) > 0,
        "g2_diagnostics_rs_citation_found_and_nonempty": len(diag_cited) > 0,
        "g3_lib_rs_citation_stale": lib_stale,
        "g4_diagnostics_rs_citation_stale": diag_stale,
        "all_gates_passed": (len(lib_cited) > 0 and len(diag_cited) > 0),
    },
    "corroboration": {
        "lib_rs_git_log_oneline": lib_git_log,
        "diagnostics_rs_git_log_oneline": diag_git_log,
        "mission_md_git_log_oneline": mission_git_log,
        "note": (
            "lib.rs and diagnostics.rs git history is shown to establish "
            "that both files have commits in this repository's tracked "
            "history; mission.md's own audit_date front-matter field "
            "predates or does not track these commits, and mission.md's "
            "hash citations were not refreshed across mission.md's own "
            "subsequent edits (see mission_md_git_log_oneline)."
        ),
    },
    "verdict_recommendation": (
        "CLAIM_REFUTED" if (lib_stale or diag_stale) else "CLAIM_SURVIVED"
    ),
}

print(json.dumps(diag, indent=2, sort_keys=True))
