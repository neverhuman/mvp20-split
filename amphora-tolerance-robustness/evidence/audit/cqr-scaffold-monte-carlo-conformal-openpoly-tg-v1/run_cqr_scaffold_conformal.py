#!/usr/bin/env python3
"""ROTATION attack on amphora-tolerance-robustness: repeated (N=60) Monte
Carlo scaffold-disjoint escalation applied to the Conformalized Quantile
Regression (CQR) sibling KPI, which has NEVER been scaffold-tested (only a
single random 60/20/20 seed=0 split).

Claim under attack (STANDING claim this module currently relies on):
  amphora-tolerance-robustness/evidence/phase0/kpis/conformalized-quantile-regression-openpoly-tg-kpi.v1.json
  "empirical_coverage_95_pi": 1.0000 (89/89) at nominal 0.95 target, single
  random seed=0 60/20/20 split. Base predictor: two GradientBoostingRegressor
  quantile models (alpha=0.025/0.975), Morgan512 r=2 + log10(MolWt) features,
  n_estimators=300, learning_rate=0.05, max_depth=4, random_state=0.
  claim_lock: "conformal_coverage_guarantee_holds_only_under_exchangeability": true
  scientific_receipt_sha256: 16fe912bb7285a7c97a174ebdef2fa86e34a9f5a525a7f86644e690221213693
  dataset_fixture_sha256: 8de5baf76f79610fe9173e63c65b824714aeb8445f9d670e1767956ea9db5eb3

Prior related work: the identical openpoly Tg corpus, under the same
scaffold-disjoint Monte Carlo protocol used here, already REFUTED the
Ridge-base split-conformal marginal coverage claim (repeated-scaffold-monte-
carlo-conformal-openpoly-tg-v1, 2026-08-03, mean 0.8746) and the RF-ML base
split-conformal sibling (rf-ml-scaffold-monte-carlo-conformal-openpoly-tg-v1,
2026-08-16, mean 0.8621, worse than Ridge). CQR is the third and last
never-scaffold-tested split-conformal sibling sharing this corpus and this
"conformal_guarantee_holds_only_under_exchangeability" claim_lock. This
attack closes that gap: identical pinned N=60 scaffold-disjoint Monte Carlo
protocol (same scaffold-assignment / 60/40 test-fraction logic as the
already-signed Ridge and RF-ML attacks) applied to the CQR base predictor
with its exact published featurization and hyperparameters.

CQR conformity score (Romano-Patterson-Candes 2019): for calibration point i,
  E_i = max(q_lo(x_i) - y_i, y_i - q_hi(x_i))
qhat = finite-sample-corrected (1-alpha) quantile of {E_i}. Test interval:
  [q_lo(x_test) - qhat, q_hi(x_test) + qhat]; covered iff y_test inside.

Pre-registered falsification criteria (fixed BEFORE looking at the N=60
results; identical to the already-signed Ridge/RF-ML attacks for direct
comparability):
  F1: paired one-sided Wilcoxon signed-rank test on
      (coverage_scaffold_safe_i - coverage_random_i) across the N draws
      rejects H0: median_diff >= 0 in favor of H1: median_diff < 0 at alpha=0.05.
  F2: fraction of the N draws with scaffold-safe coverage < 0.90 (the same
      floor this module already uses for the Ridge-base and RF-ML claims)
      exceeds 0.25.
  F3: the bootstrap (10000 resamples) 95% CI of the MEAN scaffold-safe
      coverage across the N draws excludes the nominal target 0.95.
Any one of F1/F2/F3 => CLAIM_REFUTED. None hold => CLAIM_SURVIVED, and this
receipt records exactly what F1/F2/F3 observed, plus a positive-control run.

POSITIVE CONTROL (required for a SURVIVED verdict): if F1/F2/F3 all fail to
trigger on the real data, this script re-runs the identical N=60 scaffold-
disjoint protocol against a deliberately corrupted copy of the calibration
step -- calibration-set Tg labels randomly permuted within each draw's
calibration split before computing CQR conformity scores -- which destroys
the calibration/test exchangeability the conformal guarantee depends on and
MUST collapse coverage far below 0.90. If the attack cannot detect that
planted defect, the survival verdict is invalid.
"""
import json
import hashlib
import math

import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit.Chem import AllChem, Descriptors
from rdkit.Chem.Scaffolds import MurckoScaffold
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from scipy import stats

ALPHA = 0.05
N_SEEDS = 60
COVERAGE_FLOOR = 0.90
FRAC_BREACH_THRESHOLD = 0.25
N_BOOTSTRAP = 10000
BOOT_SEED = 12345
GBM_KWARGS = dict(n_estimators=300, learning_rate=0.05, max_depth=4, random_state=0)
Q_LO_ALPHA = 0.025
Q_HI_ALPHA = 0.975


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


def fit_cqr(X_train, y_train):
    lo = GradientBoostingRegressor(loss="quantile", alpha=Q_LO_ALPHA, **GBM_KWARGS).fit(X_train, y_train)
    hi = GradientBoostingRegressor(loss="quantile", alpha=Q_HI_ALPHA, **GBM_KWARGS).fit(X_train, y_train)
    return lo, hi


def cqr_qhat(lo, hi, X_calib, y_calib, alpha=ALPHA):
    pred_lo = lo.predict(X_calib)
    pred_hi = hi.predict(X_calib)
    scores = np.maximum(pred_lo - y_calib, y_calib - pred_hi)
    n = len(scores)
    level = min(1.0, math.ceil((n + 1) * (1 - alpha)) / n)
    return float(np.quantile(scores, level, method="higher"))


def cqr_coverage(lo, hi, qhat, X_test, y_test):
    pred_lo = lo.predict(X_test)
    pred_hi = hi.predict(X_test)
    interval_lo = pred_lo - qhat
    interval_hi = pred_hi + qhat
    covered = (y_test >= interval_lo) & (y_test <= interval_hi)
    return float(np.mean(covered))


results = {}

openpoly_path = "feedback/v1/external_data/openpoly_benchmark/raw/final_polymer_properties_fromliterature.csv"
openpoly_sha256 = sha256_of_file(openpoly_path)

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
    "expected_n": 442,
}

uniq_scaffolds_all, scaf_counts_all = np.unique(scaf_arr, return_counts=True)
target_test_n = int(round(0.4 * n_total))  # fixed across all draws, matches pinned Ridge/RF-ML protocol (60/40)


def run_protocol(tg_vec, corrupt_calibration=False, corrupt_seed_offset=90000):
    draws = []
    for seed in range(N_SEEDS):
        # ---- random 60/40 split, this seed ----
        train_pool_idx, test_idx = train_test_split(idx, train_size=0.6, random_state=seed)
        proper_train_idx, calib_idx = train_test_split(train_pool_idx, train_size=0.5, random_state=seed)

        lo, hi = fit_cqr(X[proper_train_idx], tg_vec[proper_train_idx])
        calib_y = tg_vec[calib_idx].copy()
        if corrupt_calibration:
            crng = np.random.RandomState(corrupt_seed_offset + seed)
            calib_y = crng.permutation(calib_y)
        qhat_r = cqr_qhat(lo, hi, X[calib_idx], calib_y)
        coverage_random = cqr_coverage(lo, hi, qhat_r, X[test_idx], tg_vec[test_idx])

        # ---- scaffold-safe split, this seed: shuffle scaffolds, assign whole scaffolds to test ----
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
        scaf_proper_train_idx, scaf_calib_idx = train_test_split(
            scaf_train_pool_idx, train_size=0.5, random_state=seed
        )
        overlap = len(set(scaf_arr[scaf_train_pool_idx]).intersection(set(scaf_arr[scaf_test_idx])))

        lo2, hi2 = fit_cqr(X[scaf_proper_train_idx], tg_vec[scaf_proper_train_idx])
        scaf_calib_y = tg_vec[scaf_calib_idx].copy()
        if corrupt_calibration:
            crng2 = np.random.RandomState(corrupt_seed_offset + 50000 + seed)
            scaf_calib_y = crng2.permutation(scaf_calib_y)
        qhat_s = cqr_qhat(lo2, hi2, X[scaf_calib_idx], scaf_calib_y)
        coverage_scaf = cqr_coverage(lo2, hi2, qhat_s, X[scaf_test_idx], tg_vec[scaf_test_idx])

        draws.append({
            "seed": seed,
            "n_test_random": int(len(test_idx)),
            "n_test_scaffold_safe": int(len(scaf_test_idx)),
            "scaffold_overlap_train_pool_vs_test": int(overlap),
            "coverage_random": coverage_random,
            "coverage_scaffold_safe": coverage_scaf,
            "gap_scaffold_minus_random": coverage_scaf - coverage_random,
        })
    return draws


def summarize(draws):
    cov_scaf = np.array([d["coverage_scaffold_safe"] for d in draws])
    cov_rand = np.array([d["coverage_random"] for d in draws])
    gaps = cov_scaf - cov_rand

    try:
        wres = stats.wilcoxon(gaps, alternative="less", zero_method="wilcox")
        wilcoxon_stat = float(wres.statistic)
        wilcoxon_p = float(wres.pvalue)
    except Exception:
        wilcoxon_stat = None
        wilcoxon_p = None
    f1_refutes = (wilcoxon_p is not None) and (wilcoxon_p < 0.05)

    n_below_floor = int(np.sum(cov_scaf < COVERAGE_FLOOR))
    frac_below_floor = n_below_floor / N_SEEDS
    f2_refutes = frac_below_floor > FRAC_BREACH_THRESHOLD

    boot_rng = np.random.RandomState(BOOT_SEED)
    boot_means = np.array([
        boot_rng.choice(cov_scaf, size=N_SEEDS, replace=True).mean()
        for _ in range(N_BOOTSTRAP)
    ])
    ci_lo, ci_hi = np.percentile(boot_means, [2.5, 97.5])
    f3_refutes = not (ci_lo <= 0.95 <= ci_hi)

    overall_refuted = f1_refutes or f2_refutes or f3_refutes

    return {
        "summary_stats": {
            "coverage_scaffold_safe_mean": float(np.mean(cov_scaf)),
            "coverage_scaffold_safe_median": float(np.median(cov_scaf)),
            "coverage_scaffold_safe_std": float(np.std(cov_scaf, ddof=1)),
            "coverage_scaffold_safe_min": float(np.min(cov_scaf)),
            "coverage_scaffold_safe_max": float(np.max(cov_scaf)),
            "coverage_random_mean": float(np.mean(cov_rand)),
            "coverage_random_median": float(np.median(cov_rand)),
            "gap_mean": float(np.mean(gaps)),
            "gap_median": float(np.median(gaps)),
            "gap_std": float(np.std(gaps, ddof=1)),
        },
        "falsification_tests": {
            "F1_wilcoxon_signed_rank_scaffold_lt_random": {
                "statistic": wilcoxon_stat, "p_value": wilcoxon_p, "alpha": 0.05, "refutes": f1_refutes,
            },
            "F2_fraction_draws_below_floor": {
                "n_below_floor": n_below_floor, "n_seeds": N_SEEDS,
                "fraction_below_floor": frac_below_floor, "threshold": FRAC_BREACH_THRESHOLD,
                "refutes": f2_refutes,
            },
            "F3_bootstrap_ci_mean_coverage_excludes_nominal": {
                "n_bootstrap": N_BOOTSTRAP, "ci_95_lower": float(ci_lo), "ci_95_upper": float(ci_hi),
                "nominal_target": 0.95, "refutes": f3_refutes,
            },
        },
        "overall_refuted": overall_refuted,
    }


draws = run_protocol(tg, corrupt_calibration=False)
main_summary = summarize(draws)

results["n_seeds"] = N_SEEDS
results["target_test_n_fixed_across_draws"] = target_test_n
results["gbm_kwargs"] = GBM_KWARGS
results["cqr_alphas"] = {"q_lo_alpha": Q_LO_ALPHA, "q_hi_alpha": Q_HI_ALPHA}
results["featurization"] = {"morgan_bits": 512, "morgan_radius": 2, "additional_features": ["log10(molecular_weight)"], "scaler": "NONE (matches KPI's fitted_or_physical_model_artifact, GBM is scale-invariant)"}
results["draws"] = draws
results["summary_stats"] = main_summary["summary_stats"]
results["falsification_tests"] = main_summary["falsification_tests"]

overall_refuted = main_summary["overall_refuted"]

verdict = {}
positive_control = None

if overall_refuted:
    verdict["overall"] = "CLAIM_REFUTED"
    verdict["rationale"] = (
        "At least one pre-registered falsification test (F1/F2/F3) triggered for the CQR base "
        "predictor split-conformal marginal coverage claim under scaffold-disjoint (non-exchangeable) "
        "resampling of the SAME openpoly Tg corpus the KPI's own random-split evaluation used."
    )
else:
    control_draws = run_protocol(tg, corrupt_calibration=True)
    control_summary = summarize(control_draws)
    positive_control = {
        "planted_defect": "Calibration-split Tg labels randomly permuted within each of the 60 draws' "
                           "calibration set, both random-split and scaffold-safe variants, before computing "
                           "CQR conformity scores.",
        "how_planted": "In run_protocol(corrupt_calibration=True), calib_y = tg_vec[calib_idx] and "
                        "scaf_calib_y = tg_vec[scaf_calib_idx] are each replaced by a per-seed "
                        "np.random.RandomState(90000+seed[+50000]).permutation() of themselves before "
                        "CQR conformity scores max(q_lo(x)-y, y-q_hi(x)) are computed. This destroys the "
                        "exchangeability between calibration scores and test scores that the conformal "
                        "guarantee is built on, while leaving every other part of the pinned protocol (model "
                        "fit, scaffold assignment, test split, qhat quantile level) untouched.",
        "detected": bool(control_summary["overall_refuted"]),
        "evidence": {
            "control_coverage_scaffold_safe_mean": control_summary["summary_stats"]["coverage_scaffold_safe_mean"],
            "control_falsification_tests": control_summary["falsification_tests"],
        },
    }
    if not control_summary["overall_refuted"]:
        verdict["overall"] = "ATTACK_INVALID_NO_POSITIVE_CONTROL"
        verdict["rationale"] = (
            "Real-data attack did not refute the claim, but the attack also failed to detect a deliberately "
            "planted calibration-corruption defect -- it cannot be trusted to license a survival verdict."
        )
    else:
        verdict["overall"] = "CLAIM_SURVIVED"
        verdict["rationale"] = (
            "None of the three pre-registered falsification tests (F1 paired Wilcoxon, F2 fraction-below-floor, "
            "F3 bootstrap-CI-excludes-nominal) triggered across N=60 independent scaffold-disjoint draws for the "
            "CQR base predictor. A positive control (calibration-label permutation, breaking exchangeability "
            "by construction) WAS detected by the identical harness, confirming the attack has real power."
        )

results["verdict"] = verdict
if positive_control is not None:
    results["positive_control"] = positive_control

results["study_id"] = "amphora-tolerance-robustness-cqr-scaffold-monte-carlo-conformal-v1"
results["run_type"] = "AUDIT_ONLY falsification attack, N=60 scaffold-disjoint Monte Carlo probe of the CQR split-conformal sibling KPI (never previously scaffold-tested)"
results["claim_under_attack"] = {
    "claim_text": "The module's CQR-base split-conformal marginal coverage on OpenPoly Tg (1.0000 at nominal 0.95, "
                   "single random seed=0 60/20/20 split) with claim_lock 'conformal_coverage_guarantee_holds_only_under_exchangeability', "
                   "is robust to non-exchangeable (scaffold-group) deployment shift.",
    "receipt_paths": [
        "amphora-tolerance-robustness/evidence/phase0/kpis/conformalized-quantile-regression-openpoly-tg-kpi.v1.json",
    ],
    "scientific_receipt_sha256_pinned_in_kpi": "16fe912bb7285a7c97a174ebdef2fa86e34a9f5a525a7f86644e690221213693",
    "dataset_fixture_sha256_pinned_in_kpi": "8de5baf76f79610fe9173e63c65b824714aeb8445f9d670e1767956ea9db5eb3",
    "prior_analogous_attacks": [
        "amphora-tolerance-robustness/evidence/audit/repeated-scaffold-monte-carlo-conformal-openpoly-tg-v1/ (Ridge base, REFUTED, mean 0.8746)",
        "amphora-tolerance-robustness/evidence/audit/rf-ml-scaffold-monte-carlo-conformal-openpoly-tg-v1/ (RF-ML base, REFUTED, mean 0.8621)",
    ],
}
results["theory_references"] = [
    "Romano Y, Patterson E, Candes E (2019) Conformalized Quantile Regression, NeurIPS 32",
    "Bemis GW, Murcko MA (1996) J. Med. Chem. 39(15):2887-2893 -- generic scaffold definition",
    "Friedman JH (2001) Ann. Statist. 29(5):1189-1232 -- Gradient Boosting / quantile loss",
    "Wilcoxon F (1945) Biometrics Bull 1(6):80-83 -- signed-rank test",
    "Efron B, Tibshirani RJ (1993) An Introduction to the Bootstrap, Chapman & Hall -- percentile bootstrap CI",
]

print(json.dumps(results, indent=2, sort_keys=True))
