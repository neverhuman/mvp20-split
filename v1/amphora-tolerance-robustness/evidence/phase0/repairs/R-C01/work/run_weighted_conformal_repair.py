#!/usr/bin/env python3
"""R-C01 repair attempt: weighted conformal prediction (Tibshirani, Barber,
Candes, Ramdas 2019, "Conformal Prediction Under Covariate Shift", NeurIPS)
applied to the SAME 60-seed Bemis-Murcko scaffold-disjoint Monte Carlo
protocol that refuted the OpenPoly Tg split-conformal marginal-coverage claim
(receipt: repeated-scaffold-monte-carlo-conformal-openpoly-tg-v1, mean
scaffold-safe coverage 0.8746, F1/F2/F3 all triggered, CLAIM_REFUTED).

PRE-REGISTRATION (fixed BEFORE inspecting any of the 60-seed weighted-coverage
results, to avoid tuning against the held-out MC seeds the item forbids
touching):
  - Weight/discriminator model: sklearn LogisticRegression(C=1.0,
    class_weight="balanced", max_iter=2000), fit on the SAME
    StandardScaler+Morgan512+log10(MW) features already used by the attacked
    protocol, discriminating scaf_train_pool (label 0) vs scaf_test (label
    1) for EACH seed's own scaffold-safe split (no information from other
    seeds, no information from calibration-set residuals or labels y).
  - Weight function: w(x) = odds(x) = p_hat(test|x) / (1 - p_hat(test|x)),
    with p_hat clipped only to [1e-3, 1-1e-3] for numerical stability (NOT a
    tuned variance-reduction clip -- this is the standard numerical guard,
    applied identically regardless of outcome).
  - Weighted split-conformal quantile: Tibshirani et al. 2019 Algorithm 1 /
    Eq. (2.2): for test point x_{n+1} with weight w_{n+1}, normalized calib
    weights p_i = w_i / (sum_j w_j + w_{n+1}), p_{n+1} = w_{n+1} / (sum_j w_j
    + w_{n+1}); qhat(x_{n+1}) = the smallest sorted calibration residual R_(k)
    such that sum_{i<=k} p_(i) >= 1-alpha; if the required cumulative weight
    exceeds sum_i p_i (i.e. > 1 - p_{n+1}), qhat(x_{n+1}) = +inf (the
    trivial/unbounded interval -- reported honestly, not hidden).
  - alpha = 0.05 (identical nominal target to the attacked KPI).
  - NO other hyperparameter search was run against the 60-seed outcome. This
    script is executed ONCE end-to-end and its result -- pass or fail -- is
    reported as-is.

SPLITS: reproduces the attacked script's scaffold-safe train_pool/calib/test
assignment EXACTLY (same dataset load/filter order, same
np.random.RandomState(seed) scaffold shuffle, same target_test_n, same
train_test_split(..., random_state=seed) call for calib/proper_train) so that
per-seed splits are bit-identical to the refuting receipt. This is verified
programmatically below against the values embedded in the signed refuting
receipt's payload (draws[].coverage_scaffold_safe, draws[].n_test_scaffold_safe)
-- NOT re-derived by trust, but by exact recomputation and comparison.

This script does NOT modify, and does not import code from,
run_repeated_scaffold_conformal.py (sha256
96be585e27428a1f9bec0a7e2c078f9488711df5515790bc24ac35ac97cf0e09, pinned,
unmodified). It duplicates only the deterministic data-loading and
scaffold-safe-split logic necessary to guarantee identical splits, then
substitutes a different (weighted) calibration procedure for the marginal
split-conformal one.
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
from sklearn.linear_model import Ridge, LogisticRegression
from sklearn.model_selection import train_test_split

ALPHA = 0.05
N_SEEDS = 60
PROB_CLIP = (1e-3, 1 - 1e-3)

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


def weighted_qhat_per_test_point(calib_resid, w_calib, w_test, alpha=ALPHA):
    """Tibshirani et al. 2019 weighted split-conformal quantile, computed
    independently for each test point (weights depend on x_{n+1})."""
    order = np.argsort(calib_resid)
    r_sorted = calib_resid[order]
    w_sorted = w_calib[order]
    w_sum_calib = w_sorted.sum()
    out = np.empty(len(w_test))
    unbounded = np.zeros(len(w_test), dtype=bool)
    for j, wj in enumerate(w_test):
        total = w_sum_calib + wj
        p_sorted = w_sorted / total
        cum = np.cumsum(p_sorted)
        need = 1.0 - alpha
        idx = np.searchsorted(cum, need, side="left")
        if idx >= len(r_sorted):
            out[j] = np.inf
            unbounded[j] = True
        else:
            out[j] = r_sorted[idx]
    return out, unbounded


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

# Load the refuting receipt's own per-seed table for a parity/fidelity check.
# The signed receipt payload carries only summary_stats (not the per-seed
# draws); the per-seed table lives in the checked-in two-replay diagnostic,
# whose sha256 IS recorded inside the signed payload
# (reproducibility.canonical_diagnostic_sha256) -- verified below before use.
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
    scaf_proper_train_idx, scaf_calib_idx = train_test_split(
        scaf_train_pool_idx, train_size=0.5, random_state=seed
    )

    scaler2 = StandardScaler().fit(X[scaf_proper_train_idx])
    ridge2 = Ridge(alpha=1.0, solver="cholesky").fit(
        scaler2.transform(X[scaf_proper_train_idx]), tg[scaf_proper_train_idx]
    )
    scaf_calib_resid = np.abs(tg[scaf_calib_idx] - ridge2.predict(scaler2.transform(X[scaf_calib_idx])))
    qhat_s_unweighted, _ = finite_sample_qhat(scaf_calib_resid)
    scaf_test_resid = np.abs(tg[scaf_test_idx] - ridge2.predict(scaler2.transform(X[scaf_test_idx])))
    coverage_scaf_unweighted = float(np.mean(scaf_test_resid <= qhat_s_unweighted))

    # ---- parity check vs the pinned refuting receipt's own per-seed table ----
    ref = attack_draws[seed]
    assert ref["seed"] == seed
    n_test_matches = (len(scaf_test_idx) == ref["n_test_scaffold_safe"])
    cov_matches = abs(coverage_scaf_unweighted - ref["coverage_scaffold_safe"]) < 1e-9
    if not (n_test_matches and cov_matches):
        parity_mismatches += 1

    # ---- weighted conformal: discriminator train_pool(0) vs test(1) ----
    disc_scaler = StandardScaler().fit(np.vstack([X[scaf_train_pool_idx], X[scaf_test_idx]]))
    Xd_pool = disc_scaler.transform(X[scaf_train_pool_idx])
    Xd_test = disc_scaler.transform(X[scaf_test_idx])
    y_disc = np.concatenate([
        np.zeros(len(scaf_train_pool_idx)),
        np.ones(len(scaf_test_idx)),
    ])
    Xd_all = np.vstack([Xd_pool, Xd_test])
    clf = LogisticRegression(C=1.0, class_weight="balanced", max_iter=2000)
    clf.fit(Xd_all, y_disc)

    Xd_calib = disc_scaler.transform(X[scaf_calib_idx])
    p_calib = np.clip(clf.predict_proba(Xd_calib)[:, 1], *PROB_CLIP)
    w_calib = p_calib / (1 - p_calib)
    p_test = np.clip(clf.predict_proba(Xd_test)[:, 1], *PROB_CLIP)
    w_test = p_test / (1 - p_test)

    qhat_w, unbounded = weighted_qhat_per_test_point(scaf_calib_resid, w_calib, w_test, alpha=ALPHA)
    covered = scaf_test_resid <= qhat_w
    covered = covered | unbounded  # unbounded interval trivially covers
    coverage_weighted = float(np.mean(covered))
    frac_unbounded = float(np.mean(unbounded))
    finite_qhat = qhat_w[np.isfinite(qhat_w)]
    mean_finite_width = float(np.mean(finite_qhat) * 2) if len(finite_qhat) else None
    mean_unweighted_width = float(qhat_s_unweighted * 2)

    draws.append({
        "seed": seed,
        "n_test_scaffold_safe": int(len(scaf_test_idx)),
        "n_calib": int(len(scaf_calib_idx)),
        "n_test_matches_refuting_receipt": bool(n_test_matches),
        "coverage_scaffold_safe_unweighted_matches_refuting_receipt": bool(cov_matches),
        "coverage_scaffold_safe_unweighted": coverage_scaf_unweighted,
        "coverage_scaffold_safe_weighted": coverage_weighted,
        "frac_unbounded_intervals": frac_unbounded,
        "mean_finite_interval_width_weighted": mean_finite_width,
        "mean_interval_width_unweighted": mean_unweighted_width,
        "discriminator_train_auc_selfcheck": None,
    })

results["parity_check_vs_refuting_receipt"] = {
    "attack_receipt_path": ATTACK_RECEIPT_PATH,
    "n_seeds_checked": N_SEEDS,
    "n_mismatches": parity_mismatches,
    "splits_identical": parity_mismatches == 0,
}

cov_w = np.array([d["coverage_scaffold_safe_weighted"] for d in draws])
cov_u = np.array([d["coverage_scaffold_safe_unweighted"] for d in draws])
frac_unb = np.array([d["frac_unbounded_intervals"] for d in draws])

results["n_seeds"] = N_SEEDS
results["alpha"] = ALPHA
results["target_test_n_fixed_across_draws"] = target_test_n
results["draws"] = draws
results["summary_stats"] = {
    "coverage_weighted_mean": float(np.mean(cov_w)),
    "coverage_weighted_median": float(np.median(cov_w)),
    "coverage_weighted_std": float(np.std(cov_w, ddof=1)),
    "coverage_weighted_min": float(np.min(cov_w)),
    "coverage_weighted_max": float(np.max(cov_w)),
    "coverage_unweighted_mean_recomputed": float(np.mean(cov_u)),
    "coverage_unweighted_mean_from_refuting_receipt": 0.8745741048157474,
    "mean_frac_unbounded_intervals": float(np.mean(frac_unb)),
    "n_draws_weighted_below_090": int(np.sum(cov_w < 0.90)),
}
results["acceptance"] = {
    "criterion": "mean coverage_scaffold_safe_weighted over the identical 60-seed protocol >= 0.90",
    "observed_mean": float(np.mean(cov_w)),
    "threshold": 0.90,
    "met": bool(np.mean(cov_w) >= 0.90),
}

print(json.dumps(results, indent=2, sort_keys=True))
