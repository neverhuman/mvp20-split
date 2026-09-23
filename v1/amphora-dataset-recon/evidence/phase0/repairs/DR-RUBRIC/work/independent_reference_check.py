#!/usr/bin/env python3
"""Independent 'second party' re-derivation of rubric.v1.json's six formulas.
Deliberately does NOT import scorer.py -- it is a from-scratch reading of the
published rubric document plus the frozen snapshot, written to prove the
rubric's second_party_reproducibility_statement is true: anyone handed only
rubric.v1.json and a candidate's raw attributes can reach the same numbers
by table lookup and arithmetic alone.

Usage: python3 independent_reference_check.py <rubric.json> <snapshot.json> <out.json>
"""
import json
import sys


def main(rubric_path, snapshot_path, out_path):
    rubric = json.load(open(rubric_path))
    snapshot = json.load(open(snapshot_path))

    dim_tables = {}
    for d in rubric["dimensions"]:
        dim_tables[d["key"]] = d["scoring_rule"]["tables"]

    out_rows = []
    for c in snapshot["candidates"]:
        gap_fit = (dim_tables["gap_fit"]["gap_match_class"][c["gap_match_class"]]
                   + dim_tables["gap_fit"]["meets_minimum_n_and_measurement_class"][c["meets_minimum_n_and_measurement_class"]])
        prov = (dim_tables["provenance_measurement_quality"]["data_class"][c["data_class"]]
                + dim_tables["provenance_measurement_quality"]["standard_and_uncertainty_disclosed"][c["standard_and_uncertainty_disclosed"]])
        rights = dim_tables["rights_clarity"]["rights_tier"][c["rights_tier"]]
        uniq = dim_tables["uniqueness"]["redundancy_class"][c["redundancy_class"]]
        base_integrity = dim_tables["integrity_risk"]["translation_confidence"][c["translation_confidence"]]
        integrity = base_integrity - 2 * len(c.get("integrity_flags", []))
        if integrity < 0:
            integrity = 0
        acquisition = dim_tables["acquisition_cost_friction"]["reachability"][c["reachability"]]

        total = gap_fit + prov + rights + uniq + integrity + acquisition
        overall = round(total / 6.0, 4)

        if rights == 0 or acquisition == 0 or gap_fit == 0:
            verdict = "REJECTED"
        elif overall >= 7.0 and rights >= 5 and acquisition >= 4:
            verdict = "RECOMMENDED"
        else:
            verdict = "CONDITIONAL"

        out_rows.append({
            "candidate_id": c["candidate_id"],
            "dimension_scores": {
                "gap_fit": gap_fit,
                "provenance_measurement_quality": prov,
                "rights_clarity": rights,
                "uniqueness": uniq,
                "integrity_risk": integrity,
                "acquisition_cost_friction": acquisition,
            },
            "overall_score": overall,
            "verdict": verdict,
        })

    ranked = sorted(out_rows, key=lambda r: (-r["overall_score"], r["candidate_id"]))
    for i, r in enumerate(ranked, start=1):
        r["rank"] = i

    result = {
        "schema": "amphora.dataset-recon.dr-rubric-scoring-output.v1",
        "rubric_schema": rubric["schema"],
        "snapshot_schema": snapshot["schema"],
        "ranking": ranked,
    }
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2, sort_keys=True)
    print("WROTE", out_path)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
