#!/usr/bin/env python3
"""
R-C03 deliverable 2: applicability-domain (AD) gate for the Tg/density
predictors, demonstrated on the C7 cross-corpus / macro-bisection failing
pairs (amphora-molecule-property/benchmarks/tg-density-external-validity-c7-v3-final/
c7_final_tg_density_external_validity_verdict_receipt.v1.json).

Gate design (training-label range + Tanimoto distance threshold, as named by
the R-C03 objective):
  1. Tanimoto NN-distance gate: for a query molecule, compute the minimum
     Tanimoto distance (1 - similarity, Morgan r=2/512-bit, same convention
     as the C7/W7 attacks) to any molecule in the model's training set.
     ABSTAIN if this exceeds a threshold tau, calibrated PER TRAINING SET
     using cross-validation on that training set alone (never touching the
     OOD test labels): tau is set so that AT LEAST 90% of training-set
     queries (via leave-fold-out / leave-one-out) have NN-distance <= tau.
     This directly operationalizes the ">=90% within-corpus coverage" target
     by construction, and its real test is what abstention rate it produces
     on genuinely out-of-domain data it never saw.
  2. Training-label-range gate: ABSTAIN if the underlying RF's raw
     prediction falls outside [min(y_train), max(y_train)]. Reported
     honestly: bagged-tree RF predictions are convex combinations of
     training leaf labels, so this is structurally near-vacuous for THIS
     model family (it can supply near-zero marginal abstentions) -- the
     component is implemented and measured, not silently omitted, but the
     gate's real power comes from (1).
  3. Combined: ABSTAIN if either component fires.

Four legs (matching the C7 final verdict's named failing transfers):
  tg_A:      train OpenPoly (n=443)        -> test Polyuniverse Epoxy (n=5000 sample)
  tg_B:      train Polyuniverse Epoxy      -> test OpenPoly
  density_A: train RadonPy macro_a (n=16)  -> test RadonPy macro_b (n=1061)
  density_B: train RadonPy macro_b (n=1061)-> test RadonPy macro_a (n=16)

Acceptance (R-C03 deliverable 2, pre-registered):
  per leg: abstention_rate_on_failing_transfer >= 0.90
       AND within_corpus_coverage_rate         >= 0.90
  ALL FOUR legs must pass for the demonstration to be accepted.

Positive control: the Tanimoto threshold is deliberately disabled (set to
1.1, i.e. above the maximum possible Tanimoto distance of 1.0) in a second
pass over the SAME computed distances, and the abstention rate on the
failing legs is re-measured -- it must collapse towards 0%, proving this
evaluation harness has real power to detect a broken/disabled gate rather
than rubber-stamping a hardcoded pass.
"""
import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["PYTHONHASHSEED"] = "0"

import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from rdkit import Chem, RDLogger, DataStructs
from rdkit.Chem import Descriptors, rdMolDescriptors
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial.distance import squareform
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import KFold

RDLogger.DisableLog("rdApp.*")

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
OPENPOLY_CSV = ROOT / "feedback/v1/external_data/openpoly_benchmark/raw/final_polymer_properties_fromliterature.csv"
POLYUNIVERSE_CSV = ROOT / "feedback/v1/external_data/polyuniverse_epoxy/raw/Epoxy_1M_p.csv"
RADONPY_CSV = ROOT / "feedback/v1/external_data/radonpy_pi1070/raw/PI1070.csv"

SEED = 0
NBITS = 512
RADIUS = 2
POLYUNIVERSE_SAMPLE_N = 5000
COVERAGE_TARGET = 0.90
ABSTENTION_TARGET = 0.90
DISABLED_TAU = 1.1  # positive-control defect: above max possible Tanimoto distance (1.0)


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


def nn_distance(query_fps, ref_fps):
    """Min Tanimoto distance from each query fp to the ref fp set."""
    out = np.zeros(len(query_fps), dtype=np.float64)
    for i, qfp in enumerate(query_fps):
        sims = DataStructs.BulkTanimotoSimilarity(qfp, ref_fps)
        out[i] = 1.0 - max(sims)
    return out


def calibrate_tau_kfold(fps, y, seed=SEED, n_splits=5, coverage_target=COVERAGE_TARGET):
    """OOF NN-distance-to-remaining-fold distribution via k-fold CV on the
    training set only (never touches OOD test data). Returns tau (smallest
    threshold that admits >= coverage_target fraction of OOF queries, via
    the ceil-index order statistic so the coverage bound is guaranteed by
    construction) plus the OOF distance array itself for reporting."""
    n = len(y)
    idx = np.arange(n)
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=seed)
    oof_dist = np.zeros(n, dtype=np.float64)
    for train_idx, test_idx in kf.split(idx):
        ref = [fps[j] for j in train_idx]
        q = [fps[j] for j in test_idx]
        oof_dist[test_idx] = nn_distance(q, ref)
    sorted_d = np.sort(oof_dist)
    keep_n = math.ceil(coverage_target * n)
    keep_n = min(keep_n, n)
    tau = float(sorted_d[keep_n - 1])
    return tau, oof_dist


def calibrate_tau_loo(fps, y, coverage_target=COVERAGE_TARGET):
    """Leave-one-out variant for very small training sets (e.g. n=16)."""
    n = len(y)
    oof_dist = np.zeros(n, dtype=np.float64)
    for i in range(n):
        ref = [fps[j] for j in range(n) if j != i]
        oof_dist[i] = nn_distance([fps[i]], ref)[0]
    sorted_d = np.sort(oof_dist)
    keep_n = math.ceil(coverage_target * n)
    keep_n = min(keep_n, n)
    tau = float(sorted_d[keep_n - 1])
    return tau, oof_dist


def leg_result(name, X_train, fps_train, y_train, X_test, fps_test, y_test, tau, oof_dist_train):
    model = RandomForestRegressor(n_estimators=100, random_state=SEED, n_jobs=1)
    model.fit(X_train, y_train)
    preds_test = model.predict(X_test)

    label_lo, label_hi = float(np.min(y_train)), float(np.max(y_train))
    range_abstain = (preds_test < label_lo) | (preds_test > label_hi)

    nn_dist_test = nn_distance(fps_test, fps_train)
    tanimoto_abstain = nn_dist_test > tau

    combined_abstain = tanimoto_abstain | range_abstain
    abstention_rate = float(np.mean(combined_abstain))

    # within-corpus coverage: same OOF procedure that calibrated tau, i.e.
    # what fraction of the training corpus's own queries this exact tau admits
    within_admit = oof_dist_train <= tau
    coverage_rate = float(np.mean(within_admit))

    # positive control: disable the Tanimoto gate (tau -> above max possible distance)
    tanimoto_abstain_disabled = nn_dist_test > DISABLED_TAU
    combined_abstain_disabled = tanimoto_abstain_disabled | range_abstain
    abstention_rate_disabled = float(np.mean(combined_abstain_disabled))

    return {
        "leg": name,
        "n_train": int(len(y_train)),
        "n_test": int(len(y_test)),
        "train_label_range": [label_lo, label_hi],
        "tau_tanimoto_distance": tau,
        "n_tanimoto_abstain": int(np.sum(tanimoto_abstain)),
        "n_range_abstain": int(np.sum(range_abstain)),
        "n_range_abstain_marginal_beyond_tanimoto": int(np.sum(range_abstain & ~tanimoto_abstain)),
        "n_combined_abstain": int(np.sum(combined_abstain)),
        "abstention_rate_on_failing_transfer": abstention_rate,
        "abstention_rate_meets_90pct_target": bool(abstention_rate >= ABSTENTION_TARGET),
        "within_corpus_coverage_rate": coverage_rate,
        "within_corpus_coverage_meets_90pct_target": bool(coverage_rate >= COVERAGE_TARGET),
        "leg_passes_acceptance": bool(abstention_rate >= ABSTENTION_TARGET and coverage_rate >= COVERAGE_TARGET),
        "positive_control_disabled_tau": DISABLED_TAU,
        "positive_control_abstention_rate_with_gate_disabled": abstention_rate_disabled,
        "positive_control_fired": bool(abstention_rate_disabled < abstention_rate and abstention_rate_disabled < ABSTENTION_TARGET),
    }


def main():
    # ---------------- Tg: OpenPoly <-> Polyuniverse Epoxy ----------------
    op = pd.read_csv(OPENPOLY_CSV)
    op = op[op["Tg (K)"].notna() & (op["PSMILES"].notna())].reset_index(drop=True)
    X_op, fps_op, keep_op = featurize_and_fp(op["PSMILES"].tolist())
    y_op = op["Tg (K)"].to_numpy(dtype=np.float64)[keep_op]

    pu_full = pd.read_csv(POLYUNIVERSE_CSV, usecols=["Smiles", "Tg"])
    pu_full = pu_full[pu_full["Tg"].notna() & pu_full["Smiles"].notna()].reset_index(drop=True)
    pu_sample = pu_full.sample(n=POLYUNIVERSE_SAMPLE_N, random_state=SEED).reset_index(drop=True)
    X_pu, fps_pu, keep_pu = featurize_and_fp(pu_sample["Smiles"].tolist())
    y_pu = pu_sample["Tg"].to_numpy(dtype=np.float64)[keep_pu]

    tau_op, oof_op = calibrate_tau_kfold(fps_op, y_op)
    tau_pu, oof_pu = calibrate_tau_kfold(fps_pu, y_pu)

    tg_A = leg_result("tg_A_train_openpoly_test_polyuniverse", X_op, fps_op, y_op, X_pu, fps_pu, y_pu, tau_op, oof_op)
    tg_B = leg_result("tg_B_train_polyuniverse_test_openpoly", X_pu, fps_pu, y_pu, X_op, fps_op, y_op, tau_pu, oof_pu)

    # ---------------- density: RadonPy macro-bisection ----------------
    rp = pd.read_csv(RADONPY_CSV, usecols=["monomer_ID", "smiles", "density", "polymer_class"])
    rp = rp[rp["density"].notna() & rp["smiles"].notna()].reset_index(drop=True)
    X_rp, fps_rp, keep_rp = featurize_and_fp(rp["smiles"].tolist())
    y_rp = rp["density"].to_numpy(dtype=np.float64)[keep_rp]
    n_rp = len(y_rp)

    dist_matrix = np.zeros((n_rp, n_rp), dtype=np.float64)
    for i in range(n_rp):
        sims = DataStructs.BulkTanimotoSimilarity(fps_rp[i], fps_rp)
        dist_matrix[i, :] = 1.0 - np.array(sims)
    np.fill_diagonal(dist_matrix, 0.0)
    dist_matrix = (dist_matrix + dist_matrix.T) / 2.0
    condensed = squareform(dist_matrix, checks=False)
    Z = linkage(condensed, method="average")
    macro_labels = fcluster(Z, t=2, criterion="maxclust")
    mask_a = macro_labels == 1
    mask_b = macro_labels == 2
    n_a, n_b = int(mask_a.sum()), int(mask_b.sum())

    X_a, fps_a, y_a = X_rp[mask_a], [fps_rp[i] for i in range(n_rp) if mask_a[i]], y_rp[mask_a]
    X_b, fps_b, y_b = X_rp[mask_b], [fps_rp[i] for i in range(n_rp) if mask_b[i]], y_rp[mask_b]

    tau_a, oof_a = calibrate_tau_loo(fps_a, y_a)
    tau_b, oof_b = calibrate_tau_kfold(fps_b, y_b)

    density_A = leg_result("density_A_train_macro_a_test_macro_b", X_a, fps_a, y_a, X_b, fps_b, y_b, tau_a, oof_a)
    density_B = leg_result("density_B_train_macro_b_test_macro_a", X_b, fps_b, y_b, X_a, fps_a, y_a, tau_b, oof_b)

    legs = [tg_A, tg_B, density_A, density_B]
    all_pass = all(l["leg_passes_acceptance"] for l in legs)
    all_positive_controls_fired = all(l["positive_control_fired"] for l in legs)

    result = {
        "study_id": "amphora-molecule-property-rc03-deliverable2-ad-gate-v1",
        "campaign_item_id": "R-C03",
        "repair_deliverable": "2_of_3: applicability-domain gate (training-label range + Tanimoto NN-distance threshold) on Tg/density predictors",
        "seed": SEED,
        "coverage_target": COVERAGE_TARGET,
        "abstention_target": ABSTENTION_TARGET,
        "featurization": {"morgan_radius": RADIUS, "morgan_bits": NBITS, "additional_rf_feature": "log10(MolWt+1)"},
        "openpoly_csv_sha256": sha256_file(OPENPOLY_CSV),
        "polyuniverse_csv_sha256": sha256_file(POLYUNIVERSE_CSV),
        "radonpy_csv_sha256": sha256_file(RADONPY_CSV),
        "radonpy_macro_bisection": {"n_macro_a": n_a, "n_macro_b": n_b, "method": "scipy average-linkage agglomerative clustering on full Tanimoto distance matrix, fcluster maxclust=2 (same procedure as C7 fire 2)"},
        "legs": legs,
        "all_four_legs_pass_acceptance": bool(all_pass),
        "all_positive_controls_fired": bool(all_positive_controls_fired),
        "source_attack_receipts": {
            "c7_final_verdict": "amphora-molecule-property/benchmarks/tg-density-external-validity-c7-v3-final/c7_final_tg_density_external_validity_verdict_receipt.v1.json",
            "c7_fire2_density_macro_bisection": "amphora-molecule-property/benchmarks/density-butina-cluster-external-validity-c7-v2/c7_density_macro_bisection_external_validity_receipt.v1.json",
        },
    }
    out = json.dumps(result, indent=2, sort_keys=True)
    Path("diagnostic.out.json").write_text(out)
    print(json.dumps({k: v for k, v in result.items() if k != "legs"}, indent=2)[:1500])
    print("...")
    for l in legs:
        print(l["leg"], "abst=", round(l["abstention_rate_on_failing_transfer"], 4),
              "cov=", round(l["within_corpus_coverage_rate"], 4),
              "pass=", l["leg_passes_acceptance"],
              "pc_fired=", l["positive_control_fired"])
    print("ALL_PASS", all_pass, "ALL_PC_FIRED", all_positive_controls_fired)
    print("WROTE diagnostic.out.json")


if __name__ == "__main__":
    main()
