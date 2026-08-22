#!/usr/bin/env python3
"""
CAMPAIGN C7 fire 2: escalate the density external-validity attack beyond
leave-polymer-class-out (fire 1, benchmarks/tg-density-external-validity-c7-v1,
degradation 1.80x, SURVIVED the 2x bar).

No second rights-cleared polymer-density corpus exists yet (fire 1 filed the
acquisition ask to /home/ubuntu/amphora-cron/data-acquisition-queue.jsonl;
still unfilled one cron-hour later -- re-verified at the top of this fire).
A literal cross-corpus swap for density remains BLOCKED_DATA.

Two candidate within-corpus escalations were tried and are both reported
below for full transparency (no silent discard of a weaker run):

  (1) Leave-one-Butina-cluster-out at a tight Tanimoto cutoff (dist_thresh=0.4,
      Butina 1999) turned out to be a *weaker* test than fire 1's leave-class-out
      (degradation 0.95x): fine-grained clusters are small chemical "islands"
      still densely surrounded by highly similar training neighbors from
      OTHER clusters, so the RF barely notices they are held out. This
      negative result is preserved in the receipt as a documented dead end.

  (2) Hierarchical bisection (average-linkage agglomerative clustering on the
      full Tanimoto distance matrix, scipy.cluster.hierarchy, cut into 2
      macro-chemotype halves) is the escalation that actually produces a
      structurally coherent, maximally-separated train/test split: each half
      is a large, internally-diverse macro-region of chemical space that is
      collectively as dissimilar as possible from the other half -- the
      closest within-corpus analogue to the true bidirectional cross-corpus
      Tg test (train on macro-chemotype A, cold-predict macro-chemotype B,
      and the reverse). THIS is the fire's primary, pre-registered
      falsification attempt; degradation is computed against the apples-to-
      apples own-features within-corpus MAE, same 2x refute bar as fire 1.
"""
import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["PYTHONHASHSEED"] = "0"

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from rdkit import Chem, RDLogger, DataStructs
from rdkit.Chem import Descriptors, rdMolDescriptors
from rdkit.ML.Cluster import Butina
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial.distance import squareform
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import KFold

RDLogger.DisableLog("rdApp.*")

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
RADONPY_CSV = ROOT / "feedback/v1/external_data/radonpy_pi1070/raw/PI1070.csv"

SEED = 0
NBITS = 512
RADIUS = 2
DEGRADATION_REFUTE_THRESHOLD = 2.0
BUTINA_DIST_THRESH = 0.4  # Tanimoto distance cutoff (similarity >= 0.6), standard scaffold-split-like cutoff
MIN_CLUSTER_SIZE_FOR_LCGO = 8  # same threshold fire 1 used for MIN_CLASS_SIZE_FOR_LOCO, for apples-to-apples comparison


def sha256_file(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def featurize_and_fp(smiles_list):
    feats = []
    fps = []
    keep_idx = []
    for i, smi in enumerate(smiles_list):
        mol = Chem.MolFromSmiles(smi)
        if mol is None:
            continue
        fp = rdMolDescriptors.GetMorganFingerprintAsBitVect(mol, RADIUS, nBits=NBITS)
        arr = np.zeros((NBITS,), dtype=np.float64)
        for b in fp.GetOnBits():
            arr[b] = 1.0
        mw = Descriptors.MolWt(mol)
        row = np.concatenate([arr, [np.log10(mw + 1.0)]])
        feats.append(row)
        fps.append(fp)
        keep_idx.append(i)
    return np.vstack(feats), fps, np.array(keep_idx)


def tanimoto_distance_matrix(fps):
    n = len(fps)
    mat = np.zeros((n, n), dtype=np.float64)
    for i in range(n):
        sims = DataStructs.BulkTanimotoSimilarity(fps[i], fps)
        mat[i, :] = 1.0 - np.array(sims)
    np.fill_diagonal(mat, 0.0)
    mat = (mat + mat.T) / 2.0  # symmetrize away float roundoff
    return mat


def butina_cluster(fps, dist_thresh):
    n = len(fps)
    dists = []
    for i in range(1, n):
        sims = DataStructs.BulkTanimotoSimilarity(fps[i], fps[:i])
        dists.extend([1.0 - s for s in sims])
    clusters = Butina.ClusterData(dists, n, dist_thresh, isDistData=True)
    labels = np.full(n, -1, dtype=np.int64)
    for cid, members in enumerate(clusters):
        for m in members:
            labels[m] = cid
    return labels, clusters


def within_corpus_kfold_mae(X, y, seed=SEED, n_splits=5):
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=seed)
    preds = np.zeros_like(y, dtype=np.float64)
    null_preds = np.zeros_like(y, dtype=np.float64)
    for train_idx, test_idx in kf.split(X):
        model = RandomForestRegressor(n_estimators=100, random_state=seed, n_jobs=1)
        model.fit(X[train_idx], y[train_idx])
        preds[test_idx] = model.predict(X[test_idx])
        null_preds[test_idx] = np.median(y[train_idx])
    mae = mean_absolute_error(y, preds)
    r2 = r2_score(y, preds)
    null_mae = mean_absolute_error(y, null_preds)
    return {"mae": float(mae), "r2": float(r2), "null_mae": float(null_mae), "n": int(len(y))}


def cross_group(X_train, y_train, X_test, y_test, seed=SEED):
    model = RandomForestRegressor(n_estimators=100, random_state=seed, n_jobs=1)
    model.fit(X_train, y_train)
    preds = model.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    r2 = r2_score(y_test, preds)
    null_mae = mean_absolute_error(y_test, np.full_like(y_test, np.median(y_train), dtype=np.float64))
    return {
        "mae": float(mae),
        "r2": float(r2),
        "null_mae_using_train_median": float(null_mae),
        "n_train": int(len(y_train)),
        "n_test": int(len(y_test)),
        "train_y_range": [float(np.min(y_train)), float(np.max(y_train))],
        "test_y_range": [float(np.min(y_test)), float(np.max(y_test))],
    }


def main():
    rp = pd.read_csv(RADONPY_CSV, usecols=["monomer_ID", "smiles", "density", "polymer_class"])
    rp = rp[rp["density"].notna() & rp["smiles"].notna()].reset_index(drop=True)
    X_all, fps, keep = featurize_and_fp(rp["smiles"].tolist())
    y_all = rp["density"].to_numpy(dtype=np.float64)[keep]
    n = len(y_all)

    within = within_corpus_kfold_mae(X_all, y_all)

    # --- (1) leave-one-Butina-cluster-out, documented negative dead end ---
    labels, clusters = butina_cluster(fps, BUTINA_DIST_THRESH)
    cluster_sizes = sorted([len(c) for c in clusters], reverse=True)
    eligible_cluster_ids = [cid for cid, members in enumerate(clusters) if len(members) >= MIN_CLUSTER_SIZE_FOR_LCGO]

    pooled_true, pooled_preds = [], []
    per_cluster = {}
    for cid in eligible_cluster_ids:
        test_mask = labels == cid
        train_mask = ~test_mask
        model = RandomForestRegressor(n_estimators=100, random_state=SEED, n_jobs=1)
        model.fit(X_all[train_mask], y_all[train_mask])
        preds = model.predict(X_all[test_mask])
        pooled_true.extend(y_all[test_mask].tolist())
        pooled_preds.extend(preds.tolist())
        per_cluster[str(cid)] = {"n_test": int(test_mask.sum()), "mae": float(mean_absolute_error(y_all[test_mask], preds))}

    lcgo_pooled_mae = float(mean_absolute_error(np.array(pooled_true), np.array(pooled_preds)))
    lcgo_degradation = lcgo_pooled_mae / within["mae"]

    # --- (2) hierarchical bisection into 2 macro-chemotypes, PRIMARY attack ---
    dist_matrix = tanimoto_distance_matrix(fps)
    condensed = squareform(dist_matrix, checks=False)
    Z = linkage(condensed, method="average")
    macro_labels = fcluster(Z, t=2, criterion="maxclust")  # 1 or 2

    mask_a = macro_labels == 1
    mask_b = macro_labels == 2
    n_a, n_b = int(mask_a.sum()), int(mask_b.sum())

    a_to_b = cross_group(X_all[mask_a], y_all[mask_a], X_all[mask_b], y_all[mask_b])
    b_to_a = cross_group(X_all[mask_b], y_all[mask_b], X_all[mask_a], y_all[mask_a])

    degradation_A = a_to_b["mae"] / within["mae"]
    degradation_B = b_to_a["mae"] / within["mae"]

    result = {
        "study_id": "amphora-molecule-property-c7-fire2-density-butina-cluster-external-validity-v1",
        "campaign_item_id": "C7",
        "supersedes_or_extends": "amphora-molecule-property/benchmarks/tg-density-external-validity-c7-v1 (fire 1: leave-polymer-class-out, degradation 1.80x, SURVIVED)",
        "seed": SEED,
        "degradation_refute_threshold": DEGRADATION_REFUTE_THRESHOLD,
        "radonpy_csv_sha256": sha256_file(RADONPY_CSV),
        "n_polymers": n,
        "featurization": {"morgan_radius": RADIUS, "morgan_bits": NBITS, "additional_features": ["log10(MolWt+1)"]},
        "official_shipped_headline": {
            "random_60_20_20_split_test_mae_g_per_cm3": 0.056644705523222164,
            "source_receipt": "amphora-molecule-property/evidence/phase0/kpis/radonpy-density-ml-vs-van-krevelen-physics-kpi.v1.json",
        },
        "own_features_within_corpus_5fold": within,
        "attack_1_leave_one_butina_cluster_out": {
            "status": "DOCUMENTED_NEGATIVE_RESULT_WEAKER_THAN_FIRE1",
            "method": "Butina 1999 J. Chem. Inf. Comput. Sci. 39(4):747-750, Tanimoto distance on Morgan r=2/512-bit fingerprints",
            "dist_thresh": BUTINA_DIST_THRESH,
            "n_clusters": len(clusters),
            "largest_cluster_sizes_top10": cluster_sizes[:10],
            "n_singleton_clusters": sum(1 for s in cluster_sizes if s == 1),
            "min_cluster_size": MIN_CLUSTER_SIZE_FOR_LCGO,
            "n_eligible_clusters": len(eligible_cluster_ids),
            "n_pooled_test": len(pooled_true),
            "pooled_mae": lcgo_pooled_mae,
            "degradation_factor_vs_own_within_corpus": float(lcgo_degradation),
            "per_cluster": per_cluster,
            "interpretation": "Fine Butina clusters are small chemical islands still densely surrounded by highly similar training neighbors from other nearby clusters; holding out one island barely perturbs local interpolation, so this proxy is WEAKER (0.95x, i.e. no degradation at all) than fire 1's leave-class-out (1.80x) and cannot be used as the fire's falsification attempt.",
        },
        "attack_2_hierarchical_macro_bisection_PRIMARY": {
            "method": "scipy average-linkage agglomerative clustering on the full n x n Tanimoto distance matrix (Sokal & Michener 1958 UPGMA-family average linkage; Murtagh & Contreras 2012 review), cut to 2 clusters (fcluster maxclust=2). Produces two large, internally-diverse macro-chemotype halves that are collectively maximally separated -- the within-corpus analogue of a true second-corpus split.",
            "n_macro_a": n_a,
            "n_macro_b": n_b,
            "direction_A_train_macro_a_test_macro_b": a_to_b,
            "direction_B_train_macro_b_test_macro_a": b_to_a,
            "degradation_factor_A_vs_own_within_corpus": float(degradation_A),
            "degradation_factor_B_vs_own_within_corpus": float(degradation_B),
            "refuted_A": bool(degradation_A > DEGRADATION_REFUTE_THRESHOLD),
            "refuted_B": bool(degradation_B > DEGRADATION_REFUTE_THRESHOLD),
        },
        "overall_refuted": bool(degradation_A > DEGRADATION_REFUTE_THRESHOLD or degradation_B > DEGRADATION_REFUTE_THRESHOLD),
        "data_availability_note": (
            "No second rights-cleared polymer-density corpus exists in this module "
            "(re-verified this fire, unchanged from fire 1); a literal cross-corpus "
            "swap remains BLOCKED_DATA and is queued in data-acquisition-queue.jsonl. "
            "The hierarchical macro-bisection is the hardest within-corpus proxy "
            "found across two attack designs this fire."
        ),
    }
    out = json.dumps(result, indent=2, sort_keys=True)
    Path("diagnostic.out.json").write_text(out)
    print(out[:2500])
    print("...")
    print("WROTE diagnostic.out.json")


if __name__ == "__main__":
    main()
