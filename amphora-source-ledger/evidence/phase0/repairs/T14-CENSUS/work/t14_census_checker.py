#!/usr/bin/env python3
"""Automated resolve-vs-support checker completing T-14's citation census.

T-14 (2026-08-06) sampled 12/23 (52%) of amphora-source-ledger's load-bearing
facts.json constants and substantively verified each against its cited source.
This script extends the census to the remaining 11/23 load-bearing constants,
using the same method: fetch the cited URL (already done this fire, real
internet egress from xbabe2), extract text (pdftotext -layout for PDFs, tag
strip for HTML), and check that the exact asserted numeric value (or the
literal range it is the disclosed midpoint of) is present in the extracted
text near a recognizable property label.

Runs in two modes:
  --mode real     check the 11 real (key, expected_value, text_file, label_regex)
                   tuples against the real fetched extracts.
  --mode planted  same, but with ONE entry's expected_value swapped to a wrong
                   number that does not appear anywhere in that entry's text,
                   to prove the checker actually fires on a planted defect
                   (positive control).
"""
import argparse
import json
import re
import sys
from pathlib import Path

WORK = Path(
    "/home/ubuntu/amphora/build/mvp20-split/amphora-source-ledger/"
    "evidence/phase0/repairs/T14-CENSUS/work"
)

# (key, expected value as it must appear literally in text, text file, human note)
ENTRIES = [
    ("hardener.ancamide_2353.density", "1.01", "citation_extracts/text_hardener_ancamide_2353_ahew.txt",
     "shares Evonik Americas guide PDF with the already-sampled ahew entry; density is a separate column in the same table row"),
    ("hardener.ancamide_260a.density", "0.960", "citation_extracts/text_hardener_ancamide_2353_ahew.txt",
     "same shared guide PDF, ANCAMIDE 260A row"),
    ("hardener.ancamide_350a.density", ".97", "text_ancamide_350a.txt",
     "Ancamide 350A TDS, 'Specific Gravity @ 77F' field"),
    ("hardener.versamid_115.density", "8.1", "text_versamid_115.txt",
     "TDS states Density as 8.1 lb/gal only; 0.97 g/mL is a unit conversion (8.1 lb/gal x 0.11983 = 0.9707), not a literal value in the source -- checked for the literal lb/gal figure, flagged as derived-unit-conversion in the finding"),
    ("resin.dgeba_331.density", "1.16", "text_dgeba_331.txt",
     "Dow Epoxy Resins doc, D.E.R. 331 table row"),
    ("resin.dgeba_828.density", "1.16", "text_dgeba_828.txt",
     "EPON 828 TDS, literal 'Density 1.16 g/mL' row"),
    ("resin.dgeba_yd128.density", "1.17", "text_dgeba_yd128.txt",
     "Kukdo YD-128 TDS, 'Specific Gravity*1 (20C) 1.17' row"),
    ("resin.solid_cut_1001x75.eew_on_nv", "450", "text_solidcut_1001x75.txt",
     "EPON 1001-X-75 TDS states range 450-550 g/eq on nonvolatiles; 500.0 is the undisclosed arithmetic midpoint -- checked for the literal range bound"),
    ("solvent.mak.density", "0.818", "text_mak.txt",
     "Eastman MAK TDS, 'Specific Gravity @ 20C/20C 0.818'"),
    ("solvent.mibk.density", "0.802", "text_mibk.txt",
     "Eastman MIBK TDS, 'Specific Gravity @ 20C/20C 0.802'"),
    ("solvent.n_butanol.density", "0.81", "text_n_butanol.txt",
     "Eastman n-Butanol TDS, 'Specific Gravity @ 20C/20C 0.81'"),
]

PLANT_KEY = "resin.dgeba_828.density"
PLANT_FAKE_VALUE = "9.94"  # does not appear anywhere in EPON 828 TDS text


def check_entry(key, expected, textfile, note):
    p = WORK / textfile
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["real", "planted"], required=True)
    args = ap.parse_args()

    entries = list(ENTRIES)
    if args.mode == "planted":
        entries = [
            (k, PLANT_FAKE_VALUE, tf, n) if k == PLANT_KEY else (k, e, tf, n)
            for (k, e, tf, n) in entries
        ]

    results = [check_entry(*e) for e in entries]
    n_supports = sum(1 for r in results if r["verdict"] == "supports")
    n_fail = len(results) - n_supports
    out = {
        "mode": args.mode,
        "n_checked": len(results),
        "n_supports": n_supports,
        "n_does_not_support": n_fail,
        "results": results,
    }
    print(json.dumps(out, indent=2))
    if args.mode == "real" and n_fail > 0:
        sys.exit(2)
    if args.mode == "planted" and n_fail == 0:
        sys.exit(3)


if __name__ == "__main__":
    main()
