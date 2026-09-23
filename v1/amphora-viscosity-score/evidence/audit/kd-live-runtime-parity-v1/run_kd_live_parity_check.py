#!/usr/bin/env python3
"""
amphora-viscosity-score :: kd-live-runtime-parity-v1 comparator.

Falsification target (see examples/kd_live_runtime_parity_probe.rs docstring for the full
citation chain): the claim, inherited unchanged across every prior KD fire (C9 fire1/2,
W-VISC1, W-VISC2), that the Python `kd_vec` re-derivation used in every promoted KD
benchmark/receipt is "replicated verbatim from src/lib.rs:1208-1224" -- i.e. including the
four guard/validity clauses at src/lib.rs:1211-1218, not just the closed-form output line.

This comparator:
  1. Loads the live-Rust diagnostic (kd_live_runA.json), produced by calling the actual
     compiled `krieger_dougherty` primitive (not a reimplementation).
  2. Re-derives the SAME "verbatim" Python oracle used across every prior KD fire
     (kd_vec = eta_liq * (1 - phi/phi_max) ** (-eta_intr * phi_max), copied byte-for-byte
     from run_kd_ccby_reachability_probe.py / run_kd_positive_control.py) -- with NO guard
     logic added, because the point is to test whether the ALREADY-PROMOTED oracle (as
     literally written in those files) is what it claims to be.
  3. Diffs numeric fitted-curve points at 1e-9 relative tolerance (arithmetic-path check).
  4. Diffs Ok/Err agreement on the 10-case guard-rail battery (validity-path check).
  5. Runs a positive control: a mutant oracle with a wrong-exponent defect
     (-eta_intr * phi instead of -eta_intr * phi_max), of the same re-derivation-drift class
     this parity check exists to catch, and confirms it is detected.
"""
import json
import math
import sys
from pathlib import Path

EV = Path(__file__).resolve().parent
MOD = EV.parent.parent.parent

REL_TOL = 1e-9


def kd_vec_oracle(eta_liq, phi, phi_max, eta_intr):
    """Byte-for-byte copy of kd_vec from run_kd_ccby_reachability_probe.py /
    run_kd_positive_control.py -- the SAME, already-promoted oracle, no guard added."""
    return eta_liq * (1 - phi / phi_max) ** (-eta_intr * phi_max)


def kd_vec_mutant_wrong_exponent(eta_liq, phi, phi_max, eta_intr):
    """Positive-control defect: uses -eta_intr * phi instead of -eta_intr * phi_max --
    a wrong-exponent re-derivation bug, the same class of implementation-drift defect
    this parity check exists to catch."""
    return eta_liq * (1 - phi / phi_max) ** (-eta_intr * phi)


def try_oracle(fn, eta_liq, phi, phi_max, eta_intr):
    """Run a scalar KD oracle call, catching the exceptions CPython's ** can raise
    (ZeroDivisionError for 0.0**negative) and classifying complex/nan/inf results, since
    the promoted oracle has no guard and none of these are treated as failure by Python."""
    try:
        v = fn(eta_liq, phi, phi_max, eta_intr)
    except Exception as e:
        return {"python_raised": True, "exception": type(e).__name__, "value": None, "value_kind": None}
    if isinstance(v, complex):
        return {"python_raised": False, "exception": None, "value": None, "value_kind": "complex", "complex_repr": repr(v)}
    if isinstance(v, float) and math.isnan(v):
        return {"python_raised": False, "exception": None, "value": None, "value_kind": "nan"}
    if isinstance(v, float) and math.isinf(v):
        return {"python_raised": False, "exception": None, "value": None, "value_kind": "inf"}
    return {"python_raised": False, "exception": None, "value": float(v), "value_kind": "finite_real"}


def rel_diff(a, b):
    denom = max(abs(a), abs(b), 1e-300)
    return abs(a - b) / denom


def run(live_rust_path, out_path):
    live = json.loads(Path(live_rust_path).read_text())

    numeric_checks = []
    max_rel_diff = 0.0
    for fit in live["fits"]:
        eta_liq = fit["eta_liquid_pa_s"]
        phi_max = fit["phi_max"]
        eta_intr = fit["intrinsic_viscosity"]
        for pt in fit["curve"]:
            phi = pt["phi"]
            rust_v = pt["eta_pa_s_live_rust"]
            py_v = kd_vec_oracle(eta_liq, phi, phi_max, eta_intr)
            d = rel_diff(rust_v, py_v)
            max_rel_diff = max(max_rel_diff, d)
            numeric_checks.append({
                "fit_label": fit["fit_label"], "phi": phi,
                "rust_value": rust_v, "python_oracle_value": py_v,
                "rel_diff": d, "within_tolerance": d <= REL_TOL,
            })

    guard_checks = []
    guard_all_agree = True
    for case in live["edge_case_guard_battery"]:
        eta_liq, phi, phi_max, eta_intr = case["eta_liquid_pa_s"], case["phi"], case["phi_max"], case["intrinsic_viscosity"]
        rust_is_ok = case["is_ok"]
        if phi is None:
            phi = float("nan")
        py = try_oracle(kd_vec_oracle, eta_liq, phi, phi_max, eta_intr)
        python_is_ok_and_sane = (not py["python_raised"]) and py["value_kind"] == "finite_real"
        agrees = (rust_is_ok == python_is_ok_and_sane)
        if not agrees:
            guard_all_agree = False
        guard_checks.append({
            "case": case["case"],
            "eta_liquid_pa_s": eta_liq, "phi": phi if phi == phi else "NaN", "phi_max": phi_max, "intrinsic_viscosity": eta_intr,
            "rust_is_ok": rust_is_ok,
            "python_oracle_outcome": py,
            "python_is_ok_and_sane": python_is_ok_and_sane,
            "agrees_with_rust": agrees,
        })

    numeric_all_within_tolerance = all(c["within_tolerance"] for c in numeric_checks)
    refuted = (not numeric_all_within_tolerance) or (not guard_all_agree)

    # Positive control: run the SAME comparator apparatus against a mutant oracle with a
    # planted wrong-exponent defect, using the same live-Rust numeric points as ground truth.
    mutant_checks = []
    mutant_max_rel_diff = 0.0
    for fit in live["fits"]:
        eta_liq = fit["eta_liquid_pa_s"]
        phi_max = fit["phi_max"]
        eta_intr = fit["intrinsic_viscosity"]
        for pt in fit["curve"]:
            phi = pt["phi"]
            rust_v = pt["eta_pa_s_live_rust"]
            mutant_v = kd_vec_mutant_wrong_exponent(eta_liq, phi, phi_max, eta_intr)
            d = rel_diff(rust_v, mutant_v)
            mutant_max_rel_diff = max(mutant_max_rel_diff, d)
            mutant_checks.append({"fit_label": fit["fit_label"], "phi": phi, "rust_value": rust_v, "mutant_value": mutant_v, "rel_diff": d})
    mutant_detected = mutant_max_rel_diff > REL_TOL

    out = {
        "schema": "amphora.viscosity-score.kd-live-runtime-parity-comparator-diagnostic.v1",
        "module_id": "amphora-viscosity-score",
        "live_rust_source": str(Path(live_rust_path).name),
        "tolerance_rel": REL_TOL,
        "numeric_parity_checks": numeric_checks,
        "numeric_max_rel_diff": max_rel_diff,
        "numeric_all_within_tolerance": numeric_all_within_tolerance,
        "guard_rail_checks": guard_checks,
        "guard_rail_all_agree": guard_all_agree,
        "guard_rail_agree_count": sum(1 for c in guard_checks if c["agrees_with_rust"]),
        "guard_rail_total_count": len(guard_checks),
        "verdict": "CLAIM_REFUTED" if refuted else "CLAIM_SURVIVED",
        "refutation_criterion": (
            "The 'replicated verbatim from src/lib.rs:1208-1224' claim (covering both the "
            "closed-form arithmetic AND the four guard/validity clauses) would be REFUTED by "
            "observing EITHER (a) any of the 10 (fit, phi) live-Rust numeric points differing "
            "from the Python kd_vec oracle by more than 1e-9 relative, OR (b) any of the 10 "
            "guard-rail edge cases where the live-Rust Ok/Err outcome disagrees with whether the "
            "Python oracle produces a finite real (sane) value vs. raises/produces "
            "nan/inf/complex. It would SURVIVE only if all numeric points matched within "
            "tolerance AND all guard-rail cases agreed."
        ),
        "positive_control": {
            "planted_defect": "mutant Python oracle uses -eta_intr * phi instead of -eta_intr * phi_max in the Krieger-Dougherty exponent -- a wrong-exponent re-derivation bug, the same class of implementation-drift defect this parity check exists to catch",
            "how_planted": "kd_vec_mutant_wrong_exponent() in this comparator: (1 - phi/phi_max) ** (-eta_intr * phi) replaces (1 - phi/phi_max) ** (-eta_intr * phi_max); all other logic identical to the real oracle and to the live-Rust call",
            "detected": mutant_detected,
            "mutant_max_rel_diff": mutant_max_rel_diff,
            "evidence": mutant_checks,
        },
    }
    Path(out_path).write_text(json.dumps(out, indent=2, sort_keys=True))
    return out


if __name__ == "__main__":
    live_path = EV / "kd_live_runA.json"
    out_path = sys.argv[1] if len(sys.argv) > 1 else str(EV / "diagnostic.canonical.json")
    result = run(live_path, out_path)
    print("verdict:", result["verdict"])
    print("numeric_max_rel_diff:", result["numeric_max_rel_diff"])
    print("guard_rail_all_agree:", result["guard_rail_all_agree"], f"({result['guard_rail_agree_count']}/{result['guard_rail_total_count']})")
    print("positive_control_detected:", result["positive_control"]["detected"], "mutant_max_rel_diff:", result["positive_control"]["mutant_max_rel_diff"])
