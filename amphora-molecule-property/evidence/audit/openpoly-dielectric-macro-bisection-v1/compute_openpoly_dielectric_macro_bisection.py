#!/usr/bin/env python3
"""
ROTATION fire (2026-08-17): escalate the C7/W7 hierarchical macro-bisection
external-validity attack to openpoly-dielectric-constant-ml-baseline-kpi.v1.json
-- the strongest still-standing "REAL POSITIVE LIFT" claim in
amphora-molecule-property (RandomForest scaffold-safe holdout MAE=0.4040 vs
NULL 0.7027, LOSO-CV R2=+0.659, n=295).

This KPI has already survived ONE falsifying attack (2026-08-14, physical-
admissibility of the OpenPoly dielectric labels themselves: 0/295 violations
of Frohlich/Maxwell/Clausius-Mossotti/Lorentz-Lorenz inequalities). That
audit's own recommended_followups explicitly flagged this as the next open
attack: "a harder scaffold-safe or macro-bisection external-validity attack,
in the style of C7/W7, remains open for this KPI's MODEL claims as opposed
to its LABEL claims". This fire runs exactly that attack.

Every prior application of this identical method inside this module has
REFUTED the target (C7 fire2: density 13.74x/7.59x degradation; W7:
refractive_index + thermal_conductivity, both directions > 2x). The KPI's
existing "raw Bemis-Murcko scaffold-safe 80/20 holdout" split and "111-fold
LOSO-CV" are both LOCAL/fine-grained group-safe splits (single scaffold held
out at a time); neither tests transfer across a structurally distant
macro-chemotype boundary the way a 2-way Tanimoto-distance bisection does.

Pre-registered refute criterion (identical threshold to C7 fire2 / W7):
  cross-macro-chemotype MAE (either direction) > 2x the own-features
  within-corpus 5-fold MAE => REFUTED.
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
OPENPOLY_CSV = ROOT / "feedback/v1/external_data/openpoly_benchmark/raw/final_polymer_properties_fromliterature.csv"
TARGET_KPI = ROOT / "amphora-molecule-property/evidence/phase0/kpis/openpoly-dielectric-constant-ml-baseline-kpi.v1.json"

SEED = 0
NBITS = 512
RADIUS = 2
DEGRADATION_REFUTE_THRESHOLD = 2.0
PROP_COL = "Dielectric Constant Total"


def sha256_file(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


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


K_SUBCLUSTERS = 12


def balanced_macro_bisection(macro_labels_k):
    """scipy fcluster(t=2, criterion='maxclust') on this 295-molecule OpenPoly
    corpus produces a DEGENERATE top-level split (294 vs 1: a single Tanimoto
    outlier peels off the whole dendrogram before any real bisection happens
    -- confirmed empirically, see degenerate_naive_2cut in the result). A
    macro-bisection whose smaller side has n_train=1 cannot fit any model
    (R2 undefined, MAE reflects one arbitrary point) and is not a genuine test
    of cross-chemotype generalization -- reporting a verdict off it would be
    an artifact of dendrogram topology, not a real falsification. Fix, kept
    faithful to the exact same clustering primitives C7/W7 already used
    (average-linkage UPGMA on the full Tanimoto distance matrix): cut the same
    dendrogram at K_SUBCLUSTERS=12 (chosen because it is the smallest k at
    which every one of the resulting sub-clusters has size >= 1 and the two
    largest sub-clusters are no longer a single dominant blob -- sizes at
    k=12 are [120, 93, 51, 11, 5, 5, 4, 2, 1, 1, 1, 1]), then greedily bin-pack
    the 12 intact sub-clusters (largest first, always placed into whichever
    macro-side currently has fewer molecules) into exactly two macro-chemotype
    halves. Every one of the 12 base sub-clusters -- each internally coherent
    under the SAME Tanimoto/average-linkage geometry -- stays wholly on one
    side; only whole sub-clusters move, never individual molecules split out
    of their nearest-neighborhood group."""
    sizes = np.bincount(macro_labels_k)[1:]
    order = np.argsort(-sizes)  # cluster ids (0-indexed order), largest first
    bin_size = [0, 0]
    bin_of_cluster = {}
    for ci in order:
        cluster_id = ci + 1
        side = 0 if bin_size[0] <= bin_size[1] else 1
        bin_of_cluster[cluster_id] = side
        bin_size[side] += int(sizes[ci])
    macro_side = np.array([bin_of_cluster[c] for c in macro_labels_k])
    return macro_side, bin_size


def run(smiles_list, y_all):
    """Full pipeline given a smiles list + property array (allows re-run on a
    corrupted copy for the positive control)."""
    X_all, fps, keep = featurize_and_fp(smiles_list)
    y_all = y_all[keep]

    dist_matrix = tanimoto_distance_matrix(fps)
    condensed = squareform(dist_matrix, checks=False)
    Z = linkage(condensed, method="average")

    naive2 = fcluster(Z, t=2, criterion="maxclust")
    naive_sizes = sorted(int(c) for c in np.bincount(naive2)[1:])
    degenerate_naive_2cut = {
        "sizes": naive_sizes,
        "degenerate": bool(min(naive_sizes) < 10),
        "note": "raw fcluster(maxclust=2) sizes on THIS run's molecule set, reported for transparency; NOT used for the verdict when degenerate.",
    }

    labels_k = fcluster(Z, t=K_SUBCLUSTERS, criterion="maxclust")
    macro_side, bin_size = balanced_macro_bisection(labels_k)
    mask_a = macro_side == 0
    mask_b = macro_side == 1
    n_a, n_b = int(mask_a.sum()), int(mask_b.sum())

    within = within_corpus_kfold(X_all, y_all)
    a_to_b = cross_group(X_all[mask_a], y_all[mask_a], X_all[mask_b], y_all[mask_b])
    b_to_a = cross_group(X_all[mask_b], y_all[mask_b], X_all[mask_a], y_all[mask_a])
    degradation_A = a_to_b["mae"] / within["mae"]
    degradation_B = b_to_a["mae"] / within["mae"]
    refuted_A = bool(degradation_A > DEGRADATION_REFUTE_THRESHOLD)
    refuted_B = bool(degradation_B > DEGRADATION_REFUTE_THRESHOLD)
    return {
        "n_total": int(len(y_all)),
        "n_macro_a": n_a,
        "n_macro_b": n_b,
        "k_subclusters": K_SUBCLUSTERS,
        "subcluster_sizes_at_k": sorted(int(s) for s in np.bincount(labels_k)[1:]),
        "degenerate_naive_2cut": degenerate_naive_2cut,
        "own_features_within_corpus_5fold": within,
        "direction_A_train_macro_a_test_macro_b": a_to_b,
        "direction_B_train_macro_b_test_macro_a": b_to_a,
        "degradation_factor_A": float(degradation_A),
        "degradation_factor_B": float(degradation_B),
        "refuted_A": refuted_A,
        "refuted_B": refuted_B,
        "property_refuted": bool(refuted_A or refuted_B),
        "_mask_a": mask_a,
        "_keep": keep,
    }


def main():
    df = pd.read_csv(OPENPOLY_CSV)
    sub = df[df[PROP_COL].notna() & df["PSMILES"].notna()].reset_index(drop=True)

    smiles_list = sub["PSMILES"].tolist()
    y_all = sub[PROP_COL].to_numpy(dtype=np.float64)

    real = run(smiles_list, y_all)

    # ---- positive control: plant a defect the attack SHOULD catch ----
    # Verify the harness CAN detect a genuine cross-group generalization
    # failure by planting one on a copy of the real data: overwrite macro-A's
    # y-values (macro-A defined by THIS run's own balanced_macro_bisection,
    # the same k=12 bin-packed groups the real verdict is computed from -- not
    # the degenerate naive 2-cut) with a constant far outside the real range,
    # then re-running the identical, unmodified run() pipeline end-to-end
    # (including re-clustering) on the corrupted labels.
    keep_probe = real["_keep"]
    mask_a_probe = real["_mask_a"]
    y_probe = y_all[keep_probe]
    smiles_kept = [smiles_list[i] for i in keep_probe]

    y_corrupt = y_probe.copy()
    real_range = (float(np.min(y_probe)), float(np.max(y_probe)))
    plant_value = real_range[1] + 50.0
    y_corrupt[mask_a_probe] = plant_value

    corrupted = run(smiles_kept, y_corrupt)

    result = {
        "study_id": "amphora-molecule-property-openpoly-dielectric-macro-bisection-external-validity-v1",
        "campaign_item_id": "",
        "claim_under_attack": {
            "kpi_path": "amphora-molecule-property/evidence/phase0/kpis/openpoly-dielectric-constant-ml-baseline-kpi.v1.json",
            "kpi_sha256": sha256_file(TARGET_KPI),
            "claim_text": (
                "OpenPoly dielectric constant ML baseline: RandomForest scaffold-safe "
                "holdout test MAE=0.4040 vs NULL 0.7027 (+42.5%), test R2=+0.565, "
                "LOSO-CV R2=+0.659 under 111-fold raw-Bemis-Murcko-scaffold CV. "
                "'REAL POSITIVE LIFT.'"
            ),
        },
        "seed": SEED,
        "degradation_refute_threshold": DEGRADATION_REFUTE_THRESHOLD,
        "dataset_fixture_path": "feedback/v1/external_data/openpoly_benchmark/raw/final_polymer_properties_fromliterature.csv",
        "dataset_fixture_sha256_observed": sha256_file(OPENPOLY_CSV),
        "dataset_fixture_sha256_pinned_in_kpi": json.loads(TARGET_KPI.read_text())["dataset_fixture_sha256"],
        "featurization": {"morgan_radius": RADIUS, "morgan_bits": NBITS, "additional_features": ["log10(MolWt+1)"]},
        "macro_bisection_method": (
            "scipy average-linkage agglomerative clustering (UPGMA-family, "
            "Sokal & Michener 1958; Murtagh & Contreras 2012 review) on the "
            "full n x n Tanimoto distance matrix over Morgan r=2/512-bit "
            "fingerprints -- same primitives as C7 fire2 (density) and W7 "
            "(refractive_index, thermal_conductivity). The naive fcluster"
            "(maxclust=2) cut used by C7/W7 is DEGENERATE on this 295-molecule "
            "OpenPoly corpus (294 vs 1 -- see degenerate_naive_2cut in "
            "real_data_result), so this fire cuts the same dendrogram at "
            "k=12 sub-clusters instead and greedily bin-packs the 12 intact "
            "sub-clusters (largest first, into whichever macro-side is "
            "currently smaller) into two macro-chemotype halves -- see "
            "balanced_macro_bisection() in the compute script. Applied to "
            "OpenPoly dielectric constant for the first time."
        ),
        "real_data_result": {k: v for k, v in real.items() if not k.startswith("_")},
        "positive_control": {
            "planted_defect": (
                f"Deep copy of the real 295-row {PROP_COL} labels with macro-group A's "
                f"(n={int(mask_a_probe.sum())} of {len(y_probe)}, from THIS run's own "
                f"k=12 bin-packed balanced_macro_bisection, not the degenerate naive "
                f"2-cut) y-values overwritten to a constant {plant_value:.4f} (real "
                f"range was [{real_range[0]:.4f}, {real_range[1]:.4f}]), breaking any "
                "true structure-property relationship for that half while leaving "
                "macro-group B and all featurization/clustering code untouched."
            ),
            "how_planted": (
                "y_corrupt[mask_a_probe] = real_y_max + 50.0, where mask_a_probe is "
                "the exact macro-A boolean mask returned by run() on the real, "
                "uncorrupted data (the corruption never touches the clustering step "
                "itself, only the labels fed into cross_group()); the full run() "
                "pipeline, including re-clustering, is then re-executed end-to-end "
                "on the corrupted labels, unmodified."
            ),
            "corrupted_run_result": {k: v for k, v in corrupted.items() if not k.startswith("_")},
            "expected": "corrupted run's degradation_factor_A must exceed the 2.0x refute threshold (training on B, testing on the constant-overwritten A, must fail badly relative to within-corpus MAE)",
            "detected": bool(corrupted["degradation_factor_A"] > DEGRADATION_REFUTE_THRESHOLD or corrupted["degradation_factor_B"] > DEGRADATION_REFUTE_THRESHOLD),
        },
        "shipped_kpi_numbers_for_reference": {
            "holdout_test_MAE": 0.4040,
            "holdout_test_R2": 0.565,
            "LOSO_CV_R2": 0.659,
            "split_methodology_shipped": "raw Bemis-Murcko scaffold-safe 80/20 holdout AND 111-fold LOSO-CV (single scaffold held out per fold)",
        },
    }
    result["overall_refuted"] = bool(real["property_refuted"])
    result["verdict"] = "REFUTED" if result["overall_refuted"] else "SURVIVED"

    out = json.dumps(result, indent=2, sort_keys=True)
    Path("diagnostic.out.json").write_text(out)
    print(out[:3000])
    print("...")
    print("WROTE diagnostic.out.json")
    print("VERDICT", result["verdict"])


if __name__ == "__main__":
    main()
