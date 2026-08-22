#!/usr/bin/env python3
"""Build mapping-table.v3.json: supersedes 3 rows of v2 with live-verified
edition-currency corrections found by the DR-STD-MAP ISO-9227 edition-currency
audit. Additive only -- v1 and v2 are left byte-unmodified."""
import hashlib
import json
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-dataset-recon"
STDMAP_WORK = MOD / "evidence/phase0/repairs/DR-STD-MAP/work"
V2_PATH = STDMAP_WORK / "mapping-table.v2.json"
AUDIT_DIR = MOD / "evidence/audit/dr-std-map-iso9227-edition-currency-v1"

FIRE_ID = "20260815T190002-1692638-e6c8305dbc05"


def sha(b):
    return hashlib.sha256(b).hexdigest()


CORRECTIONS = {
    "DIN EN ISO 9227": {
        "new_standard_id": "DIN EN ISO 9227:2024-10",
        "astm_iso_equiv": (
            "DIN EN ISO 9227:2024-10 is the direct German/European adoption of "
            "ISO 9227:2022 + Amd 1:2024 (Deutsche Fassung EN ISO 9227:2022 + A1:2024); "
            "method-class-comparable to ASTM B117. LIVE-VERIFIED this fire "
            "(dinmedia.de): the row's prior citation ('DIN EN ISO 9227', no edition) "
            "spanned three live editions in 7 years -- 2017-07 -> 2023-03 (now "
            "WITHDRAWN) -> 2024-10 (current) -- and the underlying DR-LANG-DE "
            "disposition entry (fire 20260810T080001) never recorded which edition "
            "its license_evidence_quote was drawn from. (ISO 9227's own scope: salt "
            "spray corrosion tests.)"
        ),
        "comparability_rating": "identical_to_iso_by_direct_adoption_edition_confirmed_live_this_fire",
    },
    "NF EN ISO 9227": {
        "new_standard_id": "NF EN ISO 9227:2022 (+A1:2024)",
        "astm_iso_equiv": (
            "NF EN ISO 9227 (2022-11) + NF EN ISO 9227/A1 (2024-06) is the direct "
            "French/European adoption of ISO 9227:2022(+Amd1:2024); method-class-"
            "comparable to ASTM B117. LIVE-VERIFIED this fire (AFNOR boutique + "
            "Norm'Info): the row's prior citation ('NF EN ISO 9227', no edition) did "
            "not record that a base-edition supersession plus an amendment occurred "
            "since the DR-LANG-FR fire's snapshot_date. (ISO 9227's own scope: salt "
            "spray corrosion tests.)"
        ),
        "comparability_rating": "identical_to_iso_by_direct_adoption_edition_confirmed_live_this_fire",
    },
    "PN-EN ISO 9227": {
        "new_standard_id": "PN-EN ISO 9227:2023-02",
        "astm_iso_equiv": (
            "PN-EN ISO 9227:2023-02 is the direct Polish/European adoption of "
            "ISO 9227:2022; method-class-comparable to ASTM B117. LIVE-VERIFIED this "
            "fire (PKN sklep.pkn.pl): the row's prior citation ('PN-EN ISO 9227', no "
            "edition) did not record that PN-EN ISO 9227:2017-06 was superseded by "
            "PN-EN ISO 9227:2023-02 since the DR-LANG-CEE fire's snapshot_date. "
            "(ISO 9227's own scope: salt spray corrosion tests.)"
        ),
        "comparability_rating": "identical_to_iso_by_direct_adoption_edition_confirmed_live_this_fire",
    },
}


def main():
    v2_bytes = V2_PATH.read_bytes()
    v2 = json.loads(v2_bytes)
    v2_sha = sha(v2_bytes)

    audit_result = json.loads((AUDIT_DIR / "work/audit_result.json").read_bytes())
    assert audit_result["input_mapping_table_sha256"] == v2_sha
    assert audit_result["violation_count"] == 3

    v3 = json.loads(json.dumps(v2))  # deep copy
    changed = []
    for row in v3["rows"]:
        sid = row["standard_id"]
        if sid in CORRECTIONS:
            c = CORRECTIONS[sid]
            before = dict(row)
            row["standard_id"] = c["new_standard_id"]
            row["astm_iso_equiv"] = c["astm_iso_equiv"]
            row["comparability_rating"] = c["comparability_rating"]
            row["integrity_gap"] = True
            row["integrity_gap_reason"] = (
                "Edition-currency risk confirmed live this fire (see "
                "evidence/audit/dr-std-map-iso9227-edition-currency-v1/) -- the "
                "underlying disposition-ledger entry never recorded which edition "
                "its evidence quote was drawn from, and this standard has "
                "demonstrated repeated edition churn (including a full "
                "withdrawal-and-replace cycle for the German case) since the "
                "row's own snapshot_date."
            )
            row["methodological_deltas"] = row.get("methodological_deltas", "") + (
                " [fire3 addendum: edition now pinned to the live-current text; "
                "prior unversioned citation could not distinguish which of >=2 "
                "editions its scope-text evidence came from.]"
            )
            changed.append({"standard_id_before": before["standard_id"], "standard_id_after": row["standard_id"]})

    v3["schema"] = v2["schema"]
    v3["fire_id"] = FIRE_ID
    v3["date"] = "2026-08-15"
    v3["campaign_item_id"] = "DR-STD-MAP"
    v3["integrity_gap_count"] = sum(1 for r in v3["rows"] if r["integrity_gap"])
    v3["supersedes"] = {
        "reason": (
            "3 rows (DIN EN ISO 9227, NF EN ISO 9227, PN-EN ISO 9227) were signed "
            "integrity_gap=false with no edition/year specified, despite this fire's "
            "live evidence proving all three standards underwent edition churn "
            "(including one full withdrawal-and-replace cycle) since their original "
            "snapshot_date -- while structurally identical UNE/NP/CSN rows for the "
            "SAME underlying ISO 9227 standard are correctly flagged "
            "integrity_gap=true. See "
            "evidence/audit/dr-std-map-iso9227-edition-currency-v1/ for the "
            "falsifying audit and live evidence."
        ),
        "superseded_deleted_or_modified": False,
        "superseded_path": "amphora-dataset-recon/evidence/phase0/repairs/DR-STD-MAP/work/mapping-table.v2.json",
        "superseded_sha256": v2_sha,
        "rows_changed": changed,
    }

    out_path = STDMAP_WORK / "mapping-table.v3.json"
    out_bytes = json.dumps(v3, indent=2, sort_keys=True, ensure_ascii=False).encode("utf-8")
    out_path.write_bytes(out_bytes)
    print("WROTE", out_path, sha(out_bytes))
    print("rows_changed:", json.dumps(changed, indent=2))


if __name__ == "__main__":
    main()
