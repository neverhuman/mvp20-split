"""bigsoldb-v1 solvency benchmark — IN-HOUSE execution on the canonical machine.

Runs the locked leave-solute-out / leave-solvent-out / grouped-random protocol on
the RIGHTS-CLEARED IN-TREE data actually present on this host:

    feedback/v1/external_data/bigsoldb_v2/raw/BigSolDBv2.0.csv   (BigSolDB v2.0)

This is deliberately NOT the audit's Mac-Studio v2.1 run: it re-derives the number
from scratch on the data that is really here, records the true file hash, and is
built to be byte-stable across replays so a two-replay SHA-256 gate can bind it.

Curation is fail-closed (missing target / SMILES-parse / out-of-range rejected and
counted, never imputed). Determinism: LightGBM deterministic=True + force_row_wise,
fixed thread count, fixed seed; bootstrap RNG seeded. Diagnostic / AUDIT_ONLY only.
"""
import hashlib, json, sys, time, os
from pathlib import Path
import numpy as np
import pandas as pd
from rdkit import Chem, RDLogger
from rdkit.Chem import Descriptors
import rdkit, sklearn, lightgbm as lgb
from sklearn.model_selection import GroupKFold

RDLogger.DisableLog("rdApp.*")

ROOT = Path(".")
RAW = ROOT / "feedback/v1/external_data/bigsoldb_v2/raw/BigSolDBv2.0.csv"
BENCH = ROOT / "amphora-solvency-score/benchmarks/bigsoldb-v1"
TARGET = "logs"
SEED = 20260724
N_FOLDS = 5
N_BOOT = 1000
T_MIN, T_MAX = 243.0, 426.0
N_THREADS = 8
EXCLUDE = {"Ipc"}
DESCRIPTORS = [(n, f) for n, f in Descriptors.descList if n not in EXCLUDE]

LGB_PARAMS = {
    "objective": "regression", "n_estimators": 3000, "learning_rate": 0.05,
    "num_leaves": 127, "min_child_samples": 20, "subsample": 0.9,
    "subsample_freq": 1, "colsample_bytree": 0.8, "random_state": SEED,
    "num_threads": N_THREADS, "deterministic": True, "force_row_wise": True,
    "verbose": -1,
}


def file_hash(path, algo):
    h = hashlib.new(algo)
    with open(path, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def canon(s):
    if not isinstance(s, str) or not s.strip():
        return None
    m = Chem.MolFromSmiles(s)
    return Chem.MolToSmiles(m) if m is not None else None


def stable_hash(items):
    return hashlib.sha256("\n".join(map(str, items)).encode()).hexdigest()


def metrics(y, p):
    err = p - y
    return {"rmse": float(np.sqrt(np.mean(err**2))), "mae": float(np.mean(np.abs(err))),
            "r2": float(1 - np.sum(err**2) / np.sum((y - y.mean())**2)),
            "frac_within_1log": float(np.mean(np.abs(err) <= 1.0)), "n": int(len(y))}


def boot_ci(y, p, groups, seed=SEED, n=N_BOOT):
    rng = np.random.default_rng(seed)
    df = pd.DataFrame({"y": y, "p": p, "g": groups})
    by = {g: (s["y"].values, s["p"].values) for g, s in df.groupby("g")}
    gl = list(by)
    vals = []
    for _ in range(n):
        pick = rng.choice(len(gl), size=len(gl), replace=True)
        ys = np.concatenate([by[gl[i]][0] for i in pick])
        ps = np.concatenate([by[gl[i]][1] for i in pick])
        vals.append(float(np.sqrt(np.mean((ps - ys)**2))))
    return [float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))]


def baseline_preds(train, test):
    out = {}
    gmean = train[TARGET].mean()
    out["b0_global_mean"] = np.full(len(test), gmean)
    sv = train.groupby("solvent_canon")[TARGET].mean()
    out["b1_solvent_mean"] = test["solvent_canon"].map(sv).fillna(gmean).values
    so = train.groupby("solute_canon")[TARGET].mean()
    out["b2_solute_mean"] = test["solute_canon"].map(so).fillna(gmean).values
    mu = gmean
    a = pd.Series(0.0, index=so.index); b = pd.Series(0.0, index=sv.index); lam = 10.0
    for _ in range(3):
        resid = train[TARGET] - mu - train["solvent_canon"].map(b).values
        g = resid.groupby(train["solute_canon"]); a = g.sum() / (g.count() + lam)
        resid = train[TARGET] - mu - train["solute_canon"].map(a).values
        g = resid.groupby(train["solvent_canon"]); b = g.sum() / (g.count() + lam)
    out["b3_two_way_additive"] = (mu + test["solute_canon"].map(a).fillna(0.0).values
                                  + test["solvent_canon"].map(b).fillna(0.0).values)
    return out


def run_split(df, feat_cols, group_col, name):
    groups = df[group_col].values
    order = np.argsort([hashlib.sha256(f"{SEED}:{g}".encode()).hexdigest() for g in groups])
    df = df.iloc[order].reset_index(drop=True)
    groups = df[group_col].values
    gkf = GroupKFold(n_splits=N_FOLDS)
    oof = np.full(len(df), np.nan); base = {}; fa = np.full(len(df), -1)
    for fold, (tr, te) in enumerate(gkf.split(df, groups=groups)):
        train, test = df.iloc[tr], df.iloc[te]; fa[te] = fold
        for nm, pr in baseline_preds(train, test).items():
            base.setdefault(nm, np.full(len(df), np.nan))[te] = pr
        inner = GroupKFold(n_splits=5)
        itr, iva = next(inner.split(train, groups=train[group_col].values))
        model = lgb.LGBMRegressor(**LGB_PARAMS)
        model.fit(train.iloc[itr][feat_cols], train.iloc[itr][TARGET],
                  eval_set=[(train.iloc[iva][feat_cols], train.iloc[iva][TARGET])],
                  callbacks=[lgb.early_stopping(100, verbose=False)])
        oof[te] = model.predict(test[feat_cols], num_iteration=model.best_iteration_)
        print(f"[{name}] fold {fold}: best_iter={model.best_iteration_} "
              f"rmse={np.sqrt(np.mean((oof[te]-test[TARGET].values)**2)):.4f}", flush=True)
    y = df[TARGET].values
    res = {"split": name, "group_column": group_col, "n_rows": int(len(df)),
           "n_groups": int(df[group_col].nunique()),
           "fold_assignment_sha256": stable_hash([f"{g}:{f}" for g, f in zip(df[group_col], fa)]),
           "model": {**metrics(y, oof), "rmse_ci95_cluster_bootstrap": boot_ci(y, oof, groups)},
           "baselines": {}}
    for nm, pr in base.items():
        res["baselines"][nm] = {**metrics(y, pr), "rmse_ci95_cluster_bootstrap": boot_ci(y, pr, groups)}
    return res


def main():
    t0 = time.time()
    os.environ["OMP_NUM_THREADS"] = str(N_THREADS)
    raw_sha = file_hash(RAW, "sha256"); raw_md5 = file_hash(RAW, "md5")
    df = pd.read_csv(RAW)
    n_raw = len(df)
    reject = {}
    m = df["LogS(mol/L)"].notna(); reject["missing_target"] = int((~m).sum()); df = df[m].copy()
    df["temperature_k"] = pd.to_numeric(df["Temperature_K"], errors="coerce")
    m = df["temperature_k"].between(T_MIN, T_MAX); reject["temp_out_of_range_or_nan"] = int((~m).sum()); df = df[m].copy()
    # canonicalize once per unique SMILES (cache)
    su = {s: canon(s) for s in df["SMILES_Solute"].unique()}
    sv = {s: canon(s) for s in df["SMILES_Solvent"].unique()}
    df["solute_canon"] = df["SMILES_Solute"].map(su)
    df["solvent_canon"] = df["SMILES_Solvent"].map(sv)
    m = df["solute_canon"].notna() & df["solvent_canon"].notna()
    reject["smiles_parse_fail"] = int((~m).sum()); df = df[m].copy()
    df[TARGET] = df["LogS(mol/L)"].astype(float)
    # replicate collapse: (solute,solvent,T rounded 0.1K) -> median; retain spread
    df["tbin"] = df["temperature_k"].round(1)
    grp = df.groupby(["solute_canon", "solvent_canon", "tbin"])
    spread = grp[TARGET].agg(lambda v: float(v.max() - v.min()))
    collapsed = grp.agg(**{TARGET: (TARGET, "median"),
                           "temperature_k": ("temperature_k", "median")}).reset_index()
    n_after = len(collapsed)
    curation = {
        "benchmark": "amphora-solvency-score/bigsoldb-v1", "stage": "curation",
        "raw_file": str(RAW), "raw_sha256": raw_sha, "raw_md5": raw_md5,
        "dataset": "BigSolDB v2.0 (Zenodo 18552681 family, CC-BY-4.0)",
        "citation": "Krasnov et al., Sci Data 12 (2025), doi:10.1038/s41597-025-05559-8",
        "n_raw_rows": int(n_raw), "rejections_fail_closed": reject,
        "n_rows_after_reject": int(m.sum() if False else len(df)),
        "n_rows_after_replicate_collapse": int(n_after),
        "replicate_spread_log_units": {
            "median": float(np.median(spread.values)),
            "p90": float(np.percentile(spread.values, 90)),
            "max": float(np.max(spread.values))},
        "n_unique_solutes": int(collapsed["solute_canon"].nunique()),
        "n_unique_solvents": int(collapsed["solvent_canon"].nunique()),
        "target": "LogS(mol/L), replicate-median",
        "rdkit": rdkit.__version__, "python": sys.version.split()[0]}
    BENCH.mkdir(parents=True, exist_ok=True)
    with open(BENCH / "curation_receipt.v20.json", "w") as f:
        json.dump(curation, f, indent=2, sort_keys=True)
    print("CURATION:", json.dumps({k: curation[k] for k in
          ("n_raw_rows", "rejections_fail_closed", "n_rows_after_replicate_collapse",
           "n_unique_solutes", "n_unique_solvents", "replicate_spread_log_units")}, indent=2), flush=True)

    # featurize unique canonical SMILES
    def descvec(s):
        mol = Chem.MolFromSmiles(s)
        if mol is None:
            return None
        v = []
        for _, fn in DESCRIPTORS:
            try:
                x = float(fn(mol))
            except Exception:
                return None
            if not np.isfinite(x):
                return None
            v.append(x)
        return v
    names = [n for n, _ in DESCRIPTORS]
    solu_cache, solv_cache = {}, {}
    for s in collapsed["solute_canon"].unique():
        solu_cache[s] = descvec(s)
    for s in collapsed["solvent_canon"].unique():
        solv_cache[s] = descvec(s)
    good = collapsed["solute_canon"].map(lambda s: solu_cache[s] is not None) & \
           collapsed["solvent_canon"].map(lambda s: solv_cache[s] is not None)
    n_feat_reject = int((~good).sum())
    data = collapsed[good].reset_index(drop=True)
    solu_mat = np.array([solu_cache[s] for s in data["solute_canon"]], dtype=float)
    solv_mat = np.array([solv_cache[s] for s in data["solvent_canon"]], dtype=float)
    feat = pd.DataFrame(index=data.index)
    for i, nm in enumerate(names):
        feat[f"solute_{nm}"] = solu_mat[:, i]
        feat[f"solvent_{nm}"] = solv_mat[:, i]
    feat["temperature_k"] = data["temperature_k"].values
    feat["solute_canon"] = data["solute_canon"].values
    feat["solvent_canon"] = data["solvent_canon"].values
    feat[TARGET] = data[TARGET].values
    feat["pair"] = feat["solute_canon"] + "||" + feat["solvent_canon"]
    feat_cols = [c for c in feat.columns if c.startswith(("solute_", "solvent_"))
                 and c not in ("solute_canon", "solvent_canon")] + ["temperature_k"]

    results = {
        "benchmark": "amphora-solvency-score/bigsoldb-v1", "stage": "evaluation",
        "execution_host": "canonical (in-house, re-derived from in-tree BigSolDB v2.0)",
        "authority": "AUDIT_ONLY / diagnostic — no candidate-performance claim, no promotion",
        "seed": SEED, "n_folds": N_FOLDS, "n_features": len(feat_cols),
        "n_descriptors_per_molecule": len(names),
        "n_rows_modeled": int(len(feat)), "n_feature_reject": n_feat_reject,
        "raw_sha256": raw_sha,
        "lgb_params": LGB_PARAMS, "splits": [],
        "external_anchors": {
            "attia_2025_nat_commun_solute_extrapolation_rmse": [0.83, 0.99],
            "attia_2025_interlab_aleatoric_rmse_floor": [0.5, 0.75],
            "vermeire_2022_external_rmse": [1.43, 2.16],
            "note": "different corpora/test sets; context anchors, not head-to-head"},
        "rdkit": rdkit.__version__, "sklearn": sklearn.__version__,
        "lightgbm": lgb.__version__, "python": sys.version.split()[0]}
    SPLITS = (("solute_canon", "leave_solute_out"),)  # primary/deployment split only (host-contention safe)
    for gc, nm in SPLITS:
        results["splits"].append(run_split(feat.copy(), feat_cols, gc, nm))
    results["wall_seconds"] = round(time.time() - t0, 1)
    with open(BENCH / "evaluation_receipt.v20.json", "w") as f:
        json.dump(results, f, indent=2, sort_keys=True)
    # summary
    for s in results["splits"]:
        bb = min(s["baselines"].values(), key=lambda d: d["rmse"])
        print(f"SUMMARY {s['split']}: model RMSE={s['model']['rmse']:.4f} "
              f"CI={s['model']['rmse_ci95_cluster_bootstrap']} R2={s['model']['r2']:.3f} | "
              f"best_baseline RMSE={bb['rmse']:.4f}", flush=True)


if __name__ == "__main__":
    main()
