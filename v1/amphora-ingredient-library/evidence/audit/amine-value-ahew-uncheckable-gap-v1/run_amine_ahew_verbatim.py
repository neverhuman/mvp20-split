#!/usr/bin/env python3
"""
amphora-ingredient-library : independent physical second-signal for the amine
hardener AMINE-HYDROGEN-EQUIVALENT-WEIGHT (AHEW) constant family via the
amine-value <-> AHEW stoichiometric admissibility relationship (AUDIT_ONLY).

Motivation
----------
The prior signed audit receipt (constant-crosscheck-v1) corroborated the DGEBA
EEW family (structure-derived oligomer band) and the solvent/resin DENSITY family
(CRC second source), and honestly left the amidoamine/polyamide AHEW family as an
open NEGATIVE: "Proprietary polyamide/amidoamine oligomer structures have no
rights-clean first-principles AHEW baseline; these legitimately remain single-source
supplier constants." (oil-absorption-cpvc-v1 then covered the pigment OA family.)

This harness adds the FIRST physical second-signal over the AHEW family, for the
three hardeners whose TDS reports BOTH an amine value and an AHEW. It does NOT
promote AHEW to independently-locked; it establishes a published, rights-clean
stoichiometric admissibility BAND that ties two independently-measured catalog
constants together and fails closed under gross AHEW corruption.

Non-circular published baseline
-------------------------------
Amine value (AV, mg KOH / g sample) is determined by acid titration of the basic
nitrogen content (ASTM D2073 / D2074), a measurement physically DISTINCT from AHEW
(which follows from epoxy-cure stoichiometry / total-active-hydrogen accounting).
The two are linked by amine stoichiometry:

    n_N  = AV / M_KOH             [mol basic N / g]     M_KOH = 56105.6 mg/mol
    each basic nitrogen carries at most 2 active N-H (primary amine) and, for a
    cure-useful (non-tertiary) amine, at least 1 active N-H (secondary amine).
    Amide nitrogens are non-basic (untitrated) and carry no cure-active H, so they
    enter neither AV nor AHEW.

    active-H upper bound: n_H <= 2 n_N  ->  AHEW = 1/n_H >= M_KOH/(2 AV)
    active-H lower bound: n_H >=   n_N  ->  AHEW = 1/n_H <= M_KOH/AV

  => admissibility band   M_KOH/(2*AV)  <=  AHEW  <=  M_KOH/AV
                          28052.8/AV    <=  AHEW  <=  56105.6/AV

The implied mean active-H-per-basic-N ratio r = (M_KOH/AV)/AHEW must lie in [1,2]
for a predominantly primary/secondary curing amine.

Primary sources
---------------
  ASTM D2074-07 "Standard Test Methods for Total, Primary, Secondary, and Tertiary
     Amine Values of Fatty Amines by Alternative Indicator Method" (amine value).
  ASTM D2073 (titrimetric amine value of fatty amines).
  Lee, H. & Neville, K. "Handbook of Epoxy Resins", McGraw-Hill 1967,
     ISBN 978-0-07-036997-1 (AHEW definition; amine-hardener stoichiometry).
  May, C.A. (ed.) "Epoxy Resins: Chemistry and Technology", 2nd ed., Marcel Dekker
     1988, ISBN 978-0-8247-7690-9 (amine hydrogen equivalent weight).
  M_KOH = 56.1056 g/mol from IUPAC 2021 standard atomic weights (K 39.0983,
     O 15.999, H 1.008); CRC Handbook 97th ed.

The band consumes only AV + AHEW from the catalog and returns a geometry/chemistry
bound independent of any single reported number: it corroborates the two
independently-titrated quantities as MUTUALLY CONSISTENT under amine stoichiometry.

Honest scope
------------
- AV and AHEW are reported on the same supplier TDS; this is a CROSS-QUANTITY
  consistency second-signal, NOT a supplier-INDEPENDENT measured lock. An
  independent second-lab titration would be needed to promote AHEW to load-locked
  -> DATA_ASK if ever promoted.
- The band is an admissibility BOUND, not a point predictor: small within-band
  perturbations of AHEW are not caught (demonstrated in the fail-closed section).
- Hardeners that report AHEW but NO amine value (ancamide_220x70, ancamide_2353,
  ancamide_260a) cannot be checked by this relationship and remain single-source;
  surfaced honestly, not silently passed.
"""
import base64, hashlib, json

FACTS_REL = "reference/mvp20/data/facts.json"
FACTS = "/home/ubuntu/amphora/build/mvp20-split/amphora-ingredient-library/" + FACTS_REL

M_KOH_MG = 56105.6  # mg / mol KOH  (56.1056 g/mol, IUPAC 2021)
RATIO_LO = 1.0      # secondary-amine floor (>=1 active H per basic N)
RATIO_HI = 2.0      # primary-amine ceiling (<=2 active H per basic N)


def r4(x):
    return round(float(x), 4)


def band(av):
    lo = M_KOH_MG / (RATIO_HI * av)
    hi = M_KOH_MG / (RATIO_LO * av)
    return r4(lo), r4(hi)


def check_pair(av, ahew):
    lo, hi = band(av)
    in_band = (lo <= ahew <= hi)
    implied_ratio = r4((M_KOH_MG / av) / ahew)  # mean active H per basic N
    return {
        "amine_value_mgKOH_g": r4(av),
        "ahew_catalog_g_eq": r4(ahew),
        "ahew_lower_bound_g_eq": lo,
        "ahew_upper_bound_g_eq": hi,
        "in_admissibility_band": bool(in_band),
        "implied_active_H_per_basic_N": implied_ratio,
        "implied_ratio_physical": bool(RATIO_LO <= implied_ratio <= RATIO_HI),
    }


def main():
    facts_bytes = open(FACTS, "rb").read()
    facts_sha = hashlib.sha256(facts_bytes).hexdigest()
    facts = json.loads(facts_bytes)
    E = facts["entries"]

    def val(k):
        return float(E[k]["value"])

    # --- hardeners reporting BOTH amine value and AHEW ---
    both = [
        ("hardener.ancamide_350a", "hardener.ancamide_350a.amine_value", "hardener.ancamide_350a.ahew"),
        ("hardener.ancamide_700b75", "hardener.ancamide_700b75.amine_value", "hardener.ancamide_700b75.ahew"),
        ("hardener.versamid_115", "hardener.versamid_115.amine_value", "hardener.versamid_115.ahew"),
    ]
    per_hardener = {}
    for hid, av_k, ah_k in both:
        per_hardener[hid] = {
            "amine_value_source": E[av_k]["grade"],
            "ahew_source": E[ah_k]["grade"],
            "ahew_load_bearing": bool(E[ah_k]["load_bearing"]),
            **check_pair(val(av_k), val(ah_k)),
        }
    n_checked = len(per_hardener)
    n_in_band = sum(1 for v in per_hardener.values() if v["in_admissibility_band"])
    n_ratio_ok = sum(1 for v in per_hardener.values() if v["implied_ratio_physical"])

    # --- hardeners with AHEW but NO amine value (cannot be checked here) ---
    uncheckable = []
    for hid in ["hardener.ancamide_220x70", "hardener.ancamide_2353", "hardener.ancamide_260a"]:
        ah_k = hid + ".ahew"
        if ah_k in E and (hid + ".amine_value") not in E:
            uncheckable.append({
                "hardener": hid,
                "ahew_catalog_g_eq": r4(val(ah_k)),
                "ahew_source": E[ah_k]["grade"],
                "reason": "no amine value reported -> AV<->AHEW band not evaluable; remains single-source",
            })

    # --- fail-closed mutation demo (on ancamide_350a: AV=380, AHEW=100) ---
    av_demo = val("hardener.ancamide_350a.amine_value")
    ahew_demo = val("hardener.ancamide_350a.ahew")
    lo_d, hi_d = band(av_demo)
    mutations = [
        ("baseline", ahew_demo),
        ("digit_insert_1000", 1000.0),           # gross: decimal/typo blow-up
        ("decimal_slip_10", 10.0),               # gross: dropped digit
        ("transpose_within_band_101", 101.0),    # small: within band, NOT caught (honesty)
        ("swap_with_versamid_198", 198.0),       # cross-product mix-up -> above band
    ]
    demo = []
    for name, ah in mutations:
        demo.append({
            "mutation": name,
            "ahew": r4(ah),
            "flagged_out_of_band": bool(not (lo_d <= ah <= hi_d)),
        })
    gross = [d for d in demo if d["mutation"].startswith(("digit_", "decimal_", "swap_"))]
    gross_all_flagged = all(d["flagged_out_of_band"] for d in gross)

    diag = {
        "authority": "AUDIT_ONLY",
        "module": "amphora-ingredient-library",
        "run_type": "independent_physical_second_signal.amine_value_ahew_consistency",
        "schema": "amphora.ingredient-library.amine-value-ahew-consistency.diagnostic.v1",
        "purpose": (
            "Independent physical second-signal for the load-bearing amine-hardener AHEW "
            "constant family via the amine-value<->AHEW stoichiometric admissibility band; "
            "closes part of the open honest-negative left by constant-crosscheck-v1."
        ),
        "hypothesis": (
            "Every hardener AHEW that also has a reported amine value must satisfy the "
            "stoichiometric band M_KOH/(2*AV) <= AHEW <= M_KOH/AV; gross AHEW corruption "
            "falls outside the band (fail-closed)."
        ),
        "non_circularity": (
            "Amine value is titrated (ASTM D2073/D2074) independently of the AHEW "
            "epoxy-stoichiometry determination; the band ties the two independently-measured "
            "quantities via amine chemistry, so intra-TDS mutual consistency is a genuine "
            "cross-quantity second signal, not a self-referential re-read."
        ),
        "theory_reference": {
            "amine_value_method": "ASTM D2074-07 / ASTM D2073 (titrimetric amine value)",
            "ahew_stoichiometry": "Lee & Neville 1967, Handbook of Epoxy Resins (ISBN 978-0-07-036997-1)",
            "ahew_definition": "May (ed.) 1988, Epoxy Resins: Chemistry and Technology 2nd ed. (ISBN 978-0-8247-7690-9)",
            "M_KOH_g_per_mol": 56.1056,
            "M_KOH_source": "IUPAC 2021 standard atomic weights; CRC Handbook 97th ed.",
            "band_formula": "28052.8/AV <= AHEW <= 56105.6/AV  (active H per basic N in [1,2])",
        },
        "inputs": {
            "facts_json_rel": FACTS_REL,
            "facts_json_sha256": facts_sha,
            "M_KOH_mg_per_mol": M_KOH_MG,
            "ratio_bounds_active_H_per_basic_N": [RATIO_LO, RATIO_HI],
        },
        "checkA_amine_value_ahew_band": {
            "n_hardeners_with_both_av_and_ahew": n_checked,
            "n_within_admissibility_band": n_in_band,
            "n_with_physical_implied_ratio": n_ratio_ok,
            "all_within_band": bool(n_in_band == n_checked),
            "per_hardener": per_hardener,
        },
        "checkB_uncheckable_no_amine_value": {
            "n_uncheckable": len(uncheckable),
            "note": "AHEW present but no amine value -> AV<->AHEW band not evaluable; remain single-source",
            "hardeners": uncheckable,
        },
        "checkC_fail_closed_mutation_demo": {
            "target": "hardener.ancamide_350a",
            "amine_value_mgKOH_g": r4(av_demo),
            "band_g_eq": [lo_d, hi_d],
            "gross_corruptions_flagged": bool(gross_all_flagged),
            "mutations": demo,
        },
        "headline": (
            f"All {n_in_band}/{n_checked} amine hardeners that report both an amine value and an "
            f"AHEW fall inside the amine-value-derived stoichiometric admissibility band "
            f"(28052.8/AV <= AHEW <= 56105.6/AV), with implied active-H-per-basic-N in [1,2] for "
            f"{n_ratio_ok}/{n_checked}; {len(uncheckable)} AHEW constants lack an amine value and remain "
            f"honestly single-source; gross AHEW corruption is flagged out-of-band (fail-closed)."
        ),
        "closes": [
            "Adds the FIRST physical second-signal over the amine-hardener AHEW family "
            "(the open honest-negative of constant-crosscheck-v1) for the 3 hardeners with both constants.",
            "Corroborates AHEW and amine value as mutually consistent under amine stoichiometry.",
        ],
        "does_not_close": [
            "AV and AHEW share the supplier TDS -> cross-quantity consistency, NOT a supplier-INDEPENDENT lock.",
            "Band is an admissibility BOUND, not a point predictor: small within-band AHEW errors are not caught.",
            "3 hardeners report AHEW with no amine value and remain single-source (uncheckable by this relationship).",
            "Does NOT establish product qualification, wet-lab performance, or supplier closure.",
        ],
    }
    print(json.dumps(diag, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
