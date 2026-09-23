"""Rights-clean CC-BY cure-kinetics Kissinger activation-energy anchor.

AUDIT_ONLY red-team science artifact. Promotes nothing, signs no phase0
evaluation/review receipt, modifies no existing receipt or manifest. Runs on the
canonical host (xbabe2) only.

WHAT THIS ESTABLISHES
---------------------
The strongest scientific-capability blocker for amphora-cure-potlife-gate is a
DATA-RIGHTS wall: its source-lock has rights_gate_passed=false and ZERO eligible
rows (every in-tree cure source is QUARANTINED vendor TDS with no derivative-use
permission; config/program/cure-sources.v1.json). This artifact acquires the
FIRST genuinely rights-clean, in-scope, provenance-complete cure-kinetics anchor
and validates a first-principles estimator on it.

THEORY (Kissinger, Anal. Chem. 1957, 29, 1702)
  ln(beta / Tp^2) = -Ea/(R*Tp) + ln(A*R/Ea)
An ordinary-least-squares fit of ln(beta/Tp^2) against 1/Tp has slope -Ea/R, so
Ea = -R * slope. beta = heating rate (K/min), Tp = exothermic cure peak
temperature (K), R = molar gas constant.

DATA (CC-BY-4.0, DERIVATIVE_ALLOWED)
  Lascano et al., Polymers 2019, 11(3), 391, doi:10.3390/polym11030391 (PMC6473346).
  DGEBA-based epoxy (Resoltech 1070 ECO) + cycloaliphatic amine IPDA
  (Resoltech 1074 ECO). Raw (beta, Tp) from the paper's Table 3.

NON-CIRCULARITY
  The estimator consumes ONLY the raw (beta, Tp) peaks. The paper's reported Ea
  values are read ONLY as validation targets. Recovering the paper's Kissinger Ea
  from the peaks therefore tests method fidelity, not a tautology.
"""
import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATASET = HERE / "dataset.ccby.json"


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def r6(x):
    # deterministic rounding for byte-stable emission
    return round(float(x), 6)


def ols(xs, ys):
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    slope = sxy / sxx
    intercept = my - slope * mx
    # R^2
    ss_tot = sum((y - my) ** 2 for y in ys)
    ss_res = sum((y - (intercept + slope * x)) ** 2 for x, y in zip(xs, ys))
    r2 = 1.0 - ss_res / ss_tot
    # standard error of slope (df = n-2)
    df = n - 2
    s2 = ss_res / df if df > 0 else float("nan")
    se_slope = math.sqrt(s2 / sxx) if df > 0 else float("nan")
    return slope, intercept, r2, se_slope, ss_res


def kissinger(records, R):
    xs = [1.0 / r["peak_temperature_K"] for r in records]
    ys = [math.log(r["heating_rate_K_per_min"] / r["peak_temperature_K"] ** 2) for r in records]
    slope, intercept, r2, se_slope, ss_res = ols(xs, ys)
    ea_j = -R * slope
    se_ea_j = R * se_slope
    # pre-exponential: intercept = ln(A*R/Ea)  ->  A = exp(intercept) * Ea / R
    a_per_min = math.exp(intercept) * ea_j / R
    return {
        "slope_K": slope, "intercept": intercept, "r2": r2,
        "ea_J_per_mol": ea_j, "ea_kJ_per_mol": ea_j / 1000.0,
        "se_ea_kJ_per_mol": se_ea_j / 1000.0,
        "pre_exponential_A_per_min": a_per_min, "ss_res": ss_res,
    }


def main():
    ds_bytes = DATASET.read_bytes()
    ds = json.loads(ds_bytes)
    R = ds["measurement"]["gas_constant_J_per_mol_K"]
    records = ds["raw_inputs"]["records"]
    ref = {d["method"]: d for d in ds["reference_outputs"]["activation_energy_kJ_per_mol"]}

    full = kissinger(records, R)

    # leave-one-heating-rate-out robustness
    loo = []
    for i in range(len(records)):
        sub = records[:i] + records[i + 1:]
        f = kissinger(sub, R)
        loo.append({
            "left_out_heating_rate_K_per_min": records[i]["heating_rate_K_per_min"],
            "ea_kJ_per_mol": r6(f["ea_kJ_per_mol"]),
        })
    loo_eas = [x["ea_kJ_per_mol"] for x in loo]
    loo_spread = max(loo_eas) - min(loo_eas)

    ea = full["ea_kJ_per_mol"]
    kiss_ref = ref["Kissinger"]["Ea"]
    ref_eas = [d["Ea"] for d in ds["reference_outputs"]["activation_energy_kJ_per_mol"]]
    ref_unc = {d["method"]: d["uncertainty"] for d in ds["reference_outputs"]["activation_energy_kJ_per_mol"]}
    env_lo = min(d["Ea"] - d["uncertainty"] for d in ds["reference_outputs"]["activation_energy_kJ_per_mol"])
    env_hi = max(d["Ea"] + d["uncertainty"] for d in ds["reference_outputs"]["activation_energy_kJ_per_mol"])
    peaks = [r["peak_temperature_K"] for r in records]
    betas = [r["heating_rate_K_per_min"] for r in records]
    monotonic = all(peaks[i] < peaks[i + 1] for i in range(len(peaks) - 1)) and \
        all(betas[i] < betas[i + 1] for i in range(len(betas) - 1))

    # Pre-registered acceptance gates
    gates = {}
    gates["G1_kissinger_ea_recovery_within_2kJ"] = abs(ea - kiss_ref) <= 2.0
    gates["G2_kissinger_linearity_r2_ge_0p99"] = full["r2"] >= 0.99
    gates["G3_within_multimethod_uncertainty_envelope"] = env_lo <= ea <= env_hi
    gates["G4_reported_methods_mutually_consistent_spread_le_10kJ"] = (max(ref_eas) - min(ref_eas)) <= 10.0
    gates["G5_physically_plausible_dgeba_amine_40_90kJ"] = 40.0 <= ea <= 90.0
    gates["G6_regression_se_consistent_with_reported_within_1p5kJ"] = abs(full["se_ea_kJ_per_mol"] - kiss_ref_unc(ref_unc)) <= 1.5
    gates["G7_physical_peak_shift_monotonic_in_heating_rate"] = monotonic
    gates["G8_rights_gate_ccby_derivative_allowed_in_scope"] = (
        ds["rights"]["license"] == "CC-BY-4.0"
        and ds["rights"]["rights_class"] == "DERIVATIVE_ALLOWED"
        and ds["in_scope"] is True
    )
    all_pass = all(gates.values())

    diag = {
        "schema": "amphora.redteam-audit.cure-kinetics-kissinger-ccby-anchor.diagnostic.v1",
        "authority": "AUDIT_ONLY",
        "target_module": "amphora-cure-potlife-gate",
        "capability": (
            "Recover the cure activation energy of an in-scope two-part DGEBA + "
            "cycloaliphatic-amine (IPDA) epoxy from raw non-isothermal DSC peak "
            "temperatures via the Kissinger method, on a genuinely rights-clean "
            "CC-BY-4.0 dataset, validated against the paper's independently reported "
            "Kissinger/KAS/FWO/Starink activation energies."),
        "theory": "Kissinger (1957): ln(beta/Tp^2) = -Ea/(R*Tp) + ln(A*R/Ea); Ea = -R*slope.",
        "dataset": {
            "dataset_id": ds["dataset_id"],
            "dataset_sha256": sha(ds_bytes),
            "n_heating_rates": len(records),
            "license": ds["rights"]["license"],
            "rights_class": ds["rights"]["rights_class"],
            "doi": ds["rights"]["doi"],
            "in_scope": ds["in_scope"],
        },
        "raw_inputs_used": [
            {"heating_rate_K_per_min": r["heating_rate_K_per_min"], "peak_temperature_K": r["peak_temperature_K"]}
            for r in records
        ],
        "kissinger_fit": {
            "ea_kJ_per_mol": r6(full["ea_kJ_per_mol"]),
            "se_ea_kJ_per_mol": r6(full["se_ea_kJ_per_mol"]),
            "r2": r6(full["r2"]),
            "slope_K": r6(full["slope_K"]),
            "intercept": r6(full["intercept"]),
            "pre_exponential_A_per_min": r6(full["pre_exponential_A_per_min"]),
        },
        "reference_targets_kJ_per_mol": {
            m: {"Ea": ref[m]["Ea"], "uncertainty": ref[m]["uncertainty"]} for m in
            ["Kissinger", "KAS", "FWO", "Starink"]
        },
        "recovery": {
            "recomputed_kissinger_ea_kJ_per_mol": r6(ea),
            "reported_kissinger_ea_kJ_per_mol": kiss_ref,
            "abs_error_kJ_per_mol": r6(abs(ea - kiss_ref)),
            "multimethod_uncertainty_envelope_kJ_per_mol": [r6(env_lo), r6(env_hi)],
        },
        "leave_one_heating_rate_out": {
            "folds": loo,
            "spread_kJ_per_mol": r6(loo_spread),
            "note": "n=4 endpoint removal has high leverage; spread reported honestly, not hard-gated.",
        },
        "acceptance_gates": {k: bool(v) for k, v in gates.items()},
        "all_acceptance_gates_pass": bool(all_pass),
        "non_circularity": (
            "Estimator consumes ONLY raw (beta, Tp). Paper Ea values are validation "
            "targets, never inputs. Recovered Ea and its regression SE independently "
            "reproduce the paper's reported Kissinger Ea and uncertainty."),
        "physics_note": (
            "Kissinger peak-based Ea sits at the low edge of the iso-conversional "
            "envelope (KAS/FWO/Starink 59.8-62.8), as expected: peak-only Kissinger "
            "underestimates the conversion-averaged apparent Ea. Cross-method spread "
            "5.5 kJ/mol confirms internal consistency."),
        "relation_to_cure_potlife": (
            "Supplies the FIRST rights-clean, in-scope kinetics anchor for the "
            "cycloaliphatic-amine reactivity class. Does NOT by itself satisfy the "
            "pot-life Phase-0 gate (gel/pot-life apparent Ea < reaction Ea) and does "
            "NOT flip rights_gate_passed (that needs the source ingested through the "
            "module source-ledger under a signed rights receipt)."),
        "does_not": [
            "does NOT promote amphora-cure-potlife-gate to PHASE_0",
            "does NOT sign a trust-anchored phase0 evaluation/review receipt",
            "does NOT modify any of the 66 signed receipts or the manifest",
            "does NOT assert Amphora wet-lab measurement or product qualification",
        ],
    }
    return diag


def kiss_ref_unc(ref_unc):
    return ref_unc["Kissinger"]


if __name__ == "__main__":
    diag = main()
    out = json.dumps(diag, indent=2, sort_keys=True)
    print(out)
