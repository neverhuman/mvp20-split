#!/usr/bin/env python3
"""
W7 (ROTATION fire): escalate the C7-fire2 hierarchical macro-bisection
external-validity attack -- previously applied only to RadonPy PI1070
density (REFUTED, 13.74x/7.59x degradation) and already known-inadmissible
for static_dielectric_const (C8/W2, label-integrity REFUTED) -- to the two
RadonPy PI1070 properties in
amphora-molecule-property/evidence/phase0/kpis/multi-target-ml-radonpy-4-properties-audit-kpi.v1.json
that have NEVER been attacked with a group-safe split: refractive_index
(shipped single-task R2=+0.893, the single strongest number in that KPI)
and thermal_conductivity (shipped single-task R2=+0.542).

That KPI's own metadata records split_methodology="60/20/20 deterministic
(seed=0)" -- an ordinary random row split, not scaffold/group-safe -- on
the SAME RadonPy PI1070 corpus that density and dielectric were drawn from.
Reusing the identical, already-validated attack design (hierarchical
average-linkage agglomerative clustering on the full Tanimoto distance
matrix, cut into 2 macro-chemotype halves, bidirectional cross-group
train/test) is the correct escalation: same corpus, same featurization,
same pre-registered 2x-MAE-degradation refute bar as C7 fire 2's density
attack (amphora-molecule-property/benchmarks/density-butina-cluster-external-validity-c7-v2).

Pre-registered refute criterion (identical to C7 fire 2, applied per property):
  cross-macro-chemotype MAE (either direction) > 2x the apples-to-apples
  own-features within-corpus 5-fold MAE => REFUTED for that property.
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
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial.distance import squareform
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import KFold

RDLogger.DisableLog("rdApp.*")

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
RADONPY_CSV = ROOT / "feedback/v1/external_data/radonpy_pi1070/raw/PI1070.csv"
MULTITARGET_KPI = ROOT / "amphora-molecule-property/evidence/phase0/kpis/multi-target-ml-radonpy-4-properties-audit-kpi.v1.json"

SEED = 0
NBITS = 512
RADIUS = 2
DEGRADATION_REFUTE_THRESHOLD = 2.0
TARGET_PROPS = ["refractive_index", "thermal_conductivity"]


def sha256_file(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def featurize_and_fp(smiles_list):
    feats, fps, keep_idx = [], [], []
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
    mat = (mat + mat.T) / 2.0
    return mat


def within_corpus_kfold(X, y, seed=SEED, n_splits=5):
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=seed)
    preds = np.zeros_like(y, dtype=np.float64)
    for train_idx, test_idx in kf.split(X):
        model = RandomForestRegressor(n_estimators=100, random_state=seed, n_jobs=1)
        model.fit(X[train_idx], y[train_idx])
        preds[test_idx] = model.predict(X[test_idx])
    mae = mean_absolute_error(y, preds)
    r2 = r2_score(y, preds)
    return {"mae": float(mae), "r2": float(r2), "n": int(len(y))}


def cross_group(X_train, y_train, X_test, y_test, seed=SEED):
    model = RandomForestRegressor(n_estimators=100, random_state=seed, n_jobs=1)
    model.fit(X_train, y_train)
    preds = model.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    r2 = r2_score(y_test, preds)
    null_mae = mean_absolute_error(y_test, np.full_like(y_test, np.median(y_train), dtype=np.float64))
    return {
        "mae": float(mae), "r2": float(r2),
        "null_mae_using_train_median": float(null_mae),
        "n_train": int(len(y_train)), "n_test": int(len(y_test)),
        "train_y_range": [float(np.min(y_train)), float(np.max(y_train))],
        "test_y_range": [float(np.min(y_test)), float(np.max(y_test))],
    }


def main():
    usecols = ["monomer_ID", "smiles", "density", "static_dielectric_const",
               "refractive_index", "thermal_conductivity"]
    rp = pd.read_csv(RADONPY_CSV, usecols=usecols)
    # Same "all 4 co-reported properties present" filter the shipped multi-target KPI uses (n=1068).
    mask4 = (rp["density"].notna() & rp["static_dielectric_const"].notna() &
             rp["refractive_index"].notna() & rp["thermal_conductivity"].notna() &
             rp["smiles"].notna())
    rp4 = rp[mask4].reset_index(drop=True)

    X_all, fps, keep = featurize_and_fp(rp4["smiles"].tolist())
    rp4 = rp4.iloc[keep].reset_index(drop=True)

    dist_matrix = tanimoto_distance_matrix(fps)
    condensed = squareform(dist_matrix, checks=False)
    Z = linkage(condensed, method="average")
    macro_labels = fcluster(Z, t=2, criterion="maxclust")
    mask_a = macro_labels == 1
    mask_b = macro_labels == 2
    n_a, n_b = int(mask_a.sum()), int(mask_b.sum())

    per_property = {}
    overall_refuted = False
    for prop in TARGET_PROPS:
        y_all = rp4[prop].to_numpy(dtype=np.float64)
        within = within_corpus_kfold(X_all, y_all)
        a_to_b = cross_group(X_all[mask_a], y_all[mask_a], X_all[mask_b], y_all[mask_b])
        b_to_a = cross_group(X_all[mask_b], y_all[mask_b], X_all[mask_a], y_all[mask_a])
        degradation_A = a_to_b["mae"] / within["mae"]
        degradation_B = b_to_a["mae"] / within["mae"]
        refuted_A = bool(degradation_A > DEGRADATION_REFUTE_THRESHOLD)
        refuted_B = bool(degradation_B > DEGRADATION_REFUTE_THRESHOLD)
        overall_refuted = overall_refuted or refuted_A or refuted_B
        per_property[prop] = {
            "shipped_multi_task_r2_random_60_20_20_split": None,
            "own_features_within_corpus_5fold": within,
            "direction_A_train_macro_a_test_macro_b": a_to_b,
            "direction_B_train_macro_b_test_macro_a": b_to_a,
            "degradation_factor_A": float(degradation_A),
            "degradation_factor_B": float(degradation_B),
            "refuted_A": refuted_A,
            "refuted_B": refuted_B,
            "property_refuted": bool(refuted_A or refuted_B),
        }

    shipped = json.loads(MULTITARGET_KPI.read_text())["observed_kpi_summary"]
    for prop in TARGET_PROPS:
        per_property[prop]["shipped_multi_task_r2_random_60_20_20_split"] = shipped["multi_task_R2_per_property"][prop]
        per_property[prop]["shipped_single_task_r2_random_60_20_20_split"] = shipped["single_task_R2_per_property"][prop]

    result = {
        "study_id": "amphora-molecule-property-w7-multitarget-macro-bisection-external-validity-v1",
        "campaign_item_id": "",
        "claim_under_attack": {
            "receipt_path": "amphora-molecule-property/evidence/phase0/kpis/multi-target-ml-radonpy-4-properties-audit-kpi.v1.json",
            "claim_text": "single-task RF R2>0 on RadonPy PI1070 refractive_index (+0.893) and thermal_conductivity (+0.542) under a 60/20/20 deterministic random split generalizes.",
        },
        "seed": SEED,
        "degradation_refute_threshold": DEGRADATION_REFUTE_THRESHOLD,
        "radonpy_csv_sha256": sha256_file(RADONPY_CSV),
        "multitarget_kpi_sha256": sha256_file(MULTITARGET_KPI),
        "n_polymers_all_4_properties_present": int(len(rp4)),
        "featurization": {"morgan_radius": RADIUS, "morgan_bits": NBITS, "additional_features": ["log10(MolWt+1)"]},
        "macro_bisection": {
            "method": "scipy average-linkage agglomerative clustering on full n x n Tanimoto distance matrix (Sokal & Michener 1958 UPGMA-family; Murtagh & Contreras 2012 review), cut to 2 clusters (fcluster maxclust=2). Identical method to C7 fire 2 (density), applied on the same-corpus 4-property-complete subset (n=1068-ish) instead of the density-only subset (n=1077).",
            "n_macro_a": n_a,
            "n_macro_b": n_b,
        },
        "per_property": per_property,
        "overall_refuted": bool(overall_refuted),
        "prior_related_findings": {
            "density_same_corpus_same_method": "C7 fire 2/3: REFUTED, degradation 13.74x/7.59x (benchmarks/density-butina-cluster-external-validity-c7-v2)",
            "dielectric_same_corpus": "C8/W2: static_dielectric_const label itself found physically inadmissible (Frohlich eps>=n^2 violated in 89.5% of PI1070 rows); R2 collapses to <=0 on the physically-valid subset alone (c8_fire2_dielectric_clean_subset_receipt.v1.json)",
        },
    }
    out = json.dumps(result, indent=2, sort_keys=True)
    Path("diagnostic.out.json").write_text(out)
    print(out[:3000])
    print("...")
    print("WROTE diagnostic.out.json")


if __name__ == "__main__":
    main()
