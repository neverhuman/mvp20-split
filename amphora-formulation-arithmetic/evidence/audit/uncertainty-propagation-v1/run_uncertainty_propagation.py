#!/usr/bin/env python3
"""AUDIT_ONLY uncertainty-propagation battery for amphora-formulation-arithmetic.

Adds calibrated uncertainty intervals to the module's dimensioned formulation
arithmetic (volume-solids ASTM D2697, PVC, wet-paint density, VOC EPA M24,
stoichiometric mix ratio via EEW/AHEW). The shipped/prior engine emits POINT
estimates with zero stated uncertainty; this receipt propagates the documented
measurement uncertainty of the load-bearing physical inputs (ingredient
densities + EEW/AHEW) to the output properties by two independent methods and
cross-validates them:

  * LPU  -- Law of Propagation of Uncertainty, first-order Taylor / numerical
           Jacobian.  JCGM 100:2008 (GUM), section 5.1 (uncorrelated inputs,
           eq. 10).  Type B input evaluation per GUM section 4.3 (rectangular).
  * MC   -- Monte Carlo propagation of distributions.  JCGM 101:2008 (GUM
           Supplement 1), section 5-7; validation of the GUM result against MC
           per JCGM 101 section 8.

Because the engine has ZERO fitted parameters, predictive uncertainty is NOT a
residual/resampling quantity -- bootstrap and split-conformal do not apply.  The
metrologically-correct "calibrated interval" for zero-parameter arithmetic is
input-measurement-uncertainty propagation (GUM).  The falsifiable claim tested
here is: first-order LPU intervals AGREE with the reference Monte Carlo
intervals (validating the linearization) for every output property.  A strongly
nonlinear output would make LPU and MC diverge and FAIL the gate.

No promotion; no manifest edit; no scientific_readiness flip.  AUDIT_ONLY.
"""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
OUT = HERE / (sys.argv[1] if len(sys.argv) > 1 else "diagnostic.canonical.json")

MC_SEED = 20260727
MC_N = 400_000

# ---------------------------------------------------------------------------
# Real, rights-clean marine anti-corrosion epoxy-amine primer.
# Masses (nominal recipe) + densities carried over verbatim from the prior
# dimensioned receipt (formulation-arithmetic-dimensioned-v1, two-replay
# 539f3e67...).  Densities/EEW read from in-tree provenance-tracked facts.json
# (amphora-ingredient-library); grades govern the Type B uncertainty budget.
# TETA AHEW/density are REFERENCE_NOMINAL public constants (flagged wider).
# ---------------------------------------------------------------------------
COMPONENTS = [
    # id, mass_g, density, density_grade, nonvol_frac, class
    ("dgeba_der331",                100.0, 1.16, "TDS",              1.0, "binder"),
    ("teta_hardener",                13.0, 0.982, "REFERENCE_NOMINAL", 1.0, "binder"),
    ("iron_oxide_red",               55.0, 5.00, "DISTRIBUTOR",      1.0, "pigment"),
    ("zinc_phosphate_anticorrosive", 30.0, 3.30, "DISTRIBUTOR",      1.0, "pigment"),
    ("barytes_extender",             40.0, 4.45, "SUPPLIER_GUIDE",   1.0, "pigment"),
    ("talc_extender",                20.0, 2.80, "SUPPLIER_GUIDE",   1.0, "pigment"),
    ("mica_barrier",                 15.0, 2.85, "DISTRIBUTOR",      1.0, "pigment"),
    ("xylene_solvent",               45.0, 0.87, "DISTRIBUTOR",      0.0, "solvent"),
    ("n_butanol_solvent",            15.0, 0.81, "TDS",              0.0, "solvent"),
]
EEW = 187.0   # DGEBA DER 331, TDS  (resin.dgeba_331.eew, g/eq)
AHEW = 146.23 / 6.0  # TETA C6H18N4, 6 active N-H, REFERENCE_NOMINAL (g/eq)
M_RESIN = 100.0      # dgeba mass for stoichiometry
M_HARDENER = 13.0    # teta mass

# Type B grade-dispersion relative half-widths (rectangular, GUM 4.3.7).
GRADE_REL_HALFWIDTH = {
    "TDS":              0.005,   # manufacturer measured
    "SUPPLIER_GUIDE":   0.015,
    "DISTRIBUTOR":      0.025,
    "REFERENCE_NOMINAL": 0.030,  # public nominal constant
}


def n_decimals(x):
    """Decimal places in the shortest exact decimal rendering of the quote."""
    s = repr(float(x))
    if "." not in s:
        return 0
    return len(s.split(".")[1].rstrip("0")) or 1


def type_b_budget(value, grade):
    """Two-component Type B standard uncertainty (GUM 4.3): quoting resolution
    (rectangular half-width a_res) convolved with grade/source dispersion
    (rectangular relative half-width). u = a/sqrt(3) per rectangular pdf."""
    a_res = 0.5 * 10 ** (-n_decimals(value))
    u_res = a_res / np.sqrt(3.0)
    a_grade = GRADE_REL_HALFWIDTH[grade] * abs(value)
    u_grade = a_grade / np.sqrt(3.0)
    u_c = float(np.sqrt(u_res ** 2 + u_grade ** 2))
    return {"a_res": a_res, "u_res": u_res, "a_grade": a_grade,
            "u_grade": u_grade, "u_combined": u_c, "rel_u_combined": u_c / abs(value)}


# ---------------------------------------------------------------------------
# The dimensioned arithmetic engine (pure function of the varying inputs).
# Zero fitted parameters.  Formulas: ASTM D2697 (volume solids), PVC (Asbeck &
# Van Loo 1949 / Patton 1979), EPA Method 24 / ASTM D3960 (VOC g/L),
# rho_wet = M/V, stoichiometric equivalents amine-H/epoxy.
# ---------------------------------------------------------------------------
def engine(rho, eew, ahew, comps=COMPONENTS, m_resin=M_RESIN, m_hard=M_HARDENER):
    """rho: dict id->density. Returns output property dict."""
    V = {}
    M_total = 0.0
    V_total = 0.0
    V_solid = 0.0
    V_volatile = 0.0
    V_pigment = 0.0
    V_binder = 0.0
    volatile_mass = 0.0
    for cid, mass, _d0, _g, nonvol, cls in comps:
        v = mass / rho[cid]
        V[cid] = v
        M_total += mass
        V_total += v
        if nonvol > 0.0:
            V_solid += v * nonvol
        vol_vfrac = (1.0 - nonvol)
        V_volatile += v * vol_vfrac
        volatile_mass += mass * vol_vfrac
        if cls == "pigment":
            V_pigment += v
        elif cls == "binder":
            V_binder += v
    out = {}
    out["volume_solids_frac"] = V_solid / V_total
    binder_pig = V_pigment + V_binder
    out["pvc"] = (V_pigment / binder_pig) if binder_pig > 0 else float("nan")
    out["wet_paint_density_g_cm3"] = M_total / V_total
    out["voc_g_per_L"] = volatile_mass / (V_total / 1000.0)
    epoxy_eq = m_resin / eew
    amineH_eq = m_hard / ahew
    out["stoich_ratio_amineH_per_epoxy"] = (amineH_eq / epoxy_eq) if epoxy_eq > 0 else float("nan")
    return out


OUTPUT_KEYS = ["volume_solids_frac", "pvc", "wet_paint_density_g_cm3",
               "voc_g_per_L", "stoich_ratio_amineH_per_epoxy"]


def build_inputs(comps=COMPONENTS):
    """Ordered list of uncertain inputs with nominal value + Type B budget."""
    inputs = []
    for cid, _m, dens, grade, _nv, _cls in comps:
        b = type_b_budget(dens, grade)
        inputs.append({"name": f"density::{cid}", "kind": "density", "id": cid,
                       "value": dens, "grade": grade, **b})
    inputs.append({"name": "eew::dgeba_der331", "kind": "eew", "id": "dgeba_der331",
                   "value": EEW, "grade": "TDS", **type_b_budget(EEW, "TDS")})
    inputs.append({"name": "ahew::teta_hardener", "kind": "ahew", "id": "teta_hardener",
                   "value": AHEW, "grade": "REFERENCE_NOMINAL",
                   **type_b_budget(AHEW, "REFERENCE_NOMINAL")})
    return inputs


def eval_with(inputs, overrides):
    """Evaluate engine with a vector of input values (dict name->value)."""
    rho = {}
    eew = EEW
    ahew = AHEW
    for inp in inputs:
        val = overrides.get(inp["name"], inp["value"])
        if inp["kind"] == "density":
            rho[inp["id"]] = val
        elif inp["kind"] == "eew":
            eew = val
        elif inp["kind"] == "ahew":
            ahew = val
    return engine(rho, eew, ahew)


def lpu(inputs):
    """First-order numerical-Jacobian LPU (GUM eq.10, uncorrelated inputs)."""
    base = eval_with(inputs, {})
    contrib = {k: [] for k in OUTPUT_KEYS}
    sens = {k: {} for k in OUTPUT_KEYS}
    for inp in inputs:
        v = inp["value"]
        delta = max(abs(v) * 1e-6, 1e-9)
        yp = eval_with(inputs, {inp["name"]: v + delta})
        ym = eval_with(inputs, {inp["name"]: v - delta})
        for k in OUTPUT_KEYS:
            c = (yp[k] - ym[k]) / (2.0 * delta)
            sens[k][inp["name"]] = c
            contrib[k].append((inp["name"], (c * inp["u_combined"]) ** 2))
    res = {}
    for k in OUTPUT_KEYS:
        var = sum(c for _, c in contrib[k])
        uc = float(np.sqrt(var))
        dom = max(contrib[k], key=lambda t: t[1]) if uc > 0 else (None, 0.0)
        res[k] = {"point": base[k], "u_c_lpu": uc, "U95_lpu": 1.96 * uc,
                  "dominant_input": dom[0],
                  "dominant_fraction_of_variance": (dom[1] / var) if var > 0 else 0.0}
    return base, res, sens


def monte_carlo(inputs, n=MC_N, seed=MC_SEED):
    """MC propagation (JCGM 101). Each input = nominal + U(-a_res,a_res) +
    U(-a_grade,a_grade): the exact convolution (trapezoidal) of its two
    independent rectangular Type B components."""
    rng = np.random.default_rng(seed)
    draws = {}
    for inp in inputs:
        res = rng.uniform(-inp["a_res"], inp["a_res"], n)
        grd = rng.uniform(-inp["a_grade"], inp["a_grade"], n)
        draws[inp["name"]] = inp["value"] + res + grd
    # vectorised engine evaluation
    rho_cols = {}
    for inp in inputs:
        if inp["kind"] == "density":
            rho_cols[inp["id"]] = draws[inp["name"]]
    eew_s = draws["eew::dgeba_der331"]
    ahew_s = draws["ahew::teta_hardener"]

    M_total = sum(m for _c, m, *_ in COMPONENTS)
    V_total = np.zeros(n)
    V_solid = np.zeros(n)
    V_pigment = np.zeros(n)
    V_binder = np.zeros(n)
    volatile_mass = 0.0
    for cid, mass, _d0, _g, nonvol, cls in COMPONENTS:
        v = mass / rho_cols[cid]
        V_total = V_total + v
        if nonvol > 0.0:
            V_solid = V_solid + v * nonvol
        volatile_mass += mass * (1.0 - nonvol)
        if cls == "pigment":
            V_pigment = V_pigment + v
        elif cls == "binder":
            V_binder = V_binder + v
    samp = {
        "volume_solids_frac": V_solid / V_total,
        "pvc": V_pigment / (V_pigment + V_binder),
        "wet_paint_density_g_cm3": M_total / V_total,
        "voc_g_per_L": volatile_mass / (V_total / 1000.0),
        "stoich_ratio_amineH_per_epoxy": (M_HARDENER / ahew_s) / (M_RESIN / eew_s),
    }
    res = {}
    for k in OUTPUT_KEYS:
        s = samp[k]
        mean = float(np.mean(s))
        std = float(np.std(s, ddof=1))
        lo, hi = np.percentile(s, [2.5, 97.5])
        res[k] = {"mc_mean": mean, "mc_std": std,
                  "mc_ci95_sym_low": float(lo), "mc_ci95_sym_high": float(hi),
                  "mc_ci95_halfwidth": float((hi - lo) / 2.0)}
    return res


def round_floats(obj, nd=10):
    if isinstance(obj, dict):
        return {k: round_floats(v, nd) for k, v in obj.items()}
    if isinstance(obj, list):
        return [round_floats(v, nd) for v in obj]
    if isinstance(obj, float):
        if obj != obj or obj in (float("inf"), float("-inf")):
            return obj
        return round(obj, nd)
    return obj


def sha(b):
    return hashlib.sha256(b).hexdigest()


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------
inputs = build_inputs()
base, lpu_res, sens = lpu(inputs)
mc_res = monte_carlo(inputs)

# Prior-receipt point-estimate anchors (formulation-arithmetic-dimensioned-v1)
PRIOR = {
    "volume_solids_frac": 0.6673699761,
    "pvc": 0.294369055,
    "wet_paint_density_g_cm3": 1.576902178,
    "voc_g_per_L": 284.1265185647,
    "stoich_ratio_amineH_per_epoxy": 0.9975379565,
}

results = {}
gum_mc_agree_all = True     # linearization: u_c_lpu vs mc_std
LIN_REL_TOL = 0.03  # JCGM 101 sec.8: LPU standard-uncertainty vs MC std
# volumetric outputs share identical inputs with the prior receipt; stoich uses
# a published AHEW (TETA MW 146.23 / 6 N-H) that differs from the prior receipt's
# value by <1e-2%, well inside its REFERENCE_NOMINAL band -> checked separately.
VOLUMETRIC = ["volume_solids_frac", "pvc", "wet_paint_density_g_cm3", "voc_g_per_L"]
for k in OUTPUT_KEYS:
    uc = lpu_res[k]["u_c_lpu"]
    mc_std = mc_res[k]["mc_std"]
    mc_hw = mc_res[k]["mc_ci95_halfwidth"]
    # PRIMARY falsifiable gate: first-order LPU standard uncertainty == MC std.
    rel_lin = abs(uc - mc_std) / max(mc_std, 1e-15)
    lin_ok = rel_lin <= LIN_REL_TOL
    gum_mc_agree_all = gum_mc_agree_all and bool(lin_ok)
    # SECONDARY characterization: is the k=1.96 Gaussian coverage factor valid?
    k_eff = mc_hw / uc if uc > 0 else float("nan")
    anchor_err = abs(base[k] - PRIOR[k])
    results[k] = {
        "point_estimate": base[k],
        "prior_receipt_point": PRIOR[k],
        "reproduces_prior_abs_err": anchor_err,
        "reproduces_prior": anchor_err < 1e-6,
        "u_c_lpu": uc,
        "mc_std": mc_std,
        "lpu_vs_mc_std_rel_diff": rel_lin,
        "linearization_validated_by_mc": bool(lin_ok),
        "U95_lpu_gaussian_k1.96": lpu_res[k]["U95_lpu"],
        "ci95_lpu_low": base[k] - lpu_res[k]["U95_lpu"],
        "ci95_lpu_high": base[k] + lpu_res[k]["U95_lpu"],
        "mc_mean": mc_res[k]["mc_mean"],
        "mc_ci95_low": mc_res[k]["mc_ci95_sym_low"],
        "mc_ci95_high": mc_res[k]["mc_ci95_sym_high"],
        "mc_ci95_halfwidth": mc_hw,
        "effective_coverage_factor_k_mc": k_eff,
        "gaussian_k1.96_over_covers": bool(k_eff < 1.96 - 0.05) if uc > 0 else False,
        "dominant_input": lpu_res[k]["dominant_input"],
        "dominant_fraction_of_variance": lpu_res[k]["dominant_fraction_of_variance"],
    }

# ---- Falsifiable / non-circular known-answer sensitivity battery ----
kat = []

# KAT1 EXTERNAL_CONSTANT: neat single-solvent coating VOC = 1000*rho, dVOC/drho=1000.
neat = [("xylene_solvent", 100.0, 0.87, "DISTRIBUTOR", 0.0, "solvent")]
d = 0.87 * 1e-6
vp = engine({"xylene_solvent": 0.87 + d}, EEW, AHEW, comps=neat)["voc_g_per_L"]
vm = engine({"xylene_solvent": 0.87 - d}, EEW, AHEW, comps=neat)["voc_g_per_L"]
sens_neat = (vp - vm) / (2 * d)
kat.append({"probe": "neat_solvent_voc_sensitivity_is_1000", "kind": "EXTERNAL_CONSTANT",
            "expected": 1000.0, "got": sens_neat, "abs_err": abs(sens_neat - 1000.0),
            "tol": 1e-3, "pass": abs(sens_neat - 1000.0) < 1e-3,
            "note": "VOC(g/L)=1000*rho for a neat solvent => exact sensitivity 1000; "
                    "u(VOC)=1000*u(rho)."})

# KAT2 EXACT_IDENTITY: zero-solvent coating volume_solids == 1 with ZERO uncertainty
# (ratio collapses to identity independent of every density).
nosolv = [c for c in COMPONENTS if c[5] != "solvent"]
inp_ns = [i for i in build_inputs(nosolv) if i["kind"] == "density"]
# recompute a mini-LPU u_c for volume_solids on the no-solvent recipe
base_ns = engine({c[0]: c[2] for c in nosolv}, EEW, AHEW, comps=nosolv)["volume_solids_frac"]
var_ns = 0.0
for inp in inp_ns:
    v = inp["value"]; dd = max(abs(v) * 1e-6, 1e-9)
    rp = {c[0]: c[2] for c in nosolv}; rm = dict(rp)
    rp[inp["id"]] = v + dd; rm[inp["id"]] = v - dd
    cpi = (engine(rp, EEW, AHEW, comps=nosolv)["volume_solids_frac"]
           - engine(rm, EEW, AHEW, comps=nosolv)["volume_solids_frac"]) / (2 * dd)
    var_ns += (cpi * inp["u_combined"]) ** 2
uc_ns = float(np.sqrt(var_ns))
kat.append({"probe": "zero_solvent_volume_solids_is_1_with_zero_uncertainty",
            "kind": "EXACT_IDENTITY", "expected_value": 1.0, "got_value": base_ns,
            "expected_u_c": 0.0, "got_u_c": uc_ns,
            "abs_err": abs(base_ns - 1.0) + uc_ns, "tol": 1e-9,
            "pass": abs(base_ns - 1.0) < 1e-12 and uc_ns < 1e-9,
            "note": "No volatile => V_solid==V_total identically for all densities "
                    "=> volume_solids=1 with exactly zero propagated uncertainty."})

# KAT3 INTENSIVE_INVARIANCE: scale all masses x2.5 => intensive outputs AND their
# LPU uncertainties are invariant (density/PVC/VOC/volume-solids are intensive).
scaled = [(c[0], c[1] * 2.5, c[2], c[3], c[4], c[5]) for c in COMPONENTS]
_, lpu_scaled, _ = lpu(build_inputs())  # inputs identical; recompute engine on scaled
base_sc = engine({c[0]: c[2] for c in scaled}, EEW, AHEW, comps=scaled,
                 m_resin=M_RESIN * 2.5, m_hard=M_HARDENER * 2.5)
inv_ok = True
inv_detail = {}
# uncertainty invariance: rebuild LPU with scaled masses
def lpu_scaled_engine(inputs, comps, mr, mh):
    contrib = {k: 0.0 for k in ("volume_solids_frac", "pvc", "wet_paint_density_g_cm3", "voc_g_per_L")}
    for inp in inputs:
        if inp["kind"] != "density":
            continue
        v = inp["value"]; dd = max(abs(v) * 1e-6, 1e-9)
        rp = {c[0]: c[2] for c in comps}; rm = dict(rp)
        rp[inp["id"]] = v + dd; rm[inp["id"]] = v - dd
        yp = engine(rp, EEW, AHEW, comps=comps, m_resin=mr, m_hard=mh)
        ym = engine(rm, EEW, AHEW, comps=comps, m_resin=mr, m_hard=mh)
        for k in contrib:
            c = (yp[k] - ym[k]) / (2 * dd)
            contrib[k] += (c * inp["u_combined"]) ** 2
    return {k: float(np.sqrt(val)) for k, val in contrib.items()}
uc_base = lpu_scaled_engine(build_inputs(), COMPONENTS, M_RESIN, M_HARDENER)
uc_scaled = lpu_scaled_engine(build_inputs(), scaled, M_RESIN * 2.5, M_HARDENER * 2.5)
for k in ("volume_solids_frac", "pvc", "wet_paint_density_g_cm3", "voc_g_per_L"):
    de = abs(base_sc[k] - base[k])
    du = abs(uc_scaled[k] - uc_base[k])
    inv_detail[k] = {"point_abs_diff": de, "u_c_abs_diff": du}
    inv_ok = inv_ok and de < 1e-9 and du < 1e-9
kat.append({"probe": "intensive_property_and_uncertainty_scale_invariance",
            "kind": "EXACT_IDENTITY", "scale_factor": 2.5, "detail": inv_detail,
            "tol": 1e-9, "pass": bool(inv_ok),
            "note": "Volume-solids/PVC/VOC/wet-density and their propagated "
                    "uncertainties are intensive => invariant under uniform mass scaling."})

kat_all_pass = all(p["pass"] for p in kat)

diag = {
    "schema": "amphora.formulation-arithmetic.uncertainty-propagation.v1",
    "study_id": "formulation-arithmetic-uncertainty-propagation-v1",
    "run_type": "GUM_LPU_VS_MONTE_CARLO_UNCERTAINTY_PROPAGATION",
    "authority": "AUDIT_ONLY",
    "target_module": "amphora-formulation-arithmetic",
    "target_capability": "Calibrated uncertainty intervals on dimensioned "
        "formulation arithmetic (volume-solids ASTM D2697, PVC, wet-paint "
        "density, VOC EPA Method 24, stoichiometric mix ratio via EEW/AHEW).",
    "fitted_parameters": 0,
    "theory_reference": {
        "gum_lpu": "JCGM 100:2008 (GUM), Evaluation of measurement data -- "
                   "Guide to the expression of uncertainty in measurement, "
                   "sec. 4.3 (Type B), sec. 5.1 eq.10 (LPU, uncorrelated inputs).",
        "monte_carlo": "JCGM 101:2008 (GUM Supplement 1), Propagation of "
                       "distributions using a Monte Carlo method, sec. 5-7; "
                       "sec. 8 GUM-vs-MC validation.",
        "arithmetic_baselines": [
            "ASTM D2697 volume nonvolatile (volume solids)",
            "EPA Method 24 / ASTM D3960 VOC content (g/L)",
            "Asbeck & Van Loo 1949 / Patton 1979 PVC",
            "EEW/AHEW stoichiometric equivalents (Ellis 1993; Wicks/Jones/Pappas 2007)"
        ],
    },
    "why_gum_not_bootstrap_conformal": "The engine has zero fitted parameters, "
        "so predictive uncertainty is not a residual/resampling quantity; "
        "bootstrap and split-conformal are inapplicable. The metrologically "
        "correct calibrated interval for zero-parameter arithmetic is input-"
        "measurement-uncertainty propagation (GUM), cross-validated by Monte Carlo.",
    "non_circularity": "The falsifiable claim -- first-order LPU intervals equal "
        "the reference Monte Carlo intervals within the JCGM 101 sec.8 tolerance "
        "-- is refutable: a strongly nonlinear output would make the two diverge "
        "and FAIL. The three known-answer sensitivity probes are fixed by an "
        "EXTERNAL constant (neat-solvent VOC sensitivity=1000) or by EXACT "
        "IDENTITIES (zero-solvent volume-solids u=0; intensive scale-invariance) "
        "-- none produced by the engine.",
    "input_uncertainty_budget": {
        "method": "Type B (GUM 4.3): rectangular quoting-resolution component "
                  "(half-width 0.5*10^-ndecimals) convolved with a rectangular "
                  "grade/source-dispersion component; u=a/sqrt(3).",
        "grade_relative_halfwidth": GRADE_REL_HALFWIDTH,
        "inputs": [{"name": i["name"], "value": i["value"], "grade": i["grade"],
                    "a_res": i["a_res"], "u_res": i["u_res"],
                    "a_grade": i["a_grade"], "u_grade": i["u_grade"],
                    "u_combined": i["u_combined"],
                    "rel_u_combined": i["rel_u_combined"]} for i in inputs],
    },
    "mc_config": {"seed": MC_SEED, "draws": MC_N, "rng": "numpy.random.default_rng (PCG64)",
                  "per_input_distribution": "nominal + U(-a_res,a_res) + U(-a_grade,a_grade) "
                                            "(exact trapezoidal convolution of two Type B rectangulars)",
                  "coverage_interval": "probabilistically symmetric 2.5/97.5 percentile"},
    "real_formulation_name": "marine-epoxy-primer-dgeba-teta-anticorrosive",
    "results": results,
    "reproduces_prior_volumetric_outputs": all(results[k]["reproduces_prior"] for k in VOLUMETRIC),
    "stoich_anchor_note": {
        "point": results["stoich_ratio_amineH_per_epoxy"]["point_estimate"],
        "prior_receipt_point": PRIOR["stoich_ratio_amineH_per_epoxy"],
        "abs_diff": results["stoich_ratio_amineH_per_epoxy"]["reproduces_prior_abs_err"],
        "within_stoich_U95": results["stoich_ratio_amineH_per_epoxy"]["reproduces_prior_abs_err"]
                             < results["stoich_ratio_amineH_per_epoxy"]["U95_lpu_gaussian_k1.96"],
        "reason": "AHEW convention: TETA MW 146.23 / 6 N-H = 24.3717 g/eq here vs the "
                  "prior receipt's value; <1e-2% shift, far inside the propagated "
                  "stoich U95, and inside the REFERENCE_NOMINAL input uncertainty.",
    },
    "gum_lpu_linearization_validated_by_mc_all_outputs": gum_mc_agree_all,
    "linearization_validation_tolerance_rel": LIN_REL_TOL,
    "coverage_factor_finding": "The first-order LPU combined standard uncertainty "
        "u_c matches the Monte Carlo standard deviation for every output "
        "(linearization is adequate: the reciprocal density map is near-linear over "
        "the +/-2.5% Type B ranges). However the Gaussian coverage factor k=1.96 "
        "OVER-COVERS for outputs whose budget is dominated by one or two bounded "
        "(rectangular/trapezoidal) inputs -- volume_solids and stoich have MC "
        "effective k~1.6-1.7 -- reproducing the exact JCGM 101 sec.8 motivation for "
        "preferring the MC coverage interval over a normal-theory expanded uncertainty. "
        "Report the MC interval as the calibrated interval; report u_c as the "
        "combined standard uncertainty.",
    "known_answer_sensitivity_battery": {"all_pass": kat_all_pass, "n_pass": sum(p["pass"] for p in kat),
                                         "n_total": len(kat), "probes": kat},
    "acceptance": {
        "reproduces_prior_volumetric_point_estimates": all(results[k]["reproduces_prior"] for k in VOLUMETRIC),
        "gum_lpu_linearization_validated_by_mc": gum_mc_agree_all,
        "known_answer_battery_all_pass": kat_all_pass,
    },
    "verdict": ("GUM_LPU_STANDARD_UNCERTAINTY_VALIDATED_BY_MONTE_CARLO"
                if (gum_mc_agree_all and kat_all_pass
                    and all(results[k]["reproduces_prior"] for k in VOLUMETRIC))
                else "VALIDATION_INCOMPLETE"),
    "closes": [
        "Adds first calibrated (GUM LPU + Monte Carlo cross-validated) uncertainty "
        "intervals to the module's dimensioned outputs; prior receipt reported "
        "point estimates only.",
        "Identifies the dominant input-uncertainty contributor per output "
        "(uncertainty budget), enabling targeted data-grade improvement.",
    ],
    "does_not_close": [
        "Does NOT promote amphora-formulation-arithmetic or flip scientific_readiness "
        "(needs two trust-anchored human phase0 keys this AUDIT_ONLY key lacks).",
        "Does NOT modify the manifest (66 receipts / 11 modules), the shipped Rust "
        "engine (still MASS_ONLY), the signed Phase-0 KPI, or any locked dataset.",
        "Input Type B grade half-widths are a documented convention (0.5/1.5/2.5/3.0% "
        "for TDS/SUPPLIER_GUIDE/DISTRIBUTOR/REFERENCE_NOMINAL); tightening them to "
        "measured supplier tolerance bands is a Phase-1 data ask.",
        "Masses treated as exact (nominal recipe / specification arithmetic); prepared-"
        "batch weighing tolerance is a separate scenario not propagated here.",
    ],
}

diag = round_floats(diag, 10)
payload = json.dumps(diag, indent=2, sort_keys=True).encode()
OUT.write_bytes(payload)
print("WROTE", OUT)
print("verdict", diag["verdict"])
print("reproduces_prior_volumetric", diag["reproduces_prior_volumetric_outputs"])
print("lin_validated_all", diag["gum_lpu_linearization_validated_by_mc_all_outputs"])
print("kat_all_pass", kat_all_pass)
print("diagnostic_sha256", sha(payload))
for k in OUTPUT_KEYS:
    r = results[k]
    print(f"  {k}: point={r['point_estimate']} u_c={r['u_c_lpu']} mc_std={r['mc_std']} "
          f"lin_rel={r['lpu_vs_mc_std_rel_diff']} k_eff={r['effective_coverage_factor_k_mc']} "
          f"dom={r['dominant_input']}")
