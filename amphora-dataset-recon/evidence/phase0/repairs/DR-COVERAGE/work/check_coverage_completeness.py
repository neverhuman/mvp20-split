#!/usr/bin/env python3
"""Independent completeness checker for the DR-COVERAGE deliverable
(amphora-dataset-recon coverage-map.v1.json). AUDIT_ONLY.

Implements, byte-for-byte, the DR-COVERAGE refutation_criterion:
  "Any register gap or MODELED or ASSUMED recipe element has neither a best
  recommended source, a best conditional source, nor an explicit
  commissioned-measurement conversion, or names a source absent from the
  Dataset Ledger."

Two independent checks:
  (1) triple-null: for every gaps[] row that serves at least one real module
      gap (module_gaps non-empty -- i.e. it IS a register gap, not a bare
      infrastructure/access-path note with module_gaps==[]), at least one of
      best_recommended / best_conditional / commissioned_measurement_candidate
      must be non-null. A row failing this has an unconverted empty result.
  (2) recommended-source-in-ledger: every non-null best_recommended value must
      resolve to a dataset-ledger.v1.jsonl entry by candidate_id. (Directive
      Section 8: only RECOMMENDED-verdict candidates enter the Dataset Ledger;
      CONDITIONAL candidates are expected to live in the Disposition Ledger
      instead, so best_conditional is NOT checked against the Dataset Ledger.)

This script never imports or trusts any prior DR-LANG/DR-GAP build script --
it re-derives both facts directly from the frozen input files.
"""
import hashlib
import json
import sys
from pathlib import Path

COVERAGE_MAP = Path(sys.argv[1])
DATASET_LEDGER = Path(sys.argv[2])


def sha(b):
    return hashlib.sha256(b).hexdigest()


def run():
    cm_bytes = COVERAGE_MAP.read_bytes()
    cm = json.loads(cm_bytes)
    dl_lines = [l for l in DATASET_LEDGER.read_text().splitlines() if l.strip()]
    dl_entries = [json.loads(l) for l in dl_lines]
    dl_candidate_ids = {e.get("candidate_id") for e in dl_entries}

    gaps = cm["gaps"]

    triple_null_violations = []
    for g in gaps:
        module_gaps = g.get("module_gaps") or []
        if not module_gaps:
            # Infrastructure/access-path note, not a register gap serving a
            # module -- out of scope for the triple-null rule.
            continue
        triple = (g.get("best_recommended"), g.get("best_conditional"),
                  g.get("commissioned_measurement_candidate"))
        if all(v is None for v in triple):
            triple_null_violations.append({
                "gap_id": g["gap_id"],
                "module_gaps": module_gaps,
                "note": g.get("note"),
            })

    recommended_not_in_ledger = []
    for g in gaps:
        br = g.get("best_recommended")
        if br is not None and br not in dl_candidate_ids:
            recommended_not_in_ledger.append({
                "gap_id": g["gap_id"],
                "best_recommended": br,
            })

    refutation_criterion_fired = bool(triple_null_violations) or bool(recommended_not_in_ledger)

    result = {
        "schema": "amphora.dataset-recon.dr-coverage.completeness-check.v1",
        "input_coverage_map_sha256": sha(cm_bytes),
        "input_coverage_map_gaps_count": len(gaps),
        "input_dataset_ledger_sha256": sha(DATASET_LEDGER.read_bytes()),
        "input_dataset_ledger_entries_count": len(dl_entries),
        "input_dataset_ledger_candidate_ids": sorted(x for x in dl_candidate_ids if x),
        "triple_null_violations_count": len(triple_null_violations),
        "triple_null_violations": sorted(triple_null_violations, key=lambda r: r["gap_id"]),
        "recommended_not_in_ledger_count": len(recommended_not_in_ledger),
        "recommended_not_in_ledger": sorted(recommended_not_in_ledger, key=lambda r: r["gap_id"]),
        "refutation_criterion_fired": refutation_criterion_fired,
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    run()
