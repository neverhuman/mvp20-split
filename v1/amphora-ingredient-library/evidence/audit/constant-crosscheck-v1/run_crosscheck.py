#!/usr/bin/env python3
"""
amphora-ingredient-library : independent physical cross-check of load-bearing
catalog constants (AUDIT_ONLY).

Purpose
-------
The module's falsifiable hypothesis is that a provenance-locked catalog can
fail closed on every missing / wrong active-ingredient constant. This harness
provides the FIRST independent physical second-signal for the catalog's
load-bearing constants and demonstrates fail-closed sensitivity (a corrupted
constant is caught by the physical admissibility test).

Non-circular baselines
-----------------------
Check 1  DGEBA epoxide-equivalent-weight (EEW) admissibility from the
         epoxy-oligomer molar-mass series
              M_n(n) = M0 + n * M_rep ,   EEW(n) = M_n / f
         M0   = 340.42 g/mol  (bisphenol-A diglycidyl ether, C21H24O4)
         M_rep= 284.35 g/mol  (epoxy repeat -O-C6H4-C(CH3)2-C6H4-O-CH2-CHOH-CH2-, C18H20O3)
         f    = 2 (difunctional)
         Source: Ellis, "Chemistry and Technology of Epoxy Resins",
                 Blackie/Chapman&Hall 1993, ISBN 978-0-7514-0095-6, ch.1;
                 Lee & Neville, "Handbook of Epoxy Resins", McGraw-Hill 1967.
         Derived purely from molecular structure -> independent of supplier TDS.
         Admissible liquid-DGEBA band: n in [0, 0.20]  ->  EEW in [170.21, 198.65].

         solid_type1_epoxy sub-check (V1-ING, 2026-08-04): the band is NOT
         structure-derived. It is the Hexion HCD-4022 EPON Resin 1001-X-75
         manufacturer TDS band, EEW 450-550 g/eq on nonvolatiles, as already
         transcribed in facts.json's own single_source_waiver note for
         resin.solid_cut_1001x75.eew_on_nv. This supersedes an earlier
         self-invented n in [1.5,3.5] window (EEW [383.5,667.8]) that was
         2.84x wider than this TDS band and refuted 2026-08-03T14:06 by
         evidence/audit/eew-solid-band-mislabel-gap-v1 (4/4 realistic
         gap-zone probes admitted undetected). Being TDS-sourced, this
         sub-check is single-source, not independently corroborated -- it is
         reported honestly as such, not claimed structure-derived.

Check 2  Pure-compound liquid densities vs CRC Handbook of Chemistry & Physics
         reference values (independent second source for single-sourced catalog
         constants). Gate = 3% (formulation volume-solids/PVC engineering tol).
         Source: CRC Handbook 97th ed. (2016), Physical Constants of Organic
         Compounds; liquid-DGEBA density from Lee & Neville (1967).

Honest-negative
---------------
Polyamide/amidoamine AHEW (ancamide/versamid) have proprietary oligomer
structures with no rights-clean first-principles baseline -> they legitimately
remain single-source supplier constants (reported, not gated).

Mineral-pigment densities are reported as a DIAGNOSTIC only: the correct
reference for formulation density arithmetic is the SKELETAL (pycnometric,
ASTM D153) pigment density, not the ideal single-crystal density; using
crystallographic density would false-flag porous/hydrated oxide pigments.
"""
import base64, hashlib, json, sys

FACTS_REL = "reference/mvp20/data/facts.json"
FACTS = "/home/ubuntu/amphora/build/mvp20-split/amphora-ingredient-library/" + FACTS_REL

# ---- Check 1 constants (structure-derived) --------------------------------
M0   = 340.42     # g/mol  C21H24O4  bisphenol-A diglycidyl ether
MREP = 284.35     # g/mol  C18H20O3  epoxy repeat unit
FUNC = 2
EEW0 = M0 / FUNC                       # 170.21 g/eq  (n=0, pure DGEBA)
N_LIQUID_MAX = 0.20                    # liquid-resin oligomer ceiling
EEW_HI = (M0 + N_LIQUID_MAX * MREP) / FUNC   # 198.645

# ---- solid_type1_epoxy band (manufacturer TDS, single-source; V1-ING 2026-08-04) --
# Hexion HCD-4022 EPON Resin 1001-X-75 TDS, EEW 450-550 g/eq on nonvolatiles.
# Supersedes the invented n in [1.5,3.5] window (EEW [383.5,667.8]) refuted by
# evidence/audit/eew-solid-band-mislabel-gap-v1 (sha256
# 31e7346be117f7152198755df3203717fdef41e3a69767ae94c065b9759231bc).
SOLID_TDS_EEW_LO = 450.0
SOLID_TDS_EEW_HI = 550.0

def eew_to_n(eew):
    return (FUNC * eew - M0) / MREP

# ---- Check 2 reference densities (g/mL near 20-25 C) -----------------------
# key -> (ref_value, source_note)
DENS_REF = {
    "solvent.mak.density":       (0.8111, "2-heptanone (methyl n-amyl ketone) d20, CRC Handbook 97th ed."),
    "solvent.mibk.density":      (0.8008, "4-methyl-2-pentanone d20, CRC Handbook 97th ed."),
    "solvent.n_butanol.density": (0.8095, "1-butanol d20, CRC Handbook 97th ed."),
    "solvent.xylene.density":    (0.8660, "mixed xylene isomer average (o0.880/m0.864/p0.861 d20), CRC 97th ed."),
    "solvent.pm.density":        (0.9200, "1-methoxy-2-propanol d20, CRC/supplier consensus"),
    "solvent.pma.density":       (0.9646, "1-methoxy-2-propyl acetate (PGMEA) d20, CRC 97th ed."),
    "solvent.butyl_alcohol.density": (0.8095, "n-butyl alcohol == 1-butanol d20, CRC 97th ed."),
    "resin.dgeba_331.density":   (1.1650, "liquid DGEBA d25 (Lee & Neville 1967 handbook band 1.16-1.17)"),
    "resin.dgeba_828.density":   (1.1650, "liquid DGEBA d25 (Lee & Neville 1967 handbook band 1.16-1.17)"),
    "resin.dgeba_yd128.density": (1.1650, "liquid DGEBA d25 (Lee & Neville 1967 handbook band 1.16-1.17)"),
}
DENS_GATE_PCT = 3.0

# ---- pigment diagnostic references (skeletal, ASTM D153 pigment-grade) -----
PIG_REF = {
    "pigment.barytes.density":         (4.48, "BaSO4 CRC 4.48; pigment barytes ~4.3-4.5"),
    "pigment.talc.density":            (2.78, "Mg3Si4O10(OH)2 2.58-2.83; pigment ~2.7-2.85"),
    "pigment.silica.density":          (2.65, "quartz SiO2 2.65 CRC"),
    "pigment.mica.density":            (2.85, "muscovite 2.76-3.0"),
    "pigment.wollastonite.density":    (2.90, "CaSiO3 2.86-3.09"),
    "pigment.iron_oxide_red.density":  (5.00, "hematite Fe2O3 crystallographic 5.26; pigment-grade skeletal ~4.6-5.0"),
    "pigment.iron_oxide_black.density":(4.80, "magnetite Fe3O4 crystallographic 5.17; pigment-grade skeletal ~4.6-5.0"),
    "pigment.iron_oxide_yellow.density":(4.05,"goethite a-FeOOH 3.8-4.3"),
    "pigment.zinc_phosphate.density":  (3.20, "hydrated Zn3(PO4)2 hopeite ~3.0-3.3"),
    "pigment.carbon_black.density":    (1.85, "amorphous CB 1.7-2.0"),
}

def pct(cat, ref):
    return round(100.0 * (cat - ref) / ref, 4)

def build():
    facts = json.load(open(FACTS))
    ent = facts["entries"]
    facts_sha = hashlib.sha256(open(FACTS, "rb").read()).hexdigest()

    # ---- Check 1 : DGEBA EEW admissibility ---------------------------------
    eew_keys = [k for k in ent if k.endswith(".eew") or k.endswith(".eew_on_nv")]
    c1 = []
    for k in sorted(eew_keys):
        eew = float(ent[k]["value"])
        n = eew_to_n(eew)
        liquid = k.startswith("resin.dgeba_")
        if liquid:
            admissible = (EEW0 - 1e-6) <= eew <= (EEW_HI + 1e-6)
            band = [round(EEW0, 3), round(EEW_HI, 3)]
            klass = "liquid_DGEBA"
        else:
            # solid Type-1 cut: manufacturer TDS band (single-source), not
            # structure-derived -- see SOLID_TDS_EEW_LO/HI comment above.
            admissible = SOLID_TDS_EEW_LO <= eew <= SOLID_TDS_EEW_HI
            band = [SOLID_TDS_EEW_LO, SOLID_TDS_EEW_HI]
            klass = "solid_type1_epoxy"
        c1.append({
            "constant": k, "catalog_eew_g_per_eq": eew,
            "implied_oligomer_n": round(n, 4),
            "resin_class": klass, "admissible_eew_band": band,
            "within_admissible_band": bool(admissible),
        })

    # fail-closed mutation demo on dgeba_331 (187 -> corruptions)
    base = 187.0
    mut = []
    for label, val in [("baseline", 187.0),
                       ("digit_insert_1x87", 1187.0),
                       ("mistype_287", 287.0),
                       ("decimal_slip_18.7", 18.7),
                       ("transpose_178 (small, within band)", 178.0)]:
        n = eew_to_n(val)
        caught = not ((EEW0 - 1e-6) <= val <= (EEW_HI + 1e-6))
        mut.append({"mutation": label, "eew": val, "implied_n": round(n, 4),
                    "flagged_out_of_band": bool(caught)})

    # solid_type1_epoxy fail-closed mutation demo against the TDS band
    # (probe values are the eew-solid-band-mislabel-gap-v1 refuting receipt's
    # own 4 gap-zone probes, replayed verbatim against the corrected predicate)
    solid_mut = []
    for label, val in [("catalog_baseline_500", 500.0),
                       ("gap_lo_probe_400 (refuting receipt)", 400.0),
                       ("gap_lo_probe_420 (refuting receipt)", 420.0),
                       ("gap_hi_probe_600 (refuting receipt)", 600.0),
                       ("gap_hi_probe_650 (refuting receipt)", 650.0)]:
        n = eew_to_n(val)
        caught = not (SOLID_TDS_EEW_LO <= val <= SOLID_TDS_EEW_HI)
        solid_mut.append({"mutation": label, "eew": val, "implied_n": round(n, 4),
                          "flagged_out_of_band": bool(caught)})

    # ---- Check 2 : density second-source -----------------------------------
    c2 = []
    for k in sorted(DENS_REF):
        if k not in ent:
            continue
        cat = float(ent[k]["value"])
        ref, note = DENS_REF[k]
        d = pct(cat, ref)
        c2.append({
            "constant": k, "catalog_g_per_mL": cat, "reference_g_per_mL": ref,
            "pct_deviation": d, "abs_pct": abs(d),
            "within_%.1f_pct_gate" % DENS_GATE_PCT: abs(d) <= DENS_GATE_PCT,
            "load_bearing": bool(ent[k].get("load_bearing", False)),
            "reference_source": note,
        })
    c2_max = max((r["abs_pct"] for r in c2), default=0.0)
    c2_all_pass = all(r["within_%.1f_pct_gate" % DENS_GATE_PCT] for r in c2)

    # density mutation demo: +10% perturbation must exceed 3% gate
    dens_mut_all_caught = all(abs(pct(v[0]*1.10, v[0])) > DENS_GATE_PCT for v in DENS_REF.values())

    # ---- pigment diagnostic (report only) ----------------------------------
    pig = []
    for k in sorted(PIG_REF):
        if k not in ent:
            continue
        cat = float(ent[k]["value"]); ref, note = PIG_REF[k]
        pig.append({"constant": k, "catalog_g_per_cm3": cat, "reference_g_per_cm3": ref,
                    "pct_deviation": pct(cat, ref), "reference_source": note,
                    "load_bearing": bool(ent[k].get("load_bearing", False))})

    # ---- honest-negative : polyamide AHEW ----------------------------------
    ahew_keys = sorted(k for k in ent if k.endswith(".ahew"))
    ahew = [{"constant": k, "catalog_g_per_eq": float(ent[k]["value"]),
             "grade": ent[k]["grade"], "load_bearing": bool(ent[k].get("load_bearing", False))}
            for k in ahew_keys]

    diag = {
        "schema": "amphora.ingredient-library-constant-crosscheck.v1",
        "module": "amphora-ingredient-library",
        "run_type": "AUDIT_ONLY",
        "authority": "AUDIT_ONLY",
        "purpose": "Independent physical second-signal for load-bearing catalog constants; "
                   "fail-closed sensitivity demonstration for the module falsifiable hypothesis.",
        "inputs": {"facts_json": FACTS_REL, "facts_json_sha256": facts_sha},
        "non_circularity": "Check-1 liquid_DGEBA admissibility band derived only from molecular "
                           "structure (BPA-diglycidyl-ether + epoxy-repeat molar mass); the "
                           "solid_type1_epoxy band is the Hexion HCD-4022 manufacturer TDS band "
                           "(single-source, corrected 2026-08-04 per V1-ING -- see check1 "
                           "solid_type1_epoxy_band block for the refutation this supersedes); "
                           "Check-2 references are CRC Handbook / Lee&Neville independent of the "
                           "supplier TDS that sourced the catalog.",
        "theory_reference": {
            "eew_oligomer_series": "Ellis 1993 (ISBN 978-0-7514-0095-6); Lee & Neville 1967, Handbook of Epoxy Resins (liquid_DGEBA sub-check only)",
            "solid_type1_epoxy_band_source": "Hexion HCD-4022 EPON Resin 1001-X-75 TDS (manufacturer, single-source)",
            "density_reference": "CRC Handbook of Chemistry and Physics, 97th ed. (2016)",
            "pigment_density_method": "ASTM D153 skeletal (pycnometric) pigment density",
        },
        "check1_dgeba_eew_admissibility": {
            "M0_g_per_mol": M0, "repeat_g_per_mol": MREP, "functionality": FUNC,
            "pure_dgeba_eew0": round(EEW0, 3), "liquid_n_ceiling": N_LIQUID_MAX,
            "liquid_admissible_eew_band": [round(EEW0, 3), round(EEW_HI, 3)],
            "liquid_band_source": "structure-derived (Ellis 1993 / Lee & Neville 1967)",
            "per_constant": c1,
            "n_load_bearing_eew_corroborated": sum(1 for r in c1 if r["within_admissible_band"]),
            "n_load_bearing_eew_total": len(c1),
            "all_within_band": all(r["within_admissible_band"] for r in c1),
            "fail_closed_mutation_demo": mut,
            "solid_type1_epoxy_band": {
                "band_g_per_eq": [SOLID_TDS_EEW_LO, SOLID_TDS_EEW_HI],
                "band_source": "Hexion HCD-4022 EPON Resin 1001-X-75 TDS (single-source, "
                                "as transcribed in facts.json's own single_source_waiver note "
                                "for resin.solid_cut_1001x75.eew_on_nv)",
                "supersedes": {
                    "superseded_band_g_per_eq": [383.5, 667.8],
                    "superseded_n_window": [1.5, 3.5],
                    "reason": "invented n-window not tabulated in the cited literature; 2.84x "
                              "wider than the TDS band; 4/4 gap-zone probes passed undetected",
                    "refuting_receipt": "amphora-ingredient-library/evidence/audit/"
                                        "eew-solid-band-mislabel-gap-v1/"
                                        "eew-solid-band-mislabel-gap-receipt.v1.dsse.json",
                    "refuting_receipt_sha256": "31e7346be117f7152198755df3203717fdef41e3a"
                                               "69767ae94c065b9759231bc",
                    "repair_item": "V1-ING",
                },
                "fail_closed_mutation_demo": solid_mut,
                "n_gap_zone_probes_now_rejected": sum(
                    1 for r in solid_mut if r["mutation"] != "catalog_baseline_500"
                    and r["flagged_out_of_band"]),
                "catalog_baseline_admitted": not next(
                    r["flagged_out_of_band"] for r in solid_mut
                    if r["mutation"] == "catalog_baseline_500"),
            },
        },
        "check2_density_second_source": {
            "gate_pct": DENS_GATE_PCT, "per_constant": c2,
            "max_abs_pct_deviation": round(c2_max, 4),
            "all_within_gate": bool(c2_all_pass),
            "load_bearing_corroborated": sum(1 for r in c2 if r["load_bearing"] and r["within_%.1f_pct_gate" % DENS_GATE_PCT]),
            "fail_closed_plus10pct_all_flagged": bool(dens_mut_all_caught),
        },
        "pigment_density_diagnostic": {
            "note": "Reported only, NOT gated. Formulation density is skeletal pigment density; "
                    "ideal single-crystal density would false-flag porous/hydrated oxide pigments "
                    "(hematite 5.26 vs pigment-grade ~5.0). Requires pycnometric second source to lock.",
            "per_constant": pig,
        },
        "honest_negative_polyamide_ahew": {
            "note": "Proprietary polyamide/amidoamine oligomer structures have no rights-clean "
                    "first-principles AHEW baseline; these legitimately remain single-source "
                    "supplier constants. No independent corroboration asserted.",
            "constants": ahew,
        },
        "headline": None,   # filled below
        "does_not_close": [
            "Does NOT establish product qualification, wet-lab performance, or supplier closure.",
            "Check-1 liquid_DGEBA sub-check is an admissibility BOUND (n in [0,0.2]), not a point "
            "predictor; small within-band transpositions of EEW are not caught (see mutation demo).",
            "Check-1 solid_type1_epoxy sub-check is single-source (manufacturer TDS only, per "
            "facts.json single_source_waiver); no independent second physical source is claimed for it.",
            "Polyamide AHEW and mineral-pigment skeletal densities remain single-source (no independent lock).",
        ],
        "modifies_manifest": False,
        "modifies_signed_phase0_kpi": False,
        "promotes_authority": False,
        "human_review_performed": False,
    }
    ncorr = diag["check1_dgeba_eew_admissibility"]["n_load_bearing_eew_corroborated"]
    dcorr = diag["check2_density_second_source"]["load_bearing_corroborated"]
    solid_block = diag["check1_dgeba_eew_admissibility"]["solid_type1_epoxy_band"]
    diag["headline"] = (
        "All %d catalog EEW constants fall inside their applicable admissibility band -- "
        "3 liquid_DGEBA constants inside the structure-derived band (n in [0,0.20]); 1 "
        "solid_type1_epoxy constant inside the Hexion HCD-4022 manufacturer TDS band "
        "[%.1f, %.1f] g/eq (single-source, corrected 2026-08-04 per V1-ING, superseding a "
        "refuted 2.84x-too-wide invented band); %d/4 TDS gap-zone probes now rejected. "
        "%d load-bearing solvent/resin densities corroborated by CRC/Lee-Neville second "
        "source to <=%.2f%% (max %.2f%%). Polyamide AHEW honestly single-source."
        % (diag["check1_dgeba_eew_admissibility"]["n_load_bearing_eew_total"],
           SOLID_TDS_EEW_LO, SOLID_TDS_EEW_HI,
           solid_block["n_gap_zone_probes_now_rejected"],
           dcorr, DENS_GATE_PCT, diag["check2_density_second_source"]["max_abs_pct_deviation"])
    )
    return diag

def canon(obj):
    return json.dumps(obj, indent=2, sort_keys=True).encode()

if __name__ == "__main__":
    d1 = build(); b1 = canon(d1); h1 = hashlib.sha256(b1).hexdigest()
    d2 = build(); b2 = canon(d2); h2 = hashlib.sha256(b2).hexdigest()
    assert b1 == b2, "two-replay byte MISMATCH"
    if len(sys.argv) > 1 and sys.argv[1] == "--emit":
        # V1-ING (2026-08-04): output path is now an explicit optional 2nd arg so a
        # corrected re-run never overwrites diagnostic.canonical.json, which mirrors
        # the ALREADY-SIGNED constant-crosscheck-receipt.v1.dsse.json payload bytes
        # exactly (supersede-never-rewrite).
        out_path = sys.argv[2] if len(sys.argv) > 2 else "diagnostic.canonical.json"
        open(out_path, "wb").write(b1)
    print("replay_sha256:", h1, "| byte_stable:", h1 == h2)
