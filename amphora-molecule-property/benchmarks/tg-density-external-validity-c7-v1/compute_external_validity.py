#!/usr/bin/env python3
"""
CAMPAIGN C7 attack: external-validity of the OpenPoly Tg RF baseline and the
RadonPy density RF baseline. Deterministic (seed=0, OMP_NUM_THREADS=1).

TG: true cross-corpus test. Train RF on OpenPoly-441 (experimental, literature),
cold-predict on an independent MD-simulated corpus (Polyuniverse Epoxy, n=5000
deterministic sample) -- and the reverse direction. RadonPy PI1070 cannot serve
as the Tg cross-corpus partner: it has no Tg field at all (verified against its
raw column header), so the two rights-cleared Tg corpora in this module are
OpenPoly and Polyuniverse Epoxy.

DENSITY: OpenPoly has no density field either -- RadonPy PI1070 is the ONLY
rights-cleared polymer-density corpus in this module (verified: no 'Density'
column in OpenPoly's raw header). A literal second-corpus swap is impossible
with current rights-cleared data. As the hardest available proxy for "transfers
to out-of-corpus chemistry", this script performs leave-polymer-class-out CV
using RadonPy's own authentic polymer_class metadata (20 classes, not an
invented clustering) instead of the random 60/20/20 split the headline used.
"""
import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["PYTHONHASHSEED"] = "0"

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from rdkit import Chem, RDLogger
from rdkit.Chem import Descriptors, rdMolDescriptors
from scipy.stats import pearsonr
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
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
MIN_CLASS_SIZE_FOR_LOCO = 8
DEGRADATION_REFUTE_THRESHOLD = 2.0


def sha256_file(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def featurize(smiles_list):
    """Morgan fp (r=2, 512 bits) + log10(MolWt+1) on raw SMILES/PSMILES,
    parsed as-is with RDKit (dummy '*' attachment atoms allowed -- same
    convention as the module's shipped OpenPoly Tg baseline)."""
    feats = []
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
        keep_idx.append(i)
    return np.vstack(feats), np.array(keep_idx)


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


def cross_corpus(X_train, y_train, X_test, y_test, seed=SEED):
    model = RandomForestRegressor(n_estimators=100, random_state=seed, n_jobs=1)
    model.fit(X_train, y_train)
    preds = model.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    r2 = r2_score(y_test, preds)
    r, _ = pearsonr(y_test, preds) if len(set(y_test.tolist())) > 1 else (float("nan"), None)
    null_mae = mean_absolute_error(y_test, np.full_like(y_test, np.median(y_train), dtype=np.float64))
    return {
        "mae": float(mae),
        "r2": float(r2),
        "pearson_r": float(r) if r == r else None,
        "null_mae_using_train_median": float(null_mae),
        "n_train": int(len(y_train)),
        "n_test": int(len(y_test)),
        "train_y_median": float(np.median(y_train)),
        "train_y_range": [float(np.min(y_train)), float(np.max(y_train))],
        "test_y_median": float(np.median(y_test)),
        "test_y_range": [float(np.min(y_test)), float(np.max(y_test))],
    }


def run_tg():
    # --- OpenPoly (experimental, literature) ---
    op = pd.read_csv(OPENPOLY_CSV)
    op = op[op["Tg (K)"].notna() & (op["PSMILES"].notna())].reset_index(drop=True)
    X_op_all, keep_op = featurize(op["PSMILES"].tolist())
    y_op_all = op["Tg (K)"].to_numpy(dtype=np.float64)[keep_op]

    # --- Polyuniverse Epoxy (MD-simulated), deterministic n=5000 sample ---
    pu_full = pd.read_csv(POLYUNIVERSE_CSV, usecols=["Smiles", "Tg"])
    pu_full = pu_full[pu_full["Tg"].notna() & pu_full["Smiles"].notna()].reset_index(drop=True)
    pu_sample = pu_full.sample(n=POLYUNIVERSE_SAMPLE_N, random_state=SEED).reset_index(drop=True)
    X_pu_all, keep_pu = featurize(pu_sample["Smiles"].tolist())
    y_pu_all = pu_sample["Tg"].to_numpy(dtype=np.float64)[keep_pu]

    # A: train OpenPoly -> test Polyuniverse (cold)
    a_result = cross_corpus(X_op_all, y_op_all, X_pu_all, y_pu_all)
    # B: train Polyuniverse -> test OpenPoly (cold), reverse direction
    b_result = cross_corpus(X_pu_all, y_pu_all, X_op_all, y_op_all)

    # apples-to-apples within-corpus baselines, SAME features/model as above
    within_openpoly = within_corpus_kfold_mae(X_op_all, y_op_all)
    within_polyuniverse = within_corpus_kfold_mae(X_pu_all, y_pu_all)

    degradation_A = a_result["mae"] / within_openpoly["mae"]
    degradation_B = b_result["mae"] / within_polyuniverse["mae"]

    return {
        "openpoly_csv_sha256": sha256_file(OPENPOLY_CSV),
        "polyuniverse_csv_sha256": sha256_file(POLYUNIVERSE_CSV),
        "n_openpoly": int(len(y_op_all)),
        "n_polyuniverse_sample": int(len(y_pu_all)),
        "within_openpoly_kfold_own_features": within_openpoly,
        "within_polyuniverse_kfold_own_features": within_polyuniverse,
        "official_shipped_headline": {
            "openpoly_rf_loso_mae_K": 51.237491607666016,
            "openpoly_rf_holdout_mae_K": 42.20672417382652,
            "openpoly_null_holdout_mae_K": 52.46160125732422,
            "source_receipt": "amphora-molecule-property/evidence/phase0/kpis/openpoly-experimental-tg-ml-baseline-kpi.v1.json",
        },
        "direction_A_train_openpoly_test_polyuniverse": a_result,
        "direction_B_train_polyuniverse_test_openpoly": b_result,
        "degradation_factor_A_vs_own_within_corpus": float(degradation_A),
        "degradation_factor_B_vs_own_within_corpus": float(degradation_B),
        "refuted_A": bool(degradation_A > DEGRADATION_REFUTE_THRESHOLD),
        "refuted_B": bool(degradation_B > DEGRADATION_REFUTE_THRESHOLD),
    }


def run_density():
    rp = pd.read_csv(RADONPY_CSV, usecols=["monomer_ID", "smiles", "density", "polymer_class"])
    rp = rp[rp["density"].notna() & rp["smiles"].notna()].reset_index(drop=True)
    X_all, keep = featurize(rp["smiles"].tolist())
    y_all = rp["density"].to_numpy(dtype=np.float64)[keep]
    classes_all = rp["polymer_class"].to_numpy()[keep]

    within = within_corpus_kfold_mae(X_all, y_all)

    class_counts = pd.Series(classes_all).value_counts()
    eligible_classes = sorted(class_counts[class_counts >= MIN_CLASS_SIZE_FOR_LOCO].index.tolist())

    loco_preds = []
    loco_true = []
    loco_null_preds = []
    per_class = {}
    for c in eligible_classes:
        test_mask = classes_all == c
        train_mask = ~test_mask
        model = RandomForestRegressor(n_estimators=100, random_state=SEED, n_jobs=1)
        model.fit(X_all[train_mask], y_all[train_mask])
        preds = model.predict(X_all[test_mask])
        train_median = np.median(y_all[train_mask])
        loco_preds.extend(preds.tolist())
        loco_true.extend(y_all[test_mask].tolist())
        loco_null_preds.extend([train_median] * int(test_mask.sum()))
        per_class[str(int(c))] = {
            "n_test": int(test_mask.sum()),
            "mae": float(mean_absolute_error(y_all[test_mask], preds)),
        }

    loco_true_arr = np.array(loco_true)
    loco_preds_arr = np.array(loco_preds)
    loco_null_arr = np.array(loco_null_preds)
    loco_mae = float(mean_absolute_error(loco_true_arr, loco_preds_arr))
    loco_r2 = float(r2_score(loco_true_arr, loco_preds_arr))
    loco_null_mae = float(mean_absolute_error(loco_true_arr, loco_null_arr))

    degradation = loco_mae / within["mae"]

    return {
        "radonpy_csv_sha256": sha256_file(RADONPY_CSV),
        "n_polymers": int(len(y_all)),
        "official_shipped_headline": {
            "random_60_20_20_split_test_mae_g_per_cm3": 0.056644705523222164,
            "random_60_20_20_split_null_mae_g_per_cm3": 0.12677565217018127,
            "source_receipt": "amphora-molecule-property/evidence/phase0/kpis/radonpy-density-ml-vs-van-krevelen-physics-kpi.v1.json",
            "note": "different featurization (Van Krevelen 24-group) than this script's Morgan-fp; own_features_within below is the apples-to-apples baseline for the degradation factor.",
        },
        "own_features_within_corpus_5fold": within,
        "leave_polymer_class_out": {
            "eligible_classes": eligible_classes,
            "min_class_size": MIN_CLASS_SIZE_FOR_LOCO,
            "n_pooled_test": int(len(loco_true_arr)),
            "pooled_mae": loco_mae,
            "pooled_r2": loco_r2,
            "pooled_null_mae_train_median": loco_null_mae,
            "per_class": per_class,
        },
        "degradation_factor_leave_class_out_vs_own_within_corpus": float(degradation),
        "refuted": bool(degradation > DEGRADATION_REFUTE_THRESHOLD),
        "data_availability_note": (
            "No second rights-cleared polymer-density corpus exists in this module: "
            "OpenPoly has no Density column and Polyuniverse Epoxy has no density column "
            "(verified against both raw CSV headers). A literal cross-corpus swap "
            "(the objective's primary request) is currently BLOCKED_DATA for density; "
            "leave-polymer-class-out on RadonPy's own authentic class labels is the "
            "hardest available proxy for out-of-distribution chemistry generalization."
        ),
    }


def main():
    tg = run_tg()
    density = run_density()
    result = {
        "study_id": "amphora-molecule-property-c7-tg-density-external-validity-attack-v1",
        "campaign_item_id": "C7",
        "seed": SEED,
        "degradation_refute_threshold": DEGRADATION_REFUTE_THRESHOLD,
        "tg": tg,
        "density": density,
        "gates": {
            "tg_direction_A_data_gathered": tg["n_openpoly"] >= 400 and tg["n_polyuniverse_sample"] >= 4000,
            "tg_direction_B_data_gathered": True,
            "density_loco_eligible_classes_at_least_5": len(density["leave_polymer_class_out"]["eligible_classes"]) >= 5,
            "density_loco_pooled_n_at_least_500": density["leave_polymer_class_out"]["n_pooled_test"] >= 500,
        },
    }
    result["all_gates_passed"] = all(result["gates"].values())
    out = json.dumps(result, indent=2, sort_keys=True)
    Path("diagnostic.out.json").write_text(out)
    print(out[:2000])
    print("...")
    print("WROTE diagnostic.out.json")


if __name__ == "__main__":
    main()
