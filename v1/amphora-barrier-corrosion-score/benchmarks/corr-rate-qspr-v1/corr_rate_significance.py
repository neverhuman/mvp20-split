#!/usr/bin/env python3
"""
amphora-barrier-corrosion-score / corr-rate-qspr-v1  SIGNIFICANCE ADDENDUM
==========================================================================
Purpose: convert the existing leave-material-out corrosion-rate QSPR point
estimate (R^2 ~= 0.32, "modest positive skill over naive baselines") into a
STATISTICALLY DEFENSIBLE claim, which is the honest gate before any Phase-0
promotion of amphora-barrier-corrosion-score.

Two tests, both group-safe (materials are the cluster unit):

 (1) PAIRED CLUSTER BOOTSTRAP on Delta-RMSE = best_naive_baseline_rmse - gbm_rmse.
     The out-of-fold predictions of the GBM and of the strongest naive baseline
     (per-environment mean, which under leave-material-out is a genuinely strong
     baseline because environments ARE seen in training) are held fixed; each
     bootstrap resamples the ~600 MATERIAL clusters with replacement and
     recomputes BOTH pooled RMSEs on the same resample, then their difference.
     The model "reliably beats" the baseline iff the 95% CI of Delta-RMSE
     excludes 0 (lower bound > 0).  This is the correct paired test; comparing a
     single-model CI to a baseline point estimate (as the prior diagnostic did)
     is not.

 (2) LABEL-PERMUTATION NULL. The target y is permuted globally with a seeded RNG,
     the FULL leave-material-out GroupKFold GBM is refit on the permuted labels,
     and the leave-material-out R^2 is recorded. Repeated N_PERM times to build
     the null distribution of "skill obtainable by chance under this
     feature/split/model". Empirical one-sided p = (1 + #{null_R2 >= obs_R2})
     / (N_PERM + 1). A real signal gives p at the resolution floor.

Determinism: OMP_NUM_THREADS=1, fixed seeds, GroupKFold (no shuffle), canonical
rounding -> byte-stable two-replay SHA-256 gate ON THIS HOST. The live host env
(sklearn/numpy versions) is recorded in the artifact, because the prior signed
diagnostic's byte gate was minted under sklearn 1.9.0 and is NOT reproducible
under this host's sklearn (that fragility is itself reported here).

Authority: AUDIT_ONLY. Reuses the exact pipeline of corr_rate_qspr.py (imported,
not copied). Modifies NOTHING: not the existing signed diagnostic, not the 66
signed receipts, not module front-matter. Promotes no authority.
"""
import os
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
import json, hashlib, math, sys, platform
import numpy as np
import sklearn
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import GroupKFold

# import the frozen pipeline (same data load, features, splits, model params)
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import corr_rate_qspr as C  # noqa: E402

SEED = 0
NDEC = 6
N_BOOT = 2000
N_PERM = 100


def _model():
    # identical to corr_rate_qspr.run_cv
    return HistGradientBoostingRegressor(
        random_state=SEED, max_iter=300, learning_rate=0.05,
        max_depth=None, max_leaf_nodes=31, l2_regularization=1.0,
        early_stopping=False)


def matsafe_oof(X, y, mats, envs):
    """Leave-material-out OOF for GBM and for the per-environment-mean baseline."""
    gbm = np.full(len(y), np.nan)
    bl_env = np.full(len(y), np.nan)
    for tr, te in GroupKFold(n_splits=5).split(X, y, groups=mats):
        m = _model()
        m.fit(X[tr], y[tr])
        gbm[te] = m.predict(X[te])
        glob = float(np.mean(y[tr]))
        bl_env[te] = C.group_baseline(envs[tr], y[tr], envs[te], glob)
    return gbm, bl_env


def paired_cluster_bootstrap(y, gbm_pred, bl_pred, mats):
    """95% CI of (baseline_rmse - gbm_rmse) resampling material clusters."""
    rng = np.random.default_rng(SEED)
    uniq = np.array(sorted(set(mats.tolist())))
    idx_by_g = {g: np.where(mats == g)[0] for g in uniq}

    def rmse(pred, sel):
        e = pred[sel] - y[sel]
        return math.sqrt(float(np.mean(e ** 2)))

    deltas, gbm_r, bl_r = [], [], []
    for _ in range(N_BOOT):
        pick = rng.choice(len(uniq), size=len(uniq), replace=True)
        sel = np.concatenate([idx_by_g[uniq[p]] for p in pick])
        rg = rmse(gbm_pred, sel)
        rb = rmse(bl_pred, sel)
        gbm_r.append(rg)
        bl_r.append(rb)
        deltas.append(rb - rg)
    d = np.array(deltas)
    lo, hi = np.percentile(d, [2.5, 97.5])
    frac_pos = float(np.mean(d > 0.0))
    return {
        "delta_rmse_point": float(np.mean(bl_r) - np.mean(gbm_r)),
        "delta_rmse_ci95": [float(lo), float(hi)],
        "delta_rmse_ci95_excludes_zero": bool(lo > 0.0),
        "bootstrap_fraction_delta_gt_0": frac_pos,
        "n_bootstrap": N_BOOT,
        "cluster_unit": "material",
    }


def permutation_null(X, y, mats, envs, obs_r2):
    rng = np.random.default_rng(SEED + 1)
    null_r2 = []
    n = len(y)
    for _ in range(N_PERM):
        perm = rng.permutation(n)
        yp = y[perm]
        oof = np.full(n, np.nan)
        for tr, te in GroupKFold(n_splits=5).split(X, yp, groups=mats):
            m = _model()
            m.fit(X[tr], yp[tr])
            oof[te] = m.predict(X[te])
        _, _, r2 = C.metrics(yp, oof)
        null_r2.append(float(r2))
    null_r2 = np.array(null_r2)
    ge = int(np.sum(null_r2 >= obs_r2))
    p = (1.0 + ge) / (N_PERM + 1.0)
    return {
        "observed_leave_material_out_r2": float(obs_r2),
        "n_permutations": N_PERM,
        "null_r2_mean": float(np.mean(null_r2)),
        "null_r2_std": float(np.std(null_r2)),
        "null_r2_max": float(np.max(null_r2)),
        "null_r2_p95": float(np.percentile(null_r2, 95)),
        "n_null_ge_observed": ge,
        "empirical_p_value_one_sided": float(p),
        "p_value_resolution_floor": float(1.0 / (N_PERM + 1.0)),
    }


def rnd(o):
    if isinstance(o, float):
        return None if math.isnan(o) else round(o, NDEC)
    if isinstance(o, dict):
        return {k: rnd(o[k]) for k in sorted(o)}
    if isinstance(o, list):
        return [rnd(v) for v in o]
    return o


def main():
    rows, src_sha, n_raw = C.load()
    X, y, mats, envs, has_comp = C.build_matrix(rows)
    n = len(y)

    gbm_pred, bl_pred = matsafe_oof(X, y, mats, envs)
    _, _, gbm_r2 = C.metrics(y, gbm_pred)
    gbm_rmse, gbm_mae, _ = C.metrics(y, gbm_pred)
    bl_rmse, _, bl_r2 = C.metrics(y, bl_pred)

    boot = paired_cluster_bootstrap(y, gbm_pred, bl_pred, mats)
    perm = permutation_null(X, y, mats, envs, gbm_r2)

    verdict_beats_baseline = boot["delta_rmse_ci95_excludes_zero"]
    verdict_real_signal = perm["empirical_p_value_one_sided"] <= 0.05
    overall = "SIGNAL_CONFIRMED" if (verdict_beats_baseline and verdict_real_signal) \
        else "NOT_CONFIRMED"

    canonical = {
        "schema": "amphora.barrier-corrosion-score.corr-rate-qspr-significance.v1",
        "benchmark": "amphora-barrier-corrosion-score/corr-rate-qspr-v1",
        "addendum_to": "diagnostic.canonical.json (leave-material-out corrosion-rate QSPR)",
        "target": "log10(corrosion_rate_mm_per_year)",
        "dataset": {
            "name": "NIST CORR-DATA (Dow Chemical Co.) derived reference",
            "in_tree_path": C.SRC,
            "source_sha256": src_sha,
            "rights_class": "DERIVATIVE_ALLOWED",
            "n_raw_records": n_raw,
        },
        "cohort": {
            "n_modeled": n,
            "n_unique_materials": int(len(set(mats.tolist()))),
            "n_unique_environments": int(len(set(envs.tolist()))),
        },
        "point_estimates_this_host": {
            "gbm_leave_material_out_rmse": gbm_rmse,
            "gbm_leave_material_out_mae": gbm_mae,
            "gbm_leave_material_out_r2": gbm_r2,
            "best_naive_baseline": "per_environment_mean",
            "baseline_leave_material_out_rmse": bl_rmse,
            "baseline_leave_material_out_r2": bl_r2,
            "error_reduction_vs_baseline_pct": 100.0 * (1.0 - gbm_rmse / bl_rmse),
        },
        "test_1_paired_cluster_bootstrap_delta_rmse": boot,
        "test_2_label_permutation_null_r2": perm,
        "verdict": {
            "model_reliably_beats_baseline_ci95": verdict_beats_baseline,
            "skill_exceeds_permutation_null_p_le_0_05": verdict_real_signal,
            "overall": overall,
            "interpretation": (
                "SIGNAL_CONFIRMED means the leave-material-out GBM (a) beats the "
                "strongest naive baseline with a paired material-cluster bootstrap "
                "95% CI on Delta-RMSE that excludes zero, AND (b) achieves a "
                "leave-material-out R^2 beyond its own label-permutation null "
                "(p<=0.05). This establishes real, group-safe substrate-corrosion "
                "predictive skill. It does NOT create organic epoxy-amine "
                "coating-barrier authority; scope stays AUDIT_ONLY diagnostic."),
        },
        "reproducibility_note_prior_diagnostic": (
            "The existing signed diagnostic.canonical.json attests sklearn 1.9.0 and "
            "byte-hash e3bea4fc...; this host runs sklearn " + sklearn.__version__ +
            ". The SCIENCE reproduces (leave-material-out R^2 ~0.32 either way) but the "
            "byte-stable two-replay gate is environment-pinned and does NOT reproduce "
            "cross-version. This significance addendum is pinned to and byte-stable on "
            "THIS host env (recorded below)."),
        "host_env": {
            "python": platform.python_version(),
            "sklearn": sklearn.__version__,
            "numpy": np.__version__,
        },
        "authority": "AUDIT_ONLY",
        "does_not_close": [
            "EVALUATION_SIGNATURE_ABSENT (requires trust-anchored phase0-evaluator key)",
            "coating-barrier authority (substrate corrosion, not organic coating barrier)",
            "human / independent organizational review",
        ],
        "determinism": {"omp_num_threads": os.environ.get("OMP_NUM_THREADS"),
                        "seed": SEED, "n_bootstrap": N_BOOT, "n_permutations": N_PERM,
                        "canonical_round_decimals": NDEC},
    }
    out = json.dumps(rnd(canonical), indent=2, sort_keys=True)
    dst = sys.argv[1] if len(sys.argv) > 1 else "significance.json"
    open(dst, "w").write(out)
    sha = hashlib.sha256(out.encode()).hexdigest()
    print("SIG_CANONICAL_SHA256", sha)
    print("overall", overall,
          "delta_rmse_ci95", [round(v, 4) for v in boot["delta_rmse_ci95"]],
          "perm_p", round(perm["empirical_p_value_one_sided"], 5),
          "null_r2_max", round(perm["null_r2_max"], 4),
          "obs_r2", round(gbm_r2, 4))


if __name__ == "__main__":
    main()
