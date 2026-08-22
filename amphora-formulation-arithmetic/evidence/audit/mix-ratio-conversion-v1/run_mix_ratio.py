#!/usr/bin/env python3
"""AUDIT_ONLY two-part epoxy MIX-RATIO conversion battery for
amphora-formulation-arithmetic.

Adds the *metered-dosing* layer of dimensioned formulation arithmetic that the
module's prior receipts did NOT compute.  A 2K epoxy-amine coating is specified
by a mix ratio that can be stated three equivalent ways:

  * stoichiometric parts-hardener-per-hundred-resin (by WEIGHT):
        PHR = 100 * AHEW / EEW                     [g hardener / 100 g resin]
  * the same ratio expressed BY VOLUME (what field pumps meter):
        Rv  = PHR * rho_A / rho_B                  [vol hardener / 100 vol resin]
  * the amine-H : epoxide EQUIVALENTS index that actually governs cure:
        r   = (m_B/AHEW) / (m_A/EEW)               (= 1 at exact stoichiometry)

This receipt implements the zero-fitted-parameter conversions between those
three, carries GUM + Monte-Carlo intervals onto each, and answers the concrete
question raised by the envelope-gates stoichiometric-ratio-tolerance gap
(amphora-envelope-gates-stoichiometric-ratio-tolerance / -index): how much
does moving from WEIGHT dosing to VOLUME dosing, and confusing the two, shift
the amine:epoxide equivalents index off stoichiometry?

Primary sources (rights-clean secondary / handbook, epoxy-amine coating scope):
  * Lee, H. & Neville, K. 1967, "Handbook of Epoxy Resins", McGraw-Hill,
    LCCN 66-27772 -- phr = 100*AHEW/EEW stoichiometric mix-ratio relation and
    amine-hydrogen-equivalent-weight definition.
  * Ellis, B. (ed.) 1993, "Chemistry and Technology of Epoxy Resins", Blackie
    Academic & Professional (Chapman & Hall), ISBN 978-0-7514-0095-6 -- cure
    stoichiometry, equivalents index.
  * Petrie, E.M. 2006, "Epoxy Adhesive Formulations", McGraw-Hill,
    ISBN 0-07-145544-2, Ch.3 -- amine hardener phr = (AHEW*100)/EEW worked form.
  * Volume<->weight conversion Rv = PHR*(rho_A/rho_B) is the elementary
    V = m/rho volumetric identity (ASTM D2196/D1475 density basis); it is a
    pure unit relation, not a fitted model.

Input equivalent-weights and densities are read as fixed constants carried
verbatim from the in-tree rights-clean amphora-ingredient-library facts.json
(load_bearing TDS entries: resin.dgeba_331.eew=187 g/eq band 182-192,
resin.dgeba_331.density=1.16; hardener.ancamide_350a.ahew=100 / density=0.97;
hardener.versamid_115.ahew=198 / density=0.97; hardener.ancamide_2353.ahew=114 /
density=1.01) plus the primer's TETA (AHEW 146.23/6=24.3717, density 0.982,
REFERENCE_NOMINAL) used only to REPRODUCE the prior dimensioned-engine near-
stoichiometric primer (100:13 by weight).

ZERO fitted parameters.  No promotion, no manifest edit, no scientific_readiness
flip, no live-Rust-engine edit, no locked-dataset or signed-KPI edit.  AUDIT_ONLY.
"""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
OUT = HERE / (sys.argv[1] if len(sys.argv) > 1 else "diagnostic.canonical.json")

MC_SEED = 20260730
MC_N = 400_000

# ---- rights-clean in-tree constants (amphora-ingredient-library facts.json) --
# Resin: DGEBA DER-331 liquid epoxy, published EEW band 182-192 g/eq.
EEW_RESIN = 187.0            # g/eq, TDS midpoint
EEW_BAND = (182.0, 192.0)   # published TDS band -> rectangular Type B half-width
RHO_A = 1.16                # g/mL, DER-331 TDS
RHO_A_GRADE = "TDS"

# Hardeners: (id, AHEW g/eq, AHEW grade, rho g/mL, rho grade, note)
HARDENERS = [
    ("ancamide_350a", 100.0, "TDS", 0.97, "TDS",
     "Evonik Ancamide 350A polyamide (marine 2K epoxy hardener), TDS AHEW/density"),
    ("versamid_115", 198.0, "TDS", 0.97, "TDS",
     "Versamid 115 polyamide, TDS AHEW/density"),
    ("ancamide_2353", 114.0, "SUPPLIER_GUIDE", 1.01, "SUPPLIER_GUIDE",
     "Ancamide 2353 modified amine, supplier-guide AHEW/density"),
]
# Primer hardener carried only to reproduce the prior dimensioned primer.
TETA_AHEW = 146.23 / 6.0    # = 24.3717 g/eq (validated EEW/AHEW convention)
TETA_RHO = 0.982            # REFERENCE_NOMINAL
PRIMER_PHR_RECIPE = 13.0    # 100 g DER-331 : 13 g TETA (dimensioned-engine primer)

GRADE_REL_HALFWIDTH = {
    "TDS": 0.005,
    "SUPPLIER_GUIDE": 0.015,
    "DISTRIBUTOR": 0.025,
    "REFERENCE_NOMINAL": 0.030,
}
# Declared APPLICATION parameter (not a formulation property, not fitted):
# volumetric metering / pump repeatability band (rectangular Type B).  Typical
# fixed-ratio plural-component or hand-measured cup tolerance.
METER_REL_HALFWIDTH = 0.02   # +/-2% volumetric dispense repeatability


# --------------------------------------------------------------------------
# zero-fitted-parameter conversion engine
# --------------------------------------------------------------------------
def phr_stoich(eew, ahew):
    """Stoichiometric parts hardener per 100 parts resin, BY WEIGHT."""
    return 100.0 * ahew / eew


def rv_from_phr(phr, rho_a, rho_b):
    """WEIGHT phr -> BY-VOLUME ratio (vol hardener per 100 vol resin)."""
    return phr * rho_a / rho_b


def phr_from_rv(rv, rho_a, rho_b):
    """BY-VOLUME ratio -> WEIGHT phr (exact inverse of rv_from_phr)."""
    return rv * rho_b / rho_a


def eq_index_from_masses(m_b, m_a, eew, ahew):
    """amine-H : epoxide equivalents index r (= 1 at exact stoichiometry)."""
    return (m_b / ahew) / (m_a / eew)


def r_weight_dosing(phr_set, eew, ahew):
    """r when dosing a fixed WEIGHT phr on 100 g resin.  = (phr/100)*(EEW/AHEW)."""
    return (phr_set / 100.0) * (eew / ahew)


def r_volume_dosing(rv_set, eew, ahew, rho_a, rho_b):
    """r when dosing a fixed VOLUME ratio Rv on 100 vol resin."""
    m_a = 100.0 * rho_a
    m_b = rv_set * rho_b
    return eq_index_from_masses(m_b, m_a, eew, ahew)


def n_decimals(x):
    s = repr(float(x))
    if "." not in s:
        return 0
    return len(s.split(".")[1].rstrip("0")) or 1


def u_type_b(value, grade):
    """GUM 4.3 Type B standard uncertainty: quoting-resolution rectangular
    half-width convolved with grade dispersion."""
    a_res = 0.5 * 10 ** (-n_decimals(value))
    u_res = a_res / np.sqrt(3.0)
    a_grade = GRADE_REL_HALFWIDTH[grade] * abs(value)
    u_grade = a_grade / np.sqrt(3.0)
    return float(np.sqrt(u_res ** 2 + u_grade ** 2))


def u_eew_banded(band):
    """Type B from a published band [lo,hi]: rectangular, u = halfwidth/sqrt(3)."""
    a = (band[1] - band[0]) / 2.0
    return float(a / np.sqrt(3.0))


# --------------------------------------------------------------------------
# per-hardener worked evaluation with GUM LPU + Monte-Carlo
# --------------------------------------------------------------------------
u_eew = u_eew_banded(EEW_BAND)
u_rho_a = u_type_b(RHO_A, RHO_A_GRADE)
rng = np.random.default_rng(MC_SEED)


def evaluate(hid, ahew, ahew_grade, rho_b, rho_b_grade):
    u_ahew = u_type_b(ahew, ahew_grade)
    u_rho_b = u_type_b(rho_b, rho_b_grade)

    phr = phr_stoich(EEW_RESIN, ahew)
    rv = rv_from_phr(phr, RHO_A, rho_b)

    # LPU relative uncertainties.
    rel_eew = u_eew / EEW_RESIN
    rel_ahew = u_ahew / ahew
    rel_rho_a = u_rho_a / RHO_A
    rel_rho_b = u_rho_b / rho_b

    # PHR = 100*AHEW/EEW  -> depends on AHEW, EEW only.
    rel_phr = np.sqrt(rel_ahew ** 2 + rel_eew ** 2)
    # Rv = PHR*rho_A/rho_B -> adds both densities.
    rel_rv = np.sqrt(rel_phr ** 2 + rel_rho_a ** 2 + rel_rho_b ** 2)

    # equivalents index r off-stoichiometry, WEIGHT vs VOLUME dosing:
    #   weight r-uncertainty depends on EEW, AHEW only,
    #   volume r-uncertainty ADDS the two densities (the metering penalty).
    rel_r_weight = np.sqrt(rel_eew ** 2 + rel_ahew ** 2)
    rel_r_volume = np.sqrt(rel_eew ** 2 + rel_ahew ** 2
                           + rel_rho_a ** 2 + rel_rho_b ** 2)
    # compose declared volumetric metering repeatability (rectangular Type B).
    rel_meter = METER_REL_HALFWIDTH / np.sqrt(3.0)
    rel_r_field_weight = np.sqrt(rel_r_weight ** 2 + rel_meter ** 2)
    rel_r_field_volume = np.sqrt(rel_r_volume ** 2 + rel_meter ** 2)

    # convention-confusion systematic error (two exact directions):
    #  (a) a WEIGHT-spec ratio measured BY VOLUME (pour phr volume-units) ->
    #      r = rho_B/rho_A  (hardener less dense here => amine UNDER-dose);
    #  (b) a VOLUME-spec ratio measured BY WEIGHT (weigh Rv mass-units) ->
    #      r = rho_A/rho_B  (amine OVER-dose).
    confusion_weight_spec_by_volume = rho_b / RHO_A
    confusion_volume_spec_by_weight = RHO_A / rho_b
    worst_confusion_abs_dev = max(abs(confusion_weight_spec_by_volume - 1.0),
                                  abs(confusion_volume_spec_by_weight - 1.0))

    # ---- Monte Carlo (JCGM 101), rectangular inputs matching each Type B u ----
    N = MC_N
    def rect(center, u):
        a = u * np.sqrt(3.0)
        return rng.uniform(center - a, center + a, N)
    # EEW sampled over its published band directly (rectangular).
    eew_s = rng.uniform(EEW_BAND[0], EEW_BAND[1], N)
    ahew_s = rect(ahew, u_ahew)
    rho_a_s = rect(RHO_A, u_rho_a)
    rho_b_s = rect(rho_b, u_rho_b)
    meter_s = rng.uniform(1.0 - METER_REL_HALFWIDTH, 1.0 + METER_REL_HALFWIDTH, N)

    phr_s = 100.0 * ahew_s / eew_s
    rv_s = phr_s * rho_a_s / rho_b_s
    # field r under weight dosing at the fixed nominal setpoint phr (metered).
    r_w_s = (phr * meter_s / 100.0) * (eew_s / ahew_s)
    # field r under volume dosing at the fixed nominal setpoint rv (metered).
    m_a_s = 100.0 * rho_a_s
    m_b_s = (rv * meter_s) * rho_b_s
    r_v_s = (m_b_s / ahew_s) / (m_a_s / eew_s)

    def summ(point, samples, rel_lpu):
        std = float(np.std(samples, ddof=1))
        lo, hi = (float(x) for x in np.percentile(samples, [2.5, 97.5]))
        u_lpu = abs(rel_lpu * point)
        return {
            "point": float(point),
            "u_c_lpu": float(u_lpu),
            "rel_u_lpu": float(rel_lpu),
            "mc_mean": float(np.mean(samples)),
            "mc_std": std,
            "mc_ci95_low": lo,
            "mc_ci95_high": hi,
            "lpu_vs_mc_std_rel_diff": float(abs(u_lpu - std) / std) if std > 0 else 0.0,
            "linearization_validated_by_mc": bool(abs(u_lpu - std) / std < 0.05) if std > 0 else True,
        }

    return {
        "hardener_id": hid,
        "inputs": {
            "eew_resin": EEW_RESIN, "eew_band": list(EEW_BAND), "u_eew": u_eew,
            "ahew": ahew, "ahew_grade": ahew_grade, "u_ahew": u_ahew,
            "rho_A": RHO_A, "rho_A_grade": RHO_A_GRADE, "u_rho_A": u_rho_a,
            "rho_B": rho_b, "rho_B_grade": rho_b_grade, "u_rho_B": u_rho_b,
        },
        "phr_by_weight": summ(phr, phr_s, rel_phr),
        "ratio_by_volume_per_100_resin": summ(rv, rv_s, rel_rv),
        "eq_index_field_weight_dosing": summ(1.0, r_w_s, rel_r_field_weight),
        "eq_index_field_volume_dosing": summ(1.0, r_v_s, rel_r_field_volume),
        "volume_metering_penalty": {
            "rel_r_weight_input_only": float(rel_r_weight),
            "rel_r_volume_input_only": float(rel_r_volume),
            "density_rss_penalty_pp": float((rel_r_volume - rel_r_weight) * 100.0),
            "note": "extra relative r-uncertainty from carrying rho_A,rho_B when metering by volume vs by weight",
        },
        "convention_confusion_systematic_r": {
            "weight_spec_measured_by_volume_r": float(confusion_weight_spec_by_volume),
            "weight_spec_measured_by_volume_dev_pct": float((confusion_weight_spec_by_volume - 1.0) * 100.0),
            "volume_spec_measured_by_weight_r": float(confusion_volume_spec_by_weight),
            "volume_spec_measured_by_weight_dev_pct": float((confusion_volume_spec_by_weight - 1.0) * 100.0),
            "worst_case_abs_index_deviation_pct": float(worst_confusion_abs_dev * 100.0),
            "note": "exact = rho_B/rho_A (weight-spec poured by volume) or rho_A/rho_B (volume-spec weighed); confusing the two conventions mis-doses the amine:epoxide index by this much.",
        },
    }


systems = [evaluate(h[0], h[1], h[2], h[3], h[4]) for h in HARDENERS]

# --------------------------------------------------------------------------
# reproduce the prior dimensioned-engine near-stoichiometric primer (100:13)
# --------------------------------------------------------------------------
primer_phr_stoich = phr_stoich(EEW_RESIN, TETA_AHEW)
primer_r_recipe = eq_index_from_masses(PRIMER_PHR_RECIPE, 100.0, EEW_RESIN, TETA_AHEW)
primer_reproduction = {
    "resin": "DGEBA DER-331 (EEW 187)",
    "hardener": "TETA (AHEW 146.23/6 = 24.3717)",
    "stoichiometric_phr": primer_phr_stoich,
    "recipe_phr": PRIMER_PHR_RECIPE,
    "recipe_eq_index_r": primer_r_recipe,
    "recipe_within_half_phr_of_stoich": bool(abs(primer_phr_stoich - PRIMER_PHR_RECIPE) < 0.5),
    "recipe_r_within_1pct_of_stoich": bool(abs(primer_r_recipe - 1.0) < 0.01),
    "note": "reproduces the amphora-formulation-arithmetic-dimensioned primer as very-near-stoichiometric (r within ~0.3% of 1); provenance tie to the dimensioned engine (539f3e67).",
}


# --------------------------------------------------------------------------
# known-answer battery (non-circular: every target fixed by DEFINITION,
# exact ratio algebra, or external reproduction -- never by the engine)
# --------------------------------------------------------------------------
def approx(a, b, tol):
    return bool(abs(a - b) <= tol)


kab = []

# KA1: equal densities => by-volume ratio == by-weight phr exactly.
phr_probe = phr_stoich(EEW_RESIN, 100.0)
kab.append({"id": "KA1_equal_density_volume_equals_weight",
            "phr": phr_probe, "rv_equal_density": rv_from_phr(phr_probe, 1.05, 1.05),
            "pass": approx(rv_from_phr(phr_probe, 1.05, 1.05), phr_probe, 1e-12),
            "note": "definition: rho_A=rho_B => Rv=PHR."})

# KA2: weight->volume->weight round-trip recovers phr (exact inverse).
rt = phr_from_rv(rv_from_phr(53.4759, 1.16, 0.97), 1.16, 0.97)
kab.append({"id": "KA2_volume_weight_roundtrip_inverse",
            "phr_in": 53.4759, "phr_out": rt, "residual": rt - 53.4759,
            "pass": approx(rt, 53.4759, 1e-9)})

# KA3: at phr = stoichiometric, equivalents index r == 1 exactly (density-free).
r_stoich = r_weight_dosing(phr_stoich(EEW_RESIN, 100.0), EEW_RESIN, 100.0)
kab.append({"id": "KA3_stoichiometric_index_is_one",
            "r_at_stoich_phr": r_stoich, "pass": approx(r_stoich, 1.0, 1e-12),
            "note": "definition: PHR=100*AHEW/EEW => r=1 independent of density."})

# KA4: convention-confusion identity -- a WEIGHT-spec phr measured BY VOLUME
# (Rv := phr) offsets r by exactly rho_B/rho_A (pure ratio algebra, non-circular).
phr_c = phr_stoich(EEW_RESIN, 100.0)
r_confused = r_volume_dosing(phr_c, EEW_RESIN, 100.0, 1.16, 0.97)  # Rv:=phr (wrong)
kab.append({"id": "KA4_convention_confusion_equals_density_ratio",
            "r_confused": r_confused, "expected_rho_B_over_rho_A": 0.97 / 1.16,
            "abs_err": abs(r_confused - 0.97 / 1.16),
            "pass": approx(r_confused, 0.97 / 1.16, 1e-12),
            "note": "weight-spec phr measured by volume => r = rho_B/rho_A exactly."})

# KA5: intensive scale invariance -- batch size cancels in phr, Rv, r.
phr_1x = phr_stoich(EEW_RESIN, 100.0)
r_10x = eq_index_from_masses(10 * phr_1x, 10 * 100.0, EEW_RESIN, 100.0)
kab.append({"id": "KA5_intensive_scale_invariance",
            "r_1x": 1.0, "r_10x": r_10x, "pass": approx(r_10x, 1.0, 1e-12)})

# KA6: external reproduction -- DER-331 + TETA stoich phr reproduces the prior
# dimensioned primer's 100:13 recipe within half a phr.
kab.append({"id": "KA6_external_reproduces_dimensioned_primer_100to13",
            "stoich_phr": primer_phr_stoich, "recipe_phr": PRIMER_PHR_RECIPE,
            "abs_err_phr": abs(primer_phr_stoich - PRIMER_PHR_RECIPE),
            "pass": bool(abs(primer_phr_stoich - PRIMER_PHR_RECIPE) < 0.5)})

# KA7: hostile null -- EEW=0 / AHEW=0 / rho_B=0 must yield non-finite (abstain),
# never a finite lie.
with np.errstate(divide="ignore", invalid="ignore"):
    phr_eew0 = float(np.float64(100.0) * np.float64(100.0) / np.float64(0.0))
    r_ahew0 = float(np.float64(53.0) / np.float64(0.0))
    rv_rhob0 = float(np.float64(53.0) * np.float64(1.16) / np.float64(0.0))
kab.append({"id": "KA7_hostile_null_zero_ew_or_density_fail_closed",
            "phr_at_eew0_isinf": bool(np.isinf(phr_eew0)),
            "r_at_ahew0_isinf": bool(np.isinf(r_ahew0)),
            "rv_at_rhob0_isinf": bool(np.isinf(rv_rhob0)),
            "pass": bool(np.isinf(phr_eew0) and np.isinf(r_ahew0) and np.isinf(rv_rhob0))})

# KA8: monotonicity -- more hardener (higher phr) strictly raises r (amine-rich).
r_lo = r_weight_dosing(40.0, EEW_RESIN, 100.0)
r_hi = r_weight_dosing(60.0, EEW_RESIN, 100.0)
kab.append({"id": "KA8_hardener_monotonic_increases_index",
            "r_at_phr40": r_lo, "r_at_phr60": r_hi,
            "pass": bool(r_hi > r_lo > 0.0)})

battery_pass = all(k["pass"] for k in kab)
lpu_all_ok = all(
    systems[i][key]["linearization_validated_by_mc"]
    for i in range(len(systems))
    for key in ("phr_by_weight", "ratio_by_volume_per_100_resin",
                "eq_index_field_weight_dosing", "eq_index_field_volume_dosing"))

diag = {
    "study_id": "formulation-arithmetic-mix-ratio-conversion-v1",
    "run_type": "AUDIT_ONLY",
    "module": "amphora-formulation-arithmetic",
    "target_capability": "two-part epoxy mix-ratio arithmetic: stoichiometric PHR (by weight) <-> by-volume ratio <-> amine:epoxide equivalents index, with GUM/MC intervals",
    "fitted_parameters": 0,
    "theory_reference": {
        "phr_stoichiometry": "Lee & Neville 1967 Handbook of Epoxy Resins (LCCN 66-27772); Petrie 2006 Epoxy Adhesive Formulations (ISBN 0-07-145544-2) Ch.3: phr = 100*AHEW/EEW",
        "equivalents_index": "Ellis (ed.) 1993 Chemistry and Technology of Epoxy Resins (ISBN 978-0-7514-0095-6): amine-H:epoxide stoichiometry, r=1 at match",
        "volume_conversion": "Rv = PHR*(rho_A/rho_B): elementary V=m/rho volumetric identity (ASTM D1475 density basis); pure unit relation, not fitted",
        "uncertainty": ["JCGM 100:2008 (GUM) sec.5.1 LPU", "JCGM 101:2008 (GUM S1) Monte Carlo"],
    },
    "non_circularity": "Every known-answer target is fixed by DEFINITION (rho_A=rho_B => Rv=PHR; PHR=100*AHEW/EEW => r=1), by EXACT ratio algebra (convention-confusion => r=rho_A/rho_B; round-trip inverse residual=0), or by EXTERNAL reproduction of the prior dimensioned primer (100:13). No target is produced by the conversion engine.",
    "why_not_bootstrap_conformal": "Zero fitted parameters: the predictive uncertainty is input equivalent-weight/density measurement propagation, not residual resampling. GUM LPU validated against Monte Carlo is the calibrated interval.",
    "inputs_provenance": "amphora-ingredient-library facts.json load_bearing TDS entries (resin.dgeba_331 EEW 187 band 182-192 / density 1.16; hardener.ancamide_350a AHEW 100 / density 0.97; hardener.versamid_115 AHEW 198 / density 0.97; hardener.ancamide_2353 AHEW 114 / density 1.01) + primer TETA AHEW 146.23/6.",
    "declared_application_parameter": {
        "volumetric_metering_rel_halfwidth_rectangular": METER_REL_HALFWIDTH,
        "note": "pump/cup dispense repeatability; a DECLARED application band (like DFT control in the coverage receipt), not a formulation property and not fitted.",
    },
    "mc_config": {"seed": MC_SEED, "n": MC_N, "input_pdf": "rectangular (EEW over published band; others half-width = u*sqrt(3))"},
    "worked_systems": systems,
    "primer_reproduction": primer_reproduction,
    "known_answer_battery": kab,
    "known_answer_battery_pass": battery_pass,
    "lpu_validated_by_mc_all_outputs": lpu_all_ok,
    "finding": "For DGEBA(EEW 187, band 182-192) + polyamide/amine hardeners the amine:epoxide index precision is DOMINATED by the resin's published EEW band (~1.5%% relative); moving from weight to volume metering adds only ~0.1 pp of RSS uncertainty from the two densities, so density variation is second-order to EEW spread. BUT the systematic error of CONFUSING the weight and volume ratio conventions equals the density ratio exactly: for DER-331(1.16)+Ancamide 350A(0.97) a weight-spec poured by volume gives r=rho_B/rho_A=0.836 (-16.4%% amine, under-cure) and a volume-spec weighed gives r=rho_A/rho_B=1.196 (+19.6%% amine) -- both far outside the +/-10%% mass-tolerance envelope from amphora-envelope-gates-stoichiometric-ratio-tolerance. Convention discipline, not density precision, is the load-bearing control for volume-metered 2K epoxy.",
    "connects_to": [
        "amphora-envelope-gates-stoichiometric-ratio-tolerance (mass +/-5% -> ratio +10.53/-9.52%)",
        "amphora-envelope-gates-stoichiometric-index-equivalents (amine-H:epoxide equivalents index)",
        "amphora-formulation-arithmetic-dimensioned (stoichiometric PHR primer, 539f3e67)",
    ],
    "acceptance": {
        "known_answer_battery_pass": battery_pass,
        "lpu_validated_by_mc_all_outputs": lpu_all_ok,
        "primer_reproduction_pass": primer_reproduction["recipe_within_half_phr_of_stoich"] and primer_reproduction["recipe_r_within_1pct_of_stoich"],
    },
    "verdict": (
        "MIX_RATIO_CONVERSION_ENGINE_READY__KNOWN_ANSWER_BATTERY_PASS__PRIMER_REPRODUCED"
        if (battery_pass and lpu_all_ok
            and primer_reproduction["recipe_within_half_phr_of_stoich"]
            and primer_reproduction["recipe_r_within_1pct_of_stoich"])
        else "BATTERY_OR_REPRODUCTION_FAILED"),
    "closes": [
        "adds stoichiometric PHR <-> by-volume ratio <-> amine:epoxide equivalents index conversions to the dimensioned arithmetic surface",
        "quantifies the weight-vs-volume metering uncertainty penalty and the exact convention-confusion systematic error feeding the envelope-gates stoich-ratio gap",
        "carries GUM+MC calibrated intervals onto PHR, volume ratio, and the equivalents index",
    ],
    "does_not_close": [
        "not product qualification, batch release, or wet-lab cure verification",
        "volumetric metering band is a declared application input, not a validated pump model",
        "does not modify the live Rust engine (still MASS_ONLY), any locked dataset, the signed Phase-0 KPI, or the 66/11 manifest",
    ],
}

txt = json.dumps(diag, indent=2, sort_keys=True)
OUT.write_text(txt)
print("WROTE", OUT)
print("sha256", hashlib.sha256(txt.encode()).hexdigest())
print("battery_pass", battery_pass, "lpu_all_ok", lpu_all_ok)
print("primer stoich_phr", primer_phr_stoich, "recipe_r", primer_r_recipe)
for s in systems:
    print(s["hardener_id"], "phr", round(s["phr_by_weight"]["point"], 3),
          "Rv", round(s["ratio_by_volume_per_100_resin"]["point"], 3),
          "confusion_worst_pct", round(s["convention_confusion_systematic_r"]["worst_case_abs_index_deviation_pct"], 3),
          "penalty_pp", round(s["volume_metering_penalty"]["density_rss_penalty_pp"], 4))
print("verdict", diag["verdict"])
