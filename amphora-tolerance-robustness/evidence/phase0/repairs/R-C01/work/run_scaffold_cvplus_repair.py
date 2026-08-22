#!/usr/bin/env python3
"""R-C01 repair attempt #2: scaffold-grouped CV+ conformal (Barber, Candes,
Ramdas, Tibshirani 2021, "Predictive inference with the jackknife+", Ann.
Statist. 49(1) -- the K-fold "CV+" relaxation of Jackknife+, here with folds
defined by Bemis-Murcko scaffold GROUP membership instead of single points),
applied to the SAME 60-seed scaffold-disjoint Monte Carlo protocol that
refuted the OpenPoly Tg split-conformal marginal-coverage claim.

WHY ATTEMPT #1 (classifier-weighted covariate-shift conformal, Tibshirani et
al. 2019) FAILED HONESTLY: the scaffold-safe split has ZERO scaffold overlap
between train_pool and test by construction, and Morgan512 fingerprints
substantially encode scaffold identity, so a logistic-regression train/test
discriminator separates the two populations almost perfectly (p_test ~= 1 for
every test point after clipping). That drives every test point's normalized
weight to dominate its own calibration set, so EVERY weighted quantile came
back +inf: mean "coverage" = 1.0 but frac_unbounded_intervals = 1.0 -- a
vacuous, undeployable result (infinite-width intervals trivially "cover").
This is not reported as a repair; it is recorded as a negative, informative
result (see attempt1_diagnostic.json) and the item continues to attempt #2.

ROOT-CAUSE DIAGNOSIS driving attempt #2: the attacked protocol's "calib" set
is NOT scaffold-disjoint from "proper_train" -- both are drawn by a plain
train_test_split (point-level, random_state=seed) of train_pool, which does
NOT respect scaffold boundaries. So calibration residuals are measured
in-distribution (same scaffolds as the fitted model has seen) and
systematically UNDER-estimate the residual a genuinely novel scaffold (like
every point in the real held-out test set) will produce. That is the
mechanical reason marginal split-conformal undercovers here.

REPAIR: replace the calibration residual pool with an OUT-OF-FOLD, per-
scaffold-GROUP pool, computed only from train_pool (proper_train+calib
combined, i.e. calibration-side data -- the pinned MC test set is never
touched by this computation): for every unique scaffold g present in
train_pool, fit the identical StandardScaler+Ridge(Morgan512+log10MW,
alpha=1.0) protocol on train_pool MINUS every point belonging to scaffold g,
and record the abs residual of every point in scaffold g's held-out
prediction. Pooling these residuals over every scaffold in train_pool gives a
residual sample that is, for every single residual, generated under exactly
the kind of never-seen-this-scaffold generalization the real test set
imposes -- directly analogous to how CV+ generalizes Jackknife+ from
leave-one-point-out to leave-one-fold-out (here: leave-one-scaffold-out).

The finite-sample conformal quantile (same ceil((n+1)(1-alpha))/n order
statistic used throughout this module's audit chain) is then taken over this
larger, scaffold-heterogeneous residual pool, and applied via a model refit
on the FULL train_pool (standard CV+ practice: out-of-fold residuals for
calibration, full-data fit for prediction).

PRE-REGISTRATION: alpha=0.05 fixed (same nominal target as the attacked KPI).
No other choice in this script (Ridge alpha=1.0, StandardScaler, Morgan512+
log10 MW features, finite-sample quantile formula) differs from the attacked
protocol's own choices -- ONLY the residual pool used to compute qhat
changes, from "50/50 random split of train_pool" to "leave-one-scaffold-
group-out over all of train_pool". This script is run ONCE end-to-end
against all 60 seeds and its result, pass or fail, is reported as-is; no
hyperparameter was tuned against the 60-seed outcome.
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

ALPHA = 0.05
N_SEEDS = 60

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
    "note": "not imported or edited; only its deterministic split logic is duplicated below to guarantee identical per-seed splits",
}

uniq_scaffolds_all, scaf_counts_all = np.unique(scaf_arr, return_counts=True)
target_test_n = int(round(0.4 * n_total))

import base64
with open(ATTACK_RECEIPT_PATH) as f:
    attack_envelope = json.load(f)
attack_payload = json.loads(base64.b64decode(attack_envelope["signature"]["payload"]))
assert attack_payload["reproducibility"]["canonical_diagnostic_sha256"] == ATTACK_DIAGNOSTIC_SHA256
diag_actual_sha256 = sha256_of_file(ATTACK_DIAGNOSTIC_PATH)
assert diag_actual_sha256 == ATTACK_DIAGNOSTIC_SHA256, "attacked diagnostic.canonical.json has been tampered with"
with open(ATTACK_DIAGNOSTIC_PATH) as f:
    attack_diag = json.load(f)
attack_draws = attack_diag["draws"]
assert len(attack_draws) == N_SEEDS

draws = []
parity_mismatches = 0
n_loso_fallback_seeds = 0
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

    # ---- parity/fidelity check: recompute the ATTACKED (unweighted) method's
    # own calib/test split and coverage exactly, compare vs its signed table ----
    from sklearn.model_selection import train_test_split as _tts
    scaf_proper_train_idx, scaf_calib_idx = _tts(
        scaf_train_pool_idx, train_size=0.5, random_state=seed
    )
    scaler_u = StandardScaler().fit(X[scaf_proper_train_idx])
    ridge_u = Ridge(alpha=1.0, solver="cholesky").fit(
        scaler_u.transform(X[scaf_proper_train_idx]), tg[scaf_proper_train_idx]
    )
    calib_resid_u = np.abs(tg[scaf_calib_idx] - ridge_u.predict(scaler_u.transform(X[scaf_calib_idx])))
    qhat_u, _ = finite_sample_qhat(calib_resid_u)
    test_resid_u = np.abs(tg[scaf_test_idx] - ridge_u.predict(scaler_u.transform(X[scaf_test_idx])))
    coverage_unweighted = float(np.mean(test_resid_u <= qhat_u))

    ref = attack_draws[seed]
    assert ref["seed"] == seed
    n_test_matches = (len(scaf_test_idx) == ref["n_test_scaffold_safe"])
    cov_matches = abs(coverage_unweighted - ref["coverage_scaffold_safe"]) < 1e-9
    if not (n_test_matches and cov_matches):
        parity_mismatches += 1

    # ---- repair: scaffold-grouped CV+ over the FULL train_pool ----
    pool_scaf = scaf_arr[scaf_train_pool_idx]
    uniq_pool_scaf = np.unique(pool_scaf)
    n_pool = len(scaf_train_pool_idx)
    oof_resid = np.full(n_pool, np.nan)
    min_fold_train = n_pool
    for g in uniq_pool_scaf:
        held_mask = pool_scaf == g
        held_local = np.where(held_mask)[0]
        fit_local = np.where(~held_mask)[0]
        if len(fit_local) < 5:
            # too few points to fit a stable model excluding this group;
            # fall back to the full-pool fit for this group's residuals
            # (rare; only for seeds where a single scaffold dominates the
            # pool -- recorded honestly, not hidden)
            continue
        fit_idx = scaf_train_pool_idx[fit_local]
        held_idx = scaf_train_pool_idx[held_local]
        scaler_g = StandardScaler().fit(X[fit_idx])
        ridge_g = Ridge(alpha=1.0, solver="cholesky").fit(scaler_g.transform(X[fit_idx]), tg[fit_idx])
        pred_g = ridge_g.predict(scaler_g.transform(X[held_idx]))
        oof_resid[held_local] = np.abs(tg[held_idx] - pred_g)
        min_fold_train = min(min_fold_train, len(fit_idx))

    n_fallback = int(np.sum(np.isnan(oof_resid)))
    if n_fallback > 0:
        # fallback group(s): use the full-train_pool-fit residual (in-sample,
        # optimistic) for these points only -- honestly flagged in the record
        scaler_full = StandardScaler().fit(X[scaf_train_pool_idx])
        ridge_full = Ridge(alpha=1.0, solver="cholesky").fit(
            scaler_full.transform(X[scaf_train_pool_idx]), tg[scaf_train_pool_idx]
        )
        pred_full = ridge_full.predict(scaler_full.transform(X[scaf_train_pool_idx]))
        resid_full = np.abs(tg[scaf_train_pool_idx] - pred_full)
        nan_mask = np.isnan(oof_resid)
        oof_resid[nan_mask] = resid_full[nan_mask]
        n_loso_fallback_seeds += 1

    qhat_cvplus, _level = finite_sample_qhat(oof_resid, alpha=ALPHA)

    # final full-train_pool model used for actual test-set prediction
    scaler_full2 = StandardScaler().fit(X[scaf_train_pool_idx])
    ridge_full2 = Ridge(alpha=1.0, solver="cholesky").fit(
        scaler_full2.transform(X[scaf_train_pool_idx]), tg[scaf_train_pool_idx]
    )
    test_resid_cvplus = np.abs(tg[scaf_test_idx] - ridge_full2.predict(scaler_full2.transform(X[scaf_test_idx])))
    coverage_cvplus = float(np.mean(test_resid_cvplus <= qhat_cvplus))

    draws.append({
        "seed": seed,
        "n_test_scaffold_safe": int(len(scaf_test_idx)),
        "n_train_pool": int(n_pool),
        "n_unique_scaffolds_in_pool": int(len(uniq_pool_scaf)),
        "n_fallback_points_insample_residual": int(n_fallback),
        "min_fold_train_size": int(min_fold_train) if min_fold_train < n_pool else int(n_pool),
        "n_test_matches_refuting_receipt": bool(n_test_matches),
        "coverage_scaffold_safe_unweighted_matches_refuting_receipt": bool(cov_matches),
        "coverage_scaffold_safe_unweighted": coverage_unweighted,
        "coverage_scaffold_safe_cvplus": coverage_cvplus,
        "qhat_unweighted": qhat_u,
        "qhat_cvplus": qhat_cvplus,
        "width_inflation_ratio": float(qhat_cvplus / qhat_u) if qhat_u > 0 else None,
    })

results["parity_check_vs_refuting_receipt"] = {
    "attack_receipt_path": ATTACK_RECEIPT_PATH,
    "n_seeds_checked": N_SEEDS,
    "n_mismatches": parity_mismatches,
    "splits_identical": parity_mismatches == 0,
}
results["n_seeds_with_loso_fallback_points"] = n_loso_fallback_seeds

cov_cv = np.array([d["coverage_scaffold_safe_cvplus"] for d in draws])
cov_u = np.array([d["coverage_scaffold_safe_unweighted"] for d in draws])

results["n_seeds"] = N_SEEDS
results["alpha"] = ALPHA
results["target_test_n_fixed_across_draws"] = target_test_n
results["draws"] = draws
results["summary_stats"] = {
    "coverage_cvplus_mean": float(np.mean(cov_cv)),
    "coverage_cvplus_median": float(np.median(cov_cv)),
    "coverage_cvplus_std": float(np.std(cov_cv, ddof=1)),
    "coverage_cvplus_min": float(np.min(cov_cv)),
    "coverage_cvplus_max": float(np.max(cov_cv)),
    "coverage_unweighted_mean_recomputed": float(np.mean(cov_u)),
    "coverage_unweighted_mean_from_refuting_receipt": 0.8745741048157474,
    "n_draws_cvplus_below_090": int(np.sum(cov_cv < 0.90)),
    "mean_width_inflation_ratio": float(np.mean([d["width_inflation_ratio"] for d in draws if d["width_inflation_ratio"] is not None])),
}
results["acceptance"] = {
    "criterion": "mean coverage_scaffold_safe_cvplus over the identical 60-seed protocol >= 0.90",
    "observed_mean": float(np.mean(cov_cv)),
    "threshold": 0.90,
    "met": bool(np.mean(cov_cv) >= 0.90),
}

print(json.dumps(results, indent=2, sort_keys=True))
