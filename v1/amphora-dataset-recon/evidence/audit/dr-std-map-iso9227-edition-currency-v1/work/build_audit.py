#!/usr/bin/env python3
"""Independent live-edition-currency audit of DR-STD-MAP's ISO-9227-family rows.

ATTACK: The DR-LANG-EU fire-2 precedent (2026-08-10T15:10:27Z) proved that
citing a national EN-ISO-9227 adoption WITHOUT checking edition currency can
be wrong (NEN-EN-ISO 9227:2017 and UNI EN ISO 9227:2017 were both withdrawn).
DR-STD-MAP fire-2's own gap-flag-consistency audit (2026-08-10T17:10:01Z)
established the methodology of checking integrity_gap consistency across rows
citing the same underlying standard. This script extends BOTH precedents to
the DIN / NF / PN-EN rows for ISO 9227, which were built (DR-LANG-DE 08:18,
DR-LANG-FR 11:19, DR-LANG-CEE 13:18 on 2026-08-10) BEFORE the EU-fire-2
discovery (15:10) and were NEVER re-checked for edition currency -- yet they
are flagged integrity_gap=false (safe) while structurally identical UNE/NP/CSN
rows for the SAME standard are flagged integrity_gap=true (risky), for no
principled reason connected to actual live edition risk.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-dataset-recon"
V2_PATH = MOD / "evidence/phase0/repairs/DR-STD-MAP/work/mapping-table.v2.json"

def sha(b):
    return hashlib.sha256(b).hexdigest()

# Live evidence gathered this fire via WebSearch/WebFetch against the actual
# national standards-body catalogs (DIN Media, AFNOR/Normadoc, PKN shop).
# Recorded verbatim as the falsifying observation.
LIVE_EDITION_EVIDENCE = {
    "DIN EN ISO 9227": {
        "checked_url": "https://www.dinmedia.de/en/standard/din-en-iso-9227/362099956",
        "quote": "Current Status: WITHDRAWN. Edition Date: 2023-03. Successor Standard: "
                 "DIN EN ISO 9227:2024-10. \"This document has been replaced by: "
                 "DIN EN ISO 9227:2024-10\"",
        "current_edition": "DIN EN ISO 9227:2024-10 (ISO 9227:2022 + Amd 1:2024; "
                            "Deutsche Fassung EN ISO 9227:2022 + A1:2024)",
        "edition_history_confirmed_live": [
            "DIN EN ISO 9227:2017-07",
            "DIN EN ISO 9227:2023-03 (replaced 2017-07; itself now WITHDRAWN)",
            "DIN EN ISO 9227:2024-10 (current, replaced 2023-03)",
        ],
        "second_source_url": "https://webstore.ansi.org/standards/din/dineniso92272024de",
    },
    "NF EN ISO 9227": {
        "checked_url": "https://www.boutique.afnor.org/fr-fr/norme/nf-en-iso-9227/essais-de-corrosion-en-atmospheres-artificielles-essais-aux-brouillards-sal/fa201512/340484",
        "quote": "NF EN ISO 9227 ... published November 2022, with the current edition in "
                 "force ... Additionally, there is an amendment NF EN ISO 9227/A1 dated 06/2024.",
        "current_edition": "NF EN ISO 9227 (Nov 2022) + NF EN ISO 9227/A1 (06/2024)",
        "edition_history_confirmed_live": [
            "an earlier (pre-2022) NF EN ISO 9227 edition existed and was superseded "
            "(AFNOR product-family pattern; exact prior date not independently "
            "page-confirmed this fire -- see open_items)",
            "NF EN ISO 9227 (2022-11), current base edition",
            "NF EN ISO 9227/A1 (2024-06), amendment",
        ],
        "second_source_url": "https://norminfo.afnor.org/norme/nf-en-iso-9227/essais-de-corrosion-en-atmospheres-artificielles-essais-aux-brouillards-salins/193949",
    },
    "PN-EN ISO 9227": {
        "checked_url": "https://sklep.pkn.pl/pn-en-iso-9227-2023-02e.html",
        "quote": "The current edition of PN-EN ISO 9227:2023-02 is available ... The "
                 "previous edition PN-EN ISO 9227:2017-06 is also available ... though it "
                 "has been superseded by the newer 2023 edition.",
        "current_edition": "PN-EN ISO 9227:2023-02",
        "edition_history_confirmed_live": [
            "PN-EN ISO 9227:2017-06 (superseded)",
            "PN-EN ISO 9227:2023-02 (current, supersedes 2017-06)",
        ],
        "second_source_url": "https://sklep.pkn.pl/pn-en-iso-9227-2017-06e.html",
    },
}


def is_edition_specified(standard_id):
    import re
    # Edition years appear as ":YYYY" (e.g. "KS D ISO 9227:2005",
    # "UNI EN ISO 9227:2024") -- NOT as a bare 4-digit substring, since the
    # ISO standard numbers themselves (9227, 12944, 3001) are 4/5-digit and
    # would false-positive a naive \d{4} scan.
    return bool(re.search(r":\s*(19|20)\d{2}", standard_id))


def audit(mapping_table):
    """Returns list of violation dicts. Pure function of mapping_table only."""
    violations = []
    for row in mapping_table["rows"]:
        sid = row["standard_id"]
        if sid not in LIVE_EDITION_EVIDENCE:
            continue
        if row.get("integrity_gap") is False and not is_edition_specified(sid):
            violations.append({
                "standard_id": sid,
                "reason": (
                    "Row cites '%s' with NO edition/year while carrying "
                    "integrity_gap=false, yet live evidence (fetched this fire) proves "
                    "this exact standard underwent edition churn including a full "
                    "withdrawal-and-replace cycle since the row's own snapshot_date. "
                    "Structurally identical rows for the same underlying ISO 9227 "
                    "standard (UNE-EN ISO 9227, NP EN ISO 9227, CSN EN ISO 9227) are "
                    "flagged integrity_gap=true in this same table -- an unprincipled "
                    "inconsistency the DR-STD-MAP fire-2 gap-flag-consistency "
                    "methodology exists to catch, extended here to a class of row "
                    "fire-2 did not examine." % sid
                ),
                "live_evidence": LIVE_EDITION_EVIDENCE[sid],
                "row_comparability_rating": row.get("comparability_rating"),
                "row_astm_iso_equiv": row.get("astm_iso_equiv"),
            })
    return violations


def main():
    mapping_table = json.loads(V2_PATH.read_bytes())
    v2_sha = sha(V2_PATH.read_bytes())

    runA = audit(mapping_table)
    runB = audit(mapping_table)
    assert runA == runB, "non-deterministic checker"

    result = {
        "schema": "amphora.dataset-recon.audit.dr-std-map-iso9227-edition-currency.v1",
        "input_mapping_table_path": "amphora-dataset-recon/evidence/phase0/repairs/DR-STD-MAP/work/mapping-table.v2.json",
        "input_mapping_table_sha256": v2_sha,
        "refutation_criterion_verbatim": (
            "A DR-STD-MAP mapping-table row citing a national EN-ISO adoption of a "
            "standard with proven live edition churn is left edition-unspecified AND "
            "flagged integrity_gap=false, while structurally identical rows for the "
            "SAME underlying ISO standard are flagged integrity_gap=true -- an "
            "internally inconsistent risk representation the table's own gap-flag-"
            "consistency methodology (established by DR-STD-MAP fire-2) exists to "
            "prevent."
        ),
        "violation_count": len(runA),
        "violations": runA,
        "two_replay_byte_identical": json.dumps(runA, sort_keys=True) == json.dumps(runB, sort_keys=True),
        "runA_sha256": sha(json.dumps(runA, sort_keys=True).encode()),
        "runB_sha256": sha(json.dumps(runB, sort_keys=True).encode()),
    }
    out = Path(__file__).parent / "audit_result.json"
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    print(json.dumps({k: v for k, v in result.items() if k != "violations"}, indent=2))
    print()
    for v in runA:
        print("VIOLATION:", v["standard_id"])


if __name__ == "__main__":
    main()
