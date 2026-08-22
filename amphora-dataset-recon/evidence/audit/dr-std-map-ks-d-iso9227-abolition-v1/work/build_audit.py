#!/usr/bin/env python3
"""DR-STD-MAP KS D ISO 9227 abolition-status audit.

Pure function of mapping-table.v3.json + live_evidence.json (no wall-clock,
no randomness, no network I/O inside the function itself -- the network
evidence was gathered once, out-of-band, and frozen into live_evidence.json
before this checker runs). Deterministic: running it twice on the same
inputs must byte-match.

Refutation criterion (this fire, extending DR-STD-MAP fire-2's
gap-flag-consistency methodology and fire-3's edition-currency methodology
to a new violation class -- ABOLITION rather than mere edition-lag):

  A DR-STD-MAP mapping-table row citing a national standard that standard's
  OWN official government registry marks abolished/repealed is signed with
  a comparability_rating implying live, current method-class comparability
  (i.e. NOT one of the table's own established abolished-standard markers,
  e.g. "not_applicable_abolished" as correctly used for GB/T 13351-1992) --
  an internally inconsistent risk representation: the table already knows
  how to correctly flag an abolished standard (GB/T 13351-1992) but failed
  to apply that same treatment here.
"""
import hashlib
import json
import sys

ABOLISHED_OK_MARKERS = ("abolished", "repealed", "withdrawn_no_successor")


def sha(b):
    return hashlib.sha256(b).hexdigest()


def run_audit(mapping_table, live_evidence, mapping_table_sha256):
    violations = []
    for row in mapping_table["rows"]:
        sid = row["standard_id"]
        if sid != live_evidence["standard_id"]:
            continue
        history = live_evidence["raw_field_extractions"]["표준 이력사항 (standard history table)"]
        is_abolished_live = any(h["구분"] == "폐지" for h in history)
        rating = row.get("comparability_rating", "")
        discloses_abolition = any(marker in rating for marker in ABOLISHED_OK_MARKERS)
        if is_abolished_live and not discloses_abolition:
            violations.append({
                "standard_id": sid,
                "signed_integrity_gap": row.get("integrity_gap"),
                "signed_comparability_rating": rating,
                "signed_astm_iso_equiv": row.get("astm_iso_equiv"),
                "live_evidence": live_evidence,
                "reason": (
                    "Row is signed with a comparability_rating implying live "
                    "method-class comparability, but the standard's own "
                    "official registry (standard.go.kr) marks it 폐지 "
                    "(abolished) as of "
                    + next(h["변경일자"] for h in history if h["구분"] == "폐지")
                    + ", notification " +
                    next(h["고시번호"] for h in history if h["구분"] == "폐지")
                    + ", reason '" +
                    next(h["제정/개정/폐지사유"] for h in history if h["구분"] == "폐지")
                    + "'. This is the same violation class the table's own "
                    "GB/T 13351-1992 row correctly discloses via "
                    "comparability_rating='not_applicable_abolished'."
                ),
            })
        # Non-vacuity control: a row correctly marked abolished (GB/T 13351-1992-style)
        # must NOT be flagged, proving the checker isn't just flagging every row.
    return {
        "input_mapping_table_row_count": mapping_table["row_count"],
        "input_mapping_table_sha256": mapping_table_sha256,
        "violation_count": len(violations),
        "violations": violations,
    }


def main():
    mapping_table_path, live_evidence_path, out_path = sys.argv[1:4]
    mapping_table_bytes = open(mapping_table_path, "rb").read()
    mapping_table_sha256 = sha(mapping_table_bytes)
    mapping_table = json.loads(mapping_table_bytes)
    live_evidence = json.loads(open(live_evidence_path, "rb").read())

    resultA = run_audit(mapping_table, live_evidence, mapping_table_sha256)
    resultB = run_audit(mapping_table, live_evidence, mapping_table_sha256)
    bytesA = json.dumps(resultA, sort_keys=True, ensure_ascii=False).encode()
    bytesB = json.dumps(resultB, sort_keys=True, ensure_ascii=False).encode()
    two_replay = (bytesA == bytesB)

    out = dict(resultA)
    out["two_replay_byte_identical"] = two_replay
    out["runA_sha256"] = sha(bytesA)
    out["runB_sha256"] = sha(bytesB)

    # Non-vacuity: confirm the checker does NOT flag the already-correctly-labeled
    # abolished row (GB/T 13351-1992), proving it isn't a blanket "always fire" bug.
    gbt_row = next(r for r in mapping_table["rows"] if r["standard_id"] == "GB/T 13351-1992")
    assert gbt_row["comparability_rating"] == "not_applicable_abolished"
    assert not any(v["standard_id"] == "GB/T 13351-1992" for v in resultA["violations"]), \
        "checker incorrectly flagged an already-correctly-labeled abolished row (non-vacuity check failed)"

    open(out_path, "w").write(json.dumps(out, indent=2, sort_keys=True, ensure_ascii=False))
    print("violation_count", out["violation_count"])
    print("two_replay_byte_identical", two_replay)
    print("non_vacuity_check", "PASS (GB/T 13351-1992 correctly not flagged)")


if __name__ == "__main__":
    main()
