"""amphora-solvency-score W-SCAFFOLD attack: scaffold-safe re-split of the
BigSolDB leave-solute-out (LSO) headline, plus a positive-control leaky split.

The standing claim (evidence/phase0/kpis/, benchmarks/bigsoldb-v1/evaluation_receipt.v20.json):
  BigSolDB leave-solute-out model RMSE 0.8770 (95% CI [0.8416, 0.9154]) vs best
  naive baseline RMSE 1.1687 on 94,532 rows / 1,372 solute groups.
  W6 (2026-08-02) already hardened this against internally-contradictory duplicate
  rows and it survived. NOT yet tested: whether GroupKFold-by-solute_canon (exact
  RDKit-canonical-SMILES identity) actually protects against near-neighbor /
  congeneric-analog leakage. Two solutes that are homologs or positional isomers
  are different solute_canon groups and so CAN be split across train/test under
  the standing protocol, even though they share a Bemis-Murcko scaffold and a
  model can "cheat" by memorizing scaffold-level solubility behavior rather than
  learning genuine chemistry.

Pre-registered refutation criterion (this attack's falsification target):
  Refit the IDENTICAL locked model/features/seed/N_FOLDS on a Bemis-Murcko
  scaffold-disjoint GroupKFold (leave_scaffold_out). The standing LSO claim is
  REFUTED if either:
    (a) leave_scaffold_out model RMSE > upper 95% CI bound of the signed LSO
        headline (0.9154), i.e. performance is not even within the originally
        claimed uncertainty band once true novel-chemotype generalization is
        enforced; OR
    (b) leave_scaffold_out model no longer beats its own best baseline at a
        comparable error-reduction (error reduction collapses to <50% of the
        signed LSO error-reduction of 24.98%).
  Otherwise CLAIM_SURVIVED.

Positive control (required for a SURVIVED verdict): a deliberately leaky split
that removes ALL group protection (plain shuffled KFold, ignoring solute/solvent
identity entirely -- rows from the same solute AND same solute-solvent pair can
now appear in both train and test). This is the KIND of defect a group-safety
audit exists to catch. If the harness is sensitive, this leaky split MUST show
materially better (lower) RMSE than both the scaffold-safe and original LSO
splits, proving the RMSE-vs-split-strictness comparison here actually detects
leakage-driven optimism when it is present.
"""
import hashlib, json, sys, time, os
from pathlib import Path
import numpy as np
import pandas as pd
from rdkit import Chem, RDLogger
from rdkit.Chem import Descriptors
from rdkit.Chem.Scaffolds import MurckoScaffold
import rdkit, sklearn, lightgbm as lgb
from sklearn.model_selection import GroupKFold, KFold

RDLogger.DisableLog("rdApp.*")

ROOT = Path(".")
RAW = ROOT / "feedback/v1/external_data/bigsoldb_v2/raw/BigSolDBv2.0.csv"
BENCH = ROOT / "amphora-solvency-score/evidence/audit/bigsoldb-scaffold-safe-generalization-v1"
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


def murcko(s):
    m = Chem.MolFromSmiles(s)
    if m is None:
        return None
    try:
        scaf = MurckoScaffold.GetScaffoldForMol(m)
        smi = Chem.MolToSmiles(scaf)
        return smi if smi else "NO_RING_SCAFFOLD::" + s
    except Exception:
        return "NO_RING_SCAFFOLD::" + s


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


def run_split(df, feat_cols, group_col, name, leaky=False):
    """leaky=True: POSITIVE CONTROL -- plain shuffled KFold, group protection
    removed entirely (planted defect: same solute/solute-solvent pair rows can
    appear in both train and test)."""
    groups = df[group_col].values
    order = np.argsort([hashlib.sha256(f"{SEED}:{g}:{i}".encode()).hexdigest()
                         for i, g in enumerate(groups)] if leaky else
                        [hashlib.sha256(f"{SEED}:{g}".encode()).hexdigest() for g in groups])
    df = df.iloc[order].reset_index(drop=True)
    groups = df[group_col].values
    if leaky:
        splitter = KFold(n_splits=N_FOLDS, shuffle=True, random_state=SEED)
        split_iter = splitter.split(df)
    else:
        splitter = GroupKFold(n_splits=N_FOLDS)
        split_iter = splitter.split(df, groups=groups)
    oof = np.full(len(df), np.nan); base = {}; fa = np.full(len(df), -1)
    for fold, (tr, te) in enumerate(split_iter):
        train, test = df.iloc[tr], df.iloc[te]; fa[te] = fold
        for nm, pr in baseline_preds(train, test).items():
            base.setdefault(nm, np.full(len(df), np.nan))[te] = pr
        if leaky:
            cut = int(0.8 * len(train))
            itr_pos = np.arange(len(train))[:cut]; iva_pos = np.arange(len(train))[cut:]
        else:
            inner = GroupKFold(n_splits=5)
            itr_pos, iva_pos = next(inner.split(train, groups=train[group_col].values))
        params = dict(LGB_PARAMS)
        if leaky:
            # Positive control only: leakage lets the model memorize near-instantly,
            # so early stopping never fires against a leaked validation fold and the
            # full 3000-round budget just burns wall-clock without changing the
            # qualitative result. Cap rounds -- the point (does leakage inflate
            # apparent performance vs the group-safe arms?) is already decided by
            # round ~500 given exact/near-duplicate rows span train/test.
            params["n_estimators"] = 500
        model = lgb.LGBMRegressor(**params)
        model.fit(train.iloc[itr_pos][feat_cols], train.iloc[itr_pos][TARGET],
                  eval_set=[(train.iloc[iva_pos][feat_cols], train.iloc[iva_pos][TARGET])],
                  callbacks=[lgb.early_stopping(100, verbose=False)])
        oof[te] = model.predict(test[feat_cols], num_iteration=model.best_iteration_)
        print(f"[{name}] fold {fold}: best_iter={model.best_iteration_} "
              f"rmse={np.sqrt(np.mean((oof[te]-test[TARGET].values)**2)):.4f}", flush=True)
    y = df[TARGET].values
    # CI bootstrap always clustered by TRUE solute identity, regardless of split
    # protection used for training, so the leaky arm's CI is not itself inflated.
    ci_group = df["solute_canon"].values
    res = {"split": name, "group_column": group_col, "leaky_positive_control": leaky,
           "n_rows": int(len(df)), "n_groups": int(df[group_col].nunique()),
           "fold_assignment_sha256": stable_hash([f"{g}:{f}" for g, f in zip(df[group_col], fa)]),
           "model": {**metrics(y, oof), "rmse_ci95_cluster_bootstrap": boot_ci(y, oof, ci_group)},
           "baselines": {}}
    for nm, pr in base.items():
        res["baselines"][nm] = {**metrics(y, pr), "rmse_ci95_cluster_bootstrap": boot_ci(y, pr, ci_group)}
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
    su = {s: canon(s) for s in df["SMILES_Solute"].unique()}
    sv = {s: canon(s) for s in df["SMILES_Solvent"].unique()}
    df["solute_canon"] = df["SMILES_Solute"].map(su)
    df["solvent_canon"] = df["SMILES_Solvent"].map(sv)
    m = df["solute_canon"].notna() & df["solvent_canon"].notna()
    reject["smiles_parse_fail"] = int((~m).sum()); df = df[m].copy()
    df[TARGET] = df["LogS(mol/L)"].astype(float)
    df["tbin"] = df["temperature_k"].round(1)
    grp = df.groupby(["solute_canon", "solvent_canon", "tbin"])
    collapsed = grp.agg(**{TARGET: (TARGET, "median"),
                           "temperature_k": ("temperature_k", "median")}).reset_index()

    scaf_cache = {s: murcko(s) for s in collapsed["solute_canon"].unique()}
    collapsed["solute_scaffold"] = collapsed["solute_canon"].map(scaf_cache)
    n_scaffold_groups = collapsed["solute_scaffold"].nunique()
    n_singleton_scaffolds = int(collapsed.drop_duplicates("solute_canon")
                                 .groupby("solute_scaffold").size().eq(1).sum())

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
    feat["solute_scaffold"] = data["solute_scaffold"].values
    feat[TARGET] = data[TARGET].values
    feat_cols = [c for c in feat.columns if c.startswith(("solute_", "solvent_"))
                 and c not in ("solute_canon", "solvent_canon", "solute_scaffold")] + ["temperature_k"]

    results = {
        "benchmark": "amphora-solvency-score/bigsoldb-scaffold-safe-generalization-v1",
        "campaign_item_id": "W-SCAFFOLD",
        "attack_type": "harder_held_out_split_scaffold_safe_plus_leakage_positive_control",
        "authority": "AUDIT_ONLY / diagnostic -- no candidate-performance claim, no promotion",
        "seed": SEED, "n_folds": N_FOLDS, "n_features": len(feat_cols),
        "n_descriptors_per_molecule": len(names),
        "n_rows_modeled": int(len(feat)), "n_feature_reject": n_feat_reject,
        "raw_sha256": raw_sha, "raw_md5": raw_md5,
        "n_unique_solutes": int(collapsed["solute_canon"].nunique()),
        "n_unique_solute_scaffolds": int(n_scaffold_groups),
        "n_singleton_solute_scaffolds": n_singleton_scaffolds,
        "standing_claim": {
            "receipt": "amphora-solvency-score/benchmarks/bigsoldb-v1/inhouse_benchmark_receipt.v1.dsse.json",
            "leave_solute_out_model_rmse": 0.8770255643028615,
            "leave_solute_out_model_rmse_ci95": [0.8416341720920943, 0.9154344725058612],
            "leave_solute_out_best_baseline_rmse": 1.1686915142248226,
            "leave_solute_out_error_reduction_pct": round(100 * (1 - 0.8770255643028615 / 1.1686915142248226), 2),
        },
        "lgb_params": LGB_PARAMS,
        "lgb_params_leaky_positive_control_note": "n_estimators capped to 500 for the "
            "leaky arm only (identical all other params/seed) -- leakage collapses the "
            "early-stopping validation loss near-instantly so the full 3000-round budget "
            "only burns wall-clock; capping does not change the qualitative leakage signal.",
        "splits": [],
        "rdkit": rdkit.__version__, "sklearn": sklearn.__version__,
        "lightgbm": lgb.__version__, "python": sys.version.split()[0]}
    SPLITS = (("solute_scaffold", "leave_scaffold_out", False),
              ("solute_canon", "leaky_no_group_protection_positive_control", True))
    for gc, nm, leaky in SPLITS:
        results["splits"].append(run_split(feat.copy(), feat_cols, gc, nm, leaky=leaky))
    results["wall_seconds"] = round(time.time() - t0, 1)
    BENCH.mkdir(parents=True, exist_ok=True)
    with open(BENCH / f"diagnostic.{sys.argv[1]}.json", "w") as f:
        json.dump(results, f, indent=2, sort_keys=True)
    for s in results["splits"]:
        bb = min(s["baselines"].values(), key=lambda d: d["rmse"])
        print(f"SUMMARY {s['split']}: model RMSE={s['model']['rmse']:.4f} "
              f"CI={s['model']['rmse_ci95_cluster_bootstrap']} R2={s['model']['r2']:.3f} | "
              f"best_baseline RMSE={bb['rmse']:.4f}", flush=True)


if __name__ == "__main__":
    main()
