#!/usr/bin/env python3
"""
amphora-barrier-corrosion-score : st19168-preregistered-v1 FROZEN ANALYSIS SCRIPT.

*** THIS FILE IS THE HASH-LOCKED COMMITMENT. ***
Its SHA-256 (computed by sign_preregistration.py, NOT by this file, to avoid a
self-hashing quine) is recorded in the signed DSSE receipt
`preregistration-receipt.v1.dsse.json` BEFORE ST-19168 rights are cleared and
BEFORE this script is ever run on the real workbook. Any post-unlock execution
against the real ST-19168 extraction can be checked byte-for-byte against that
committed hash: if the bytes differ, the post-hoc run does NOT count as the
pre-registered analysis and must be disclosed as an amendment with a diff.

Full statistical plan: see PREREGISTRATION.md in this directory. Summary:

  Population   : up to 10 ST-19168 coating systems with a matched
                 (EIS |Z| at 0.01 Hz, rust-creep) endpoint pair.
  Truth        : rust_creep_mm (PRIMARY, lower = better barrier);
                 eis_log10_z_ohm_0p01hz reported as a SECONDARY corroborating
                 endpoint, not part of the locked gate.
  Predictors   : locked_barrier_index (the module's live scorer output,
                 metrics.barrier_index); solids_pct and pvc_pct (the two
                 pre-registered hostile nulls, unchanged from
                 benchmarks/barrier-null-char-v1).
  Estimator    : Kendall's tau-b (tie-robust -- material here because
                 rust-creep endpoints in this domain are frequently exactly
                 0). All tau-b / permutation / bootstrap statistics below use
                 ONE vectorized primitive (`batch_tau_b`) whose numerator and
                 tie-correction denominator are both derived from elementwise
                 pairwise sign comparisons, so ties are handled identically
                 (and correctly) everywhere -- point estimate, permutation
                 null, and bootstrap resamples alike.
  Primary test : one-sided exact permutation test of tau(locked, truth) > 0
                 (H0: no rank association). scipy's own exact-method p-value
                 (Kendall & Gibbons 1990, "Rank Correlation Methods", 5th ed.,
                 ISBN 0-19-520837-4) is cross-checked against an independent,
                 from-scratch full-enumeration permutation using
                 `batch_tau_b` -- non-circularity: two independently-coded
                 statistics must agree before the gate is trusted.
  Superiority  : locked vs solids-only and locked vs pvc-only, each via a
                 paired bootstrap of the SAME n systems (Efron & Tibshirani
                 1993, "An Introduction to the Bootstrap", ISBN
                 0-412-04231-2), one-sided p = P(tau_locked - tau_null <= 0),
                 cross-checked by a stricter permutation-based robustness
                 statistic (truth independent of BOTH predictors
                 simultaneously).
  Gatekeeping  : fixed-sequence / hierarchical gatekeeping (Maurer, Hothorn &
                 Lehmacher 1995, Biom. J. 37:829; Bauer, Roehmel, Maurer &
                 Hothorn 1998, Stat. Med. 17:2133) -- Step 2 is only evaluated
                 if Step 1 passes, Step 3 only if Step 2 passes. This mirrors
                 the mission's own compound "AND" criterion and controls the
                 family-wise Type-I error at alpha WITHOUT a Bonferroni power
                 penalty, which n=10 cannot afford.
  alpha        : 0.05, one-sided, for every step.
  n            : target 10; the script accepts and reports honestly on
                 whatever complete-case n the real unlock delivers (n<6
                 auto-fails closed -- see FEASIBILITY_FLOOR below).

Non-circularity / honesty: this script's hostile nulls (solids_pct, pvc_pct)
must be the SAME formulation covariates already locked in
benchmarks/barrier-null-char-v1 -- it does not invent new nulls after seeing
data. locked_barrier_index must come from a live `rtk cargo test` /
candidate-contract run of amphora-barrier-corrosion-score/src/lib.rs against
each system's declared formulation, NOT be re-derived from the truth endpoints
themselves (that would be leakage). This script performs no such re-derivation
-- it only consumes an already-computed locked_barrier_index column.
"""
import argparse
import hashlib
import itertools
import json
import sys
from pathlib import Path

import numpy as np
from scipy.stats import kendalltau

ALPHA = 0.05
LOCKED_TAU_TARGET = 0.50
FEASIBILITY_FLOOR = 6           # below this n, exact/MC inference is not meaningful; fail closed
EXACT_ENUM_MAX_N = 10           # full n! enumeration cap for the from-scratch exact cross-check
MC_NSIM = 200_000
BOOT_NSIM = 100_000
PERM_SEED = 190168100
BOOT_SEED_SOLIDS = 190168200
BOOT_SEED_PVC = 190168300
ROBUST_PERM_SEED_SOLIDS = 190168410
ROBUST_PERM_SEED_PVC = 190168420


def load_systems(path):
    d = json.loads(Path(path).read_bytes())
    systems = d["systems"]
    required = {"system_id", "rust_creep_mm", "eis_log10_z_ohm_0p01hz",
                "locked_barrier_index", "solids_pct", "pvc_pct"}
    for s in systems:
        missing = required - set(s)
        if missing:
            raise ValueError(f"system {s.get('system_id')} missing fields {missing}")
    return systems


def truth_score(systems):
    # higher truth_score = better barrier; rust creep is lower=better so negate
    return np.array([-s["rust_creep_mm"] for s in systems], dtype=float)


# ---------------------------------------------------------------------------
# Single vectorized tau-b primitive used EVERYWHERE below (point estimate,
# permutation nulls, bootstrap resamples). Ties handled identically in all
# call sites because concordance and tie-correction both come from the same
# elementwise pairwise-sign comparison.
# ---------------------------------------------------------------------------
def batch_tau_b(X, Y):
    """X, Y: (B, n) arrays (B may be 1). Returns tau_b: (B,) array."""
    X = np.atleast_2d(X)
    Y = np.atleast_2d(Y)
    n = X.shape[1]
    pi, pj = np.triu_indices(n, k=1)
    xs = np.sign(X[:, pi] - X[:, pj])
    ys = np.sign(Y[:, pi] - Y[:, pj])
    num = (xs * ys).sum(axis=1)
    n0 = n * (n - 1) / 2.0
    n1 = (xs == 0).sum(axis=1)
    n2 = (ys == 0).sum(axis=1)
    denom = np.sqrt((n0 - n1) * (n0 - n2))
    with np.errstate(invalid="ignore", divide="ignore"):
        tau = np.where(denom > 0, num / denom, 0.0)
    return tau


def tau_b_point(x, y):
    return float(batch_tau_b(np.asarray(x)[None, :], np.asarray(y)[None, :])[0])


def all_perm_index_array(n):
    return np.array(list(itertools.permutations(range(n))), dtype=np.int16)


def exact_or_mc_permutation_pvalue(x, truth, seed):
    """Independent from-scratch permutation null for tau_b(x, truth): permute
    the TRUTH labels (x, the predictor, is fixed), recompute tau each time via
    batch_tau_b. Full enumeration for n<=EXACT_ENUM_MAX_N; else Monte Carlo."""
    n = len(truth)
    x = np.asarray(x, dtype=float)
    truth = np.asarray(truth, dtype=float)
    obs_tau = tau_b_point(x, truth)

    if n <= EXACT_ENUM_MAX_N:
        idx_perms = all_perm_index_array(n)
        truth_perm = truth[idx_perms]                    # (n_perms, n)
        x_batch = np.repeat(x[None, :], idx_perms.shape[0], axis=0)
        perm_taus = batch_tau_b(x_batch, truth_perm)
        method, n_eval = "exact_full_enumeration", int(idx_perms.shape[0])
    else:
        rng = np.random.default_rng(seed)
        perm_idx = np.array([rng.permutation(n) for _ in range(MC_NSIM)])
        truth_perm = truth[perm_idx]
        x_batch = np.repeat(x[None, :], MC_NSIM, axis=0)
        perm_taus = batch_tau_b(x_batch, truth_perm)
        method, n_eval = "monte_carlo", MC_NSIM

    ge = int(np.sum(perm_taus >= obs_tau - 1e-12))
    p = (ge + 1) / (n_eval + 1)
    return {
        "observed_tau": round(obs_tau, 6),
        "method": method,
        "n_reference_permutations": n_eval,
        "p_value_one_sided": round(float(p), 8),
    }


def paired_bootstrap_superiority(locked, null_pred, truth, seed):
    n = len(truth)
    locked = np.asarray(locked, dtype=float)
    null_pred = np.asarray(null_pred, dtype=float)
    truth = np.asarray(truth, dtype=float)
    point_delta = tau_b_point(locked, truth) - tau_b_point(null_pred, truth)

    rng = np.random.default_rng(seed)
    resample_idx = rng.integers(0, n, size=(BOOT_NSIM, n))
    locked_rs = locked[resample_idx]
    null_rs = null_pred[resample_idx]
    truth_rs = truth[resample_idx]
    tau_locked_b = batch_tau_b(locked_rs, truth_rs)
    tau_null_b = batch_tau_b(null_rs, truth_rs)
    deltas = tau_locked_b - tau_null_b

    p_one_sided = (int(np.sum(deltas <= 0)) + 1) / (BOOT_NSIM + 1)
    ci_lo, ci_hi = np.percentile(deltas, [2.5, 97.5])
    return {
        "n_bootstrap": BOOT_NSIM,
        "point_estimate_delta_tau": round(point_delta, 6),
        "bootstrap_mean_delta_tau": round(float(np.mean(deltas)), 6),
        "bootstrap_ci_95_delta_tau": [round(float(ci_lo), 6), round(float(ci_hi), 6)],
        "p_value_one_sided_delta_gt_0": round(float(p_one_sided), 8),
    }


def robustness_permutation_superiority(locked, null_pred, truth, seed):
    """Stricter secondary null: truth independent of BOTH predictors
    simultaneously (permute truth once per draw, recompute both taus under
    the SAME permuted truth). More conservative than the bootstrap;
    documented as a cross-check, not a replacement."""
    n = len(truth)
    locked = np.asarray(locked, dtype=float)
    null_pred = np.asarray(null_pred, dtype=float)
    truth = np.asarray(truth, dtype=float)
    obs_delta = tau_b_point(locked, truth) - tau_b_point(null_pred, truth)

    if n <= EXACT_ENUM_MAX_N:
        idx_perms = all_perm_index_array(n)
        truth_perm = truth[idx_perms]
        n_eval = int(idx_perms.shape[0])
        method = "exact_full_enumeration"
    else:
        rng = np.random.default_rng(seed)
        perm_idx = np.array([rng.permutation(n) for _ in range(MC_NSIM)])
        truth_perm = truth[perm_idx]
        n_eval = MC_NSIM
        method = "monte_carlo"

    locked_batch = np.repeat(locked[None, :], n_eval, axis=0)
    null_batch = np.repeat(null_pred[None, :], n_eval, axis=0)
    tau_locked_perm = batch_tau_b(locked_batch, truth_perm)
    tau_null_perm = batch_tau_b(null_batch, truth_perm)
    deltas = tau_locked_perm - tau_null_perm

    ge = int(np.sum(deltas >= obs_delta - 1e-12))
    p = (ge + 1) / (n_eval + 1)
    return {
        "method": method,
        "n_reference_permutations": n_eval,
        "observed_delta_tau": round(float(obs_delta), 6),
        "p_value_one_sided": round(float(p), 8),
    }


def run(input_path):
    systems = load_systems(input_path)
    n = len(systems)
    truth = truth_score(systems)
    locked = np.array([s["locked_barrier_index"] for s in systems], dtype=float)
    solids = np.array([s["solids_pct"] for s in systems], dtype=float)
    pvc = np.array([s["pvc_pct"] for s in systems], dtype=float)
    eis = np.array([s["eis_log10_z_ohm_0p01hz"] for s in systems], dtype=float)

    result = {
        "schema": "amphora.barrier-corrosion-score.st19168-preregistered-analysis-result.v1",
        "module": "amphora-barrier-corrosion-score",
        "n_systems": n,
        "alpha": ALPHA,
        "locked_tau_target": LOCKED_TAU_TARGET,
        "input_system_ids": [s["system_id"] for s in systems],
    }

    if n < FEASIBILITY_FLOOR:
        result["feasibility"] = "FAIL_CLOSED_INSUFFICIENT_N"
        result["verdict"] = "NOT_EVALUABLE"
        result["reason"] = f"n={n} < FEASIBILITY_FLOOR={FEASIBILITY_FLOOR}; no inference attempted."
        return result

    result["feasibility"] = "OK"

    tau_locked = tau_b_point(locked, truth)
    tau_solids = tau_b_point(solids, truth)
    tau_pvc = tau_b_point(pvc, truth)
    tau_locked_eis = tau_b_point(locked, eis)
    _, asym_p_locked = kendalltau(locked, truth, variant="b", method="asymptotic")
    _, asym_p_solids = kendalltau(solids, truth, variant="b", method="asymptotic")
    _, asym_p_pvc = kendalltau(pvc, truth, variant="b", method="asymptotic")

    result["point_estimates"] = {
        "tau_locked_vs_rust_creep_truth": round(tau_locked, 6),
        "tau_solids_only_vs_rust_creep_truth": round(tau_solids, 6),
        "tau_pvc_only_vs_rust_creep_truth": round(tau_pvc, 6),
        "tau_locked_vs_eis_secondary_truth": round(tau_locked_eis, 6),
        "asymptotic_p_locked": round(float(asym_p_locked), 8),
        "asymptotic_p_solids": round(float(asym_p_solids), 8),
        "asymptotic_p_pvc": round(float(asym_p_pvc), 8),
    }

    try:
        _, scipy_exact_p = kendalltau(locked, truth, variant="b", method="exact", alternative="greater")
        scipy_exact_p = float(scipy_exact_p)
    except Exception as e:
        scipy_exact_p = None
        result["scipy_exact_method_error"] = str(e)

    fromscratch = exact_or_mc_permutation_pvalue(locked, truth, PERM_SEED)

    result["primary_test_step1"] = {
        "hypothesis": "tau(locked_barrier_index, -rust_creep_mm) > 0, one-sided, AND observed tau >= 0.50",
        "observed_tau": round(tau_locked, 6),
        "meets_magnitude_target_tau_ge_0p50": bool(tau_locked >= LOCKED_TAU_TARGET),
        "scipy_exact_p_value_one_sided": round(scipy_exact_p, 8) if scipy_exact_p is not None else None,
        "fromscratch_independent_permutation": fromscratch,
        "cross_check_agreement": bool(
            scipy_exact_p is not None and abs(scipy_exact_p - fromscratch["p_value_one_sided"]) < 0.02
        ),
    }
    step1_significant = bool(scipy_exact_p is not None and scipy_exact_p < ALPHA)
    step1_pass = bool(step1_significant and tau_locked >= LOCKED_TAU_TARGET)
    result["primary_test_step1"]["step_pass"] = step1_pass

    gate = {"step1_primary_locked_target": step1_pass}

    if step1_pass:
        boot_solids = paired_bootstrap_superiority(locked, solids, truth, BOOT_SEED_SOLIDS)
        robust_solids = robustness_permutation_superiority(locked, solids, truth, ROBUST_PERM_SEED_SOLIDS)
        step2_pass = bool(boot_solids["p_value_one_sided_delta_gt_0"] < ALPHA)
        result["step2_superiority_vs_solids_only_null"] = {
            "hypothesis": "tau(locked,truth) > tau(solids_only,truth), one-sided",
            "paired_bootstrap": boot_solids,
            "permutation_robustness_crosscheck": robust_solids,
            "step_pass": step2_pass,
        }
        gate["step2_superiority_vs_solids"] = step2_pass
    else:
        result["step2_superiority_vs_solids_only_null"] = {"skipped": True, "reason": "fixed-sequence gatekeeping: step1 failed"}
        gate["step2_superiority_vs_solids"] = None

    if gate.get("step2_superiority_vs_solids"):
        boot_pvc = paired_bootstrap_superiority(locked, pvc, truth, BOOT_SEED_PVC)
        robust_pvc = robustness_permutation_superiority(locked, pvc, truth, ROBUST_PERM_SEED_PVC)
        step3_pass = bool(boot_pvc["p_value_one_sided_delta_gt_0"] < ALPHA)
        result["step3_superiority_vs_pvc_only_null"] = {
            "hypothesis": "tau(locked,truth) > tau(pvc_only,truth), one-sided",
            "paired_bootstrap": boot_pvc,
            "permutation_robustness_crosscheck": robust_pvc,
            "step_pass": step3_pass,
        }
        gate["step3_superiority_vs_pvc"] = step3_pass
    else:
        result["step3_superiority_vs_pvc_only_null"] = {"skipped": True, "reason": "fixed-sequence gatekeeping: step1 or step2 failed"}
        gate["step3_superiority_vs_pvc"] = None

    all_pass = all(v is True for v in gate.values())
    result["gate_summary"] = gate
    result["verdict"] = "LOCKED_KPI_SUPPORTED_ALL_GATES_PASS" if all_pass else "LOCKED_KPI_NOT_SUPPORTED"
    result["does_not_close"] = [
        "This is a single ST-19168-derived corroborating analysis, not the locked mission.md "
        "primary KPI itself (a blinded four-track independent-panel comparison). It cannot "
        "promote authority, phase, or manifest state on its own.",
        "n<=10 is far below the Bonett-Wright (2000) n~25 needed for 80% power at tau=0.5 "
        "one-sided alpha=0.05 -- see PREREGISTRATION.md honest power section.",
    ]
    return result


def canon(obj):
    return json.dumps(obj, indent=2, sort_keys=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("input_json")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    res = run(args.input_json)
    text = canon(res)
    if args.out:
        Path(args.out).write_text(text)
    else:
        print(text)
    print("RESULT_SHA256", hashlib.sha256(text.encode()).hexdigest(), file=sys.stderr)
