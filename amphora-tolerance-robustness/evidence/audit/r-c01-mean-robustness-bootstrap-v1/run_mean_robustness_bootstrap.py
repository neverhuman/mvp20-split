#!/usr/bin/env python3
"""
Attack: statistical-robustness audit of the R-C01 'repair' claim.

The R-C01 done receipt (2026-08-11) claims:
    mean(coverage_scaffold_safe_pac_repaired) over the pinned 60-seed
    scaffold-disjoint Monte Carlo protocol >= 0.90 (observed 0.9072572375383322)
and reports this as CLAIM_SURVIVED / repair accepted.

That number is a bare point estimate. The ORIGINAL refutation of the un-repaired
0.9683 claim (repeated-scaffold-monte-carlo-conformal-openpoly-tg-v1, 2026-08-03)
did NOT accept a point estimate -- it computed a bootstrap CI and a fraction-
below-floor test and declared REFUTED because the CI excluded the target.
This script applies the IDENTICAL statistical apparatus (percentile bootstrap
CI on the mean, over the same 60 per-seed draws, plus fraction-of-resamples-
below-threshold) to the ACCEPTED repair's own 60 values, extracted verbatim
from the DSSE-signed done receipt's per_seed_table.

This is a pure re-analysis of already-committed numbers (no new simulation,
no re-fit of any model) -- it cannot be described as re-tuning a hyperparameter
against the outcome. It asks one question: is "0.9073 >= 0.90" a robust finding
or is it statistically indistinguishable from a true mean below the 0.90 floor,
given the observed seed-to-seed variance (std=0.0985, driven by extreme
scaffold-imbalance)?

A positive control is run alongside: the SAME bootstrap procedure applied to
a deliberately-degraded copy of the 60 values (each value multiplied by 0.80,
simulating a materially worse repair) must show a CI that clearly excludes
0.90 from above (i.e. the procedure must be capable of flagging a bad repair
as failing robustness, not just echo whatever point estimate it is given).
"""
import json
import base64
import hashlib
import sys

import numpy as np

RECEIPT_PATH = "amphora-tolerance-robustness/evidence/phase0/repairs/R-C01/done/r-c01-pac-corrected-scaffold-repair-done-receipt.v1.dsse.json"
THRESHOLD = 0.90
N_BOOT = 100000
SEED = 1729  # fixed for two-replay byte-stability; not a wall-clock RNG

def load_values(path):
    d = json.load(open(path))
    payload = json.loads(base64.b64decode(d["signature"]["payload"]))
    tbl = payload["per_seed_table"]
    vals = np.array([r["coverage_scaffold_safe_pac_repaired"] for r in tbl], dtype=float)
    assert len(vals) == 60, f"expected 60 seeds, got {len(vals)}"
    reported_mean = payload["acceptance_criterion"]["observed_mean"]
    assert abs(vals.mean() - reported_mean) < 1e-9, (
        f"re-extracted mean {vals.mean()!r} does not match receipt's reported "
        f"observed_mean {reported_mean!r}"
    )
    return vals, payload


def bootstrap_mean_ci(vals, n_boot, threshold, rng):
    n = len(vals)
    boot_means = np.empty(n_boot, dtype=float)
    for i in range(n_boot):
        sample = rng.choice(vals, size=n, replace=True)
        boot_means[i] = sample.mean()
    lo, hi = np.percentile(boot_means, [2.5, 97.5])
    frac_below = float(np.mean(boot_means < threshold))
    return {
        "point_estimate_mean": float(vals.mean()),
        "std": float(vals.std(ddof=1)),
        "se_normal_approx": float(vals.std(ddof=1) / np.sqrt(n)),
        "ci95_normal_approx": [
            float(vals.mean() - 1.96 * vals.std(ddof=1) / np.sqrt(n)),
            float(vals.mean() + 1.96 * vals.std(ddof=1) / np.sqrt(n)),
        ],
        "ci95_bootstrap_percentile": [float(lo), float(hi)],
        "n_boot": n_boot,
        "frac_bootstrap_resamples_below_threshold": frac_below,
        "ci_lower_excludes_threshold_from_below": bool(lo >= threshold),
    }


def main():
    vals, payload = load_values(RECEIPT_PATH)

    rng_real = np.random.default_rng(SEED)
    real_result = bootstrap_mean_ci(vals, N_BOOT, THRESHOLD, rng_real)

    # Positive control: deliberately degrade the repair (simulate a materially
    # worse fix) and confirm the SAME procedure correctly flags it as failing
    # robustness (CI clearly excludes 0.90 from above / large frac_below).
    degraded_vals = np.clip(vals * 0.80, 0.0, 1.0)
    rng_ctrl = np.random.default_rng(SEED + 1)
    control_result = bootstrap_mean_ci(degraded_vals, N_BOOT, THRESHOLD, rng_ctrl)

    verdict = "ROBUST" if real_result["ci_lower_excludes_threshold_from_below"] else "NOT_ROBUST_CI_STRADDLES_THRESHOLD"

    out = {
        "attack": "bootstrap-mean-robustness-audit-r-c01",
        "input_receipt": RECEIPT_PATH,
        "input_receipt_claim": payload["claim_under_attack"],
        "input_receipt_reported_verdict": payload["verdict"],
        "threshold": THRESHOLD,
        "n_seeds": len(vals),
        "seed_rng": SEED,
        "real": real_result,
        "positive_control": {
            "planted_defect": "each of the 60 real coverage_scaffold_safe_pac_repaired values multiplied by 0.80 (simulating a materially degraded repair), clipped to [0,1]",
            "how_planted": "vals * 0.80 applied elementwise to the exact 60 values extracted from the receipt's per_seed_table before bootstrapping",
            "result": control_result,
            "detected": bool(control_result["ci95_bootstrap_percentile"][1] < THRESHOLD),
            "evidence": f"degraded mean={control_result['point_estimate_mean']:.4f}, 95% bootstrap CI={control_result['ci95_bootstrap_percentile']}, frac_below_threshold={control_result['frac_bootstrap_resamples_below_threshold']:.4f}",
        },
        "verdict_on_real_claim": verdict,
    }
    print(json.dumps(out, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
