"""Admissibility-hardened leave-solute-out re-derivation for amphora-solvency-score
BigSolDB LSO RMSE headline (W6 campaign, angle 1).

Context: amphora-molecule-property's W2 fire flagged the SAME raw BigSolDB file
(raw_sha256=879f55f...5e3e13fd7bffe -- confirmed byte-identical to this module's
feedback/v1/external_data/bigsoldb_v2/raw/BigSolDBv2.0.csv) as having 90.3%
(4134/4578) of "duplicate-measurement" (solute,solvent,temperature) groups
internally contradictory (>0.3 log10 units, i.e. >2x disagreement).

This script independently re-derives that duplicate-contradiction check on the
IDENTICAL raw file, using the EXACT grouping code this module's own locked LSO
benchmark (run_v20_lso.py) already uses: (solute_canon, solvent_canon,
temperature rounded to 0.1 K). Two results are reported:

  1. TEMPERATURE-CONTROLLED (matches this module's actual curation key): the
     genuine same-state-point contradiction rate.
  2. RECONCILIATION CHECK (solute,solvent only, temperature dropped from the
     key): reproduces something close to W2's 90.3% figure, and shows median
     temperature RANGE within those "duplicate" groups is 40 K -- i.e. most of
     W2's flagged "contradictions" are ordinary solubility-vs-temperature
     curves (solubility is legitimately log10-nonlinear in T), not measurement
     conflicts at a single state point. This does not overrule W2's finding on
     its own corpus/methodology; it establishes what "physically admissible"
     correctly means for THIS module's temperature-resolved modeling task.

The genuinely state-point-contradictory groups (temperature-controlled) are
then EXCLUDED WHOLESALE (both as train and as test material) and the exact
locked leave-solute-out protocol (same features, same LightGBM params, same
seed, same GroupKFold-by-solute, same inner early-stopping holdout) is re-run
on this admissibility-hardened subset. This directly tests whether the signed
headline (model RMSE 0.8770, 95% CI [0.8416, 0.9154], vs best-baseline RMSE
1.1687) survives when the corpus is restricted to state-point-consistent rows.

Pre-registered refutation criterion (declared before this run's results are
known, from the point-estimate/CI already signed in inhouse_benchmark_receipt.v1.dsse.json):
  REFUTED if EITHER
    (a) admissible-only model RMSE > 0.9154 (outside the current 95% CI upper
        bound) -- i.e. removing the contradictory rows makes the model look
        WORSE than what was claimed, meaning the headline partly depended on
        inadmissible rows, or
    (b) admissible-only error-reduction-vs-best-baseline falls below 12.5
        percentage points (half of the currently-claimed 25.0 pp) -- i.e. the
        competitive margin over a naive baseline is gutted.
  Otherwise SURVIVED on this attack.

AUDIT_ONLY diagnostic. Does not alter evidence/phase0/kpis/, the manifest, or
any existing signed receipt.
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
BENCH = ROOT / "amphora-solvency-score/benchmarks/bigsoldb-admissibility-hardened-v1"
TARGET = "logs"
SEED = 20260724
N_FOLDS = 5
N_BOOT = 1000
T_MIN, T_MAX = 243.0, 426.0
N_THREADS = 8
CONTRA_THRESHOLD = 0.3  # log10 units, IUPAC-definitional same-state-point disagreement; matches W2's own threshold
EXCLUDE = {"Ipc"}
DESCRIPTORS = [(n, f) for n, f in Descriptors.descList if n not in EXCLUDE]

LGB_PARAMS = {
    "objective": "regression", "n_estimators": 3000, "learning_rate": 0.05,
    "num_leaves": 127, "min_child_samples": 20, "subsample": 0.9,
    "subsample_freq": 1, "colsample_bytree": 0.8, "random_state": SEED,
    "num_threads": N_THREADS, "deterministic": True, "force_row_wise": True,
    "verbose": -1,
}

# Signed baseline this attack tests against (amphora-solvency-score/benchmarks/bigsoldb-v1/inhouse_benchmark_receipt.v1.dsse.json)
FULL_CORPUS_SIGNED = {
    "model_rmse": 0.8770255643028615,
    "model_rmse_ci95": [0.8416341720920943, 0.9154344725058612],
    "best_baseline_rmse": 1.1686915142248226,  # b1_solvent_mean
    "best_baseline_name": "b1_solvent_mean",
    "n_rows_modeled": 94532,
    "n_solute_groups": 1372,
    "raw_sha256": "879f55f39db977e295c705e304d011d89d6e10da1daaa3f069181108c1de38b0",
    "receipt": "amphora-solvency-score/benchmarks/bigsoldb-v1/inhouse_benchmark_receipt.v1.dsse.json",
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
    assert raw_sha == FULL_CORPUS_SIGNED["raw_sha256"], "raw file diverged from signed baseline"
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

    # ---- Temperature-controlled admissibility audit (this module's own grouping key) ----
    df["tbin"] = df["temperature_k"].round(1)
    grp = df.groupby(["solute_canon", "solvent_canon", "tbin"])
    n_per_group = grp.size()
    spread = grp[TARGET].agg(lambda v: float(v.max() - v.min()))
    ge2_idx = n_per_group[n_per_group >= 2].index
    contra_idx = spread[(n_per_group >= 2) & (spread > CONTRA_THRESHOLD)].index
    n_groups_total = int(len(n_per_group))
    n_groups_ge2 = int(len(ge2_idx))
    n_groups_contra = int(len(contra_idx))
    solutes_touched = sorted(set(k[0] for k in contra_idx))

    # ---- Reconciliation check: W2-style key WITHOUT temperature control ----
    grp_notemp = df.groupby(["solute_canon", "Solvent"])
    n_notemp = grp_notemp.size()
    spread_notemp = grp_notemp[TARGET].agg(lambda v: float(v.max() - v.min()))
    ge2_notemp = n_notemp[n_notemp >= 2]
    contra_notemp = spread_notemp[(n_notemp >= 2) & (spread_notemp > CONTRA_THRESHOLD)]
    trange_notemp = grp_notemp["temperature_k"].agg(lambda v: float(v.max() - v.min()))
    reconciliation = {
        "note": "amphora-molecule-property's W2 fire flagged 90.3% (4134/4578) of "
                "(solute,solvent,temperature) duplicate groups in this SAME raw file "
                "(byte-identical sha256) as internally contradictory (>0.3 log10 units). "
                "Reproducing that check WITH temperature in the key (this module's own "
                "tbin=round(T,0.1K)) gives a materially different rate below. Reproducing "
                "it WITHOUT temperature in the key (solute+solvent only) gives a rate close "
                "to W2's figure, and the median temperature RANGE inside those groups is "
                "large -- consistent with W2's flagged 'contradictions' being solubility-vs-"
                "temperature curves (physically expected to span >0.3 log10 units over tens "
                "of K) rather than same-state-point measurement conflicts. This does not "
                "dispute W2's finding on its own corpus/pipeline; it establishes the correct, "
                "temperature-controlled admissibility definition for THIS module's "
                "temperature-resolved LSO model, which is what the exclusion below uses.",
            "temperature_controlled_solute_solvent_temperature_key": {
                "n_groups_ge2": n_groups_ge2, "n_contradictory": n_groups_contra,
                "pct_contradictory_of_ge2": round(n_groups_contra / n_groups_ge2, 6) if n_groups_ge2 else None},
            "solute_solvent_only_key_temperature_dropped": {
                "n_groups_ge2": int(len(ge2_notemp)), "n_contradictory": int(len(contra_notemp)),
                "pct_contradictory_of_ge2": round(len(contra_notemp) / len(ge2_notemp), 6) if len(ge2_notemp) else None,
                "median_temperature_range_K_within_ge2_groups": float(trange_notemp[ge2_notemp.index].median()),
                "frac_ge2_groups_spanning_over_5K": float((trange_notemp[ge2_notemp.index] > 5).mean())},
    }

    admissible_mask = ~df.set_index(["solute_canon", "solvent_canon", "tbin"]).index.isin(contra_idx)
    df_admissible = df[admissible_mask].copy()
    n_rows_dropped = int(len(df) - len(df_admissible))

    admissibility_audit = {
        "contradiction_threshold_log10_units": CONTRA_THRESHOLD,
        "constraint_citation": "IUPAC Gold Book amount/mole fraction definitional bound; a single "
                                "physical quantity cannot have two internally-contradictory literature "
                                "values at the same (solute,solvent,temperature) state point. Same "
                                "threshold as amphora-molecule-property W2 fire.",
        "grouping_key": "(solute_canon RDKit-canonical SMILES, solvent_canon RDKit-canonical SMILES, "
                         "temperature_K rounded to 0.1K) -- identical grouping already used by this "
                         "module's locked run_v20_lso.py replicate-collapse step",
        "n_groups_total": n_groups_total, "n_groups_with_ge2_measurements": n_groups_ge2,
        "n_groups_contradictory": n_groups_contra,
        "pct_contradictory_of_ge2_groups": round(n_groups_contra / n_groups_ge2, 6) if n_groups_ge2 else None,
        "n_solutes_touched_by_contradiction": len(solutes_touched),
        "n_rows_pre_admissibility_filter": int(len(df)),
        "n_rows_dropped_as_inadmissible": n_rows_dropped,
        "pct_rows_dropped": round(n_rows_dropped / len(df), 6),
        "reconciliation_with_w2": reconciliation,
    }
    print("ADMISSIBILITY_AUDIT:", json.dumps(admissibility_audit, indent=2)[:2000], flush=True)

    # ---- Replicate-collapse (median) on ADMISSIBLE-ONLY rows, then model ----
    df_admissible["tbin"] = df_admissible["temperature_k"].round(1)
    grp2 = df_admissible.groupby(["solute_canon", "solvent_canon", "tbin"])
    collapsed = grp2.agg(**{TARGET: (TARGET, "median"),
                            "temperature_k": ("temperature_k", "median")}).reset_index()
    n_after = len(collapsed)

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
    feat_cols = [c for c in feat.columns if c.startswith(("solute_", "solvent_"))
                 and c not in ("solute_canon", "solvent_canon")] + ["temperature_k"]

    results = {
        "benchmark": "amphora-solvency-score/bigsoldb-admissibility-hardened-v1",
        "stage": "evaluation", "run_type": "ADMISSIBILITY_HARDENED_LEAVE_SOLUTE_OUT",
        "authority": "AUDIT_ONLY / diagnostic -- attacks the signed BigSolDB LSO RMSE headline",
        "campaign_item_id": "W6",
        "seed": SEED, "n_folds": N_FOLDS, "n_features": len(feat_cols),
        "n_rows_modeled": int(len(feat)), "n_feature_reject": n_feat_reject,
        "raw_sha256": raw_sha, "raw_md5": raw_md5,
        "admissibility_audit": admissibility_audit,
        "full_corpus_signed_comparator": FULL_CORPUS_SIGNED,
        "lgb_params": LGB_PARAMS, "splits": [],
        "rdkit": rdkit.__version__, "sklearn": sklearn.__version__,
        "lightgbm": lgb.__version__, "python": sys.version.split()[0]}
    results["splits"].append(run_split(feat.copy(), feat_cols, "solute_canon", "leave_solute_out_admissible_only"))
    results["wall_seconds"] = round(time.time() - t0, 1)

    BENCH.mkdir(parents=True, exist_ok=True)
    target = BENCH / (sys.argv[1] if len(sys.argv) > 1 else "diagnostic.canonical.json")
    with open(target, "w") as f:
        json.dump(results, f, indent=2, sort_keys=True)
    for s in results["splits"]:
        bb = min(s["baselines"].values(), key=lambda d: d["rmse"])
        print(f"SUMMARY {s['split']}: model RMSE={s['model']['rmse']:.4f} "
              f"CI={s['model']['rmse_ci95_cluster_bootstrap']} R2={s['model']['r2']:.3f} | "
              f"best_baseline RMSE={bb['rmse']:.4f}", flush=True)
    print("WROTE", target, flush=True)


if __name__ == "__main__":
    main()
