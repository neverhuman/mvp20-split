#!/usr/bin/env python3
"""Deterministic scorer for rubric.v1.json applied to a frozen candidate
snapshot. Pure function of (rubric.v1.json, candidate_snapshot*.json) --
no wall-clock, no randomness, no unordered-iteration dependence. Canonical
output is json.dumps(..., sort_keys=True) so byte-identity across replays
is a meaningful determinism test.

Usage: python3 scorer.py <rubric.json> <snapshot.json> <out.json>
"""
import json
import sys


def score_candidate(rubric, c):
    dims = {d["key"]: d for d in rubric["dimensions"]}

    def lookup(dim_key, field):
        tbl = dims[dim_key]["scoring_rule"]["tables"][field]
        return tbl

    gap_fit = (lookup("gap_fit", "gap_match_class")[c["gap_match_class"]]
               + lookup("gap_fit", "meets_minimum_n_and_measurement_class")[c["meets_minimum_n_and_measurement_class"]])

    provenance = (lookup("provenance_measurement_quality", "data_class")[c["data_class"]]
                  + lookup("provenance_measurement_quality", "standard_and_uncertainty_disclosed")[c["standard_and_uncertainty_disclosed"]])

    rights = lookup("rights_clarity", "rights_tier")[c["rights_tier"]]

    uniqueness = lookup("uniqueness", "redundancy_class")[c["redundancy_class"]]

    base_integrity = lookup("integrity_risk", "translation_confidence")[c["translation_confidence"]]
    integrity = max(0, base_integrity - 2 * len(c.get("integrity_flags", [])))

    acquisition = lookup("acquisition_cost_friction", "reachability")[c["reachability"]]

    scores = {
        "gap_fit": gap_fit,
        "provenance_measurement_quality": provenance,
        "rights_clarity": rights,
        "uniqueness": uniqueness,
        "integrity_risk": integrity,
        "acquisition_cost_friction": acquisition,
    }
    overall = round(sum(scores.values()) / 6.0, 4)

    if rights == 0 or acquisition == 0 or gap_fit == 0:
        verdict = "REJECTED"
    elif overall >= 7.0 and rights >= 5 and acquisition >= 4:
        verdict = "RECOMMENDED"
    else:
        verdict = "CONDITIONAL"

    return {
        "candidate_id": c["candidate_id"],
        "dimension_scores": scores,
        "overall_score": overall,
        "verdict": verdict,
    }


def run(rubric_path, snapshot_path):
    rubric = json.load(open(rubric_path))
    snapshot = json.load(open(snapshot_path))
    results = [score_candidate(rubric, c) for c in snapshot["candidates"]]
    ranked = sorted(results, key=lambda r: (-r["overall_score"], r["candidate_id"]))
    for i, r in enumerate(ranked, start=1):
        r["rank"] = i
    return {
        "schema": "amphora.dataset-recon.dr-rubric-scoring-output.v1",
        "rubric_schema": rubric["schema"],
        "snapshot_schema": snapshot["schema"],
        "ranking": ranked,
    }


if __name__ == "__main__":
    rubric_path, snapshot_path, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
    out = run(rubric_path, snapshot_path)
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2, sort_keys=True)
    print("WROTE", out_path)
