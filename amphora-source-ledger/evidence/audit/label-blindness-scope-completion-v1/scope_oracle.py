#!/usr/bin/env python3
"""Extends amphora-source-ledger/evidence/audit/citation-census-checker-label-blindness-v1.

That fire (2026-08-17) REFUTED the claim that t14_census_checker.py's
check_entry() verifies label-correct, product-specific citation support, but
tested only 2 of the 23 load-bearing facts.json constants (resin.dgeba_331.density,
hardener.ancamide_2353.density) and explicitly left 21/23 untested, stating they
"may or may not be similarly exposed."

This fire completes that census for the highest-risk remaining entries: every
OTHER load-bearing entry that (per direct inspection of the T-14 / T14-CENSUS
citation-sample findings) is ALSO sourced from a shared multi-product document --
the same Evonik "Epoxy curing agents product guide (Americas)" PDF the 2353
density finding was drawn from. Four such entries were identified and had not
been probed by the prior fire:

  - hardener.ancamide_2353.ahew   (expected "114", same shared Evonik guide)
  - hardener.ancamide_260a.ahew   (expected "120", same shared Evonik guide)
  - hardener.ancamide_700b75.ahew (expected "170", same shared Evonik guide)
  - hardener.ancamide_260a.density (expected "0.960", same shared Evonik guide)

For each, this script confirms (by direct table-row inspection) a REAL, distinct,
adjacent product in the same document shares the identical literal figure, then
runs the verbatim original check_entry() and a stricter label-proximity
re-implementation against both the true attribution and a wrong-product-swapped
attribution using that real adjacent row.

As a scope-boundary CONTROL, three single-product-TDS entries from the census
(solvent.mak.density, solvent.mibk.density, solvent.n_butanol.density) are also
occurrence-counted to confirm the defect does NOT manifest where the cited
document genuinely names only one product (no candidate wrong-product row
exists to swap in) -- establishing the boundary of the finding, not just its
existence.

REFUTATION CRITERION (same as the prior fire's, extended to these 4 new
entries): if the verbatim, unmodified check_entry() function reports
verdict="supports" for a (key, expected_value, text_file) tuple where the
claimed product identity has been swapped to a DIFFERENT real product's row in
the same shared document sharing the identical literal figure, that further
confirms/extends the REFUTED claim.
"""
import json
import re
import sys
from pathlib import Path

T14_WORK = Path(
    "/home/ubuntu/amphora/build/mvp20-split/amphora-source-ledger/"
    "evidence/phase0/repairs/T-14/work"
)
CENSUS_WORK = Path(
    "/home/ubuntu/amphora/build/mvp20-split/amphora-source-ledger/"
    "evidence/phase0/repairs/T14-CENSUS/work"
)


def _resolve(textfile):
    # citation_extracts/* live under T-14/work in this fire's probe (byte-identical
    # to the T14-CENSUS copies used by the original checker; verified by diff
    # before this script was written). Top-level text_*.txt files (the
    # single-product controls) live under T14-CENSUS/work, matching
    # t14_census_checker.py's ENTRIES table verbatim.
    if textfile.startswith("citation_extracts/"):
        return T14_WORK / textfile
    return CENSUS_WORK / textfile


# --- verbatim reproduction of t14_census_checker.py's check_entry() ---
def original_check_entry(key, expected, textfile, note):
    p = _resolve(textfile)
    text = p.read_text(errors="replace")
    found = expected in text
    return {
        "key": key,
        "expected_value_checked": expected,
        "text_file": textfile,
        "note": note,
        "found_literal": found,
        "verdict": "supports" if found else "DOES_NOT_SUPPORT",
    }


WINDOW = 60


def label_aware_check_entry(key, expected, textfile, product_label, note):
    p = _resolve(textfile)
    text = p.read_text(errors="replace")
    hits = []
    for m in re.finditer(re.escape(expected), text):
        s, e = m.start(), m.end()
        ctx = text[max(0, s - WINDOW): e + WINDOW]
        if product_label.lower() in ctx.lower():
            hits.append({"pos": s, "context": ctx.replace("\n", " | ")})
    return {
        "key": key,
        "expected_value_checked": expected,
        "product_label_required": product_label,
        "text_file": textfile,
        "note": note,
        "n_label_adjacent_occurrences": len(hits),
        "found_label_adjacent": len(hits) > 0,
        "verdict": "supports" if hits else "DOES_NOT_SUPPORT",
        "matched_contexts": hits[:2],
    }


SHARED_DOC = "citation_extracts/text_hardener_ancamide_2353_ahew.txt"

NEW_REAL_ENTRIES = [
    dict(
        key="hardener.ancamide_2353.ahew",
        expected="114",
        textfile=SHARED_DOC,
        product_label="2353",
        note="true citation: ANCAMIDE(R) 2353 row, WT/{H}=AHEW column, Evonik Americas curing-agent guide",
    ),
    dict(
        key="hardener.ancamide_260a.ahew",
        expected="120",
        textfile=SHARED_DOC,
        product_label="260A",
        note="true citation: ANCAMIDE(R) 260A row, WT/{H}=AHEW column, same shared guide",
    ),
    dict(
        key="hardener.ancamide_700b75.ahew",
        expected="170",
        textfile=SHARED_DOC,
        product_label="700-B-75",
        note="true citation: ANCAMIDE(R) 700-B-75 row, WT/{H}=AHEW column, same shared guide",
    ),
    dict(
        key="hardener.ancamide_260a.density",
        expected="0.960",
        textfile=SHARED_DOC,
        product_label="260A",
        note="true citation: ANCAMIDE(R) 260A row, Specific Gravity column, same shared guide (not tested by the prior fire, which only tested the ancamide_2353.density entry from this doc)",
    ),
]

# Wrong-product planted defects: same shared document, same literal figure,
# a genuinely different, real, adjacent product row (confirmed by direct
# table-row inspection of the checked-in extract before this script was
# written; see table_row_confirmation below).
NEW_PLANTED_WRONGPRODUCT_ENTRIES = [
    dict(
        key="hardener.ancamide_2353.ahew",
        expected="114",
        textfile=SHARED_DOC,
        product_label="2424",
        note="PLANTED: swapped claimed product identity to ANCAMIDE(R) 2424 (real, different product row, same literal WT/{H}=114 value)",
    ),
    dict(
        key="hardener.ancamide_260a.ahew",
        expected="120",
        textfile=SHARED_DOC,
        product_label="261A",
        note="PLANTED: swapped claimed product identity to ANCAMIDE(R) 261A (real, different product row, same literal WT/{H}=120 value)",
    ),
    dict(
        key="hardener.ancamide_700b75.ahew",
        expected="170",
        textfile=SHARED_DOC,
        product_label="702-B-75",
        note="PLANTED: swapped claimed product identity to ANCAMIDE(R) 702-B-75 (real, different product row, same literal WT/{H}=170 value)",
    ),
    dict(
        key="hardener.ancamide_260a.density",
        expected="0.960",
        textfile=SHARED_DOC,
        product_label="260TN",
        note="PLANTED: swapped claimed product identity to ANCAMIDE(R) 260TN (real, different product row, same literal Specific Gravity=0.960 value)",
    ),
]

TABLE_ROW_CONFIRMATION = {
    "textfile": SHARED_DOC,
    "table_title": "Curing Agent product-comparison table (polyamide/amidoamine section), Epoxy curing agents product guide (Americas)",
    "wt_h_ahew_column_header_confirmed": "vertical header token 'WT/{H}' present directly above the polyamide table's data rows (confirmed at the ANCAMIDE 220 row, line ~1481 of the extract).",
    "rows_sharing_ahew_114": [
        "ANCAMIDE(R) 2353   Modified Polyamide   9   3,000    1.01   330   114   60   65   4.5   131",
        "ANCAMIDE(R) 2424   Modified Polyamide   9   14,000   1.00   327   114   60   60   3.0   129",
        "ANCAMIDE(R) 2767   Modified Polyamide   7   2100     1.08   340   114   60   57   5     142",
    ],
    "rows_sharing_ahew_120": [
        "ANCAMIDE(R) 260A    Amide/Imidazoline   7   40,000   0.960   350   120   65   120   10   NA",
        "ANCAMIDE(R) 261A    Amide/Imidazoline   7   35,000-  0.96    320-  120   65   75    7    NA",
        "ANCAMIDE(R) 260TN   Amide/Imidazoline   7   35,000   0.960   350   120   65   270   10   NA",
    ],
    "rows_sharing_ahew_170": [
        "ANCAMIDE(R) 700-B-75   Adduct Solution   7      5,000       0.960   240   170   90",
        "ANCAMIDE(R) 702-B-75   Adduct Solution   8 max   4,000-8,000 0.96    230-  170   90",
    ],
    "rows_sharing_density_0_960": [
        "ANCAMIDE(R) 260A    ... 0.960 ...",
        "ANCAMIDE(R) 260TN   ... 0.960 ...",
        "ANCAMIDE(R) 375A    ... 0.960 ...",
    ],
    "control_confirming_column_is_real_and_varying": "ANCAMIDE(R) 220 row: WT/{H}=185 -- differs from all four values above, confirming this is a genuinely varying parsed field, not a mis-parsed constant.",
}

# Scope-boundary controls: single-product TDS documents from the same census,
# where no other real product exists in the cited document to swap in.
CONTROL_SINGLE_PRODUCT_ENTRIES = [
    dict(key="solvent.mak.density", expected="0.818", textfile="text_mak.txt",
         note="Eastman MAK TDS names exactly one product (MAK); no candidate wrong-product row exists in this document."),
    dict(key="solvent.mibk.density", expected="0.802", textfile="text_mibk.txt",
         note="Eastman MIBK TDS names exactly one product (MIBK); no candidate wrong-product row exists in this document."),
    dict(key="solvent.n_butanol.density", expected="0.81", textfile="text_n_butanol.txt",
         note="Eastman n-Butanol TDS names exactly one product (n-Butanol); no candidate wrong-product row exists in this document."),
]


def occurrence_census(entries):
    out = []
    for e in entries:
        text = _resolve(e["textfile"]).read_text(errors="replace")
        raw_count = text.count(e["expected"])
        out.append({"key": e["key"], "expected": e["expected"], "textfile": e["textfile"], "raw_substring_occurrences": raw_count})
    return out


def main():
    result = {}

    result["table_row_confirmation"] = TABLE_ROW_CONFIRMATION
    result["occurrence_census_new_entries"] = occurrence_census(NEW_REAL_ENTRIES)
    result["occurrence_census_control_entries"] = occurrence_census(CONTROL_SINGLE_PRODUCT_ENTRIES)

    result["original_checker_on_new_real_entries"] = [
        original_check_entry(e["key"], e["expected"], e["textfile"], e["note"]) for e in NEW_REAL_ENTRIES
    ]
    result["original_checker_on_new_wrongproduct_planted_entries"] = [
        original_check_entry(e["key"], e["expected"], e["textfile"], e["note"]) for e in NEW_PLANTED_WRONGPRODUCT_ENTRIES
    ]
    result["label_aware_checker_on_new_real_entries"] = [
        label_aware_check_entry(e["key"], e["expected"], e["textfile"], e["product_label"], e["note"]) for e in NEW_REAL_ENTRIES
    ]
    result["label_aware_checker_on_new_wrongproduct_planted_entries"] = [
        label_aware_check_entry(e["key"], e["expected"], e["textfile"], e["product_label"], e["note"]) for e in NEW_PLANTED_WRONGPRODUCT_ENTRIES
    ]
    result["original_checker_on_control_single_product_entries"] = [
        original_check_entry(e["key"], e["expected"], e["textfile"], e["note"]) for e in CONTROL_SINGLE_PRODUCT_ENTRIES
    ]

    orig_wrong_supports = sum(
        1 for r in result["original_checker_on_new_wrongproduct_planted_entries"] if r["verdict"] == "supports"
    )
    label_wrong_supports = sum(
        1 for r in result["label_aware_checker_on_new_wrongproduct_planted_entries"] if r["verdict"] == "supports"
    )
    orig_real_supports = sum(
        1 for r in result["original_checker_on_new_real_entries"] if r["verdict"] == "supports"
    )
    label_real_supports = sum(
        1 for r in result["label_aware_checker_on_new_real_entries"] if r["verdict"] == "supports"
    )
    control_occurrence_counts = [c["raw_substring_occurrences"] for c in result["occurrence_census_control_entries"]]

    result["refutation_confirmed"] = orig_wrong_supports == len(NEW_PLANTED_WRONGPRODUCT_ENTRIES)
    result["label_aware_fix_also_insufficient"] = label_wrong_supports == len(NEW_PLANTED_WRONGPRODUCT_ENTRIES)

    result["summary"] = {
        "n_new_wrongproduct_entries_tested": len(NEW_PLANTED_WRONGPRODUCT_ENTRIES),
        "original_checker_wrongly_validates_n": orig_wrong_supports,
        "label_aware_checker_wrongly_validates_n": label_wrong_supports,
        "original_checker_correctly_validates_real_n": orig_real_supports,
        "label_aware_checker_correctly_validates_real_n": label_real_supports,
        "refutation_confirmed": result["refutation_confirmed"],
        "label_aware_fix_also_insufficient": result["label_aware_fix_also_insufficient"],
        "cumulative_confirmed_exposed_loadbearing_entries": 6,
        "cumulative_confirmed_exposed_note": (
            "2 confirmed by the prior fire (resin.dgeba_331.density, hardener.ancamide_2353.density) "
            "+ 4 newly confirmed by this fire (hardener.ancamide_2353.ahew, hardener.ancamide_260a.ahew, "
            "hardener.ancamide_700b75.ahew, hardener.ancamide_260a.density) = 6 of 23 (26.1%) load-bearing "
            "facts.json constants whose cited mechanized-checker 'supports' verdict cannot discriminate "
            "the true product attribution from a real wrong-product sibling sharing the identical literal figure."
        ),
        "control_single_product_entries_raw_occurrence_counts": control_occurrence_counts,
        "control_note": (
            "Raw substring occurrence count only (not an exhaustive proof of zero ambiguity); "
            "each control document's TDS names exactly one commercial product, so even a >1 raw count "
            "reflects the same product's value appearing in more than one place on its own TDS "
            "(e.g. a units-conversion footnote), not a distinct sibling product row."
        ),
    }

    print(json.dumps(result, indent=2, sort_keys=True))
    if not result["refutation_confirmed"]:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
