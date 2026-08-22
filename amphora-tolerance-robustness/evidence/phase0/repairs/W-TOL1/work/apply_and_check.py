#!/usr/bin/env python3
"""W-TOL1 step 1: apply the RETRACTION-INDEX.md patch on the live tree and
re-run the ORIGINAL V1-RESOLVE mechanical sweep script (byte-identical copy,
unmodified) against the post-patch tree, twice, to confirm (a) the patch
landed exactly as authored off-host and (b) the literal-PENDING mechanical
failure this item was assigned to close is gone for both target rows.
"""
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-tolerance-robustness"
IDX = MOD / "evidence/phase0/kpis/RETRACTION-INDEX.md"
REPAIR = MOD / "evidence/phase0/repairs/W-TOL1"
WORK = REPAIR / "work"

EXPECTED_BEFORE_SHA = "1a2bdc3b90b5b64f495b52365c4b6a283823191922376985f82db30d78796c1b"
EXPECTED_AFTER_SHA = "40960ebd3b6141bc87406b63410e58950406271cc76d3616a757f85cfbf32bfa"
ORIG_SWEEP_SCRIPT = ROOT / "amphora-redteam-audit/evidence/phase0/repairs/V1-RESOLVE/work/run_v1_resolve_sweep.py"
EXPECTED_ORIG_SWEEP_SHA = "ed71f8eaf065af033936de4d23cc4ee3cf54beddd51c970f1cb52f36ddd25823"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def main():
    before_bytes = IDX.read_bytes()
    assert sha(before_bytes) == EXPECTED_BEFORE_SHA, "live file does not match the pre-fire snapshot; abort"

    after_path = WORK / "RETRACTION-INDEX.md.after"
    after_bytes = after_path.read_bytes()
    assert sha(after_bytes) == EXPECTED_AFTER_SHA, "authored patch does not match expected hash; abort"

    orig_sweep_bytes = ORIG_SWEEP_SCRIPT.read_bytes()
    assert sha(orig_sweep_bytes) == EXPECTED_ORIG_SWEEP_SHA, "V1-RESOLVE sweep script changed on disk; abort"

    # apply the patch to the live file
    IDX.write_bytes(after_bytes)
    assert sha(IDX.read_bytes()) == EXPECTED_AFTER_SHA

    # re-run the ORIGINAL, unmodified V1-RESOLVE mechanical sweep script twice
    # (two-replay gate on the diagnostic itself) against the now-patched tree
    runA = subprocess.run([sys.executable, str(ORIG_SWEEP_SCRIPT)], cwd=str(ROOT),
                           capture_output=True, check=True).stdout
    runB = subprocess.run([sys.executable, str(ORIG_SWEEP_SCRIPT)], cwd=str(ROOT),
                           capture_output=True, check=True).stdout
    assert runA == runB, "sweep script not byte-stable across two replays"
    (WORK / "diagnostic.postrepair.runA.json").write_bytes(runA)
    (WORK / "diagnostic.postrepair.runB.json").write_bytes(runB)

    diag = json.loads(runA.decode())
    tol_rows = diag["modules"]["amphora-tolerance-robustness"]["rows"]
    assert len(tol_rows) == 2, f"expected 2 rows, found {len(tol_rows)}"

    row_summ = []
    for r in tol_rows:
        row_summ.append({
            "claim_excerpt": r["claim_excerpt"],
            "literal_pending": r["literal_pending"],
            "superseded_by_paths_cited": r["superseded_by_paths_cited"],
            "superseded_by_exists": r["superseded_by_exists"],
            "superseded_by_verifies": r["superseded_by_verifies"],
            "superseded_by_cell": r["superseded_by_cell"],
        })

    out = {
        "index_before_sha256": sha(before_bytes),
        "index_after_sha256": sha(IDX.read_bytes()),
        "index_after_expected_sha256": EXPECTED_AFTER_SHA,
        "orig_sweep_script_path": "amphora-redteam-audit/evidence/phase0/repairs/V1-RESOLVE/work/run_v1_resolve_sweep.py",
        "orig_sweep_script_sha256": sha(orig_sweep_bytes),
        "postrepair_sweep_two_replay_byte_identical": runA == runB,
        "postrepair_sweep_runA_sha256": sha(runA),
        "tolerance_robustness_rows_postrepair": row_summ,
        "no_literal_pending_remains": all(not r["literal_pending"] for r in row_summ),
        "both_rows_cite_R_C01": all("R-C01" in r["superseded_by_cell"] for r in row_summ),
        "row2_explicitly_disclaims_mismatched_referent": (
            "does not republish a corrected coverage number" in row_summ[1]["superseded_by_cell"]
            or "must not be read as resolving this row" in row_summ[1]["superseded_by_cell"]
        ),
    }
    (WORK / "postrepair-check.v1.json").write_text(json.dumps(out, indent=2, sort_keys=True))
    print(json.dumps(out, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
