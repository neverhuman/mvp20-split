"""bigsoldb-v1 locked benchmark, revision 2: incumbent-HSP head-to-head,
conformal prediction intervals, and an applicability domain.

What revision 1 could not answer
--------------------------------
Revision 1 compared a LightGBM descriptor model against four statistical
baselines (global / per-solvent / per-solute means, ridge-damped two-way
additive). Beating a marginal mean is a weak result, and it does not test
this module's stated falsifiable hypothesis, which is that a measured,
group-held-out model "can outperform HSP-only screening" (docs/mission.md).
Hansen solubility parameters are the incumbent industrial method for solvent
selection in coatings. Revision 2 supplies that incumbent as a first-class
competitor, three ways, from weakest to strongest:

  b4_hsp_ra_screen  OLS on Hansen distance Ra and temperature. This is
                    literal HSP screening: one number, "like dissolves like".
  b5_hsp_ridge      Ridge on the full HSP-derived feature set (both molecules'
                    delta_D/delta_P/delta_H, their differences, Ra, solute
                    molar volume, temperature).
  b6_hsp_gbm        LightGBM on exactly those HSP features - same model class
                    and same hyperparameters as our model, restricted to HSP
                    information. This isolates "what HSP theory knows" from
                    "what gradient boosting does", so a win cannot be
                    attributed to model capacity alone.

Every comparison runs on an identical row set (rows where both molecules have
HSP), with identical folds, so the head-to-head is apples-to-apples.

Calibrated uncertainty
----------------------
A screening gate needs to know when to abstain, so a point RMSE is not a
usable KPI on its own. We add split-conformal prediction intervals
(Vovk et al. 2005; Lei et al., JASA 2018) in the grouped setting: within each
outer training fold a disjoint set of *solutes* is held out for calibration,
so calibration molecules are unseen by the model and disjoint from test
molecules. Two variants:
  - standard   : fixed half-width from the (1-alpha) residual quantile
  - normalized : half-width scaled by a learned difficulty estimate
                 sigma(x), giving adaptive per-candidate intervals
Empirical coverage is measured out-of-fold and is the headline KPI, because
an interval that does not cover at its nominal rate is worse than no interval.
Note the module's prior negative result on this exact question: bootstrap
prediction intervals in amphora-tolerance-robustness reached only 25.1%
coverage at nominal 95%, which is why conformal is used here.

Applicability domain
--------------------
Out-of-fold error is stratified by Morgan-fingerprint Tanimoto similarity to
the nearest training solute. This turns the benchmark into an operational
rule: it states the similarity band within which the stated accuracy holds,
and therefore where the gate must abstain.

Status: LOCKED_INTERNAL diagnostic. No candidate-performance, product
qualification, or wet-lab claim is made or implied.
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from rdkit import Chem, RDLogger
from rdkit.Chem import rdFingerprintGenerator
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hsp as hspmod  # noqa: E402

RDLogger.DisableLog("rdApp.*")

BENCH = Path("amphora-solvency-score/benchmarks/bigsoldb-v1")
SEED = 20260724
N_FOLDS = 5
N_BOOT = 1000
ALPHA = 0.05  # nominal 95% intervals
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
    err = np.asarray(p) - np.asarray(y)
    return {
        "rmse": float(np.sqrt(np.mean(err**2))),
        "mae": float(np.mean(np.abs(err))),
        "r2": float(1 - np.sum(err**2) / np.sum((y - y.mean()) ** 2)),
        "frac_within_1log": float(np.mean(np.abs(err) <= 1.0)),
        "n": int(len(y)),
    }


def cluster_bootstrap_ci(y, p, groups, n_boot=N_BOOT, seed=SEED):
    """95% CI for RMSE, resampling whole groups (solutes), not rows."""
    rng = np.random.default_rng(seed)
    df = pd.DataFrame({"y": y, "p": p, "g": groups})
    by_g = {g: (s["y"].values, s["p"].values) for g, s in df.groupby("g")}
    gl = list(by_g)
    vals = []
    for _ in range(n_boot):
        pick = rng.choice(len(gl), size=len(gl), replace=True)
        ys = np.concatenate([by_g[gl[i]][0] for i in pick])
        ps = np.concatenate([by_g[gl[i]][1] for i in pick])
        vals.append(float(np.sqrt(np.mean((ps - ys) ** 2))))
    return [float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))]


def paired_bootstrap_delta(y, p_a, p_b, groups, n_boot=N_BOOT, seed=SEED):
    """Paired cluster bootstrap on RMSE(b) - RMSE(a).

    Positive delta means model `a` is better. The CI and the sign-consistency
    fraction are what license (or refuse) a lift claim.
    """
    rng = np.random.default_rng(seed + 1)
    df = pd.DataFrame({"y": y, "a": p_a, "b": p_b, "g": groups})
    by_g = {g: (s["y"].values, s["a"].values, s["b"].values)
            for g, s in df.groupby("g")}
    gl = list(by_g)
    deltas = []
    for _ in range(n_boot):
        pick = rng.choice(len(gl), size=len(gl), replace=True)
        ys = np.concatenate([by_g[gl[i]][0] for i in pick])
        as_ = np.concatenate([by_g[gl[i]][1] for i in pick])
        bs = np.concatenate([by_g[gl[i]][2] for i in pick])
        ra_ = np.sqrt(np.mean((as_ - ys) ** 2))
        rb_ = np.sqrt(np.mean((bs - ys) ** 2))
        deltas.append(float(rb_ - ra_))
    deltas = np.array(deltas)
    return {
        "rmse_delta_mean": float(deltas.mean()),
        "rmse_delta_ci95": [float(np.percentile(deltas, 2.5)),
                            float(np.percentile(deltas, 97.5))],
        "frac_bootstrap_favouring_model": float(np.mean(deltas > 0)),
    }


# ---------------------------------------------------------------------------
# HSP feature construction
# ---------------------------------------------------------------------------
def build_hsp_frame(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    pub = hspmod.published_hsp_by_canonical_smiles()

    solvents = sorted(df["solvent_canon"].unique())
    solutes = sorted(df["solute_canon"].unique())

    solv_hsp, solv_src = {}, {}
    for s in solvents:
        if s in pub:
            solv_hsp[s] = pub[s]
            solv_src[s] = "published_hansen_table_a1"
        else:
            est = hspmod.hvk_hsp(s)
            if est is not None:
                solv_hsp[s] = est[:3]
                solv_src[s] = "hoftyzer_van_krevelen_estimate"

    sol_hsp = {}
    for s in solutes:
        est = hspmod.hvk_hsp(s)
        if est is not None:
            sol_hsp[s] = est  # (dD, dP, dH, V)

    keep = df["solvent_canon"].isin(solv_hsp) & df["solute_canon"].isin(sol_hsp)
    out = df[keep].copy()

    sv = np.array([solv_hsp[s] for s in out["solvent_canon"]], dtype=float)
    su = np.array([sol_hsp[s] for s in out["solute_canon"]], dtype=float)
    out["hsp_solvent_dD"], out["hsp_solvent_dP"], out["hsp_solvent_dH"] = sv.T
    out["hsp_solute_dD"] = su[:, 0]
    out["hsp_solute_dP"] = su[:, 1]
    out["hsp_solute_dH"] = su[:, 2]
    out["hsp_solute_V"] = su[:, 3]
    out["hsp_ddD"] = out["hsp_solute_dD"] - out["hsp_solvent_dD"]
    out["hsp_ddP"] = out["hsp_solute_dP"] - out["hsp_solvent_dP"]
    out["hsp_ddH"] = out["hsp_solute_dH"] - out["hsp_solvent_dH"]
    out["hsp_Ra"] = np.sqrt(
        4.0 * out["hsp_ddD"] ** 2 + out["hsp_ddP"] ** 2 + out["hsp_ddH"] ** 2
    )
    out["hsp_log_V"] = np.log(out["hsp_solute_V"])
    out["inv_T"] = 1.0 / out["temperature_k"]
    out["Ra_over_T"] = out["hsp_Ra"] / out["temperature_k"]

    coverage = {
        "rows_in": int(len(df)),
        "rows_with_complete_hsp": int(len(out)),
        "row_coverage_fraction": float(len(out) / len(df)),
        "solvents_total": len(solvents),
        "solvents_published": int(sum(
            1 for v in solv_src.values() if v == "published_hansen_table_a1")),
        "solvents_group_contribution": int(sum(
            1 for v in solv_src.values()
            if v == "hoftyzer_van_krevelen_estimate")),
        "solvents_unresolved": int(len(solvents) - len(solv_hsp)),
        "solutes_total": len(solutes),
        "solutes_estimable": len(sol_hsp),
        "solutes_abstained": int(len(solutes) - len(sol_hsp)),
        "solute_hsp_source": "hoftyzer_van_krevelen_groups_fedors_volume",
        "note": (
            "Solvent HSP uses published experimental values where available; "
            "solutes necessarily use group contribution because leave-solute-out "
            "evaluation requires HSP for molecules with no tabulated value. "
            "Molecules the estimator cannot support abstain rather than guess."
        ),
    }
    return out, coverage


HSP_FEATURES = [
    "hsp_solute_dD", "hsp_solute_dP", "hsp_solute_dH",
    "hsp_solvent_dD", "hsp_solvent_dP", "hsp_solvent_dH",
    "hsp_ddD", "hsp_ddP", "hsp_ddH", "hsp_Ra",
    "hsp_solute_V", "hsp_log_V",
    "temperature_k", "inv_T", "Ra_over_T",
]


def hsp_baselines(train, test):
    """The three incumbent-HSP competitors, fitted on training rows only."""
    out = {}

    xa_tr = train[["hsp_Ra", "temperature_k"]].values
    xa_te = test[["hsp_Ra", "temperature_k"]].values
    out["b4_hsp_ra_screen"] = LinearRegression().fit(
        xa_tr, train[TARGET].values).predict(xa_te)

    sc = StandardScaler().fit(train[HSP_FEATURES].values)
    out["b5_hsp_ridge"] = Ridge(alpha=1.0).fit(
        sc.transform(train[HSP_FEATURES].values), train[TARGET].values
    ).predict(sc.transform(test[HSP_FEATURES].values))

    gbm = lgb.LGBMRegressor(**{**LGB_PARAMS, "n_estimators": 1200})
    gbm.fit(train[HSP_FEATURES].values, train[TARGET].values)
    out["b6_hsp_gbm"] = gbm.predict(test[HSP_FEATURES].values)
    return out


def stat_baselines(train, test):
    out = {}
    gmean = train[TARGET].mean()
    out["b0_global_mean"] = np.full(len(test), gmean)
    sv = train.groupby("solvent_canon")[TARGET].mean()
    out["b1_solvent_mean"] = test["solvent_canon"].map(sv).fillna(gmean).values
    so = train.groupby("solute_canon")[TARGET].mean()
    out["b2_solute_mean"] = test["solute_canon"].map(so).fillna(gmean).values
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


# ---------------------------------------------------------------------------
# Applicability domain
# ---------------------------------------------------------------------------
def morgan_fps(smiles_list):
    gen = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
    out = {}
    for s in smiles_list:
        mol = Chem.MolFromSmiles(s)
        out[s] = gen.GetFingerprint(mol) if mol is not None else None
    return out


def nearest_train_similarity(test_solutes, train_solutes, fps):
    from rdkit import DataStructs
    train_fps = [fps[s] for s in train_solutes if fps.get(s) is not None]
    sims = {}
    for s in test_solutes:
        f = fps.get(s)
        if f is None or not train_fps:
            sims[s] = np.nan
        else:
            sims[s] = float(max(DataStructs.BulkTanimotoSimilarity(f, train_fps)))
    return sims


# ---------------------------------------------------------------------------
# Conformal prediction
# ---------------------------------------------------------------------------
def conformal_fold(train, test, feat_cols, group_col, rng_seed):
    """Split-conformal in the grouped setting.

    The calibration set is a disjoint set of solutes, so calibration residuals
    are genuinely out-of-sample with respect to both the model and the test
    molecules. Returns standard and normalized (difficulty-scaled) intervals.
    """
    gkf = GroupKFold(n_splits=4)
    idx_fit, idx_cal = next(gkf.split(train, groups=train[group_col].values))
    fit, cal = train.iloc[idx_fit], train.iloc[idx_cal]

    model = lgb.LGBMRegressor(**LGB_PARAMS)
    inner = GroupKFold(n_splits=5)
    itr, iva = next(inner.split(fit, groups=fit[group_col].values))
    model.fit(
        fit.iloc[itr][feat_cols], fit.iloc[itr][TARGET],
        eval_set=[(fit.iloc[iva][feat_cols], fit.iloc[iva][TARGET])],
        callbacks=[lgb.early_stopping(100, verbose=False)],
    )
    ni = model.best_iteration_

    cal_pred = model.predict(cal[feat_cols], num_iteration=ni)
    cal_res = np.abs(cal[TARGET].values - cal_pred)
    test_pred = model.predict(test[feat_cols], num_iteration=ni)

    n = len(cal_res)
    q_level = min(1.0, np.ceil((n + 1) * (1 - ALPHA)) / n)
    q_std = float(np.quantile(cal_res, q_level, method="higher"))

    # normalized conformal: learn sigma(x) = E[|residual|] on the fit set
    fit_pred = model.predict(fit[feat_cols], num_iteration=ni)
    fit_res = np.abs(fit[TARGET].values - fit_pred)
    sig = lgb.LGBMRegressor(**{**LGB_PARAMS, "n_estimators": 600})
    sig.fit(fit[feat_cols], np.log1p(fit_res))
    s_cal = np.expm1(sig.predict(cal[feat_cols])).clip(0.05, None)
    s_te = np.expm1(sig.predict(test[feat_cols])).clip(0.05, None)
    q_nrm = float(np.quantile(cal_res / s_cal, q_level, method="higher"))

    return {
        "pred": test_pred,
        "half_std": np.full(len(test), q_std),
        "half_nrm": q_nrm * s_te,
        "n_calibration": int(n),
        "n_calibration_groups": int(cal[group_col].nunique()),
    }


# ---------------------------------------------------------------------------
def run_split(df, feat_cols, group_col, split_name, with_conformal=False,
              with_ad=False, fps=None):
    groups = df[group_col].values
    order = np.argsort([hashlib.sha256(f"{SEED}:{g}".encode()).hexdigest()
                        for g in groups])
    df = df.iloc[order].reset_index(drop=True)
    groups = df[group_col].values

    gkf = GroupKFold(n_splits=N_FOLDS)
    n = len(df)
    oof_model = np.full(n, np.nan)
    oof_base: dict[str, np.ndarray] = {}
    fold_assign = np.full(n, -1)
    half_std = np.full(n, np.nan)
    half_nrm = np.full(n, np.nan)
    conf_pred = np.full(n, np.nan)
    ad_sim = np.full(n, np.nan)
    conf_meta = []

    for fold, (tr, te) in enumerate(gkf.split(df, groups=groups)):
        train, test = df.iloc[tr], df.iloc[te]
        fold_assign[te] = fold

        for name, pred in {**stat_baselines(train, test),
                           **hsp_baselines(train, test)}.items():
            oof_base.setdefault(name, np.full(n, np.nan))[te] = pred

        inner = GroupKFold(n_splits=5)
        itr, iva = next(inner.split(train, groups=train[group_col].values))
        model = lgb.LGBMRegressor(**LGB_PARAMS)
        model.fit(
            train.iloc[itr][feat_cols], train.iloc[itr][TARGET],
            eval_set=[(train.iloc[iva][feat_cols], train.iloc[iva][TARGET])],
            callbacks=[lgb.early_stopping(100, verbose=False)],
        )
        oof_model[te] = model.predict(test[feat_cols],
                                      num_iteration=model.best_iteration_)
        print(f"[{split_name}] fold {fold}: best_iter={model.best_iteration_} "
              f"rmse={np.sqrt(np.mean((oof_model[te]-test[TARGET].values)**2)):.4f}",
              flush=True)

        if with_conformal:
            c = conformal_fold(train, test, feat_cols, group_col, SEED + fold)
            conf_pred[te] = c["pred"]
            half_std[te] = c["half_std"]
            half_nrm[te] = c["half_nrm"]
            conf_meta.append({k: c[k] for k in
                              ("n_calibration", "n_calibration_groups")})
            print(f"[{split_name}] fold {fold}: conformal half-width "
                  f"std={c['half_std'][0]:.3f}", flush=True)

        if with_ad and fps is not None:
            sims = nearest_train_similarity(
                test["solute_canon"].unique(),
                train["solute_canon"].unique(), fps)
            ad_sim[te] = test["solute_canon"].map(sims).values

    y = df[TARGET].values
    result = {
        "split": split_name,
        "group_column": group_col,
        "n_rows": int(n),
        "n_groups": int(df[group_col].nunique()),
        "fold_assignment_sha256": stable_hash(
            [f"{g}:{f}" for g, f in zip(df[group_col], fold_assign)]),
        "model": {**metrics(y, oof_model),
                  "rmse_ci95_cluster_bootstrap": cluster_bootstrap_ci(
                      y, oof_model, groups)},
        "baselines": {},
        "head_to_head_vs_model": {},
    }
    for name, pred in sorted(oof_base.items()):
        result["baselines"][name] = {
            **metrics(y, pred),
            "rmse_ci95_cluster_bootstrap": cluster_bootstrap_ci(y, pred, groups),
        }
        result["head_to_head_vs_model"][name] = paired_bootstrap_delta(
            y, oof_model, pred, groups)

    if with_conformal:
        cov_std = float(np.mean(np.abs(y - conf_pred) <= half_std))
        cov_nrm = float(np.mean(np.abs(y - conf_pred) <= half_nrm))
        result["conformal"] = {
            "nominal_coverage": 1 - ALPHA,
            "calibration": "grouped split-conformal; calibration solutes "
                           "disjoint from both training and test solutes",
            "standard": {
                "empirical_coverage": cov_std,
                "median_interval_width": float(2 * np.nanmedian(half_std)),
            },
            "normalized": {
                "empirical_coverage": cov_nrm,
                "median_interval_width": float(2 * np.nanmedian(half_nrm)),
                "iqr_interval_width": [
                    float(2 * np.nanpercentile(half_nrm, 25)),
                    float(2 * np.nanpercentile(half_nrm, 75))],
            },
            "conformal_model_rmse": metrics(y, conf_pred)["rmse"],
            "folds": conf_meta,
        }

    if with_ad:
        bands = [(0.0, 0.3), (0.3, 0.5), (0.5, 0.7), (0.7, 0.85), (0.85, 1.01)]
        strata = []
        for lo, hi in bands:
            m = (ad_sim >= lo) & (ad_sim < hi)
            if m.sum() < 50:
                continue
            s = {"tanimoto_band": [lo, hi], **metrics(y[m], oof_model[m])}
            if with_conformal:
                s["conformal_coverage_normalized"] = float(
                    np.mean(np.abs(y[m] - conf_pred[m]) <= half_nrm[m]))
            strata.append(s)
        result["applicability_domain"] = {
            "definition": "max Tanimoto (Morgan r=2, 2048 bit) from the test "
                          "solute to any training solute",
            "median_nearest_train_similarity": float(np.nanmedian(ad_sim)),
            "strata": strata,
        }
    return result


def main() -> None:
    t0 = time.time()
    raw = pd.read_parquet(BENCH / "features.parquet")
    df, coverage = build_hsp_frame(raw)
    df["pair"] = df["solute_canon"] + "||" + df["solvent_canon"]

    feat_cols = [c for c in raw.columns
                 if c.startswith(("solute_", "solvent_"))
                 and c not in ("solute_canon", "solvent_canon", "solvent_name")]
    feat_cols.append("temperature_k")

    print(json.dumps(coverage, indent=2), flush=True)
    hsp_validation = hspmod.validate_hvk()["summary"]
    print(json.dumps(hsp_validation, indent=2), flush=True)

    fps = morgan_fps(sorted(df["solute_canon"].unique()))

    results = {
        "benchmark": "amphora-solvency-score/bigsoldb-v1",
        "revision": 2,
        "stage": "evaluation",
        "seed": SEED,
        "n_folds": N_FOLDS,
        "target": "LogS(mol/L), replicate-median",
        "n_features_model": len(feat_cols),
        "n_features_hsp_baselines": len(HSP_FEATURES),
        "lgb_params": dict(LGB_PARAMS),
        "hsp_coverage": coverage,
        "hsp_estimator_known_answer_validation": hsp_validation,
        "splits": [],
        "external_anchors": {
            "attia_2025_nat_commun_solute_extrapolation_rmse": [0.83, 0.99],
            "attia_2025_interlab_aleatoric_rmse_floor": [0.5, 0.75],
            "vermeire_2022_external_rmse": [1.43, 2.16],
            "note": "different corpora/test sets; context anchors, not head-to-head",
        },
        "claim_lock": "LOCKED_INTERNAL diagnostic; no candidate-performance, "
                      "product qualification, or wet-lab claim.",
    }

    out_path = BENCH / "evaluation_receipt_v2.json"
    for group_col, name, conf, ad in (
        ("solute_canon", "leave_solute_out", True, True),
        ("solvent_canon", "leave_solvent_out", False, False),
        ("pair", "grouped_random_in_domain", False, False),
    ):
        r = run_split(df, feat_cols, group_col, name,
                      with_conformal=conf, with_ad=ad, fps=fps)
        results["splits"].append(r)
        results["wall_seconds"] = round(time.time() - t0, 1)
        with open(out_path, "w") as f:
            json.dump(results, f, indent=2)
        print(f"=== wrote {name} to {out_path}", flush=True)

    results["versions"] = {
        "python": sys.version.split()[0],
        "lightgbm": lgb.__version__,
        "rdkit": Chem.rdBase.rdkitVersion,
        "numpy": np.__version__,
        "pandas": pd.__version__,
    }
    results["wall_seconds"] = round(time.time() - t0, 1)
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(json.dumps(results["splits"][0]["head_to_head_vs_model"], indent=2))


if __name__ == "__main__":
    main()
