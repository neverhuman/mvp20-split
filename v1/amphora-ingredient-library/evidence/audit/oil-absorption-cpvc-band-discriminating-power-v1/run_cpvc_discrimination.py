#!/usr/bin/env python3
"""
amphora-ingredient-library : discriminating-power audit of the CPVC
plausibility-band gate signed in oil-absorption-cpvc-v1 (AUDIT_ONLY).

Claim under attack
-------------------
evidence/audit/oil-absorption-cpvc-v1/oil-absorption-cpvc-receipt.v1.dsse.json
purpose: "First independent physical second-signal for the pigment oil-absorption
constant family: Daniel/Asbeck-Van Loo CPVC envelope + fail-closed gate."
closes: "...gross OA corruption fails closed."
headline: "...10/10 within the mineral-extender plausibility band [0.30,0.75]..."

This receipt presents the CPVC plausibility-band check (CPVC_PLAUS_LO/HI =
[0.30, 0.75]) as an INDEPENDENT physical second-signal that adds fail-closed
detection power over the existing, tighter, coatings-literature ASTM D281
OA-class-band check (LIT_OA_BAND) computed in the SAME oracle. checkC in the
live oracle demonstrates this only against synthetic order-of-magnitude
corruptions (10x / 0.1x). This audit tests the claim against (a) the actual
OA/density pairs in the live catalog, including the one real, already-
disclosed anomaly (pigment.iron_oxide_yellow.oil_abs = 14, flagged in the
target receipt itself as below its own D281 literature class band), and
(b) the full admissible-OA interval implied by the CPVC plausibility band,
compared against the tighter literature band, for every pigment.

Falsifiable prediction the target receipt's framing requires
--------------------------------------------------------------
If the CPVC plausibility-band gate is a genuine independent fail-closed
second-signal (as opposed to a strictly weaker echo of the literature-band
check already computed in the same oracle), then for the ONE real data point
in the live catalog that the literature-band check itself flags as anomalous
(iron_oxide_yellow), the CPVC gate must ALSO flag it as implausible.

REFUTING OBSERVATION: it does not. Live oracle constants (imported directly
from the target's own run_cpvc.py, not retyped) give
CPVC(iron_oxide_yellow) = 0.6254, comfortably inside [0.30, 0.75].
Additionally, for 7 of the 9 literature-band-covered pigments the ENTIRE
published D281 literature band is a strict subset of the OA interval the
CPVC plausibility band would accept -- meaning the CPVC gate is mathematically
incapable of ever flagging a value inside the literature band as implausible
for those 7 pigments, and for the other 2 (barytes, iron_oxide_yellow) it is
tighter only outside the literature band's own extremes, never inside it.
The CPVC gate's "10/10 within plausibility band" headline is therefore not
informative: it is close to a mathematical guarantee for any physically
sane OA value (correct or wrong) at these densities, not a genuine test.
"""
import base64, hashlib, json, sys, importlib.util

ROOT = "/home/ubuntu/amphora/build/mvp20-split"
TARGET_DIR = ROOT + "/amphora-ingredient-library/evidence/audit/oil-absorption-cpvc-v1"
FACTS_REL = "reference/mvp20/data/facts.json"
FACTS = ROOT + "/amphora-ingredient-library/" + FACTS_REL
TARGET_RECEIPT = TARGET_DIR + "/oil-absorption-cpvc-receipt.v1.dsse.json"
TARGET_ORACLE = TARGET_DIR + "/run_cpvc.py"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def load_target_oracle():
    spec = importlib.util.spec_from_file_location("target_run_cpvc", TARGET_ORACLE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def oa_for_cpvc(cpvc, rho_pig, rho_oil):
    """Invert the target oracle's own cpvc_from_oa(oa, rho) for OA at a given CPVC."""
    v_pig = 100.0 / rho_pig
    v_oil = v_pig * (1.0 - cpvc) / cpvc
    return v_oil * rho_oil


def build():
    tgt = load_target_oracle()
    facts = json.load(open(FACTS))
    ent = facts["entries"]
    facts_sha = sha(open(FACTS, "rb").read())
    target_oracle_sha = sha(open(TARGET_ORACLE, "rb").read())
    target_receipt_sha = sha(open(TARGET_RECEIPT, "rb").read())

    rows = []
    for oak, (lo, hi, note) in sorted(tgt.LIT_OA_BAND.items()):
        base = oak[: -len(".oil_abs")]
        denk = base + ".density"
        rho = float(ent[denk]["value"])
        oa_actual = float(ent[oak]["value"])
        cpvc_actual = tgt.cpvc_from_oa(oa_actual, rho, tgt.RHO_OIL)
        oa_cpvc_lo = oa_for_cpvc(tgt.CPVC_PLAUS_HI, rho, tgt.RHO_OIL)  # CPVC=hi -> OA lower edge
        oa_cpvc_hi = oa_for_cpvc(tgt.CPVC_PLAUS_LO, rho, tgt.RHO_OIL)  # CPVC=lo -> OA upper edge
        lit_band_fully_inside_cpvc_band = (oa_cpvc_lo <= lo) and (hi <= oa_cpvc_hi)
        actual_flagged_by_lit_band = not (lo <= oa_actual <= hi)
        actual_flagged_by_cpvc_band = not (tgt.CPVC_PLAUS_LO <= cpvc_actual <= tgt.CPVC_PLAUS_HI)
        max_multiplicative_slack_lit = min(oa_actual / lo, hi / oa_actual) if lo > 0 else None
        max_multiplicative_slack_cpvc = min(oa_actual / oa_cpvc_lo, oa_cpvc_hi / oa_actual) if oa_cpvc_lo > 0 else None
        rows.append({
            "constant_oa": oak,
            "rho_pig_g_per_cm3": rho,
            "oa_actual_g_per_100g": oa_actual,
            "cpvc_actual": round(cpvc_actual, 4),
            "literature_d281_band_g_per_100g": [lo, hi],
            "cpvc_plausibility_implied_oa_band_g_per_100g": [round(oa_cpvc_lo, 2), round(oa_cpvc_hi, 2)],
            "literature_band_fully_subsumed_by_cpvc_band": bool(lit_band_fully_inside_cpvc_band),
            "actual_value_flagged_by_literature_band": bool(actual_flagged_by_lit_band),
            "actual_value_flagged_by_cpvc_band": bool(actual_flagged_by_cpvc_band),
            "multiplicative_slack_before_literature_band_trips": round(max_multiplicative_slack_lit, 3),
            "multiplicative_slack_before_cpvc_band_trips": round(max_multiplicative_slack_cpvc, 3),
        })

    n_covered = len(rows)
    n_subsumed = sum(1 for r in rows if r["literature_band_fully_subsumed_by_cpvc_band"])
    n_lit_flags = sum(1 for r in rows if r["actual_value_flagged_by_literature_band"])
    n_cpvc_flags_of_lit_flagged = sum(
        1 for r in rows
        if r["actual_value_flagged_by_literature_band"] and r["actual_value_flagged_by_cpvc_band"])
    avg_slack_lit = sum(r["multiplicative_slack_before_literature_band_trips"] for r in rows) / n_covered
    avg_slack_cpvc = sum(r["multiplicative_slack_before_cpvc_band_trips"] for r in rows) / n_covered

    falsification_criterion = (
        "If the CPVC plausibility-band gate ([%.2f,%.2f]) is a genuine independent "
        "fail-closed second-signal (not strictly subsumed by the literature-band gate "
        "already computed in the same oracle), then for every real catalog OA value the "
        "literature-band check itself flags as anomalous, the CPVC gate must ALSO flag it."
        % (tgt.CPVC_PLAUS_LO, tgt.CPVC_PLAUS_HI)
    )
    criterion_would_be_refuted_if = "n_lit_flags >= 1 and n_cpvc_flags_of_lit_flagged < n_lit_flags"
    observed_refutes_criterion = bool(n_lit_flags >= 1 and n_cpvc_flags_of_lit_flagged < n_lit_flags)

    diag = {
        "schema": "amphora.ingredient-library.oil-absorption-cpvc-band-discriminating-power-audit.v1",
        "module": "amphora-ingredient-library",
        "run_type": "AUDIT_ONLY",
        "authority": "AUDIT_ONLY",
        "attacks": {
            "receipt": "amphora-ingredient-library/evidence/audit/oil-absorption-cpvc-v1/oil-absorption-cpvc-receipt.v1.dsse.json",
            "claim": "CPVC plausibility-band gate [0.30,0.75] is an independent physical "
                     "second-signal / fail-closed gate over the pigment oil-absorption family, "
                     "distinct from (adds power beyond) the literature D281 OA-class-band check "
                     "computed in the same oracle.",
        },
        "purpose": "Test whether the CPVC plausibility-band gate signed in oil-absorption-cpvc-v1 "
                   "has independent discriminating power, or is mathematically subsumed by (strictly "
                   "weaker than) the literature OA-class-band check already computed in the same oracle.",
        "method": "Imported the TARGET receipt's own live oracle module (run_cpvc.py) directly -- "
                  "reused its LIT_OA_BAND dict, RHO_OIL, CPVC_PLAUS_LO/HI, and cpvc_from_oa() verbatim, "
                  "no retyped constants -- inverted cpvc_from_oa() to find, per pigment, the full OA "
                  "interval the CPVC plausibility band would accept, and compared it against the "
                  "already-published literature band for the same pigment, plus the actual live "
                  "catalog value.",
        "non_circularity": "Consumes only the target's own oracle module + the live facts.json; "
                           "the OA-interval inversion is an exact algebraic inverse of the target's "
                           "own cpvc_from_oa(), so it cannot introduce a discrepancy the target's own "
                           "function would not reproduce forwards.",
        "falsification_criterion": falsification_criterion,
        "criterion_would_be_refuted_if": criterion_would_be_refuted_if,
        "inputs": {
            "facts_json": FACTS_REL, "facts_json_sha256": facts_sha,
            "target_oracle_sha256": target_oracle_sha,
            "target_receipt_sha256": target_receipt_sha,
        },
        "per_constant": rows,
        "results": {
            "n_pigments_literature_band_covered": n_covered,
            "n_literature_band_fully_subsumed_by_cpvc_band": n_subsumed,
            "n_real_catalog_values_flagged_by_literature_band": n_lit_flags,
            "n_of_those_also_flagged_by_cpvc_band": n_cpvc_flags_of_lit_flagged,
            "named_unflagged_anomaly": (
                "pigment.iron_oxide_yellow.oil_abs = 14 g/100g: literature-band-flagged "
                "(band [28.0,80.0]) but CPVC = 0.6254 is inside [0.30,0.75] -- NOT flagged"
                if n_lit_flags >= 1 and n_cpvc_flags_of_lit_flagged < n_lit_flags else None
            ),
            "avg_multiplicative_slack_literature_band": round(avg_slack_lit, 3),
            "avg_multiplicative_slack_cpvc_band": round(avg_slack_cpvc, 3),
            "cpvc_band_slack_vs_literature_band_ratio": round(avg_slack_cpvc / avg_slack_lit, 3),
            "observed_refutes_criterion": observed_refutes_criterion,
        },
        "verdict": "CLAIM_REFUTED" if observed_refutes_criterion else "CLAIM_SURVIVED",
        "headline": None,
        "closes": "Demonstrates the CPVC plausibility-band gate in oil-absorption-cpvc-v1 is not an "
                  "independent fail-closed second-signal on the real catalog: its own literature-band "
                  "anomaly (iron_oxide_yellow) passes the CPVC gate undetected, the literature band is "
                  "a strict subset of the CPVC-accepted OA interval for 7/9 covered pigments, and on "
                  "average the CPVC gate tolerates %.1fx more multiplicative OA error than the "
                  "literature band before tripping." % (avg_slack_cpvc / avg_slack_lit),
        "does_not_close": [
            "Does NOT claim the Daniel/Asbeck-Van Loo CPVC identity itself is wrong -- the physical "
            "relationship and its hard geometric bound (0,1) are untouched.",
            "Does NOT retract the literature OA-class-band check, which is the tighter and more "
            "informative of the two gates in the target oracle.",
            "Does NOT modify facts.json, the module manifest, or any signed Phase-0 KPI.",
            "Does NOT alter the target oil-absorption-cpvc-v1 receipt in place -- that artifact is "
            "left byte-identical; this is a new, separate audit receipt.",
        ],
        "modifies_manifest": False,
        "modifies_module_manifest": False,
        "modifies_locked_dataset": False,
        "modifies_signed_phase0_kpi": False,
        "promotes_authority": False,
        "flips_scientific_readiness": False,
        "human_review_performed": False,
    }
    diag["headline"] = (
        "CPVC plausibility-band gate [%.2f,%.2f] signed in oil-absorption-cpvc-v1 is subsumed by "
        "(strictly weaker than) the oracle's own literature D281 OA-class-band check for %d/%d "
        "covered pigments; the one real catalog anomaly the literature band flags "
        "(iron_oxide_yellow, OA=14) is NOT flagged by the CPVC gate (CPVC=0.6254 inside [0.30,0.75]); "
        "CPVC gate tolerates %.1fx more multiplicative OA error on average before tripping than the "
        "literature band -> the 'independent fail-closed second-signal' framing is refuted on the "
        "real catalog, even though checkC's synthetic 10x/0.1x mutation demo (unaffected) still holds."
        % (tgt.CPVC_PLAUS_LO, tgt.CPVC_PLAUS_HI, n_subsumed, n_covered, avg_slack_cpvc / avg_slack_lit)
    )
    return diag


def canon(obj):
    return json.dumps(obj, indent=2, sort_keys=True).encode()


if __name__ == "__main__":
    d1 = build(); b1 = canon(d1); h1 = sha(b1)
    d2 = build(); b2 = canon(d2); h2 = sha(b2)
    assert b1 == b2, "two-replay byte MISMATCH"
    if len(sys.argv) > 1 and sys.argv[1] == "--emit":
        open("diagnostic.canonical.json", "wb").write(b1)
        open("diagnostic.runB.json", "wb").write(b2)
    print("replay_sha256:", h1, "| byte_stable:", h1 == h2)
    print("verdict:", d1["verdict"])
    print("headline:", d1["headline"])
