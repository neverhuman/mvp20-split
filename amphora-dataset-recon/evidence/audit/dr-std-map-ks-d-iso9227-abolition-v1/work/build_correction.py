#!/usr/bin/env python3
"""Build mapping-table.v4.json: supersede-never-rewrite correction of the
KS D ISO 9227:2005 row found abolished-but-undisclosed by build_audit.py.
v3 is left byte-unmodified on disk."""
import copy
import hashlib
import json
import sys


def sha(b):
    return hashlib.sha256(b).hexdigest()


def build_correction(v3, live_evidence, fire_id, date):
    v4 = copy.deepcopy(v3)
    v4["fire_id"] = fire_id
    v4["date"] = date

    history = live_evidence["raw_field_extractions"]["표준 이력사항 (standard history table)"]
    abolition = next(h for h in history if h["구분"] == "폐지")
    establishment = next(h for h in history if h["구분"] == "제정")

    found = False
    for row in v4["rows"]:
        if row["standard_id"] == "KS D ISO 9227:2005":
            found = True
            row["standard_id"] = "KS D ISO 9227:2005 (ABOLISHED 2005-12-28, per standard.go.kr)"
            row["comparability_rating"] = "not_applicable_abolished"
            row["astm_iso_equiv"] = (
                "N/A -- moot, standard is abolished. (Prior mapping-table.v3.json "
                "claimed 'ISO 9227:1990 (identical adoption, per KSA)'; that "
                "adoption relationship is a historical fact about the now-dead "
                "text, not a live comparability claim.)"
            )
            row["methodological_deltas"] = (
                "N/A -- abolished, no current text to diff. Same treatment as "
                "GB/T 13351-1992 (this table's other abolished-standard row)."
            )
            row["integrity_gap"] = False
            row["integrity_gap_reason"] = (
                "Resolved, not open: abolition status is now confirmed live via "
                "the standard's own official registry, so there is no further "
                "uncertainty to close (same logic as GB/T 13351-1992)."
            )
            row["fire4_correction_note"] = (
                "FIRE-4 CORRECTION (supersedes fire-3 row of the same "
                "standard_id, amphora-dataset-recon/evidence/audit/"
                "dr-std-map-iso9227-edition-currency-v1/"
                "dr-std-map-iso9227-edition-currency-receipt.v1.dsse.json, "
                "mapping-table.v3.json): fire-3's own 'open_items_remaining_for_a_"
                "future_fire' explicitly flagged this row's status as "
                "undischarged because kssn.net/standard.go.kr are JS-rendered "
                "search forms fire-3's WebFetch could not resolve. This fire "
                "resolved it via raw curl (bypassing JS rendering) plus an "
                "independent WebFetch cross-check against standard.go.kr's own "
                "structured record for ksNo=KSDISO9227: 표준번호 field itself "
                "carries the '(폐지)' suffix; 표준 이력사항 (standard history) "
                "table shows 제정 (established) " + establishment["변경일자"] +
                " notification " + establishment["고시번호"] +
                ", then 폐지 (abolished) " + abolition["변경일자"] +
                " notification " + abolition["고시번호"] + ", reason '" +
                abolition["제정/개정/폐지사유"] + "' (duplicate of KS D 9502, "
                "already a separate correctly-mapped row in this same table). "
                "The prior row treated the abolition-confirmation date "
                "(2005-12-28) as if it were merely the standard's 'vintage' "
                "(standard_id suffix ':2005') while signing integrity_gap=false "
                "and a comparability_rating implying live method-class "
                "comparability -- materially misrepresenting a dead standard as "
                "current. Fixed using this table's own established "
                "abolished-standard pattern (GB/T 13351-1992, "
                "comparability_rating='not_applicable_abolished')."
            )
    if not found:
        raise AssertionError("KS D ISO 9227:2005 row not found in mapping-table.v3.json")

    v4["integrity_gap_count"] = sum(1 for r in v4["rows"] if r["integrity_gap"])
    return v4


def main():
    v3_path, live_evidence_path, out_path, fire_id, date = sys.argv[1:6]
    v3 = json.loads(open(v3_path, "rb").read())
    live_evidence = json.loads(open(live_evidence_path, "rb").read())
    v4 = build_correction(v3, live_evidence, fire_id, date)
    open(out_path, "w").write(json.dumps(v4, indent=2, sort_keys=True, ensure_ascii=False))
    print("row_count", v4["row_count"])
    print("integrity_gap_count", v4["integrity_gap_count"])


if __name__ == "__main__":
    main()
