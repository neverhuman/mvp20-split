#!/usr/bin/env python3
"""amphora-molecule-generator: attack on molgen-deterministic-grammar-yield-v1's
reported "feasible-fraction 1.0000 (bootstrap 95% CI [1.0000,1.0000])" claim.

CLAIM UNDER ATTACK: the signed receipt
`evidence/audit/molgen-deterministic-grammar-yield-v1/molgen-deterministic-grammar-yield-receipt.v1.dsse.json`
reports `feasible_fraction_over_hardeners=1.0` with `feasible_fraction_bootstrap95_ci=[1.0,1.0]`
over n=38 difunctional-hardener proposals, all 38 of which pass SA<6. The
module's own mission.md KPI register requires "calibrated intervals ... for
empirical claims" (Efron 1979 bootstrap, cited by that receipt as the
uncertainty-quantification method).

ATTACK: a percentile bootstrap resampled WITH REPLACEMENT from a sample where
every observed value is identical (here: all 38 values = 1, i.e. "feasible")
is mathematically guaranteed to return exactly that same degenerate point
for every possible seed, B, and even up-sampled resample size, REGARDLESS of
the true sample size n. It carries ZERO information about the sampling
uncertainty of the true population feasible fraction and is not a valid
calibrated interval at a boundary (k=n or k=0). The correct interval for a
successes/n binomial proportion is the exact Clopper & Pearson (1934,
Biometrika 26(4):404-413) interval, which for k=n=38 is NOT [1,1] but
[0.9075, 1.0000] at 95% two-sided confidence -- meaning the data are fully
consistent with a true feasibility rate as low as ~90.7%, not "100% with
95% confidence" as the reported CI implies.

FALSIFICATION CRITERION (declared up front): the reported bootstrap CI is
INADMISSIBLE (attack succeeds / CLAIM_REFUTED) if the exact Clopper-Pearson
lower bound at the same (k=38, n=38) differs from the reported bootstrap
lower bound (1.0000) by more than 0.02 (2 percentage points) -- a gap that
size means the reported interval materially overstates certainty relative
to the accepted exact-binomial standard. The attack would FAIL (CLAIM_SURVIVES)
if the CP lower bound came out within 0.02 of 1.0000, or if the bootstrap
degeneracy could not be reproduced independent of seed/B/resample-size.

Also demonstrates: (a) the degeneracy is structural, not a seed artifact --
independently reproduced across 5 distinct seeds, 3 different B, and 3
different resample sizes, always exactly [1,1]; (b) the same bootstrap
routine IS locally well-behaved (non-degenerate) one observation off the
boundary (k=37/n=38), proving the failure is specific to the boundary the
receipt happens to land on, not a general bootstrap-implementation bug.

Usage: run_molgen_ci_admissibility.py <out.json>
"""
import json
import random
import statistics
import sys

from scipy.stats import beta

ROOT = "/home/ubuntu/amphora/build/mvp20-split"
MODDIR = f"{ROOT}/amphora-molecule-generator"
TARGET_DIAG = f"{MODDIR}/evidence/audit/molgen-deterministic-grammar-yield-v1/diagnostic.canonical.json"
TARGET_RECEIPT = (f"{MODDIR}/evidence/audit/molgen-deterministic-grammar-yield-v1/"
                   "molgen-deterministic-grammar-yield-receipt.v1.dsse.json")

GAP_INADMISSIBLE_THRESHOLD = 0.02  # 2 percentage points, declared a priori


def q(vals, frac):
    s = sorted(vals)
    if len(s) == 1:
        return s[0]
    pos = frac * (len(s) - 1)
    lo = int(pos)
    hi = min(lo + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (pos - lo)


def bootstrap_ci(values, statfn, seed, B, lo=2.5, hi=97.5):
    rng = random.Random(seed)
    n = len(values)
    stats = []
    for _ in range(B):
        sample = [values[rng.randrange(n)] for _ in range(n)]
        stats.append(statfn(sample))
    return q(stats, lo / 100.0), q(stats, hi / 100.0)


def clopper_pearson(k, n, alpha=0.05):
    if k == 0:
        lo = 0.0
    else:
        lo = beta.ppf(alpha / 2, k, n - k + 1)
    if k == n:
        hi = 1.0
    else:
        hi = beta.ppf(1 - alpha / 2, k + 1, n - k)
    return float(lo), float(hi)


def main(outpath):
    with open(TARGET_DIAG) as fh:
        target_diag = json.load(fh)
    gg = target_diag["generator_grammar"]
    n_hardeners = gg["difunctional_hardener_universe"]
    feas_frac_reported = gg["feasible_fraction_over_hardeners"]
    reported_ci = tuple(gg["feasible_fraction_bootstrap95_ci"])
    boot_seed_reported = gg["bootstrap_seed"]
    boot_B_reported = gg["bootstrap_resamples"]

    k_feasible = round(feas_frac_reported * n_hardeners)
    assert k_feasible == n_hardeners, (
        "attack pinned to the k==n boundary case actually present in the "
        f"target receipt; got k={k_feasible} n={n_hardeners}")
    feas_flags = [1] * n_hardeners  # exact reconstruction: all-feasible, per target diagnostic

    # === 1. reproduce the target receipt's own bootstrap exactly ============
    reproduced_ci = bootstrap_ci(feas_flags, lambda s: sum(s) / len(s),
                                  boot_seed_reported, boot_B_reported)
    reproduction_matches_receipt = (
        round(reproduced_ci[0], 4) == round(reported_ci[0], 4)
        and round(reproduced_ci[1], 4) == round(reported_ci[1], 4))

    # === 2. structural-degeneracy sweep: seed x B x resample-size ===========
    seeds = [11, 22, 20260728, 999983, 424242]
    Bs = [200, 2000, 10000]
    resample_sizes = [n_hardeners, 100, 1000]
    degeneracy_grid = []
    all_degenerate = True
    for sd in seeds:
        for B in Bs:
            for rs in resample_sizes:
                rng = random.Random(sd)
                stats = []
                for _ in range(B):
                    sample = [feas_flags[rng.randrange(n_hardeners)] for _ in range(rs)]
                    stats.append(sum(sample) / len(sample))
                lo, hi = q(stats, 0.025), q(stats, 0.975)
                is_degenerate = (lo == 1.0 and hi == 1.0)
                if not is_degenerate:
                    all_degenerate = False
                degeneracy_grid.append({"seed": sd, "B": B, "resample_size": rs,
                                        "ci": [lo, hi], "degenerate": is_degenerate})

    # === 3. control: one step off the boundary (k=n-1) IS well-behaved =====
    off_boundary_flags = [1] * (n_hardeners - 1) + [0]
    off_boundary_ci = bootstrap_ci(off_boundary_flags, lambda s: sum(s) / len(s),
                                    boot_seed_reported, boot_B_reported)
    off_boundary_degenerate = (off_boundary_ci[0] == off_boundary_ci[1])

    # === 4. exact Clopper-Pearson (1934) reference interval =================
    cp_lo, cp_hi = clopper_pearson(k_feasible, n_hardeners)

    # === 5. admissibility verdict ===========================================
    lower_gap = reported_ci[0] - cp_lo  # positive => bootstrap overstates certainty
    inadmissible = lower_gap > GAP_INADMISSIBLE_THRESHOLD

    headline = (
        f"Attack on molgen-deterministic-grammar-yield-v1's reported feasible-fraction "
        f"bootstrap 95% CI [{reported_ci[0]:.4f},{reported_ci[1]:.4f}] over k={k_feasible}/n={n_hardeners} "
        f"(all-feasible boundary): percentile bootstrap at k=n is mathematically degenerate "
        f"({sum(1 for g in degeneracy_grid if g['degenerate'])}/{len(degeneracy_grid)} seed x B x "
        f"resample-size combinations collapse to exactly [1.0000,1.0000], vs 0/1 for the "
        f"k=n-1 off-boundary control); the admissible exact Clopper-Pearson (1934) 95% CI for "
        f"the SAME k/n is [{cp_lo:.4f},{cp_hi:.4f}] -- a {lower_gap:.4f} lower-bound gap "
        f"({'EXCEEDS' if inadmissible else 'within'} the a-priori {GAP_INADMISSIBLE_THRESHOLD} "
        f"admissibility threshold), meaning the data are fully consistent with a true population "
        f"feasible rate as low as {cp_lo:.4f} rather than the "
        f"100%-certain reading implied by the reported interval. "
        f"VERDICT: {'CLAIM_REFUTED (reported CI is statistically inadmissible)' if inadmissible else 'CLAIM_SURVIVED'}."
    )

    diag = {
        "study_id": "molgen-grammar-yield-bootstrap-ci-inadmissibility-v1",
        "schema": "amphora.molecule-generator.grammar-yield-ci-inadmissibility-diagnostic.v1",
        "purpose": (
            "Falsification attack on the calibrated-interval component of "
            "molgen-deterministic-grammar-yield-v1's headline feasible-fraction claim: "
            "test whether its reported bootstrap 95% CI is an admissible confidence "
            "interval at the k=n boundary it lands on."),
        "attacked_claim": {
            "receipt": ("amphora-molecule-generator/evidence/audit/"
                        "molgen-deterministic-grammar-yield-v1/"
                        "molgen-deterministic-grammar-yield-receipt.v1.dsse.json"),
            "field": "generator_grammar.feasible_fraction_bootstrap95_ci",
            "reported_point_estimate": feas_frac_reported,
            "reported_ci": list(reported_ci),
            "reported_n": n_hardeners,
            "reported_k": k_feasible,
            "reported_bootstrap_seed": boot_seed_reported,
            "reported_bootstrap_B": boot_B_reported,
        },
        "headline": headline,
        "theory_reference": {
            "bootstrap": "Efron 1979 Ann. Statist. 7(1):1-26 (percentile bootstrap, cited by target receipt)",
            "exact_binomial_interval": "Clopper & Pearson 1934 Biometrika 26(4):404-413",
            "boundary_bootstrap_failure": (
                "Efron & Tibshirani 1993 'An Introduction to the Bootstrap' Ch. 13 notes "
                "percentile-bootstrap unreliability at parameter boundaries; a sample with "
                "zero within-sample variance (all-identical observations) resamples to the "
                "same statistic with probability 1, independent of true n."),
        },
        "falsification_criterion": {
            "declared_a_priori": True,
            "rule": ("CLAIM_REFUTED if reported_bootstrap_lower - clopper_pearson_lower > "
                     f"{GAP_INADMISSIBLE_THRESHOLD}"),
            "gap_threshold": GAP_INADMISSIBLE_THRESHOLD,
        },
        "reproduction_of_target_bootstrap": {
            "reproduced_ci": [round(reproduced_ci[0], 6), round(reproduced_ci[1], 6)],
            "matches_receipt_reported_ci": bool(reproduction_matches_receipt),
        },
        "degeneracy_sweep": {
            "n_combinations": len(degeneracy_grid),
            "n_degenerate": sum(1 for g in degeneracy_grid if g["degenerate"]),
            "all_degenerate": bool(all_degenerate),
            "seeds_tested": seeds,
            "B_values_tested": Bs,
            "resample_sizes_tested": resample_sizes,
            "grid": degeneracy_grid,
        },
        "off_boundary_control": {
            "description": "same bootstrap routine at k=n-1=37/n=38 (one simulated infeasible)",
            "k": n_hardeners - 1,
            "n": n_hardeners,
            "ci": [round(off_boundary_ci[0], 6), round(off_boundary_ci[1], 6)],
            "degenerate": bool(off_boundary_degenerate),
            "interpretation": (
                "Non-degenerate off-boundary CI confirms the bootstrap routine itself is "
                "correctly implemented; degeneracy is specific to the k=n boundary the "
                "target receipt happens to occupy, not a general implementation defect."),
        },
        "clopper_pearson_reference": {
            "k": k_feasible,
            "n": n_hardeners,
            "alpha": 0.05,
            "lower": round(cp_lo, 6),
            "upper": round(cp_hi, 6),
            "lower_gap_vs_reported_bootstrap": round(lower_gap, 6),
        },
        "admissibility_verdict": {
            "inadmissible": bool(inadmissible),
            "verdict": "CLAIM_REFUTED" if inadmissible else "CLAIM_SURVIVED",
            "interpretation": (
                "The reported bootstrap 95% CI [1.0000,1.0000] materially understates "
                "sampling uncertainty at this sample size: the data are consistent with a "
                "true population feasible fraction as low as "
                f"{cp_lo:.4f} at 95% confidence under the accepted exact-binomial standard, "
                "not the ~100%-certainty reading a naive reader takes from the reported "
                "interval. This does not dispute that all 38 OBSERVED productions pass SA<6 "
                "(a deterministic fact); it disputes the CALIBRATED-INTERVAL claim mission.md "
                "requires for empirical KPIs, which mission.md and the target receipt's own "
                "cited theory (Efron 1979) explicitly demand."
                if inadmissible else
                "Reported CI was within the a-priori admissibility threshold of the exact "
                "Clopper-Pearson reference; attack failed to refute."
            ),
        },
        "does_not_close": [
            "Does not dispute the deterministic fact that all 38 currently-enumerated "
            "grammar productions individually pass SA<6 -- that observation stands.",
            "Does not modify, supersede, or invalidate the underlying "
            "molgen-deterministic-grammar-yield-v1 receipt; this is an independent "
            "AUDIT_ONLY companion finding.",
            "Does not claim the true feasible fraction IS below 90.7%; only that the "
            "reported interval cannot rule that out and should not have been presented "
            "as [1.0000,1.0000].",
            "AUDIT_ONLY: module runtime stays LOCKED_INTERNAL; no proposals emitted; no "
            "Phase-0 promotion; scientific_readiness stays UNVALIDATED.",
        ],
        "rights_posture": (
            "No new dataset consumed; operates only on the already-checked-in "
            "diagnostic.canonical.json from molgen-deterministic-grammar-yield-v1 and "
            "public statistical theory (Clopper & Pearson 1934, Efron 1979). Manifest "
            "(66 receipts / 11 modules) untouched; no locked dataset or signed Phase-0 "
            "KPI modified."),
    }

    with open(outpath, "w") as fh:
        fh.write(json.dumps(diag, indent=2, sort_keys=True))
    print("WROTE", outpath)
    print("reported_ci", reported_ci, "reproduced_ci", reproduced_ci,
          "matches", reproduction_matches_receipt)
    print("cp_lo", round(cp_lo, 6), "cp_hi", round(cp_hi, 6))
    print("lower_gap", round(lower_gap, 6), "inadmissible", inadmissible)
    print("all_degenerate_in_sweep", all_degenerate)
    print("off_boundary_degenerate", off_boundary_degenerate)


if __name__ == "__main__":
    main(sys.argv[1])
