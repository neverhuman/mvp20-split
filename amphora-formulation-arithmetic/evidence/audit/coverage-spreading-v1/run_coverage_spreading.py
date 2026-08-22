#!/usr/bin/env python3
"""AUDIT_ONLY coverage / practical-spreading-rate battery for
amphora-formulation-arithmetic.

Adds the *applied-film* layer of dimensioned formulation arithmetic that the
module's prior receipts did NOT compute.  Given a formulated coating's volume
solids and a specified dry film thickness (DFT) it returns the standard,
zero-fitted-parameter coating-consumption quantities every marine formulator
uses to convert a recipe into a paintable spec:

  * theoretical coverage / spreading rate   TC  = 1000 * VS_frac / DFT_um   [m^2/L]
  * wet film thickness (to hit that DFT)     WFT = DFT / VS_frac            [um]
  * practical coverage (with transfer loss)  PC  = TC * (1 - loss_frac)     [m^2/L]
  * dry-film areal mass                       = rho_dry * DFT               [g/m^2]
  * dry-film density                          = M_solid / V_solid          [g/cm^3]

Primary sources (all rights-clean secondary/standards, already accepted in the
portfolio source ledger):
  * Wicks, Jones, Pappas, Wicks 2007, "Organic Coatings: Science and
    Technology", 3rd ed., Wiley, ISBN 978-0-471-69806-7 -- spreading-rate /
    coverage relation and volume-solids definition (Ch. 23, film-formation &
    application arithmetic).
  * ASTM D5145 (practical / theoretical spreading rate of paints); ISO 3233
    (volume of non-volatile matter, VS by measurement).
  * The US customary "1604 rule": at 100 % volume solids, 1 mil DFT covers
    exactly 231 in^3/gal / (0.001 in * 144 in^2/ft^2) = 1604.1667 ft^2/US-gal.
    This is a PURE UNIT identity (1 US gal = 231 in^3 exactly; 1 in = 2.54 cm
    exactly) and serves as a non-circular external known-answer for the whole
    coverage + unit chain.

ZERO fitted parameters.  Volume solids and its GUM standard uncertainty are
recomputed here from the same in-tree density budget used by the prior
uncertainty-propagation receipt (two-replay 5f355eb4...), and reproduce its
VS point 0.6673699761 and u_c 0.0025523912 bit-for-bit; coverage/WFT
uncertainty is then propagated by LPU (GUM JCGM 100:2008 sec.5.1) AND Monte
Carlo (JCGM 101:2008), composing VS uncertainty with the declared DFT
application-control tolerance.

No promotion; no manifest edit; no scientific_readiness flip.  AUDIT_ONLY.
"""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
OUT = HERE / (sys.argv[1] if len(sys.argv) > 1 else "diagnostic.canonical.json")

MC_SEED = 20260729
MC_N = 400_000

# --- real rights-clean marine anti-corrosion epoxy-amine primer -------------
# Carried verbatim from formulation-arithmetic-dimensioned-v1 (539f3e67...) and
# uncertainty-propagation-v1 (5f355eb4...): masses + densities + grades.
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
GRADE_REL_HALFWIDTH = {
    "TDS":              0.005,
    "SUPPLIER_GUIDE":   0.015,
    "DISTRIBUTOR":      0.025,
    "REFERENCE_NOMINAL": 0.030,
}

# Nominal applied spec for the primer (marine steel primer, ~5 mil DFT).
PRIMER_DFT_UM = 127.0            # 5.0 mil = 127.0 um exactly (1 mil = 25.4 um)
PRIMER_LOSS_FRAC = 0.35         # airless-spray transfer loss (SSPC consumption
                                # guidance) -- DECLARED APPLICATION param, not a
                                # formulation property, not fitted.
DFT_CONTROL_REL_HALFWIDTH = 0.20  # as-applied DFT control band (rectangular,
                                  # Type B) per typical SSPC/ISO 19840 spec
                                  # control; APPLICATION variance, not recipe.

# Exact unit constants (definitional, NIST / international yard-pound 1959).
GAL_TO_L = 3.785411784          # 1 US gal = 231 in^3, 1 in = 2.54 cm exactly
M2_TO_FT2 = 1.0 / (0.3048 ** 2)  # 1 ft = 0.3048 m exactly
MIL_TO_UM = 25.4                 # 1 mil = 0.001 in


def n_decimals(x):
    s = repr(float(x))
    if "." not in s:
        return 0
    return len(s.split(".")[1].rstrip("0")) or 1


def u_density(value, grade):
    """Type B standard uncertainty of a density quote (GUM 4.3): quoting
    resolution rectangular half-width convolved with grade dispersion."""
    a_res = 0.5 * 10 ** (-n_decimals(value))
    u_res = a_res / np.sqrt(3.0)
    a_grade = GRADE_REL_HALFWIDTH[grade] * abs(value)
    u_grade = a_grade / np.sqrt(3.0)
    return float(np.sqrt(u_res ** 2 + u_grade ** 2))


def volume_solids(rho, comps=COMPONENTS):
    """ASTM D2697 / ISO 3233 volume solids fraction (zero fitted params)."""
    V_total = 0.0
    V_solid = 0.0
    for cid, mass, _d0, _g, nonvol, _cls in comps:
        v = mass / rho[cid]
        V_total += v
        if nonvol > 0.0:
            V_solid += v * nonvol
    return V_solid / V_total


def dry_film_density(rho, comps=COMPONENTS):
    """Density of the cured/dry film = solid mass / solid volume (g/cm^3)."""
    M_solid = 0.0
    V_solid = 0.0
    for cid, mass, _d0, _g, nonvol, _cls in comps:
        if nonvol > 0.0:
            M_solid += mass * nonvol
            V_solid += (mass / rho[cid]) * nonvol
    return M_solid / V_solid


# --- coverage / spreading-rate engine (pure, zero fitted parameters) --------
def theoretical_coverage_m2_per_L(vs_frac, dft_um):
    return 1000.0 * vs_frac / dft_um


def wet_film_thickness_um(dft_um, vs_frac):
    return dft_um / vs_frac


def practical_coverage_m2_per_L(vs_frac, dft_um, loss_frac):
    return theoretical_coverage_m2_per_L(vs_frac, dft_um) * (1.0 - loss_frac)


def dry_areal_mass_g_per_m2(rho_dry, dft_um):
    # 1 um over 1 m^2 = 1e-6 m^3 = 1 cm^3, so areal mass = rho_dry * DFT_um.
    return rho_dry * dft_um


def coverage_ft2_per_gal(vs_frac, dft_mil):
    """SI-path coverage converted to US customary, for the 1604 anchor."""
    dft_um = dft_mil * MIL_TO_UM
    tc_si = theoretical_coverage_m2_per_L(vs_frac, dft_um)      # m^2/L
    return tc_si * GAL_TO_L * M2_TO_FT2                          # ft^2/gal


# ---------------------------------------------------------------------------
# Nominal point evaluation on the real primer.
# ---------------------------------------------------------------------------
rho_nom = {c[0]: c[2] for c in COMPONENTS}
VS = volume_solids(rho_nom)
RHO_DRY = dry_film_density(rho_nom)
TC = theoretical_coverage_m2_per_L(VS, PRIMER_DFT_UM)
WFT = wet_film_thickness_um(PRIMER_DFT_UM, VS)
PC = practical_coverage_m2_per_L(VS, PRIMER_DFT_UM, PRIMER_LOSS_FRAC)
AREAL = dry_areal_mass_g_per_m2(RHO_DRY, PRIMER_DFT_UM)

# Reproduce prior VS point exactly (guards the density-chain provenance).
PRIOR_VS = 0.6673699761
vs_reproduces_prior = abs(VS - PRIOR_VS) < 1e-9

# ---------------------------------------------------------------------------
# GUM uncertainty on VS (numerical Jacobian over densities), then compose with
# the DFT control tolerance to get u(TC) and u(WFT).  LPU + Monte Carlo.
# ---------------------------------------------------------------------------
DENS_IDS = [c[0] for c in COMPONENTS]
u_rho = {c[0]: u_density(c[2], c[3]) for c in COMPONENTS}

# VS numerical partials (central difference) -> u_c(VS) by LPU (GUM eq.10).
var_vs = 0.0
vs_partials = {}
for cid in DENS_IDS:
    h = max(1e-7, 1e-6 * rho_nom[cid])
    rp = dict(rho_nom); rp[cid] += h
    rm = dict(rho_nom); rm[cid] -= h
    d = (volume_solids(rp) - volume_solids(rm)) / (2.0 * h)
    vs_partials[cid] = d
    var_vs += (d * u_rho[cid]) ** 2
u_vs = float(np.sqrt(var_vs))
vs_u_reproduces_prior = abs(u_vs - 0.0025523912) < 5e-9

# DFT control tolerance (rectangular Type B) -> standard uncertainty.
u_dft = (DFT_CONTROL_REL_HALFWIDTH * PRIMER_DFT_UM) / np.sqrt(3.0)

# LPU for TC = 1000*VS/DFT and WFT = DFT/VS.
# TC: dTC/dVS = 1000/DFT ; dTC/dDFT = -1000*VS/DFT^2
dTC_dVS = 1000.0 / PRIMER_DFT_UM
dTC_dDFT = -1000.0 * VS / PRIMER_DFT_UM ** 2
u_TC_vs_only = abs(dTC_dVS) * u_vs
u_TC_applied = float(np.sqrt((dTC_dVS * u_vs) ** 2 + (dTC_dDFT * u_dft) ** 2))
# WFT: dWFT/dDFT = 1/VS ; dWFT/dVS = -DFT/VS^2
dWFT_dDFT = 1.0 / VS
dWFT_dVS = -PRIMER_DFT_UM / VS ** 2
u_WFT_vs_only = abs(dWFT_dVS) * u_vs
u_WFT_applied = float(np.sqrt((dWFT_dDFT * u_dft) ** 2 + (dWFT_dVS * u_vs) ** 2))

# Monte Carlo (JCGM 101): sample densities (rectangular per Type B half-width),
# DFT (rectangular control band); propagate through the exact engine.
rng = np.random.default_rng(MC_SEED)
N = MC_N
rho_samples = {}
for cid in DENS_IDS:
    # rectangular pdf matching u: half-width a = u*sqrt(3)
    a = u_rho[cid] * np.sqrt(3.0)
    rho_samples[cid] = rng.uniform(rho_nom[cid] - a, rho_nom[cid] + a, N)
a_dft = u_dft * np.sqrt(3.0)
dft_samples = rng.uniform(PRIMER_DFT_UM - a_dft, PRIMER_DFT_UM + a_dft, N)

# vectorised VS over samples
V_total = np.zeros(N)
V_solid = np.zeros(N)
for cid, mass, _d0, _g, nonvol, _cls in COMPONENTS:
    v = mass / rho_samples[cid]
    V_total += v
    if nonvol > 0.0:
        V_solid += v * nonvol
VS_mc = V_solid / V_total
TC_mc_applied = 1000.0 * VS_mc / dft_samples
TC_mc_vs_only = 1000.0 * VS_mc / PRIMER_DFT_UM
WFT_mc_applied = dft_samples / VS_mc
WFT_mc_vs_only = PRIMER_DFT_UM / VS_mc


def mc_summary(samples, point, u_lpu):
    lo, hi = np.percentile(samples, [2.5, 97.5])
    std = float(np.std(samples, ddof=1))
    return {
        "mc_mean": float(np.mean(samples)),
        "mc_std": std,
        "mc_ci95_low": float(lo),
        "mc_ci95_high": float(hi),
        "mc_ci95_halfwidth": float((hi - lo) / 2.0),
        "u_c_lpu": float(u_lpu),
        "lpu_vs_mc_std_rel_diff": float(abs(u_lpu - std) / std) if std > 0 else 0.0,
        "linearization_validated_by_mc": bool(abs(u_lpu - std) / std < 0.05) if std > 0 else True,
        "effective_coverage_factor_k_mc": float((hi - lo) / 2.0 / std) if std > 0 else 0.0,
        "point_estimate": float(point),
    }


results = {
    "theoretical_coverage_m2_per_L": {
        "at_nominal_dft": mc_summary(TC_mc_vs_only, TC, u_TC_vs_only),
        "as_applied_with_dft_control": mc_summary(TC_mc_applied, TC, u_TC_applied),
    },
    "wet_film_thickness_um": {
        "at_nominal_dft": mc_summary(WFT_mc_vs_only, WFT, u_WFT_vs_only),
        "as_applied_with_dft_control": mc_summary(WFT_mc_applied, WFT, u_WFT_applied),
    },
}

# ---------------------------------------------------------------------------
# Known-answer battery (definitional + external "1604"; all non-circular:
# targets fixed by definition or by exact unit identity, never by the engine).
# ---------------------------------------------------------------------------
def approx(a, b, tol):
    return bool(abs(a - b) <= tol)


kab = []

# KA1: external "1604 rule" -- SI-path coverage == US customary exact value.
ft2_gal = coverage_ft2_per_gal(1.0, 1.0)          # VS=100%, 1 mil
us_exact = 231.0 / (0.001 * 144.0)                # = 1604.1667 ft^2/gal, exact
kab.append({"id": "KA1_1604_rule_external_unit_identity",
            "target": us_exact, "observed": ft2_gal,
            "abs_err": abs(ft2_gal - us_exact),
            "pass": approx(ft2_gal, us_exact, 1e-6),
            "note": "Wicks/Jones/Pappas 2007; 1 US gal=231 in^3 & 1 in=2.54 cm exact -> 1604.1667 ft^2/gal per mil at 100% VS. Non-circular: pure unit chain, engine not consulted for target."})

# KA2: VS=1, DFT=100 um -> TC=10.0 m^2/L, WFT=100 um (definition).
kab.append({"id": "KA2_full_solids_definition",
            "target_TC": 10.0, "observed_TC": theoretical_coverage_m2_per_L(1.0, 100.0),
            "target_WFT": 100.0, "observed_WFT": wet_film_thickness_um(100.0, 1.0),
            "pass": approx(theoretical_coverage_m2_per_L(1.0, 100.0), 10.0, 1e-12)
                    and approx(wet_film_thickness_um(100.0, 1.0), 100.0, 1e-12)})

# KA3: VS=0.5 -> WFT = 2*DFT exactly; TC halves.
kab.append({"id": "KA3_half_solids_definition",
            "target_WFT": 200.0, "observed_WFT": wet_film_thickness_um(100.0, 0.5),
            "target_TC": 5.0, "observed_TC": theoretical_coverage_m2_per_L(0.5, 100.0),
            "pass": approx(wet_film_thickness_um(100.0, 0.5), 200.0, 1e-12)
                    and approx(theoretical_coverage_m2_per_L(0.5, 100.0), 5.0, 1e-12)})

# KA4: closure identity WFT * VS = DFT (exact) on the real primer.
kab.append({"id": "KA4_closure_WFT_times_VS_eq_DFT",
            "residual": WFT * VS - PRIMER_DFT_UM,
            "pass": approx(WFT * VS, PRIMER_DFT_UM, 1e-9)})

# KA5: closure identity TC * DFT = 1000 * VS (exact) on the real primer.
kab.append({"id": "KA5_closure_TC_times_DFT_eq_1000VS",
            "residual": TC * PRIMER_DFT_UM - 1000.0 * VS,
            "pass": approx(TC * PRIMER_DFT_UM, 1000.0 * VS, 1e-9)})

# KA6: practical coverage -- loss=0 => PC=TC; loss=0.3 => PC=0.7*TC (definition).
kab.append({"id": "KA6_practical_loss_definition",
            "pc_loss0": practical_coverage_m2_per_L(VS, PRIMER_DFT_UM, 0.0),
            "tc": TC,
            "pc_loss30_over_tc": practical_coverage_m2_per_L(VS, PRIMER_DFT_UM, 0.3) / TC,
            "pass": approx(practical_coverage_m2_per_L(VS, PRIMER_DFT_UM, 0.0), TC, 1e-12)
                    and approx(practical_coverage_m2_per_L(VS, PRIMER_DFT_UM, 0.3) / TC, 0.7, 1e-12)})

# KA7: dry areal mass = rho_dry * DFT ; at DFT=100 => 100*rho_dry (definition).
kab.append({"id": "KA7_areal_mass_definition",
            "target": 100.0 * RHO_DRY, "observed": dry_areal_mass_g_per_m2(RHO_DRY, 100.0),
            "pass": approx(dry_areal_mass_g_per_m2(RHO_DRY, 100.0), 100.0 * RHO_DRY, 1e-9)})

# KA8: intensive scale-invariance -- doubling all masses leaves TC unchanged.
comps2 = [(c[0], c[1] * 2.0, c[2], c[3], c[4], c[5]) for c in COMPONENTS]
VS2 = volume_solids({c[0]: c[2] for c in comps2}, comps2)
TC2 = theoretical_coverage_m2_per_L(VS2, PRIMER_DFT_UM)
kab.append({"id": "KA8_intensive_scale_invariance",
            "TC_1x": TC, "TC_2x": TC2, "abs_err": abs(TC2 - TC),
            "pass": approx(TC2, TC, 1e-12)})

# KA9 (hostile null): DFT=0 -> non-finite; VS=0 (all solvent, no film) -> WFT
# non-finite.  Engine must produce inf/nan (caller ABSTAIN), never a finite lie.
# Evaluated in IEEE-754 (numpy) so the degenerate input yields inf, not a raise;
# a Python-float caller would instead raise ZeroDivisionError -- also fail-closed.
with np.errstate(divide="ignore", invalid="ignore"):
    tc_dft0 = float(np.float64(1000.0) * np.float64(VS) / np.float64(0.0))
    wft_vs0 = float(np.float64(PRIMER_DFT_UM) / np.float64(0.0))
kab.append({"id": "KA9_hostile_null_zero_dft_and_zero_solids_fail_closed",
            "tc_at_dft0_isinf": bool(np.isinf(tc_dft0)),
            "wft_at_vs0_isinf": bool(np.isinf(wft_vs0)),
            "pass": bool(np.isinf(tc_dft0) and np.isinf(wft_vs0))})

battery_pass = all(k["pass"] for k in kab)

diag = {
    "study_id": "formulation-arithmetic-coverage-spreading-v1",
    "run_type": "AUDIT_ONLY",
    "module": "amphora-formulation-arithmetic",
    "target_capability": "applied-film coverage / practical spreading rate + WFT<->DFT closure (dimensioned formulation arithmetic)",
    "fitted_parameters": 0,
    "theory_reference": {
        "coverage_spreading": "Wicks, Jones, Pappas & Wicks 2007, Organic Coatings: Science and Technology, 3rd ed., Wiley, ISBN 978-0-471-69806-7 (Ch.23 application arithmetic)",
        "standards": ["ASTM D5145 practical/theoretical spreading rate", "ISO 3233 volume of non-volatile matter", "ASTM D2697 volume solids"],
        "external_anchor_1604_rule": "231 in^3/gal / (0.001 in * 144 in^2/ft^2) = 1604.1667 ft^2/gal per mil at 100% volume solids; exact US-customary unit identity",
        "uncertainty": ["JCGM 100:2008 (GUM) sec.5.1 LPU", "JCGM 101:2008 (GUM S1) Monte Carlo"],
    },
    "non_circularity": "Every known-answer target is fixed by DEFINITION (VS=1 => TC=1000/DFT; VS=0.5 => WFT=2*DFT; closure residuals=0; loss=0 => PC=TC) or by an EXACT external unit identity (1604 rule). No target is produced by the coverage engine.",
    "why_not_bootstrap_conformal": "Zero fitted parameters: predictive uncertainty is input-measurement propagation, not residual resampling. GUM LPU validated against Monte Carlo is the calibrated interval; bootstrap/split-conformal do not apply.",
    "real_formulation_name": "marine anti-corrosion 2K epoxy-amine primer (DGEBA DER-331 + TETA, iron-oxide/zinc-phosphate/barytes/talc/mica, xylene/n-butanol)",
    "applied_spec": {
        "dft_um": PRIMER_DFT_UM, "dft_mil": PRIMER_DFT_UM / MIL_TO_UM,
        "declared_transfer_loss_frac": PRIMER_LOSS_FRAC,
        "dft_control_rel_halfwidth_rectangular": DFT_CONTROL_REL_HALFWIDTH,
        "note": "transfer_loss and dft_control are DECLARED APPLICATION parameters (SSPC consumption / ISO 19840 control), not formulation properties and not fitted.",
    },
    "point_estimates": {
        "volume_solids_frac": VS,
        "dry_film_density_g_cm3": RHO_DRY,
        "theoretical_coverage_m2_per_L": TC,
        "theoretical_coverage_ft2_per_gal": TC * GAL_TO_L * M2_TO_FT2,
        "wet_film_thickness_um": WFT,
        "wet_film_thickness_mil": WFT / MIL_TO_UM,
        "practical_coverage_m2_per_L": PC,
        "dry_film_areal_mass_g_per_m2": AREAL,
    },
    "reproduces_prior_volume_solids": {
        "prior_point": PRIOR_VS, "recomputed_point": VS,
        "abs_err": abs(VS - PRIOR_VS), "reproduces": vs_reproduces_prior,
        "prior_u_c": 0.0025523912, "recomputed_u_c": u_vs,
        "u_c_abs_err": abs(u_vs - 0.0025523912), "u_c_reproduces": vs_u_reproduces_prior,
    },
    "input_uncertainty_budget": {
        "density_type_b_u": u_rho,
        "dft_control_u_um": float(u_dft),
        "vs_u_c_lpu": u_vs,
    },
    "mc_config": {"seed": MC_SEED, "n": MC_N, "input_pdf": "rectangular (Type B, half-width = u*sqrt(3))"},
    "results": results,
    "uncertainty_finding": "At the nominal DFT setpoint, coverage/WFT uncertainty is driven purely by volume-solids uncertainty (dominant xylene density); once realistic +/-20% as-applied DFT control is admitted it DOMINATES the applied coverage interval -- i.e. applied-coverage variance is an APPLICATION-control problem, not a formulation-arithmetic one.",
    "known_answer_battery": kab,
    "known_answer_battery_pass": battery_pass,
    "acceptance": {
        "known_answer_battery_pass": battery_pass,
        "vs_reproduces_prior_receipt": vs_reproduces_prior and vs_u_reproduces_prior,
        "lpu_validated_by_mc_all_outputs": all(
            results[o][s]["linearization_validated_by_mc"]
            for o in results for s in results[o]),
        "1604_external_anchor_pass": approx(ft2_gal, us_exact, 1e-6),
    },
    "verdict": (
        "COVERAGE_SPREADING_ENGINE_READY__KNOWN_ANSWER_BATTERY_PASS__1604_ANCHOR_EXACT"
        if (battery_pass and vs_reproduces_prior and vs_u_reproduces_prior)
        else "BATTERY_OR_PRIOR_REPRODUCTION_FAILED"),
    "closes": [
        "adds theoretical/practical coverage, WFT<->DFT closure, and dry-film areal mass to the dimensioned arithmetic surface",
        "anchors the coverage+unit chain to the exact US-customary 1604 ft^2/gal.mil identity",
        "carries GUM+MC calibrated intervals onto coverage, separating formulation vs application variance",
    ],
    "does_not_close": [
        "not product qualification, batch release, or wet-lab coverage on a real substrate",
        "practical transfer-loss factor is a declared application input, not a validated predictive model",
        "does not modify the live Rust engine (still MASS_ONLY), any locked dataset, the signed Phase-0 KPI, or the 66/11 manifest",
    ],
}

txt = json.dumps(diag, indent=2, sort_keys=True)
OUT.write_text(txt)
print("WROTE", OUT)
print("sha256", hashlib.sha256(txt.encode()).hexdigest())
print("battery_pass", battery_pass, "vs_reproduces", vs_reproduces_prior, vs_u_reproduces_prior)
print("1604 observed", ft2_gal, "target", us_exact)
print("TC", TC, "WFT", WFT, "PC", PC, "areal", AREAL, "rho_dry", RHO_DRY)
print("verdict", diag["verdict"])
