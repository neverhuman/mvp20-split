#!/usr/bin/env python3
"""R-C01 repair attempt #3 (final form used for the fire's checkpoint):
CORRECT scaffold-grouped CV+ construction per Barber, Candes, Ramdas,
Tibshirani (2021) "Predictive inference with the jackknife+", Ann. Statist.
49(1):486-507, Algorithm/Definition for K-fold CV+ (here: folds = Bemis-
Murcko scaffold groups within train_pool, i.e. "leave-one-scaffold-out CV+"),
applied to the SAME 60-seed scaffold-disjoint Monte Carlo protocol that
refuted the OpenPoly Tg split-conformal marginal-coverage claim.

Supersedes the fire's attempt #2 (run_scaffold_cvplus_repair.py), which used
a SIMPLIFIED approximation (pool the out-of-fold residuals, then apply their
quantile around a single final full-train_pool-fit prediction). That
approximation collapses fold-to-fold model variability and understates
interval width; it reached mean coverage 0.8825 (< 0.90 threshold, checkpoint
result). This script implements the literature's actual CV+ interval, which
uses, for EVERY training point i belonging to fold g(i), the fold-excluded
model's OWN prediction on the test point (not a single pooled model), giving
asymmetric per-test-point bounds:

  C(x_test) = [ k_lo-th smallest of {mu_{-g(i)}(x_test) - R_i^CV}_{i=1..n},
                k_hi-th smallest of {mu_{-g(i)}(x_test) + R_i^CV}_{i=1..n} ]
  k_lo = ceil(alpha*(n+1)),  k_hi = ceil((1-alpha)*(n+1))   (1-indexed, clipped to [1,n])

alpha=0.05 (same nominal target as the attacked KPI; not tuned against any
60-seed outcome -- this is the SAME alpha used throughout this module's own
audit chain and the attacked KPI itself). Model family, features, and Ridge
hyperparameter are unchanged from the attacked protocol; only the calibration
construction differs (K-fold-by-scaffold CV+ instead of a single random
50/50 point-level split-conformal).
"""
import json
import hashlib
import math

import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit.Chem import AllChem, Descriptors
from rdkit.Chem.Scaffolds import MurckoScaffold
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from sklearn.model_selection import train_test_split as _tts

ALPHA = 0.05
N_SEEDS = 60
MIN_FOLD_FIT_SIZE = 5

ATTACK_SCRIPT_SHA256 = "96be585e27428a1f9bec0a7e2c078f9488711df5515790bc24ac35ac97cf0e09"
ATTACK_RECEIPT_PATH = "amphora-tolerance-robustness/evidence/audit/repeated-scaffold-monte-carlo-conformal-openpoly-tg-v1/repeated-scaffold-monte-carlo-conformal-openpoly-tg-receipt.v1.dsse.json"
ATTACK_DIAGNOSTIC_PATH = "amphora-tolerance-robustness/evidence/audit/repeated-scaffold-monte-carlo-conformal-openpoly-tg-v1/diagnostic.canonical.json"
ATTACK_DIAGNOSTIC_SHA256 = "4d4582e74ca2fc8b2566fd9336bcff6594ecc8837a40195b417c66a9d37756f9"


def sha256_of_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def morgan_features(smiles_list, n_bits=512, radius=2):
    X = np.zeros((len(smiles_list), n_bits + 1), dtype=float)
    ok = np.zeros(len(smiles_list), dtype=bool)
    for i, smi in enumerate(smiles_list):
        mol = Chem.MolFromSmiles(smi)
        if mol is None:
            continue
        fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=n_bits)
        arr = np.zeros((n_bits,), dtype=float)
        for b in fp.GetOnBits():
            arr[b] = 1.0
        X[i, :n_bits] = arr
        wt = Descriptors.MolWt(mol)
        X[i, n_bits] = math.log10(wt) if wt > 0 else 0.0
        ok[i] = True
    return X, ok


def bemis_murcko_scaffold(smiles):
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    try:
        scaf = MurckoScaffold.GetScaffoldForMol(mol)
        return Chem.MolToSmiles(scaf) if scaf is not None else ""
    except Exception:
        return None


def finite_sample_qhat(residuals, alpha=ALPHA):
    n = len(residuals)
    level = min(1.0, math.ceil((n + 1) * (1 - alpha)) / n)
    return float(np.quantile(residuals, level, method="higher")), level


results = {}

openpoly_path = "feedback/v1/external_data/openpoly_benchmark/raw/final_polymer_properties_fromliterature.csv"
openpoly_sha256 = sha256_of_file(openpoly_path)
attack_script_sha256_actual = sha256_of_file(
    "amphora-tolerance-robustness/evidence/audit/repeated-scaffold-monte-carlo-conformal-openpoly-tg-v1/run_repeated_scaffold_conformal.py"
)

df = pd.read_csv(openpoly_path)
df = df[["PSMILES", "Tg (K)"]].dropna()
df = df.rename(columns={"Tg (K)": "Tg"})
df = df[(df["Tg"] > 100) & (df["Tg"] < 700)].reset_index(drop=True)

smiles = df["PSMILES"].tolist()
tg = df["Tg"].to_numpy(dtype=float)

X, ok = morgan_features(smiles)
X = X[ok]
tg = tg[ok]
smiles_kept = [s for s, k in zip(smiles, ok) if k]
scaffolds = [bemis_murcko_scaffold(s) for s in smiles_kept]
scaf_arr = np.array([s if s is not None else f"__none_{i}__" for i, s in enumerate(scaffolds)])

n_total = len(tg)
idx = np.arange(n_total)

results["dataset"] = {
    "path": openpoly_path,
    "sha256": openpoly_sha256,
    "expected_sha256": "8de5baf76f79610fe9173e63c65b824714aeb8445f9d670e1767956ea9db5eb3",
    "sha256_matches_prior_signed_receipts": openpoly_sha256 == "8de5baf76f79610fe9173e63c65b824714aeb8445f9d670e1767956ea9db5eb3",
    "n_polymers_after_filter": int(n_total),
}
results["attack_script_pin"] = {
    "path": "amphora-tolerance-robustness/evidence/audit/repeated-scaffold-monte-carlo-conformal-openpoly-tg-v1/run_repeated_scaffold_conformal.py",
    "expected_sha256": ATTACK_SCRIPT_SHA256,
    "actual_sha256": attack_script_sha256_actual,
    "matches": attack_script_sha256_actual == ATTACK_SCRIPT_SHA256,
    "modified": False,
}

uniq_scaffolds_all, scaf_counts_all = np.unique(scaf_arr, return_counts=True)
target_test_n = int(round(0.4 * n_total))

import base64
with open(ATTACK_RECEIPT_PATH) as f:
    attack_envelope = json.load(f)
attack_payload = json.loads(base64.b64decode(attack_envelope["signature"]["payload"]))
assert attack_payload["reproducibility"]["canonical_diagnostic_sha256"] == ATTACK_DIAGNOSTIC_SHA256
assert sha256_of_file(ATTACK_DIAGNOSTIC_PATH) == ATTACK_DIAGNOSTIC_SHA256
with open(ATTACK_DIAGNOSTIC_PATH) as f:
    attack_diag = json.load(f)
attack_draws = attack_diag["draws"]
assert len(attack_draws) == N_SEEDS

draws = []
parity_mismatches = 0
n_seeds_with_fallback = 0
for seed in range(N_SEEDS):
    rng = np.random.RandomState(seed)
    perm = rng.permutation(len(uniq_scaffolds_all))
    uniq_shuffled = uniq_scaffolds_all[perm]
    test_mask = np.zeros(n_total, dtype=bool)
    running = 0
    for scf in uniq_shuffled:
        if running >= target_test_n:
            break
        members = np.where(scaf_arr == scf)[0]
        test_mask[members] = True
        running += len(members)

    scaf_test_idx = idx[test_mask]
    scaf_train_pool_idx = idx[~test_mask]
    n_test = len(scaf_test_idx)
    n_pool = len(scaf_train_pool_idx)

    # ---- fidelity/parity check vs attacked (unweighted) method's own table ----
    scaf_proper_train_idx, scaf_calib_idx = _tts(scaf_train_pool_idx, train_size=0.5, random_state=seed)
    scaler_u = StandardScaler().fit(X[scaf_proper_train_idx])
    ridge_u = Ridge(alpha=1.0, solver="cholesky").fit(scaler_u.transform(X[scaf_proper_train_idx]), tg[scaf_proper_train_idx])
    calib_resid_u = np.abs(tg[scaf_calib_idx] - ridge_u.predict(scaler_u.transform(X[scaf_calib_idx])))
    qhat_u, _ = finite_sample_qhat(calib_resid_u)
    test_resid_u = np.abs(tg[scaf_test_idx] - ridge_u.predict(scaler_u.transform(X[scaf_test_idx])))
    coverage_unweighted = float(np.mean(test_resid_u <= qhat_u))
    ref = attack_draws[seed]
    assert ref["seed"] == seed
    n_test_matches = (n_test == ref["n_test_scaffold_safe"])
    cov_matches = abs(coverage_unweighted - ref["coverage_scaffold_safe"]) < 1e-9
    if not (n_test_matches and cov_matches):
        parity_mismatches += 1

    # ---- scaffold-grouped CV+ ----
    pool_scaf = scaf_arr[scaf_train_pool_idx]
    uniq_pool_scaf, inv = np.unique(pool_scaf, return_inverse=True)
    n_folds = len(uniq_pool_scaf)

    R_cv = np.full(n_pool, np.nan)             # out-of-fold abs residual per pool point
    pred_neg_fold_on_test = np.full((n_pool, n_test), np.nan)  # mu_{-g(i)}(x_test_j)
    n_fallback_points = 0

    X_test = X[scaf_test_idx]
    for f_id, g in enumerate(uniq_pool_scaf):
        held_local = np.where(inv == f_id)[0]
        fit_local = np.where(inv != f_id)[0]
        if len(fit_local) < MIN_FOLD_FIT_SIZE:
            n_fallback_points += len(held_local)
            continue
        fit_idx = scaf_train_pool_idx[fit_local]
        held_idx = scaf_train_pool_idx[held_local]
        scaler_g = StandardScaler().fit(X[fit_idx])
        ridge_g = Ridge(alpha=1.0, solver="cholesky").fit(scaler_g.transform(X[fit_idx]), tg[fit_idx])
        R_cv[held_local] = np.abs(tg[held_idx] - ridge_g.predict(scaler_g.transform(X[held_idx])))
        pred_test_g = ridge_g.predict(scaler_g.transform(X_test))
        pred_neg_fold_on_test[held_local, :] = pred_test_g[np.newaxis, :]

    if n_fallback_points > 0:
        scaler_full = StandardScaler().fit(X[scaf_train_pool_idx])
        ridge_full = Ridge(alpha=1.0, solver="cholesky").fit(scaler_full.transform(X[scaf_train_pool_idx]), tg[scaf_train_pool_idx])
        resid_full = np.abs(tg[scaf_train_pool_idx] - ridge_full.predict(scaler_full.transform(X[scaf_train_pool_idx])))
        pred_test_full = ridge_full.predict(scaler_full.transform(X_test))
        nan_mask = np.isnan(R_cv)
        R_cv[nan_mask] = resid_full[nan_mask]
        pred_neg_fold_on_test[nan_mask, :] = pred_test_full[np.newaxis, :]
        n_seeds_with_fallback += 1

    lower_candidates = pred_neg_fold_on_test - R_cv[:, np.newaxis]   # (n_pool, n_test)
    upper_candidates = pred_neg_fold_on_test + R_cv[:, np.newaxis]

    n = n_pool
    k_lo = max(1, min(n, math.ceil(ALPHA * (n + 1))))
    k_hi = max(1, min(n, math.ceil((1 - ALPHA) * (n + 1))))
    lower_sorted = np.sort(lower_candidates, axis=0)
    upper_sorted = np.sort(upper_candidates, axis=0)
    lower_bound = lower_sorted[k_lo - 1, :]
    upper_bound = upper_sorted[k_hi - 1, :]

    tg_test = tg[scaf_test_idx]
    covered = (tg_test >= lower_bound) & (tg_test <= upper_bound)
    coverage_cvplus2 = float(np.mean(covered))
    mean_width_cvplus2 = float(np.mean(upper_bound - lower_bound))
    mean_width_unweighted = float(2 * qhat_u)

    draws.append({
        "seed": seed,
        "n_test_scaffold_safe": int(n_test),
        "n_train_pool": int(n_pool),
        "n_folds_scaffold_groups": int(n_folds),
        "n_fallback_points_insample": int(n_fallback_points),
        "n_test_matches_refuting_receipt": bool(n_test_matches),
        "coverage_scaffold_safe_unweighted_matches_refuting_receipt": bool(cov_matches),
        "coverage_scaffold_safe_unweighted": coverage_unweighted,
        "coverage_scaffold_safe_cvplus_v2": coverage_cvplus2,
        "mean_width_cvplus_v2": mean_width_cvplus2,
        "mean_width_unweighted": mean_width_unweighted,
        "width_inflation_ratio": (mean_width_cvplus2 / mean_width_unweighted) if mean_width_unweighted > 0 else None,
    })

results["parity_check_vs_refuting_receipt"] = {
    "attack_receipt_path": ATTACK_RECEIPT_PATH,
    "n_seeds_checked": N_SEEDS,
    "n_mismatches": parity_mismatches,
    "splits_identical": parity_mismatches == 0,
}
results["n_seeds_with_loso_fallback_points"] = n_seeds_with_fallback

cov_cv2 = np.array([d["coverage_scaffold_safe_cvplus_v2"] for d in draws])
cov_u = np.array([d["coverage_scaffold_safe_unweighted"] for d in draws])

results["n_seeds"] = N_SEEDS
results["alpha"] = ALPHA
results["target_test_n_fixed_across_draws"] = target_test_n
results["draws"] = draws
results["summary_stats"] = {
    "coverage_cvplus_v2_mean": float(np.mean(cov_cv2)),
    "coverage_cvplus_v2_median": float(np.median(cov_cv2)),
    "coverage_cvplus_v2_std": float(np.std(cov_cv2, ddof=1)),
    "coverage_cvplus_v2_min": float(np.min(cov_cv2)),
    "coverage_cvplus_v2_max": float(np.max(cov_cv2)),
    "coverage_unweighted_mean_recomputed": float(np.mean(cov_u)),
    "coverage_unweighted_mean_from_refuting_receipt": 0.8745741048157474,
    "n_draws_cvplus_v2_below_090": int(np.sum(cov_cv2 < 0.90)),
    "mean_width_inflation_ratio": float(np.mean([d["width_inflation_ratio"] for d in draws if d["width_inflation_ratio"] is not None])),
}
results["acceptance"] = {
    "criterion": "mean coverage_scaffold_safe_cvplus_v2 over the identical 60-seed protocol >= 0.90",
    "observed_mean": float(np.mean(cov_cv2)),
    "threshold": 0.90,
    "met": bool(np.mean(cov_cv2) >= 0.90),
}

print(json.dumps(results, indent=2, sort_keys=True))
