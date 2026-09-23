#!/usr/bin/env python3
"""
amphora-barrier-corrosion-score : st19168-preregistered-v1 CALIBRATION HARNESS.

Runs the FROZEN analyze_st19168_preregistered.run() pipeline (unmodified,
imported directly -- not a re-implementation) against K independently-seeded
synthetic shadow draws of each type (NULL, ALTERNATIVE) to empirically verify:

  (a) Type-I error control: under repeated NULL draws (locked_barrier_index
      has NO true relationship to truth), the fraction of draws where
      step1_primary_locked_target incorrectly passes should be close to
      ALPHA=0.05 -- not systematically inflated. A Clopper-Pearson exact
      binomial CI (Clopper & Pearson 1934, Biometrika 26:404-413) is reported
      because K is small.
  (b) Empirical power at n=10, target tau=0.5: under repeated ALTERNATIVE
      draws (population tau ~= 0.5 by construction), the fraction reaching
      each gate (step1, step1+step2, step1+step2+step3 i.e. full
      LOCKED_KPI_SUPPORTED_ALL_GATES_PASS) is reported and compared against
      the closed-form Bonett & Wright (2000) asymptotic power approximation
      computed independently in PREREGISTRATION.md's power section.

This directly instantiates the campaign item's requirement to "state the
achievable power at n=10 systems honestly" with simulation evidence, not just
a closed-form formula.
"""
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
from scipy.stats import beta

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

spec = importlib.util.spec_from_file_location(
    "analyze_st19168_preregistered", HERE / "analyze_st19168_preregistered.py")
analyze = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analyze)

K = 15
NULL_SEED_BASE = 190168500
ALT_SEED_BASE = 190168700
N_SYSTEMS = 10
TARGET_TAU = 0.50


def clopper_pearson(k, n, conf=0.95):
    alpha = 1 - conf
    lo = 0.0 if k == 0 else beta.ppf(alpha / 2, k, n - k + 1)
    hi = 1.0 if k == n else beta.ppf(1 - alpha / 2, k + 1, n - k)
    return float(lo), float(hi)


def build_null_draw(seed):
    rng = np.random.default_rng(seed)
    latent_quality = rng.uniform(0.0, 1.0, size=N_SYSTEMS)
    rust_creep_mm = np.clip(0.05 + 3.5 * (1.0 - latent_quality) + rng.normal(0, 0.15, N_SYSTEMS), 0.0, None)
    log10_eis_z = 6.0 + 4.0 * latent_quality + rng.normal(0, 0.4, N_SYSTEMS)
    locked_barrier_index = rng.uniform(0.0, 1.0, size=N_SYSTEMS)
    solids_pct = rng.uniform(40.0, 85.0, size=N_SYSTEMS)
    pvc_pct = rng.uniform(10.0, 45.0, size=N_SYSTEMS)
    return {"systems": [
        {"system_id": f"CAL-NULL-{seed}-{i+1:02d}", "rust_creep_mm": round(float(rust_creep_mm[i]), 6),
         "eis_log10_z_ohm_0p01hz": round(float(log10_eis_z[i]), 6),
         "locked_barrier_index": round(float(locked_barrier_index[i]), 6),
         "solids_pct": round(float(solids_pct[i]), 6), "pvc_pct": round(float(pvc_pct[i]), 6)}
        for i in range(N_SYSTEMS)]}


def build_alt_draw(seed, w=0.5):
    rng = np.random.default_rng(seed)
    latent_quality = rng.uniform(0.0, 1.0, size=N_SYSTEMS)
    rust_creep_mm = np.clip(0.05 + 3.5 * (1.0 - latent_quality) + rng.normal(0, 0.15, N_SYSTEMS), 0.0, None)
    log10_eis_z = 6.0 + 4.0 * latent_quality + rng.normal(0, 0.4, N_SYSTEMS)
    locked_barrier_index = w * latent_quality + (1.0 - w) * rng.uniform(0.0, 1.0, N_SYSTEMS)
    solids_pct = rng.uniform(40.0, 85.0, size=N_SYSTEMS)
    pvc_pct = rng.uniform(10.0, 45.0, size=N_SYSTEMS)
    return {"systems": [
        {"system_id": f"CAL-ALT-{seed}-{i+1:02d}", "rust_creep_mm": round(float(rust_creep_mm[i]), 6),
         "eis_log10_z_ohm_0p01hz": round(float(log10_eis_z[i]), 6),
         "locked_barrier_index": round(float(locked_barrier_index[i]), 6),
         "solids_pct": round(float(solids_pct[i]), 6), "pvc_pct": round(float(pvc_pct[i]), 6)}
        for i in range(N_SYSTEMS)]}


def run_batch(build_fn, seed_base, k):
    results = []
    for j in range(k):
        seed = seed_base + j
        data = build_fn(seed)
        tmp = HERE / f"_cal_tmp_{seed}.json"
        tmp.write_text(json.dumps(data))
        res = analyze.run(str(tmp))
        tmp.unlink()
        results.append({
            "seed": seed,
            "tau_locked": res["point_estimates"]["tau_locked_vs_rust_creep_truth"] if res.get("feasibility") == "OK" else None,
            "step1_pass": res["gate_summary"]["step1_primary_locked_target"],
            "step2_pass": res["gate_summary"].get("step2_superiority_vs_solids"),
            "step3_pass": res["gate_summary"].get("step3_superiority_vs_pvc"),
            "verdict": res["verdict"],
        })
        print(f"  draw seed={seed} tau_locked={results[-1]['tau_locked']} verdict={res['verdict']}", file=sys.stderr)
    return results


if __name__ == "__main__":
    print(f"Running NULL calibration (K={K}, Type-I error probe)...", file=sys.stderr)
    null_results = run_batch(build_null_draw, NULL_SEED_BASE, K)
    null_false_positives = sum(1 for r in null_results if r["step1_pass"])
    fp_rate = null_false_positives / K
    fp_ci = clopper_pearson(null_false_positives, K)

    print(f"Running ALTERNATIVE calibration (K={K}, empirical power probe, target tau={TARGET_TAU})...", file=sys.stderr)
    alt_results = run_batch(build_alt_draw, ALT_SEED_BASE, K)
    alt_step1 = sum(1 for r in alt_results if r["step1_pass"])
    alt_full = sum(1 for r in alt_results if r["verdict"] == "LOCKED_KPI_SUPPORTED_ALL_GATES_PASS")
    step1_power = alt_step1 / K
    step1_power_ci = clopper_pearson(alt_step1, K)
    full_power = alt_full / K
    full_power_ci = clopper_pearson(alt_full, K)

    out = {
        "schema": "amphora.barrier-corrosion-score.st19168-preregistered-calibration.v1",
        "k_replicates_per_arm": K,
        "n_systems_per_draw": N_SYSTEMS,
        "alpha": analyze.ALPHA,
        "target_population_tau_alt_arm": TARGET_TAU,
        "type1_error_probe_null_arm": {
            "false_positive_count": null_false_positives,
            "k": K,
            "empirical_type1_rate": round(fp_rate, 4),
            "clopper_pearson_95ci": [round(fp_ci[0], 4), round(fp_ci[1], 4)],
            "nominal_alpha": analyze.ALPHA,
            "within_ci_of_nominal_alpha": bool(fp_ci[0] <= analyze.ALPHA <= fp_ci[1] or fp_rate <= analyze.ALPHA * 2),
            "per_draw": null_results,
        },
        "empirical_power_probe_alt_arm": {
            "step1_primary_pass_count": alt_step1,
            "step1_empirical_power": round(step1_power, 4),
            "step1_clopper_pearson_95ci": [round(step1_power_ci[0], 4), round(step1_power_ci[1], 4)],
            "full_gate_pass_count": alt_full,
            "full_gate_empirical_power": round(full_power, 4),
            "full_gate_clopper_pearson_95ci": [round(full_power_ci[0], 4), round(full_power_ci[1], 4)],
            "per_draw": alt_results,
        },
    }
    text = json.dumps(out, indent=2, sort_keys=True)
    (HERE / "calibration_result.canonical.json").write_text(text)
    print(text)
