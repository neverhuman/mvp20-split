#!/usr/bin/env python3
"""amphora-design-rule-score  AUDIT_ONLY scientific increment (STATISTICAL-METHODOLOGY axis).

FALSIFICATION ATTACK on the module's currently-surviving significance claim
"guth_gold_directional_concordance_exceeds_chance_leak_free"
(split-integrity-dedup-v1: C=0.7111, test-only cluster-bootstrap CI
[0.6155, 0.7980]; guth-gold-nested-refit-bootstrap-v1: nested train-refit
CI [0.6352, 0.7270], SURVIVED a harder train-refit bootstrap on 2026-08-02).

Both surviving receipts hold the leave-one-iteration-out FOLD STRUCTURE
fixed: there are only G=3 clusters (DoE iterations, sizes 17/26/15) in the
entire leak-free 58-row Purformance dataset. Neither bootstrap variant ever
resamples which points are assigned to which of the 3 iterations -- that
axis of uncertainty is structurally unresamplable because there are only 3
iterations in the whole population. Cameron, Gelbach & Miller 2008 (the
paper both parent receipts cite as their own bootstrap's justification)
explicitly warn that cluster-robust / cluster-bootstrap inference becomes
unreliable (anti-conservative: nominal 95% CIs cover the truth far less
than 95% of the time) when the number of clusters G is small (rule-of-thumb
G>=20-30; G=3 here is far below any regime in which the method's own
citation claims validity).

This receipt does not merely assert that concern -- it MEASURES it. Attack:
Monte-Carlo COVERAGE CALIBRATION under a genuine null. For M independent
label-permutation nulls (true relationship between (Vernetzung, HDI-IPDI,
Mattierungsmittel, Pigmentpaste) and Kratzharte destroyed by permuting y
across all 58 rows, exact real X and exact real g/fold-size structure
preserved), refit Guth-Gold via the identical LOIO protocol and construct
a 95% CI with each bootstrap variant. Under a well-calibrated method, the
one-sided false-positive rate (fraction of null simulations whose 95% CI
lower bound exceeds 0.5, i.e. spuriously "excludes chance") should be close
to the nominal ~2.5%. If the observed empirical rate is far higher, this
proves the exact CI machinery behind the standing claim is unreliable with
G=3 clusters -- the real-data CI excluding 0.5 cannot be trusted as
evidence of skill because the method manufactures such exclusions from pure
noise at an inflated rate.

PRE-REGISTERED REFUTATION CRITERION (fixed before running):
  empirical one-sided false-positive rate > 3x nominal (i.e. > 7.5%) for
  EITHER the parent test-only protocol or the nested train-refit protocol
  => REFUTES reliance on "CI excludes chance" as genuine evidence for the
  standing claim.
  Both protocols staying at <= 7.5% => claim SURVIVES this attack.

Identical dataset, dedup protocol, arm definition, and fold assignment as
benchmarks/split-integrity-dedup-v1 and
benchmarks/guth-gold-nested-refit-bootstrap-v1.

Theory / method references:
  * Guth & Gold 1938 Phys. Rev. 53:322; Guth 1945 J. Appl. Phys. 16:20-25
  * Hanley & McNeil 1982 Radiology 143(1):29-36 (AUC = pairwise concordance)
  * Efron & Tibshirani 1993 An Introduction to the Bootstrap
  * Cameron, Gelbach & Miller 2008 Rev. Econ. Stat. 90(3):414-427 (cluster
    bootstrap; explicit small-G warning, Sec. IV-V; parent method's own
    citation)
  * Cameron & Miller 2015 J. Human Resources 50(2):317-372 ("A Practitioner's
    Guide to Cluster-Robust Inference" -- G<20-30 rule of thumb, wild
    cluster bootstrap recommended for small G)
  * MacKinnon & Webb 2017 J. Applied Econometrics 32(2):233-254 (few-cluster
    inference can be severely size-distorted)
  * Kaufman, Rosset, Perlich 2012 ACM TKDD 6(4):15 (leakage; motivates the
    leak-free 58-row protocol this receipt inherits)
  * Cordts, Sassmannshausen, Rendel, Klein, Reddemann, Berge 2024 Chem.
    Mater. (Purformance, Zenodo 13742098, CC-BY-4.0)

Byte-stable: every stochastic step is np.random.default_rng(SEED).
"""
import json, hashlib, sys, io, zipfile
import numpy as np
import pandas as pd
from scipy.optimize import least_squares
import sklearn, scipy, openpyxl

ROOT = "/home/ubuntu/amphora/build/mvp20-split/amphora-design-rule-score"
ZIP = ROOT + "/reference/purformance/zenodo-13742098/Experiment.zip"
FEATS = ["Vernetzung", "HDI-IPDI", "Mattierungsmittel", "Pigmentpaste"]
TARGET = "Kratzhärte"
LOCKED_ZIP_SHA = "b6e89fe900b1aaf73beb882eeb07dfaf702e0818c9f443de6e84aaa8e32b0036"
ITER = (1, 2, 3)
CHANCE = 0.5
NOMINAL_FPR = 0.025
REFUTE_THRESHOLD = 0.075  # 3x nominal

M_A, B_A = 1000, 2000   # parent test-only protocol calibration (cheap: no refit in bootstrap loop)
M_B, B_B = 80, 400      # nested train-refit protocol calibration (expensive: refit every replicate)

# ---------------------------------------------------------------- load (identical to parent receipts)
zf = zipfile.ZipFile(ZIP)
per_iter = {}
for i in ITER:
    df = pd.read_excel(io.BytesIO(zf.read(f"Experiment/iteration_{i}_doe_actual.xlsx")))
    per_iter[i] = [(tuple(np.round(list(r[FEATS]), 9)), float(round(r[TARGET], 9)))
                   for _, r in df.iterrows()]
zip_sha = hashlib.sha256(open(ZIP, "rb").read()).hexdigest()

raw_rows = [(i, f, t) for i in ITER for (f, t) in per_iter[i]]
seen, dedup_rows = {}, []
for i, f, t in raw_rows:
    if (f, t) in seen:
        continue
    seen[(f, t)] = i
    dedup_rows.append((i, f, t))

X = np.array([r[1] for r in dedup_rows], float)
y = np.array([r[2] for r in dedup_rows], float)
g = np.array([r[0] for r in dedup_rows], int)
n = len(y)
fold_sizes = {int(k): int((g == k).sum()) for k in ITER}

# ---------------------------------------------------------------- Guth-Gold 1938 arm (identical fit as parent receipts)
def gg_fit_predict(Xt, yt, Xe):
    V, H, M, P = Xt.T
    def resid(th):
        phi = th[3] * M + th[4] * P
        return th[0] * (1 + th[1] * V + th[2] * H) * (1 + 2.5 * phi + 14.1 * phi * phi) - yt
    s = least_squares(resid, [yt.mean(), 0.1, 0.1, 0.05, 0.05],
                      bounds=([0, -2, -2, 0, 0], [np.inf, 5, 5, 0.3, 0.3]),
                      max_nfev=20000).x
    Ve, He, Me, Pe = Xe.T
    phi = s[3] * Me + s[4] * Pe
    return s[0] * (1 + s[1] * Ve + s[2] * He) * (1 + 2.5 * phi + 14.1 * phi * phi)

def loio_pred(Xf, yf, gf, fitfn):
    p = np.zeros(len(yf))
    for i in ITER:
        tr, te = gf != i, gf == i
        p[te] = fitfn(Xf[tr], yf[tr], Xf[te])
    return p

def pair_index_for(idx):
    ii, jj = [], []
    for a in range(len(idx)):
        for b in range(a + 1, len(idx)):
            ii.append(idx[a]); jj.append(idx[b])
    return np.array(ii, int), np.array(jj, int)

def pair_index(gf):
    ii_all, jj_all = [], []
    for k in ITER:
        idx = np.where(gf == k)[0]
        ii, jj = pair_index_for(idx)
        ii_all.append(ii); jj_all.append(jj)
    return np.concatenate(ii_all), np.concatenate(jj_all)

II, JJ = pair_index(g)
fold_idx = {k: np.where(g == k)[0] for k in ITER}

def concordance_at(yv, p, ii, jj):
    dy = yv[ii] - yv[jj]
    m = dy != 0
    ds = p[ii][m] - p[jj][m]
    dyv = dy[m]
    nn = len(dyv)
    if nn == 0:
        return 0.5, 0
    conc = (np.sign(ds) == np.sign(dyv)).sum()
    ties = (ds == 0).sum()
    return float((conc + 0.5 * ties) / nn), int(nn)

def concordance(yv, p):
    return concordance_at(yv, p, II, JJ)

# ---------------------------------------------------------------- reproduce real point estimate (sanity)
p_obs = loio_pred(X, y, g, gg_fit_predict)
C_obs, n_pairs = concordance(y, p_obs)
PARENT_C_OBS = 0.7111307420494699
reproduces_parent_point_estimate = bool(round(C_obs, 10) == round(PARENT_C_OBS, 10))

train_idx_by_fold = {i: np.where(g != i)[0] for i in ITER}
test_idx_by_fold = {i: np.where(g == i)[0] for i in ITER}

# ================================================================== PROTOCOL A: parent test-only cluster bootstrap, calibrated under M_A nulls
# Fully vectorized per-null: precompute local (triu) pair indices once per
# fold size, then broadcast the B_A within-fold bootstrap resamples as a
# single (B_A, fold_size) numpy array instead of a python loop over pairs.
LOCAL_PAIRS = {}
for k in ITER:
    fs = fold_sizes[k]
    lii, ljj = np.triu_indices(fs, k=1)
    LOCAL_PAIRS[k] = (lii, ljj)

rng_perm_a = np.random.default_rng(101)
excl_a = np.zeros(M_A, dtype=bool)
excl_a_upper = np.zeros(M_A, dtype=bool)
C_obs_a = np.empty(M_A)
for m in range(M_A):
    y_null = y.copy()
    rng_perm_a.shuffle(y_null)
    p_null = loio_pred(X, y_null, g, gg_fit_predict)
    C_obs_a[m], _ = concordance(y_null, p_null)
    rng_b = np.random.default_rng(2000 + m)
    conc_tot = np.zeros(B_A)
    tie_tot = np.zeros(B_A)
    nn_tot = np.zeros(B_A)
    for k in ITER:
        idx = fold_idx[k]
        fs = len(idx)
        resampled = rng_b.choice(idx, size=(B_A, fs), replace=True)
        p_res = p_null[resampled]
        y_res = y_null[resampled]
        lii, ljj = LOCAL_PAIRS[k]
        dy = y_res[:, lii] - y_res[:, ljj]
        ds = p_res[:, lii] - p_res[:, ljj]
        mask = dy != 0
        sign_match = (np.sign(ds) == np.sign(dy)) & mask
        tie = (ds == 0) & mask
        conc_tot += sign_match.sum(axis=1)
        tie_tot += tie.sum(axis=1)
        nn_tot += mask.sum(axis=1)
    with np.errstate(invalid="ignore", divide="ignore"):
        C_boot = np.where(nn_tot > 0, (conc_tot + 0.5 * tie_tot) / np.maximum(nn_tot, 1), 0.5)
    lo, hi = float(np.percentile(C_boot, 2.5)), float(np.percentile(C_boot, 97.5))
    excl_a[m] = lo > CHANCE
    excl_a_upper[m] = hi < CHANCE

fpr_a = float(excl_a.mean())
fpr_a_upper = float(excl_a_upper.mean())
fpr_a_either = float((excl_a | excl_a_upper).mean())

# ================================================================== PROTOCOL B: nested train-refit bootstrap, calibrated under M_B nulls (reduced scale for cost)
rng_perm_b = np.random.default_rng(303)
excl_b = np.zeros(M_B, dtype=bool)
excl_b_upper = np.zeros(M_B, dtype=bool)
C_obs_b = np.empty(M_B)
fit_failures_b = 0
for m in range(M_B):
    y_null = y.copy()
    rng_perm_b.shuffle(y_null)
    p_null = loio_pred(X, y_null, g, gg_fit_predict)
    C_obs_b[m], _ = concordance(y_null, p_null)
    rng_b = np.random.default_rng(9000 + m)
    C_boot = np.empty(B_B)
    for b in range(B_B):
        p_b = np.zeros(n)
        for i in ITER:
            tr = train_idx_by_fold[i]
            te = test_idx_by_fold[i]
            tr_resampled = rng_b.choice(tr, size=len(tr), replace=True)
            try:
                p_b[te] = gg_fit_predict(X[tr_resampled], y_null[tr_resampled], X[te])
            except Exception:
                fit_failures_b += 1
                p_b[te] = y_null[tr_resampled].mean()
        C_boot[b] = concordance(y_null, p_b)[0]
    lo, hi = float(np.percentile(C_boot, 2.5)), float(np.percentile(C_boot, 97.5))
    excl_b[m] = lo > CHANCE
    excl_b_upper[m] = hi < CHANCE

fpr_b = float(excl_b.mean())
fpr_b_upper = float(excl_b_upper.mean())
fpr_b_either = float((excl_b | excl_b_upper).mean())

# ---------------------------------------------------------------- verdict
protocol_a_refutes = fpr_a > REFUTE_THRESHOLD
protocol_b_refutes = fpr_b > REFUTE_THRESHOLD
claim_refuted = bool(protocol_a_refutes or protocol_b_refutes)

interp = (
    "COVERAGE-CALIBRATION ATTACK on the module's currently-surviving significance claim "
    "'guth_gold_directional_concordance_exceeds_chance_leak_free' (split-integrity-dedup-v1 C=%.4f "
    "CI[0.6155,0.7980]; guth-gold-nested-refit-bootstrap-v1 CI[0.6352,0.7270], SURVIVED "
    "2026-08-02). Both surviving CIs are built over a G=3-cluster leave-one-iteration-out structure "
    "(fold sizes 17/26/15) and never resample which points are assigned to which of the 3 DoE "
    "iterations -- that axis is structurally fixed because only 3 iterations exist in the whole "
    "population. Cameron, Gelbach & Miller 2008 (cited by the parent receipt as the bootstrap's own "
    "justification) explicitly warn that cluster-bootstrap inference is unreliable for G below "
    "roughly 20-30. This receipt MEASURES that warning directly: %d (protocol A, parent test-only) "
    "and %d (protocol B, nested train-refit) independent true-null simulations (y permuted across "
    "all 58 rows, exact real X and exact real fold structure preserved, so H0: no true "
    "feature-target relationship holds exactly) were each run through the identical CI-construction "
    "machinery as the two standing receipts. PRE-REGISTERED REFUTATION CRITERION: one-sided "
    "empirical false-positive rate (fraction of null CIs whose 95%% lower bound spuriously exceeds "
    "0.5) > 7.5%% (3x the nominal ~2.5%%) for EITHER protocol. "
    "OBSERVED: protocol A (parent test-only, M=%d, B=%d) empirical FPR = %.4f (%.2f%%) "
    "[lower-bound-exceeds-chance], %.4f (%.2f%%) [upper-bound-below-chance], %.4f (%.2f%%) "
    "[either tail]. Protocol B (nested train-refit, M=%d, B=%d) empirical FPR = %.4f (%.2f%%) "
    "[lower-bound-exceeds-chance], %.4f (%.2f%%) [upper-bound-below-chance], %.4f (%.2f%%) "
    "[either tail]. VERDICT: %s. %s"
) % (
    PARENT_C_OBS, M_A, M_B,
    M_A, B_A, fpr_a, 100 * fpr_a, fpr_a_upper, 100 * fpr_a_upper, fpr_a_either, 100 * fpr_a_either,
    M_B, B_B, fpr_b, 100 * fpr_b, fpr_b_upper, 100 * fpr_b_upper, fpr_b_either, 100 * fpr_b_either,
    "CLAIM REFUTED -- at least one CI-construction protocol behind the standing claim manufactures "
    "spurious 'excludes chance' exclusions from pure noise at a rate far above nominal, so the "
    "real-data CI excluding 0.5 cannot be trusted as genuine evidence of skill" if claim_refuted else
    "CLAIM SURVIVES -- both protocols' empirical false-positive rates stay within the "
    "pre-registered tolerance despite G=3, so the real-data CI exclusion of 0.5 is not explained "
    "by miscalibration of the interval-construction method alone",
    "This does not certify the standing point estimate C_obs=0.7111 is itself correct or "
    "generalizable -- only that this specific class of attack (CI miscalibration under few "
    "clusters) does/does not explain it." ,
)

body = {
    "schema": "amphora.design-rule-score.cluster-count-coverage-calibration-receipt.v1",
    "module": "amphora-design-rule-score",
    "authority": "AUDIT_ONLY",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "closes_gate": None,
    "modifies_existing_receipts": False,
    "modifies_manifest": False,
    "modifies_module_manifest": False,
    "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "human_review_performed": False,
    "attacks_claim": "amphora-design-rule-score/evidence/phase0/kpis/purformance-scratch-hardness-dedup-superseding-kpi.v1.json :: guth_gold_directional_concordance_exceeds_chance_leak_free",
    "attacks_receipts": [
        "benchmarks/split-integrity-dedup-v1/split-integrity-deduplication-receipt.v1.json",
        "benchmarks/guth-gold-nested-refit-bootstrap-v1/guth-gold-nested-refit-bootstrap-receipt.v1.json",
    ],
    "target": TARGET,
    "target_unit": "N (Erichsen 435 nano-scratch)",
    "features": FEATS,
    "input_zip_sha256": zip_sha,
    "input_zip_matches_locked_dataset_fixture": bool(zip_sha == LOCKED_ZIP_SHA),
    "protocol": "leave-one-iteration-out over the 58 leak-free unique (feature,target) observations, folds 17/26/15 (identical construction as split-integrity-dedup-v1)",
    "n_observations": int(n),
    "fold_sizes": fold_sizes,
    "n_within_fold_comparable_pairs": n_pairs,
    "n_clusters": 3,
    "arm": "P1_guth_gold_1938 (Guth & Gold 1938 Phys. Rev. 53:322, 5-param bounded least_squares, identical to parent receipts)",
    "point_estimate": {
        "C_obs": C_obs,
        "parent_receipted_C_obs": PARENT_C_OBS,
        "reproduces_parent_point_estimate": reproduces_parent_point_estimate,
    },
    "nominal_one_sided_false_positive_rate": NOMINAL_FPR,
    "refutation_threshold_one_sided_fpr": REFUTE_THRESHOLD,
    "protocol_a_parent_test_only": {
        "description": "identical bootstrap machinery as split-integrity-dedup-v1: per-fold Guth-Gold fit ONCE on true (permuted-null) training data, then B_A within-fold-stratified resamples of held-out points (no refit) recompute concordance",
        "n_null_simulations": M_A,
        "bootstrap_resamples_per_null": B_A,
        "empirical_lower_bound_exceeds_chance_rate": fpr_a,
        "empirical_upper_bound_below_chance_rate": fpr_a_upper,
        "empirical_either_tail_exclusion_rate": fpr_a_either,
        "refutes_claim": bool(protocol_a_refutes),
        "null_C_obs_mean": float(C_obs_a.mean()),
        "null_C_obs_std": float(C_obs_a.std(ddof=1)),
    },
    "protocol_b_nested_train_refit": {
        "description": "identical bootstrap machinery as guth-gold-nested-refit-bootstrap-v1: per-replicate per-fold resample of TRAINING rows with replacement, Guth-Gold refit from scratch on resampled (permuted-null) training data, scored against original held-out fold",
        "n_null_simulations": M_B,
        "bootstrap_resamples_per_null": B_B,
        "fit_failures": fit_failures_b,
        "empirical_lower_bound_exceeds_chance_rate": fpr_b,
        "empirical_upper_bound_below_chance_rate": fpr_b_upper,
        "empirical_either_tail_exclusion_rate": fpr_b_either,
        "refutes_claim": bool(protocol_b_refutes),
        "null_C_obs_mean": float(C_obs_b.mean()),
        "null_C_obs_std": float(C_obs_b.std(ddof=1)),
    },
    "refutation_criterion": (
        "one-sided empirical false-positive rate (fraction of true-null Monte-Carlo simulations, "
        "exact real X and fold structure preserved, y permuted) whose 95%% CI lower bound spuriously "
        "exceeds 0.5 chance, > 7.5%% (3x nominal ~2.5%%) for EITHER the parent test-only or the "
        "nested train-refit bootstrap protocol"
    ),
    "claim_refuted": claim_refuted,
    "honest_interpretation": interp,
    "claim_scope": ("Statistical-methodology audit only, restricted to the Purformance HTE 2K-PUR "
                     "lacquer scratch-hardness leak-free 58-observation, G=3-cluster benchmark. "
                     "Does not modify or delete split-integrity-dedup-v1 or "
                     "guth-gold-nested-refit-bootstrap-v1. Grants no batch-release, qualification, "
                     "optimizer, or product-performance authority. n=58 leak-free observations from "
                     "a single formulator and a single instrument; G=3 DoE iterations is the entire "
                     "population of clusters available, so no attack can supply more independent "
                     "cluster-level replication than this dataset physically contains."),
    "theory_references": [
        "Guth & Gold 1938 Phys. Rev. 53:322 (Einstein-Guth-Gold filler reinforcement)",
        "Guth 1945 J. Appl. Phys. 16:20-25",
        "Hanley & McNeil 1982 Radiology 143(1):29-36 (AUC = pairwise concordance)",
        "Efron & Tibshirani 1993 An Introduction to the Bootstrap",
        "Cameron, Gelbach & Miller 2008 Rev. Econ. Stat. 90(3):414-427 (cluster bootstrap; parent method's own citation, explicit small-G warning)",
        "Cameron & Miller 2015 J. Human Resources 50(2):317-372 (Practitioner's Guide to Cluster-Robust Inference)",
        "MacKinnon & Webb 2017 J. Applied Econometrics 32(2):233-254 (few-cluster inference size distortion)",
        "Kaufman, Rosset, Perlich 2012 ACM TKDD 6(4):15 (leakage; motivates leak-free protocol)",
        "Cordts, Sassmannshausen, Rendel, Klein, Reddemann, Berge 2024 Chem. Mater. (Purformance, Zenodo 13742098)",
    ],
    "license": "CC-BY-4.0 (dataset)",
    "toolkit": {"name": "scipy+numpy+pandas+openpyxl",
                "python_version": "%d.%d.%d" % sys.version_info[:3],
                "sklearn_version": sklearn.__version__, "scipy_version": scipy.__version__,
                "numpy_version": np.__version__, "pandas_version": pd.__version__,
                "openpyxl_version": openpyxl.__version__},
}

canon = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
out = sys.argv[1] if len(sys.argv) > 1 else "cluster_calibration.canonical.json"
open(out, "wb").write(canon)
print("canonical_sha256", hashlib.sha256(canon).hexdigest())
print("C_obs", C_obs, "reproduces_parent", reproduces_parent_point_estimate)
print("protocol_a_fpr_lower", fpr_a, "refutes", protocol_a_refutes)
print("protocol_b_fpr_lower", fpr_b, "refutes", protocol_b_refutes)
print("claim_refuted", claim_refuted)
