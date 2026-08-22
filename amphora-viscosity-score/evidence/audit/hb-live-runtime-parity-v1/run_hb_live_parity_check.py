#!/usr/bin/env python3
"""amphora-viscosity-score -- HB live-runtime parity falsification probe.

CLAIM UNDER ATTACK: evidence/phase0/kpis/herschel-bulkley-ccby-amorim2021-kpi.v1.json
(promoted 2026-08-04, re-verified 2026-08-14) -- "Herschel-Bulkley yield-flow path
(src/lib.rs:1227) evaluated at published fitted parameters". Every prior fire computed
this comparison with a Python "verbatim re-derivation" of the formula
(run_hb_benchmark.py) and never called the compiled Rust primitive. This probe closes
that gap: it diffs the live compiled-Rust output (examples/hb_live_runtime_parity_probe.rs,
cargo run --example) against the disclosed Python re-derivation, at machine-precision
tolerance, for all 6 formulations x 4 shear rates, plus a guard-rail edge-case battery.

REFUTATION CRITERION: would REFUTE the "re-derivation matches src/lib.rs:1227 verbatim"
claim if ANY (row, shear_rate) pair shows |rust - python| / |rust| > 1e-9, OR if ANY
guard-rail edge case shows the live Rust Ok/Err outcome disagreeing with the Python
oracle's raise/no-raise outcome. SURVIVES if all pairs match within tolerance and all
edge cases agree.

POSITIVE CONTROL: a mutant Python oracle (flow_index_n instead of flow_index_n - 1.0 in
the exponent -- exactly the class of re-derivation defect this parity check exists to
catch) is compared against the SAME live-Rust values. This must show large deviations
proving the check is capable of detecting a genuine implementation-drift defect.

Deterministic: pure arithmetic on committed constants, no RNG, no network.
"""
import json
import hashlib
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIVE_RUST_PATH = HERE / "hb_live_runA.json"
SOURCE_LOCK_PATH = HERE.parent / "herschel-bulkley-ccby-amorim2021-v1" / "source_amorim2021_hb_table2.v1.json"

TOLERANCE_REL = 1e-9


def sha256_of(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def herschel_bulkley_python_oracle(tau0, K, n, gamma_dot):
    """Verbatim re-derivation, identical in form to
    evidence/audit/herschel-bulkley-ccby-amorim2021-v1/run_hb_benchmark.py's
    herschel_bulkley_apparent_viscosity, matching src/lib.rs:1227-1243."""
    if not (tau0 == tau0) or tau0 < 0.0:
        raise ValueError("tau0")
    if not (K > 0.0 and K == K):
        raise ValueError("K")
    if not (n > 0.0 and n == n):
        raise ValueError("n")
    if not (gamma_dot > 0.0 and gamma_dot == gamma_dot):
        raise ValueError("gamma_dot")
    return tau0 / gamma_dot + K * (gamma_dot ** (n - 1.0))


def herschel_bulkley_mutant_oracle(tau0, K, n, gamma_dot):
    """PLANTED DEFECT for the positive control: exponent uses n instead of (n - 1.0),
    the same class of re-derivation-drift bug (wrong exponent term) this parity check
    exists to catch. All other guard logic identical."""
    if not (tau0 == tau0) or tau0 < 0.0:
        raise ValueError("tau0")
    if not (K > 0.0 and K == K):
        raise ValueError("K")
    if not (n > 0.0 and n == n):
        raise ValueError("n")
    if not (gamma_dot > 0.0 and gamma_dot == gamma_dot):
        raise ValueError("gamma_dot")
    return tau0 / gamma_dot + K * (gamma_dot ** n)  # BUG: should be (n - 1.0)


def run():
    live = json.loads(LIVE_RUST_PATH.read_bytes())
    live_sha256 = sha256_of(LIVE_RUST_PATH)
    source_lock_sha256 = sha256_of(SOURCE_LOCK_PATH)

    # --- Real attack: live Rust vs disclosed Python re-derivation ---
    row_results = []
    max_rel_diff = 0.0
    all_within_tolerance = True
    for row in live["rows"]:
        tau0 = row["tau0_pa_corrected"]
        K = row["K_pa_sn_corrected"]
        n = row["n"]
        curve_out = []
        for pt in row["curve"]:
            g = pt["shear_rate_s_inv"]
            rust_v = pt["eta_apparent_pa_s_live_rust"]
            py_v = herschel_bulkley_python_oracle(tau0, K, n, g)
            rel_diff = abs(rust_v - py_v) / abs(rust_v) if rust_v != 0 else abs(rust_v - py_v)
            max_rel_diff = max(max_rel_diff, rel_diff)
            within = rel_diff <= TOLERANCE_REL
            all_within_tolerance = all_within_tolerance and within
            curve_out.append({
                "shear_rate_s_inv": g,
                "rust_live": rust_v,
                "python_oracle": py_v,
                "rel_diff": rel_diff,
                "within_tolerance": within,
            })
        row_results.append({"sample": row["sample"], "tau0": tau0, "K": K, "n": n, "curve": curve_out})

    # --- Guard-rail edge case parity ---
    edge_results = []
    all_edge_cases_agree = True
    for ec in live["edge_case_guard_battery"]:
        t0, K, n, g = ec["tau0"], ec["K"], ec["n"], ec["gamma_dot"]
        rust_is_ok = ec["is_ok"]
        if t0 is None:
            # serde_json serializes non-finite f64 (NaN/Infinity) as JSON null, so the
            # exact bit-pattern can't be recovered from the live-Rust output; reconstruct
            # the INTENDED input from the case label (both cases were constructed with a
            # specific non-finite tau0 -- see hb_live_runtime_parity_probe.rs) and feed
            # that exact value to the Python oracle, so its guard is genuinely exercised
            # rather than assumed.
            if ec["case"] == "nan_yield_stress":
                t0 = float("nan")
            elif ec["case"] == "infinite_yield_stress":
                t0 = float("inf")
            else:
                raise AssertionError(f"unexpected null tau0 for case {ec['case']}")
        try:
            herschel_bulkley_python_oracle(t0, K, n, g)
            py_is_ok = True
        except ValueError:
            py_is_ok = False
        agree = (rust_is_ok == py_is_ok)
        all_edge_cases_agree = all_edge_cases_agree and agree
        edge_results.append({
            "case": ec["case"], "rust_is_ok": rust_is_ok, "python_oracle_is_ok": py_is_ok, "agree": agree,
        })

    real_attack_fired = (not all_within_tolerance) or (not all_edge_cases_agree)

    # --- Positive control: mutant oracle vs the SAME live-Rust values ---
    mutant_max_rel_diff = 0.0
    mutant_any_breach = False
    mutant_example = None
    for row in live["rows"]:
        tau0 = row["tau0_pa_corrected"]
        K = row["K_pa_sn_corrected"]
        n = row["n"]
        for pt in row["curve"]:
            g = pt["shear_rate_s_inv"]
            rust_v = pt["eta_apparent_pa_s_live_rust"]
            mutant_v = herschel_bulkley_mutant_oracle(tau0, K, n, g)
            rel_diff = abs(rust_v - mutant_v) / abs(rust_v) if rust_v != 0 else abs(rust_v - mutant_v)
            if rel_diff > mutant_max_rel_diff:
                mutant_max_rel_diff = rel_diff
                mutant_example = {
                    "sample": row["sample"], "shear_rate_s_inv": g,
                    "rust_live": rust_v, "mutant_python_oracle": mutant_v, "rel_diff": rel_diff,
                }
            if rel_diff > TOLERANCE_REL:
                mutant_any_breach = True

    diagnostic = {
        "schema": "amphora.viscosity-score.hb-live-runtime-parity-check-diagnostic.v1",
        "module": "amphora-viscosity-score",
        "claim_under_attack": "evidence/phase0/kpis/herschel-bulkley-ccby-amorim2021-kpi.v1.json :: HERSCHEL_BULKLEY (src/lib.rs:1227) benchmark numbers reflect the compiled primitive, not merely a disclosed Python re-derivation",
        "live_rust_diagnostic_sha256": live_sha256,
        "source_lock_sha256": source_lock_sha256,
        "tolerance_rel": TOLERANCE_REL,
        "row_results": row_results,
        "edge_case_results": edge_results,
        "max_rel_diff_real_attack": max_rel_diff,
        "all_within_tolerance_real_attack": all_within_tolerance,
        "all_edge_cases_agree_real_attack": all_edge_cases_agree,
        "real_attack_fired": real_attack_fired,
        "verdict": "CLAIM_REFUTED" if real_attack_fired else "CLAIM_SURVIVED",
        "positive_control": {
            "planted_defect": "mutant Python oracle uses gamma_dot**n instead of gamma_dot**(n-1) in the Herschel-Bulkley consistency term -- a wrong-exponent re-derivation bug, the exact class of drift this parity check exists to catch",
            "how_planted": "herschel_bulkley_mutant_oracle() in this script: K * (gamma_dot ** n) replaces K * (gamma_dot ** (n - 1.0)); all guard logic and inputs otherwise identical to the real oracle and to the live-Rust call",
            "detected": mutant_any_breach,
            "evidence": mutant_example,
            "mutant_max_rel_diff": mutant_max_rel_diff,
        },
    }
    return diagnostic


if __name__ == "__main__":
    import sys
    out = run()
    text = json.dumps(out, indent=2, sort_keys=True)
    if len(sys.argv) > 1:
        Path(sys.argv[1]).write_text(text)
    else:
        print(text)
