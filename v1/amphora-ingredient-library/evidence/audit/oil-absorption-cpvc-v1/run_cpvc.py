#!/usr/bin/env python3
"""
amphora-ingredient-library : independent physical second-signal for the pigment
oil-absorption constant family via the Daniel / Asbeck-Van Loo critical pigment
volume concentration (CPVC) relationship (AUDIT_ONLY).

Motivation
----------
The prior signed audit receipt (constant-crosscheck-v1) corroborated the DGEBA
EEW family (structure-derived oligomer band) and the solvent/resin DENSITY family
(CRC second source), and honestly left the pigment oil-absorption (OA) constants
untouched -- every OA entry in facts.json is flagged load_bearing:false, grade
ESTIMATE/DISTRIBUTOR, single-source. This harness adds the FIRST physical
second-signal over that OA family. It does NOT promote the OA constants to
load-bearing; it establishes a published physical *plausibility envelope* that
(a) ties two independent catalog constants (OA and skeletal density) together
through a rights-clean textbook relationship, (b) produces a formulation-relevant
derived quantity (CPVC) with a hard physical-necessity gate, and (c) fails closed
under gross OA corruption.

Non-circular published baseline
-------------------------------
Daniel oil-absorption -> CPVC identity (per 100 g pigment):
    V_pig  = 100 / rho_pig            [mL]   (skeletal density)
    V_oil  = OA   / rho_oil           [mL]   (OA in g linseed oil / 100 g pigment)
    CPVC   = V_pig / (V_pig + V_oil)         [volume fraction]
At CPVC the just-sufficient binder (here the D281 linseed-oil probe) exactly fills
the interparticle void of the densest-packed pigment bed.
Primary sources:
  Asbeck, W.K. & Van Loo, M. "Critical Pigment Volume Relationships",
     Ind. Eng. Chem. 41(7) 1470-1475 (1949).
  Patton, T.C. "Paint Flow and Pigment Dispersion", 2nd ed., Wiley 1979,
     ch. on CPVC & oil absorption (ISBN 978-0-471-03272-3).
  Bierwagen, G.P. "CPVC calculations", J. Coat. Technol. 64(806) 1992.
Oil-absorption method reference: ASTM D281 (spatula rub-out, g oil / 100 g pigment).
rho_oil = 0.935 g/mL, acid-refined linseed oil (D281 probe, Patton 1979).

The relationship is independent of the supplier TDS that sourced each OA value:
it consumes only OA + skeletal density and returns a packing fraction whose
admissible range is fixed by geometry (0 < CPVC < 1) and by the coatings-literature
class band for mineral extenders / oxides.

Honest scope
------------
- OA constants remain non-load-bearing single-source supplier ESTIMATEs; this
  receipt asserts a physical *envelope*, NOT a supplier-independent measured lock
  (that needs a second D281 measurement -> DATA_ASK if ever promoted).
- carbon_black OA is a DBP/OAN structure number, NOT ASTM D281 -> EXCLUDED from
  the D281 literature-band check (method mismatch), CPVC reported diagnostic-only.
- iron_oxide_yellow OA=14 is BELOW the acicular-goethite class band -> surfaced as
  an honest anomaly, not silently passed.
"""
import base64, hashlib, json, sys

FACTS_REL = "reference/mvp20/data/facts.json"
FACTS = "/home/ubuntu/amphora/build/mvp20-split/amphora-ingredient-library/" + FACTS_REL

RHO_OIL = 0.935  # g/mL acid-refined linseed oil, ASTM D281 probe (Patton 1979)

# Coatings-literature ASTM D281 class-typical OA bands (g oil / 100 g pigment).
# Source: Patton 1979 (Paint Flow & Pigment Dispersion) + standard pigment-
# technology class ranges. Bands are deliberately WIDE (class envelopes, not
# grade point values). carbon_black excluded (DBP/OAN method != D281).
LIT_OA_BAND = {
    "pigment.barytes.oil_abs":          (6.0, 18.0,  "BaSO4 blocky extender, low OA class 6-15 (Patton 1979)"),
    "pigment.talc.oil_abs":             (20.0, 55.0, "platy Mg3Si4O10(OH)2, class 22-50 grade-dependent"),
    "pigment.silica.oil_abs":           (18.0, 45.0, "crystalline silica extender, class 20-40"),
    "pigment.mica.oil_abs":             (25.0, 70.0, "platy muscovite, high-OA class 25-65"),
    "pigment.wollastonite.oil_abs":     (16.0, 35.0, "acicular CaSiO3, low-OA class 20-30"),
    "pigment.iron_oxide_red.oil_abs":   (13.0, 40.0, "synthetic hematite, class 15-35"),
    "pigment.iron_oxide_black.oil_abs": (13.0, 35.0, "synthetic magnetite, class 15-30"),
    "pigment.iron_oxide_yellow.oil_abs":(28.0, 80.0, "acicular alpha-FeOOH goethite, HIGH-OA class 30-75"),
    "pigment.zinc_phosphate.oil_abs":   (13.0, 35.0, "Zn3(PO4)2 anti-corrosive pigment, class 15-30"),
}
OA_METHOD_MISMATCH = {"pigment.carbon_black.oil_abs"}  # DBP/OAN, not D281

# Physical-necessity gate + coatings plausibility band for CPVC (volume fraction).
CPVC_HARD_LO, CPVC_HARD_HI = 0.0, 1.0          # geometric necessity
CPVC_PLAUS_LO, CPVC_PLAUS_HI = 0.30, 0.75      # mineral extender/oxide class envelope


def cpvc_from_oa(oa, rho_pig, rho_oil=RHO_OIL):
    v_pig = 100.0 / rho_pig
    v_oil = oa / rho_oil
    return v_pig / (v_pig + v_oil)


def build():
    facts = json.load(open(FACTS))
    ent = facts["entries"]
    facts_sha = hashlib.sha256(open(FACTS, "rb").read()).hexdigest()

    # ---- CheckA : Daniel CPVC over every pigment with OA + density ----------
    rows = []
    oa_keys = sorted(k for k in ent if k.endswith(".oil_abs"))
    for oak in oa_keys:
        base = oak[: -len(".oil_abs")]
        denk = base + ".density"
        if denk not in ent:
            continue
        oa = float(ent[oak]["value"])
        rho = float(ent[denk]["value"])
        cpvc = cpvc_from_oa(oa, rho)
        method_ok = oak not in OA_METHOD_MISMATCH
        lit = LIT_OA_BAND.get(oak)
        if lit and method_ok:
            lo, hi, note = lit
            oa_in_band = lo <= oa <= hi
            band = [lo, hi]
        else:
            oa_in_band = None
            band = None
            note = ("DBP/OAN structure number, NOT ASTM D281 -- excluded from band check"
                    if not method_ok else "no class band")
        rows.append({
            "constant_oa": oak,
            "constant_density": denk,
            "oa_g_per_100g": round(oa, 4),
            "skeletal_density_g_per_cm3": round(rho, 4),
            "cpvc_volume_fraction": round(cpvc, 4),
            "cpvc_pct": round(100.0 * cpvc, 2),
            "cpvc_within_hard_physical_bound": bool(CPVC_HARD_LO < cpvc < CPVC_HARD_HI),
            "cpvc_within_plausibility_band": bool(CPVC_PLAUS_LO <= cpvc <= CPVC_PLAUS_HI),
            "oa_d281_band": band,
            "oa_within_literature_band": (None if oa_in_band is None else bool(oa_in_band)),
            "oa_method_is_d281": bool(method_ok),
            "oa_grade": ent[oak].get("grade"),
            "oa_load_bearing": bool(ent[oak].get("load_bearing", False)),
            "literature_note": note,
        })

    n_total = len(rows)
    n_hard = sum(1 for r in rows if r["cpvc_within_hard_physical_bound"])
    n_plaus = sum(1 for r in rows if r["cpvc_within_plausibility_band"])
    checked = [r for r in rows if r["oa_within_literature_band"] is not None]
    n_oa_in_band = sum(1 for r in checked if r["oa_within_literature_band"])
    oa_anomalies = [r["constant_oa"] for r in checked if not r["oa_within_literature_band"]]
    method_excluded = [r["constant_oa"] for r in rows if not r["oa_method_is_d281"]]

    # ---- CheckB : monotonicity / physical-sensitivity of the Daniel map -----
    # With OA on a per-100g mass basis, CPVC is strictly DECREASING in OA
    # (more void-filling oil) and strictly DECREASING in skeletal density
    # (same pigment mass occupies less volume -> smaller pigment volume fraction).
    mono_oa = (cpvc_from_oa(10.0, 2.8) > cpvc_from_oa(20.0, 2.8) > cpvc_from_oa(40.0, 2.8))
    mono_rho = (cpvc_from_oa(29.0, 2.0) > cpvc_from_oa(29.0, 3.0) > cpvc_from_oa(29.0, 4.5))

    # ---- CheckC : fail-closed mutation demo on talc OA (29 baseline) --------
    tk = "pigment.talc.oil_abs"
    rho_talc = float(ent["pigment.talc.density"]["value"])
    oa_talc = float(ent[tk]["value"])
    muts = []
    for label, val in [("baseline", oa_talc),
                       ("decimal_slip_2.9", oa_talc / 10.0),
                       ("digit_insert_290", oa_talc * 10.0),
                       ("transpose_92", 92.0),
                       ("mistype_39_small_within_band", 39.0)]:
        c = cpvc_from_oa(val, rho_talc)
        in_plaus = CPVC_PLAUS_LO <= c <= CPVC_PLAUS_HI
        muts.append({
            "mutation": label, "oa_g_per_100g": round(val, 4),
            "cpvc_pct": round(100.0 * c, 2),
            "within_plausibility_band": bool(in_plaus),
            "flagged": bool(not in_plaus),
        })

    diag = {
        "schema": "amphora.ingredient-library-oil-absorption-cpvc.v1",
        "module": "amphora-ingredient-library",
        "run_type": "AUDIT_ONLY",
        "authority": "AUDIT_ONLY",
        "purpose": "First independent physical second-signal for the pigment oil-absorption "
                   "constant family: Daniel/Asbeck-Van Loo CPVC envelope + fail-closed gate.",
        "hypothesis": "Catalog OA + skeletal density map, via the published Daniel CPVC identity, "
                      "to packing fractions inside the geometric bound (0,1) and the coatings class "
                      "envelope; gross OA corruption is driven outside the envelope (fails closed).",
        "inputs": {"facts_json": FACTS_REL, "facts_json_sha256": facts_sha},
        "non_circularity": "CPVC identity consumes only catalog OA + skeletal density and returns a "
                           "geometry-fixed packing fraction; the D281 literature bands are coatings-"
                           "textbook class envelopes (Patton 1979) independent of the supplier TDS "
                           "that sourced each catalog OA value.",
        "theory_reference": {
            "cpvc_relationship": "Asbeck & Van Loo, Ind. Eng. Chem. 41(7):1470-1475 (1949)",
            "textbook": "Patton, Paint Flow and Pigment Dispersion, 2nd ed., Wiley 1979 (ISBN 978-0-471-03272-3)",
            "cpvc_calc": "Bierwagen, J. Coat. Technol. 64(806) 1992",
            "oil_absorption_method": "ASTM D281 (linseed-oil spatula rub-out, g/100g)",
            "rho_oil_g_per_mL": RHO_OIL,
        },
        "constants": {
            "rho_oil_g_per_mL": RHO_OIL,
            "cpvc_hard_bound": [CPVC_HARD_LO, CPVC_HARD_HI],
            "cpvc_plausibility_band": [CPVC_PLAUS_LO, CPVC_PLAUS_HI],
        },
        "checkA_daniel_cpvc": {
            "n_pigments_with_oa_and_density": n_total,
            "n_cpvc_within_hard_physical_bound": n_hard,
            "n_cpvc_within_plausibility_band": n_plaus,
            "all_cpvc_within_hard_bound": bool(n_hard == n_total),
            "per_constant": rows,
        },
        "checkA_oa_literature_band": {
            "n_oa_checked_against_d281_band": len(checked),
            "n_oa_within_literature_band": n_oa_in_band,
            "oa_anomalies_below_or_above_class_band": oa_anomalies,
            "oa_excluded_method_mismatch": method_excluded,
        },
        "checkB_monotonicity": {
            "cpvc_strictly_decreasing_in_oa": bool(mono_oa),
            "cpvc_strictly_decreasing_in_density_at_fixed_mass_basis_oa": bool(mono_rho),
            "both_physical_directions_hold": bool(mono_oa and mono_rho),
        },
        "checkC_fail_closed_mutation_demo": {
            "target": tk, "baseline_oa": round(oa_talc, 4), "talc_density": round(rho_talc, 4),
            "mutations": muts,
            "gross_corruptions_flagged": bool(all(m["flagged"] for m in muts if m["mutation"] not in
                                                  ("baseline", "mistype_39_small_within_band"))),
        },
        "headline": None,
        "closes": "Provides a rights-clean published physical envelope (Daniel CPVC) linking the "
                  "catalog oil-absorption and skeletal-density families; all admissible OA/density pairs "
                  "yield geometrically valid CPVC, gross OA corruption fails closed.",
        "does_not_close": [
            "Does NOT promote OA constants to load-bearing; they remain single-source supplier ESTIMATEs.",
            "Does NOT establish a measured supplier-independent OA lock (needs a second D281 measurement).",
            "CPVC envelope is a plausibility bound, NOT a point predictor of a formulated coating's CPVC "
            "(dispersion state, particle packing, and binder wetting shift real CPVC).",
            "carbon_black OA is a DBP/OAN structure number, not D281 -> excluded from band check.",
            "iron_oxide_yellow catalog OA (14) is below the acicular-goethite class band -> flagged, not resolved.",
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
        "Daniel/Asbeck-Van Loo CPVC identity applied to %d catalog pigment OA+density pairs: "
        "%d/%d within the geometric bound (0,1) and %d/%d within the mineral-extender plausibility "
        "band [%.2f,%.2f]; %d/%d OA values inside coatings-literature D281 class bands "
        "(anomaly: %s; method-excluded: %s); CPVC monotone in both physical directions; "
        "gross OA corruption fails closed."
        % (n_total, n_hard, n_total, n_plaus, n_total, CPVC_PLAUS_LO, CPVC_PLAUS_HI,
           n_oa_in_band, len(checked),
           ",".join(oa_anomalies) or "none", ",".join(method_excluded) or "none")
    )
    return diag


def canon(obj):
    return json.dumps(obj, indent=2, sort_keys=True).encode()


if __name__ == "__main__":
    d1 = build(); b1 = canon(d1); h1 = hashlib.sha256(b1).hexdigest()
    d2 = build(); b2 = canon(d2); h2 = hashlib.sha256(b2).hexdigest()
    assert b1 == b2, "two-replay byte MISMATCH"
    if len(sys.argv) > 1 and sys.argv[1] == "--emit":
        open("diagnostic.canonical.json", "wb").write(b1)
        open("diagnostic.runB.json", "wb").write(b2)
    print("replay_sha256:", h1, "| byte_stable:", h1 == h2)
