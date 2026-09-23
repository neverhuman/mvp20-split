"""R-S05 positive control.

The r_crit bisection (search range r in [1e-4, 1.0], the full physically-meaningful range
for a secondary:primary rate ratio) already showed the H2 direction-reversal criterion is
UNREACHABLE for DETA/TETA at resin-dgeba: the starved-vs-rich sol-fraction asymmetry is
topologically forced by the g>>f functionality mismatch (g=5 or 6 vs f=2) and barely moves
across the entire r range (DETA: 5.02 to 5.25 percentage points; TETA: 4.72 to 4.88).
No chemically meaningful r can be planted to make the reversal-detection arm of this harness
fire -- that arm has no positive control available (an honest, logged finding, not a gap in
the fire's diligence).

The harness carries a SECOND, load-bearing falsifying mechanism: the RDKit per-atom
rederivation-vs-fixture structural-integrity gate (functionality_rederivation_agrees_with_
fixture), which gates ok_infra and forces verdict=INFRASTRUCTURE_FAILED (refuses to certify
a corroboration) if the declared amine-H site count for a hardener does not match what RDKit
independently re-derives from its SMILES. This is exactly the kind of defect the attack
exists to catch: a silently wrong site-count label would misconfigure the Monte Carlo pool
sizes and invalidate every downstream direction-rule number without this gate.

This script plants that defect: a copy of the real fixture with hardener-deta's
reactive_amine_hydrogen_count corrupted from 5 (correct: 2 primary N-sites x 2H + 1
pre-existing secondary N-site x 1H) to 4 (as if the internal secondary N-H were missed by a
labeling error), and confirms the harness's own rederivation gate detects it.
"""
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import run_deta_teta_reactivity as harness

FIX = harness.FIX
OUT = harness.OUT


def sha(b):
    return hashlib.sha256(b).hexdigest()


def main():
    real_raw = FIX.read_bytes()
    real_sha = sha(real_raw)
    fix = json.loads(real_raw)
    tampered = json.loads(json.dumps(fix))  # deep copy
    found = False
    for rec in tampered["records"]:
        if rec["record_id"] == "hardener-deta":
            before = rec["facts"]["reactive_amine_hydrogen_count"]
            assert before == 5, before
            rec["facts"]["reactive_amine_hydrogen_count"] = 4
            found = True
    assert found, "hardener-deta record not found in fixture"
    tampered_raw = json.dumps(tampered, indent=2, sort_keys=False).encode()
    tampered_sha = sha(tampered_raw)
    assert tampered_sha != real_sha

    # --- run 1: REAL input, must NOT fire (claim survives) ---
    diag_real = harness.main(mutate_extreme_r=None, fixture_override_bytes=real_raw)

    # --- run 2: TAMPERED input (planted defect), MUST fire ---
    diag_tampered = harness.main(mutate_extreme_r=None, fixture_override_bytes=tampered_raw)

    result = {
        "schema": "amphora.molecule-role-ranker.r-s05-positive-control.v1",
        "purpose": (
            "Demonstrates the harness's structural-integrity gate (functionality_"
            "rederivation_agrees_with_fixture) fires on a planted defect of the kind the "
            "attack exists to catch, since the direction-reversal criterion itself has no "
            "reachable positive control for this g>>f-dominated system (see r_crit "
            "bisection: no reversal found across the full r in [1e-4, 1.0] range)."),
        "planted_defect": {
            "field": "amphora-molecule-role-ranker/reference/phase0-role-known-answer.v1.json"
                     " -> records[record_id=hardener-deta].facts.reactive_amine_hydrogen_count",
            "how_planted": "deep-copied the real fixture in memory, changed hardener-deta's "
                           "reactive_amine_hydrogen_count from 5 (correct, RDKit-verified: 2 "
                           "primary N-H2 sites + 1 pre-existing secondary N-H site) to 4 (as "
                           "if the internal secondary N-H were missed by a labeling error). "
                           "The on-disk fixture file was never touched -- both runs pass "
                           "in-memory byte strings to the harness's fixture_override_bytes "
                           "parameter.",
            "real_fixture_sha256": real_sha, "tampered_fixture_sha256": tampered_sha,
        },
        "run_against_real_input": {
            "fixture_sha256": real_sha,
            "rederivation_agrees": diag_real["functionality_rederivation_agrees_with_fixture"],
            "verdict": diag_real["verdict"],
            "fired": diag_real["verdict"] == "INFRASTRUCTURE_FAILED",
            "expected": "must NOT fire (rederivation_agrees=True, verdict corroborates)",
        },
        "run_against_tampered_input": {
            "fixture_sha256": tampered_sha,
            "rederivation_agrees": diag_tampered["functionality_rederivation_agrees_with_fixture"],
            "verdict": diag_tampered["verdict"],
            "fired": diag_tampered["verdict"] == "INFRASTRUCTURE_FAILED",
            "expected": "MUST fire (rederivation_agrees=False, verdict=INFRASTRUCTURE_FAILED)",
            "hardener_site_structure_deta": diag_tampered["hardener_site_structure"]["hardener-deta"],
        },
        "detected": bool(diag_tampered["verdict"] == "INFRASTRUCTURE_FAILED"
                        and diag_real["verdict"] != "INFRASTRUCTURE_FAILED"),
        "r_crit_no_positive_control_available_note": (
            "the direction-reversal criterion was independently checked to be unreachable "
            "for ANY r in the full physically-meaningful [1e-4, 1.0] range (see "
            "r_crit_bisection in diagnostic.canonical.json: reversal_found_in_range=false "
            "for both DETA and TETA) -- a topologically-forced g>>f result, not a weak "
            "attack; this is why the positive control targets the harness's OTHER live "
            "falsifying mechanism (structural-integrity gate) instead."),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    txt = json.dumps(result, indent=2, sort_keys=True)
    path = OUT / "positive_control.canonical.json"
    path.write_text(txt)
    print("WROTE", path)
    print("sha256", sha(txt.encode()))
    print("detected", result["detected"])
    print("real_verdict", diag_real["verdict"])
    print("tampered_verdict", diag_tampered["verdict"])


if __name__ == "__main__":
    main()
