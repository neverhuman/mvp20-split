#!/usr/bin/env python3
"""
amphora-viscosity-score :: campaign item W-VISC2
Positive control for the W-VISC1 Krieger-Dougherty / Finke-et-al-2021 benchmark.

Demonstrates the benchmark harness is sensitive to defective input, not just
descriptively reporting whatever number comes out. Two checks are run on the
5 digitized (wt_pct, eta) points from W-VISC1:

  1. Physical-admissibility monotonicity check: apparent viscosity at fixed
     shear rate (10 1/s) MUST increase monotonically with solids loading
     (more rigid filler -> higher viscosity; confirmed true for all 9 curves
     in the source Fig. 8, including the 4 excluded ones). This is a
     necessary condition independent of any curve-fit.
  2. Curve-fit goodness-of-fit (R^2) for both the fixed-Einstein-intrinsic-
     viscosity (2-param) and free-intrinsic-viscosity (3-param) Krieger-
     Dougherty fits, replicated verbatim from run_kd_ccby_reachability_probe.py
     (itself replicated verbatim from src/lib.rs:1208-1224).

The planted defect is a 10x decimal-shift error (eta at 15.0 wt.% changed
9.55 -> 0.955 Pa.s) -- chosen because this portfolio has an independently
documented history of exactly this failure class (decimal-convention /
locale-typography misreads, up to 169x, in other modules' source data).
The defect is planted on a COPY of the digitized input; the original W-VISC1
digitized values and diagnostic.canonical.json are never modified.
"""
import hashlib
import json
import sys
import numpy as np
from scipy.optimize import curve_fit, differential_evolution


def kd_vec(phi, eta_liq, phi_max, eta_intr):
    return eta_liq * (1 - phi / phi_max) ** (-eta_intr * phi_max)


def wt_pct_to_phi(wt_pct, rho_particle_g_cm3, rho_matrix_g_cm3):
    f = wt_pct / 100.0
    v_p = f / rho_particle_g_cm3
    v_m = (1.0 - f) / rho_matrix_g_cm3
    return v_p / (v_p + v_m)


def monotonicity_check(wt_pct_sorted_asc, eta_sorted_asc):
    violations = []
    for i in range(1, len(eta_sorted_asc)):
        if eta_sorted_asc[i] <= eta_sorted_asc[i - 1]:
            violations.append({
                "wt_pct_lower": wt_pct_sorted_asc[i - 1],
                "eta_lower": eta_sorted_asc[i - 1],
                "wt_pct_higher": wt_pct_sorted_asc[i],
                "eta_higher": eta_sorted_asc[i],
                "note": "higher solids loading produced LOWER apparent viscosity "
                        "-- physically inadmissible for a rigid-filler suspension",
            })
    return violations


def fit_fixed_einstein(phi, eta):
    ss_tot = float(np.sum((eta - eta.mean()) ** 2))

    def f(phi_, eta_liq, phi_max):
        return kd_vec(phi_, eta_liq, phi_max, 2.5)
    bounds = ([0.01, float(phi.max()) * 1.01], [10.0, 0.95])
    popt, _ = curve_fit(f, phi, eta, p0=[1.0, 0.6], bounds=bounds, maxfev=20000)
    pred = f(phi, *popt)
    r2 = 1 - float(np.sum((pred - eta) ** 2)) / ss_tot
    return {
        "eta_liquid_fit_pa_s": round(float(popt[0]), 6),
        "phi_max_fit": round(float(popt[1]), 6),
        "r_squared": round(r2, 6),
        "predicted_eta_pa_s": [round(float(x), 4) for x in pred],
    }


def fit_free_intrinsic(phi, eta):
    ss_tot = float(np.sum((eta - eta.mean()) ** 2))

    def sse(params):
        eta_liq, phi_max, eta_intr = params
        if phi_max <= float(phi.max()) * 1.001:
            return 1e12
        pred = kd_vec(phi, eta_liq, phi_max, eta_intr)
        return float(np.sum((pred - eta) ** 2))
    bounds = [(0.1, 5.0), (float(phi.max()) * 1.01, 0.95), (0.1, 100.0)]
    res = differential_evolution(sse, bounds, seed=1, maxiter=2000, tol=1e-12,
                                  popsize=40, polish=True)
    eta_liq, phi_max, eta_intr = res.x
    pred = kd_vec(phi, eta_liq, phi_max, eta_intr)
    r2 = 1 - float(np.sum((pred - eta) ** 2)) / ss_tot
    return {
        "eta_liquid_fit_pa_s": round(float(eta_liq), 6),
        "phi_max_fit": round(float(phi_max), 6),
        "intrinsic_viscosity_fit": round(float(eta_intr), 4),
        "r_squared": round(r2, 6),
        "predicted_eta_pa_s": [round(float(x), 4) for x in pred],
    }


def run(out_path):
    rho_p_central = 3.02
    rho_m_central = 1.175

    clean = [
        {"wt_pct": 20.0, "eta_pa_s": 22.4},
        {"wt_pct": 17.5, "eta_pa_s": 14.1},
        {"wt_pct": 15.0, "eta_pa_s": 9.55},
        {"wt_pct": 12.5, "eta_pa_s": 5.92},
        {"wt_pct": 10.0, "eta_pa_s": 3.42},
    ]
    # planted defect: 10x decimal-shift error on the 15.0 wt.% point (9.55 -> 0.955)
    defected = json.loads(json.dumps(clean))
    for d in defected:
        if d["wt_pct"] == 15.0:
            d["eta_pa_s"] = round(d["eta_pa_s"] / 10.0, 3)

    def analyze(points, label):
        pts_sorted = sorted(points, key=lambda d: d["wt_pct"])
        wt_asc = [d["wt_pct"] for d in pts_sorted]
        eta_asc = [d["eta_pa_s"] for d in pts_sorted]
        mono_violations = monotonicity_check(wt_asc, eta_asc)

        wt = np.array([d["wt_pct"] for d in points])
        eta = np.array([d["eta_pa_s"] for d in points])
        phi = wt_pct_to_phi(wt, rho_p_central, rho_m_central)

        fixed_result = fit_fixed_einstein(phi, eta)
        free_result = fit_free_intrinsic(phi, eta)

        return {
            "label": label,
            "points": points,
            "monotonicity_check": {
                "rule": "apparent viscosity at fixed shear rate must strictly increase "
                        "with solids wt.% for a rigid-filler suspension (confirmed true "
                        "for all 9 published curves in Fig. 8, including excluded ones)",
                "violations": mono_violations,
                "passed": len(mono_violations) == 0,
            },
            "fixed_einstein_2p5_fit": fixed_result,
            "free_intrinsic_3param_fit": free_result,
        }

    clean_result = analyze(clean, "clean (W-VISC1 digitized values, unmodified)")
    defect_result = analyze(defected, "defected (planted 10x decimal-shift on 15.0 wt.% point: 9.55 -> 0.955 Pa.s)")

    output = {
        "schema": "amphora.viscosity-score.krieger-dougherty-positive-control.v1",
        "campaign_item_id": "W-VISC2",
        "purpose": "Positive control: show the benchmark harness fires on a defect planted "
                   "in its own input, per the survival-receipt requirement.",
        "planted_defect": {
            "how_planted": "Copied the 5 digitized (wt_pct, eta_pa_s) points from "
                            "run_kd_ccby_reachability_probe.py verbatim, then divided the "
                            "eta_pa_s value of the wt_pct=15.0 point by 10 (9.55 -> 0.955), "
                            "simulating a decimal-place / locale-typography misread of the "
                            "kind independently documented elsewhere in this portfolio.",
            "kind": "10x decimal-shift error on one digitized data point",
        },
        "clean": clean_result,
        "defected": defect_result,
        "detection_summary": {
            "monotonicity_check_detected": (
                clean_result["monotonicity_check"]["passed"]
                and not defect_result["monotonicity_check"]["passed"]
            ),
            "fixed_einstein_r_squared_clean": clean_result["fixed_einstein_2p5_fit"]["r_squared"],
            "fixed_einstein_r_squared_defected": defect_result["fixed_einstein_2p5_fit"]["r_squared"],
            "free_intrinsic_r_squared_clean": clean_result["free_intrinsic_3param_fit"]["r_squared"],
            "free_intrinsic_r_squared_defected": defect_result["free_intrinsic_3param_fit"]["r_squared"],
        },
    }
    output_json = json.dumps(output, indent=2, sort_keys=True).encode()
    with open(out_path, "wb") as fh:
        fh.write(output_json)
    return hashlib.sha256(output_json).hexdigest()


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "positive_control_diagnostic.json"
    h = run(out)
    print("wrote", out, "sha256", h)
