#!/usr/bin/env python3
"""ROTATION attack on amphora-tolerance-robustness: repeated (multi-seed) Monte
Carlo escalation of the W5 scaffold-safe split-conformal exchangeability probe.

Claim under attack (STANDING claim this module currently relies on):
  amphora-tolerance-robustness/evidence/phase0/kpis/split-conformal-prediction-openpoly-tg-kpi.v1.json
  "empirical_coverage_95_pi": 0.9683257918552036 (frozen Push-20 Ridge base predictor)
  claim_lock: "conformal_coverage_guarantee_holds_only_under_exchangeability": true
  and its Morgan/Ridge-protocol cousins:
    jackknife-plus-cvplus-openpoly-tg-v1, mondrian-conformal-openpoly-tg-v1,
    normalized-adaptive-conformal-openpoly-tg-v1,
    training-conditional-pac-tolerance-openpoly-tg-v1

Prior attack (W5, fire 20260802T060002, ledger-recorded, receipt
evidence/audit/conformal-coverage-attack-v1/): ran ONE Bemis-Murcko
scaffold-disjoint (non-exchangeable) train/calibration/test split (seed=0)
on the SAME StandardScaler+Ridge(Morgan512+log10MW) protocol used by this
module's own jackknife+/CV+ / Mondrian / normalized-adaptive / training-
conditional-PAC audit chain, and found marginal coverage SURVIVED
(0.9719 scaffold-safe vs 0.9326 random-split, single draw). The W5 receipt
explicitly flagged this as a "single seed=0 draw" limitation.

ESCALATION (this attack): repeat the identical scaffold-safe vs random-split
protocol over N=60 independent seeds (0..59) to test whether the single-draw
survival was a favorable draw from a distribution that, under repeated
sampling, actually undercuts the exchangeability-dependent marginal-coverage
claim. This directly stress-tests robustness rather than a single point.

Pre-registered falsification criteria (fixed BEFORE looking at the N=60
results):
  F1: paired one-sided Wilcoxon signed-rank test on
      (coverage_scaffold_safe_i - coverage_random_i) across the N draws
      rejects H0: median_diff >= 0 in favor of H1: median_diff < 0
      (scaffold-safe systematically undercovers vs random) at alpha=0.05.
  F2: fraction of the N draws with scaffold-safe coverage < 0.90 (the same
      floor used in W5, derived from this module's own signed
      training-conditional-PAC 5th-percentile bound of 0.9226) exceeds 0.25
      (a quarter of independent draws breach the floor -> not a fluke).
  F3: the bootstrap (10000 resamples) 95% CI of the MEAN scaffold-safe
      coverage across the N draws excludes the nominal target 0.95.
Any one of F1/F2/F3 => CLAIM_REFUTED for the exchangeability-dependent
marginal coverage claim. None hold => CLAIM_SURVIVED, and this receipt
records exactly what F1/F2/F3 observed.
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
from sklearn.model_selection import train_test_split
from scipy import stats

ALPHA = 0.05
N_SEEDS = 60
COVERAGE_FLOOR = 0.90
FRAC_BREACH_THRESHOLD = 0.25
N_BOOTSTRAP = 10000
BOOT_SEED = 12345


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
target_test_n = int(round(0.4 * n_total))  # fixed across all draws, matches W5 (60/40)

draws = []
for seed in range(N_SEEDS):
    # ---- random 60/40 split, this seed ----
    train_pool_idx, test_idx = train_test_split(idx, train_size=0.6, random_state=seed)
    proper_train_idx, calib_idx = train_test_split(train_pool_idx, train_size=0.5, random_state=seed)

    scaler = StandardScaler().fit(X[proper_train_idx])
    ridge = Ridge(alpha=1.0, solver="cholesky").fit(scaler.transform(X[proper_train_idx]), tg[proper_train_idx])
    calib_resid = np.abs(tg[calib_idx] - ridge.predict(scaler.transform(X[calib_idx])))
    qhat_r, _ = finite_sample_qhat(calib_resid)
    test_resid = np.abs(tg[test_idx] - ridge.predict(scaler.transform(X[test_idx])))
    coverage_random = float(np.mean(test_resid <= qhat_r))

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

    scaler2 = StandardScaler().fit(X[scaf_proper_train_idx])
    ridge2 = Ridge(alpha=1.0, solver="cholesky").fit(
        scaler2.transform(X[scaf_proper_train_idx]), tg[scaf_proper_train_idx]
    )
    scaf_calib_resid = np.abs(tg[scaf_calib_idx] - ridge2.predict(scaler2.transform(X[scaf_calib_idx])))
    qhat_s, _ = finite_sample_qhat(scaf_calib_resid)
    scaf_test_resid = np.abs(tg[scaf_test_idx] - ridge2.predict(scaler2.transform(X[scaf_test_idx])))
    coverage_scaf = float(np.mean(scaf_test_resid <= qhat_s))

    draws.append({
        "seed": seed,
        "n_test_random": int(len(test_idx)),
        "n_test_scaffold_safe": int(len(scaf_test_idx)),
        "scaffold_overlap_train_pool_vs_test": int(overlap),
        "coverage_random": coverage_random,
        "coverage_scaffold_safe": coverage_scaf,
        "gap_scaffold_minus_random": coverage_scaf - coverage_random,
    })

cov_scaf = np.array([d["coverage_scaffold_safe"] for d in draws])
cov_rand = np.array([d["coverage_random"] for d in draws])
gaps = cov_scaf - cov_rand

# fidelity check vs W5's single seed=0 draw
seed0 = draws[0]
results["fidelity_check_vs_w5_seed0"] = {
    "w5_coverage_scaffold_safe_seed0": 0.9719101123595506,
    "this_coverage_scaffold_safe_seed0": seed0["coverage_scaffold_safe"],
    "matches": abs(seed0["coverage_scaffold_safe"] - 0.9719101123595506) < 1e-9,
    "w5_coverage_random_seed0": 0.9325842696629213,
    "this_coverage_random_seed0": seed0["coverage_random"],
    "matches_random": abs(seed0["coverage_random"] - 0.9325842696629213) < 1e-9,
}

# F1: one-sided Wilcoxon signed-rank test, H1: scaffold-safe < random
try:
    wres = stats.wilcoxon(gaps, alternative="less", zero_method="wilcox")
    wilcoxon_stat = float(wres.statistic)
    wilcoxon_p = float(wres.pvalue)
except Exception as e:
    wilcoxon_stat = None
    wilcoxon_p = None

f1_refutes = (wilcoxon_p is not None) and (wilcoxon_p < 0.05)

# F2: fraction of draws below floor
n_below_floor = int(np.sum(cov_scaf < COVERAGE_FLOOR))
frac_below_floor = n_below_floor / N_SEEDS
f2_refutes = frac_below_floor > FRAC_BREACH_THRESHOLD

# F3: bootstrap 95% CI of mean coverage_scaf across draws
boot_rng = np.random.RandomState(BOOT_SEED)
boot_means = np.array([
    boot_rng.choice(cov_scaf, size=N_SEEDS, replace=True).mean()
    for _ in range(N_BOOTSTRAP)
])
ci_lo, ci_hi = np.percentile(boot_means, [2.5, 97.5])
f3_refutes = not (ci_lo <= 0.95 <= ci_hi)

overall_refuted = f1_refutes or f2_refutes or f3_refutes

results["n_seeds"] = N_SEEDS
results["target_test_n_fixed_across_draws"] = target_test_n
results["draws"] = draws
results["summary_stats"] = {
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
}
results["falsification_tests"] = {
    "F1_wilcoxon_signed_rank_scaffold_lt_random": {
        "description": "One-sided Wilcoxon signed-rank test on paired (coverage_scaffold_safe - coverage_random) "
                        "across N=60 independent seeds; H1: scaffold-safe systematically undercovers vs random split.",
        "statistic": wilcoxon_stat,
        "p_value": wilcoxon_p,
        "alpha": 0.05,
        "refutes": f1_refutes,
    },
    "F2_fraction_draws_below_floor": {
        "description": f"Fraction of {N_SEEDS} independent scaffold-safe draws with coverage < {COVERAGE_FLOOR} "
                        f"(floor derived from this module's own signed training-conditional-PAC 5th-percentile bound 0.9226).",
        "n_below_floor": n_below_floor,
        "n_seeds": N_SEEDS,
        "fraction_below_floor": frac_below_floor,
        "threshold": FRAC_BREACH_THRESHOLD,
        "refutes": f2_refutes,
    },
    "F3_bootstrap_ci_mean_coverage_excludes_nominal": {
        "description": "10000-resample bootstrap 95% CI of the mean scaffold-safe coverage across the N=60 draws; "
                        "refutes if this CI excludes the nominal 0.95 target.",
        "n_bootstrap": N_BOOTSTRAP,
        "ci_95_lower": float(ci_lo),
        "ci_95_upper": float(ci_hi),
        "nominal_target": 0.95,
        "refutes": f3_refutes,
    },
}
results["verdict"] = {
    "overall": "CLAIM_REFUTED" if overall_refuted else "CLAIM_SURVIVED",
    "rationale": (
        "At least one pre-registered falsification test (F1/F2/F3) triggered."
        if overall_refuted else
        "None of the three pre-registered falsification tests (F1 paired Wilcoxon, F2 fraction-below-floor, "
        "F3 bootstrap-CI-excludes-nominal) triggered across N=60 independent scaffold-disjoint draws. "
        "The W5 single-seed survival was NOT a lucky draw: the exchangeability-dependent marginal coverage "
        "claim for OpenPoly Tg split-conformal prediction is robust to repeated non-exchangeable "
        "(scaffold-group-level) resampling, though per-scaffold conditional undercoverage (already "
        "documented in the module's own signed Mondrian receipt) is not addressed by this marginal test."
    ),
}

results["study_id"] = "amphora-tolerance-robustness-repeated-scaffold-monte-carlo-conformal-v1"
results["run_type"] = "AUDIT_ONLY falsification attack, repeated (N=60) Monte Carlo escalation of prior W5 single-seed scaffold-safe split-conformal probe"
results["claim_under_attack"] = {
    "claim_text": "The module's split-conformal marginal coverage on OpenPoly Tg (0.9683 at nominal 0.95, and its Morgan/Ridge-protocol cousins in the jackknife+/CV+, Mondrian, normalized-adaptive, and training-conditional-PAC audit chain, all claiming coverage_lock 'conformal_coverage_guarantee_holds_only_under_exchangeability') is robust to non-exchangeable (scaffold-group) deployment shift.",
    "receipt_paths": [
        "amphora-tolerance-robustness/evidence/phase0/kpis/split-conformal-prediction-openpoly-tg-kpi.v1.json",
        "amphora-tolerance-robustness/evidence/audit/jackknife-plus-cvplus-openpoly-tg-v1/jackknife-plus-cvplus-openpoly-tg-receipt.v1.dsse.json",
        "amphora-tolerance-robustness/evidence/audit/mondrian-conformal-openpoly-tg-v1/mondrian-conformal-openpoly-tg-receipt.v1.dsse.json",
    ],
    "prior_attack": "amphora-tolerance-robustness/evidence/audit/conformal-coverage-attack-v1/conformal-coverage-attack-receipt.v1.dsse.json (W5, single seed=0 scaffold-safe draw, SURVIVED)",
}
results["theory_references"] = [
    "Bemis GW, Murcko MA (1996) J. Med. Chem. 39(15):2887-2893 -- generic scaffold definition",
    "Papadopoulos H, Proedrou K, Vovk V, Gammerman A (2002) ECML -- split-conformal prediction",
    "Wilcoxon F (1945) Biometrics Bull 1(6):80-83 -- signed-rank test",
    "Efron B, Tibshirani RJ (1993) An Introduction to the Bootstrap, Chapman & Hall -- percentile bootstrap CI",
]

print(json.dumps(results, indent=2, sort_keys=True))
