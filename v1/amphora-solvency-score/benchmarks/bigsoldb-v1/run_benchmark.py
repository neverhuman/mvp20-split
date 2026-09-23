"""bigsoldb-v1 locked benchmark: splits, baselines, model, KPIs, receipt.

Protocol (locked before any model fitting; seed and split hashes recorded):
  - Primary split: leave-solute-out (LSO) 5-fold, grouped by canonical solute
    SMILES. Measures extrapolation to unseen molecules — the deployment case
    for a solvency screen on novel candidates.
  - Secondary split: leave-solvent-out (LSVO) 5-fold, grouped by solvent.
  - Reference split: grouped-random 5-fold on (solute, solvent) pairs
    (in-domain; temperature interpolation within known pairs is excluded by
    grouping pairs, not rows).
  Baselines (must be beaten for any lift claim):
    b0 global-mean, b1 per-solvent mean, b2 per-solute mean,
    b3 two-way additive (solvent offset + solute offset, ridge-damped).
  Model: LightGBM on RDKit 2D descriptors (solute + solvent) + temperature.
  KPIs: RMSE, MAE, R2, frac|err|<=1 log, with 95% cluster bootstrap CIs
    (clustered on the split group, 1000 resamples).
External anchors (same task family, for context not equivalence):
  - Attia et al. 2025 (Nat Commun, doi:10.1038/s41467-025-62717-7): solute-
    extrapolation RMSE 0.83-0.99 log; inter-lab aleatoric floor ~0.5-0.75.
  - Vermeire et al. 2022 thermodynamic-cycle model: RMSE 1.43-2.16 on the
    same external test sets.
All results are diagnostic (LOCKED_INTERNAL); no candidate-performance claim.
"""

import hashlib
import json
import sys
import time
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold

BENCH = Path("amphora-solvency-score/benchmarks/bigsoldb-v1")
SEED = 20260724
N_FOLDS = 5
N_BOOT = 1000
TARGET = "logs"

LGB_PARAMS = {
    "objective": "regression",
    "n_estimators": 3000,
    "learning_rate": 0.05,
    "num_leaves": 127,
    "min_child_samples": 20,
    "subsample": 0.9,
    "subsample_freq": 1,
    "colsample_bytree": 0.8,
    "random_state": SEED,
    "n_jobs": 28,
    "verbose": -1,
}


def stable_hash(items) -> str:
    return hashlib.sha256("\n".join(map(str, items)).encode()).hexdigest()


def metrics(y, p):
    err = p - y
    return {
        "rmse": float(np.sqrt(np.mean(err**2))),
        "mae": float(np.mean(np.abs(err))),
        "r2": float(1 - np.sum(err**2) / np.sum((y - y.mean()) ** 2)),
        "frac_within_1log": float(np.mean(np.abs(err) <= 1.0)),
        "n": int(len(y)),
    }


def cluster_bootstrap_rmse_ci(y, p, groups, n_boot=N_BOOT, seed=SEED):
    rng = np.random.default_rng(seed)
    df = pd.DataFrame({"y": y, "p": p, "g": groups})
    by_g = {g: (sub["y"].values, sub["p"].values) for g, sub in df.groupby("g")}
    gl = list(by_g)
    vals = []
    for _ in range(n_boot):
        pick = rng.choice(len(gl), size=len(gl), replace=True)
        ys = np.concatenate([by_g[gl[i]][0] for i in pick])
        ps = np.concatenate([by_g[gl[i]][1] for i in pick])
        vals.append(float(np.sqrt(np.mean((ps - ys) ** 2))))
    return [float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))]


def baseline_preds(train, test):
    out = {}
    gmean = train[TARGET].mean()
    out["b0_global_mean"] = np.full(len(test), gmean)
    sv = train.groupby("solvent_canon")[TARGET].mean()
    out["b1_solvent_mean"] = test["solvent_canon"].map(sv).fillna(gmean).values
    so = train.groupby("solute_canon")[TARGET].mean()
    out["b2_solute_mean"] = test["solute_canon"].map(so).fillna(gmean).values
    # b3: y ~ mu + a_solute + b_solvent, ridge-damped offsets, 3 sweeps
    mu = gmean
    a = pd.Series(0.0, index=so.index)
    b = pd.Series(0.0, index=sv.index)
    lam = 10.0
    for _ in range(3):
        resid = train[TARGET] - mu - train["solvent_canon"].map(b).values
        g = resid.groupby(train["solute_canon"])
        a = g.sum() / (g.count() + lam)
        resid = train[TARGET] - mu - train["solute_canon"].map(a).values
        g = resid.groupby(train["solvent_canon"])
        b = g.sum() / (g.count() + lam)
    out["b3_two_way_additive"] = (
        mu
        + test["solute_canon"].map(a).fillna(0.0).values
        + test["solvent_canon"].map(b).fillna(0.0).values
    )
    return out


def run_split(df, feat_cols, group_col, split_name):
    groups = df[group_col].values
    order = np.argsort([hashlib.sha256(f"{SEED}:{g}".encode()).hexdigest() for g in groups])
    df = df.iloc[order].reset_index(drop=True)
    groups = df[group_col].values

    gkf = GroupKFold(n_splits=N_FOLDS)
    oof_model = np.full(len(df), np.nan)
    oof_base = {}
    fold_assign = np.full(len(df), -1)

    for fold, (tr, te) in enumerate(gkf.split(df, groups=groups)):
        train, test = df.iloc[tr], df.iloc[te]
        fold_assign[te] = fold
        for name, pred in baseline_preds(train, test).items():
            oof_base.setdefault(name, np.full(len(df), np.nan))[te] = pred

        # inner grouped holdout for early stopping (no test leakage)
        inner_groups = train[group_col].values
        inner = GroupKFold(n_splits=5)
        itr, iva = next(inner.split(train, groups=inner_groups))
        model = lgb.LGBMRegressor(**LGB_PARAMS)
        model.fit(
            train.iloc[itr][feat_cols],
            train.iloc[itr][TARGET],
            eval_set=[(train.iloc[iva][feat_cols], train.iloc[iva][TARGET])],
            callbacks=[lgb.early_stopping(100, verbose=False)],
        )
        oof_model[te] = model.predict(test[feat_cols], num_iteration=model.best_iteration_)
        print(f"[{split_name}] fold {fold}: best_iter={model.best_iteration_} "
              f"test_rmse={np.sqrt(np.mean((oof_model[te]-test[TARGET].values)**2)):.4f}",
              flush=True)

    y = df[TARGET].values
    result = {
        "split": split_name,
        "group_column": group_col,
        "n_rows": int(len(df)),
        "n_groups": int(df[group_col].nunique()),
        "fold_assignment_sha256": stable_hash(
            [f"{g}:{f}" for g, f in zip(df[group_col], fold_assign)]
        ),
        "model": {
            **metrics(y, oof_model),
            "rmse_ci95_cluster_bootstrap": cluster_bootstrap_rmse_ci(y, oof_model, groups),
        },
        "baselines": {},
    }
    for name, pred in oof_base.items():
        result["baselines"][name] = {
            **metrics(y, pred),
            "rmse_ci95_cluster_bootstrap": cluster_bootstrap_rmse_ci(y, pred, groups),
        }
    return result


def main() -> None:
    t0 = time.time()
    df = pd.read_parquet(BENCH / "features.parquet")
    df["pair"] = df["solute_canon"] + "||" + df["solvent_canon"]
    feat_cols = [
        c for c in df.columns
        if c.startswith(("solute_", "solvent_"))
        and c not in ("solute_canon", "solvent_canon", "solvent_name")
    ]
    feat_cols.append("temperature_k")

    results = {
        "benchmark": "amphora-solvency-score/bigsoldb-v1",
        "stage": "evaluation",
        "seed": SEED,
        "n_folds": N_FOLDS,
        "target": "LogS(mol/L), replicate-median",
        "n_features": len(feat_cols),
        "lgb_params": {k: v for k, v in LGB_PARAMS.items()},
        "splits": [],
        "external_anchors": {
            "attia_2025_nat_commun_solute_extrapolation_rmse": [0.83, 0.99],
            "attia_2025_interlab_aleatoric_rmse_floor": [0.5, 0.75],
            "vermeire_2022_external_rmse": [1.43, 2.16],
            "note": "different corpora/test sets; context anchors, not head-to-head",
        },
    }
    for group_col, name in (
        ("solute_canon", "leave_solute_out"),
        ("solvent_canon", "leave_solvent_out"),
        ("pair", "grouped_random_in_domain"),
    ):
        results["splits"].append(run_split(df.copy(), feat_cols, group_col, name))
        with open(BENCH / "evaluation_receipt.json", "w") as f:
            json.dump(results, f, indent=2)

    results["wall_seconds"] = round(time.time() - t0, 1)
    results["python"] = sys.version.split()[0]
    results["lightgbm"] = lgb.__version__
    with open(BENCH / "evaluation_receipt.json", "w") as f:
        json.dump(results, f, indent=2)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
