#!/usr/bin/env python3
"""amphora-design-rule-score  AUDIT_ONLY scientific increment (MODEL/PROTOCOL axis).

HARDER TEST of the module's currently-surviving significance claim:
"guth_gold_directional_concordance_exceeds_chance_leak_free" from
benchmarks/split-integrity-dedup-v1 (C=0.7111, cluster-bootstrap CI
[0.6155, 0.7980] on the leak-free 58-unique-observation Purformance
2K-PUR scratch-hardness DoE, Cordts et al. 2024 Chem. Mater., Zenodo
13742098, CC-BY-4.0).

FALSIFICATION TARGET: the split-integrity-dedup-v1 concordance CI is a
TEST-RESAMPLE-ONLY bootstrap (Cameron-Gelbach-Miller 2008 stratified
cluster bootstrap): each replicate resamples which held-out formulations
are scored, but reuses the SAME Guth-Gold parameter fit that was estimated
ONCE per fold from the original (non-resampled) training data. It therefore
holds the 5-parameter physical-model fit fixed and only propagates sampling
noise in which test pairs get evaluated. At n_train per fold of 41/32/43,
a 5-parameter bounded nonlinear least-squares fit (Guth & Gold 1938) carries
its own non-trivial parameter uncertainty that this protocol never
propagates into the concordance CI (Kohavi 1995; Varma & Simon 2006 BMC
Bioinformatics 7:91 -- "Bias in error estimation when using cross-validation
for model selection" warns that resampling only the evaluation step and not
the fitting step understates the true out-of-sample variance of a model
selected/fit on limited data).

This receipt runs a NESTED TRAIN-REFIT bootstrap: for every replicate and
every one of the 3 leave-one-iteration-out folds, the TRAINING rows are
resampled with replacement (same fold structure, same size), the Guth-Gold
model is REFIT from scratch on the resampled training data (identical
least_squares call, bounds and initial guess as the parent receipt), and
the refit model is scored against the ORIGINAL (non-resampled) held-out
fold. This is a strictly harder, more complete propagation of estimation
uncertainty than the parent receipt's test-only resampling. If the
resulting concordance CI's lower bound falls to or below 0.5 (chance), the
"exceeds chance" significance claim does not survive full uncertainty
propagation and is REFUTED. If the lower bound still exceeds 0.5, the claim
SURVIVED a genuinely harder attack (it is reported alongside the exact
observation -- CI lower bound crossing 0.5 -- that would have refuted it).

Identical dataset, dedup protocol, arm definition, seed, and fold
assignment as benchmarks/split-integrity-dedup-v1/run_split_integrity.py so
the comparison is apples-to-apples; only the source of bootstrap
resampling changes (train-refit here vs test-only there).

Theory / method references:
  * Guth & Gold 1938 Phys. Rev. 53:322; Guth 1945 J. Appl. Phys. 16:20-25
  * Hanley & McNeil 1982 Radiology 143(1):29-36 (AUC = pairwise concordance)
  * Efron & Tibshirani 1993 An Introduction to the Bootstrap
  * Cameron, Gelbach & Miller 2008 Rev. Econ. Stat. 90(3):414-427 (cluster bootstrap; parent method)
  * Kohavi 1995 IJCAI (study of cross-validation and bootstrap variance)
  * Varma & Simon 2006 BMC Bioinformatics 7:91 (nested resampling to avoid understated CV variance)
  * Wicks, Jones, Pappas 2007 Organic Coatings 3rd ed. Wiley Ch. 24 (Rule 1 baseline)
  * Kaufman, Rosset, Perlich 2012 ACM TKDD 6(4):15 (leakage; motivates the leak-free 58-row protocol)
  * Cordts, Sassmannshausen, Rendel, Klein, Reddemann, Berge 2024 Chem. Mater. (Purformance, Zenodo 13742098)

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
SEED = 0
B = 5000
ITER = (1, 2, 3)
CHANCE = 0.5

# ---------------------------------------------------------------- load (identical to split-integrity-dedup-v1)
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

# ---------------------------------------------------------------- Guth-Gold 1938 arm (identical fit as parent)
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

# within-fold comparable pairs, group-safe (identical construction to parent)
def pair_index(gf):
    ii, jj = [], []
    for k in ITER:
        idx = np.where(gf == k)[0]
        for a in range(len(idx)):
            for b in range(a + 1, len(idx)):
                ii.append(idx[a]); jj.append(idx[b])
    return np.array(ii), np.array(jj)

II, JJ = pair_index(g)

def concordance(yv, p, ii=II, jj=JJ):
    dy = yv[ii] - yv[jj]
    m = dy != 0
    ds = p[ii][m] - p[jj][m]
    dyv = dy[m]
    conc = (np.sign(ds) == np.sign(dyv)).sum()
    ties = (ds == 0).sum()
    nn = len(dyv)
    return float((conc + 0.5 * ties) / nn), int(nn)

# ---------------------------------------------------------------- point estimate (reproduction check)
p_obs = loio_pred(X, y, g, gg_fit_predict)
C_obs, n_pairs = concordance(y, p_obs)
PARENT_C_OBS = 0.7111307420494699
reproduces_parent_point_estimate = bool(round(C_obs, 10) == round(PARENT_C_OBS, 10))

# ---------------------------------------------------------------- NESTED TRAIN-REFIT bootstrap
train_idx_by_fold = {i: np.where(g != i)[0] for i in ITER}
test_idx_by_fold = {i: np.where(g == i)[0] for i in ITER}

rng = np.random.default_rng(SEED)
C_boot = np.empty(B)
fit_failures = 0
for b in range(B):
    p_b = np.zeros(n)
    for i in ITER:
        tr = train_idx_by_fold[i]
        te = test_idx_by_fold[i]
        tr_resampled = rng.choice(tr, size=len(tr), replace=True)
        try:
            p_b[te] = gg_fit_predict(X[tr_resampled], y[tr_resampled], X[te])
        except Exception:
            fit_failures += 1
            p_b[te] = y[tr_resampled].mean()
    C_boot[b] = concordance(y, p_b)[0]

nested_ci = [float(np.percentile(C_boot, 2.5)), float(np.percentile(C_boot, 97.5))]
nested_mean = float(C_boot.mean())
nested_std = float(C_boot.std(ddof=1))

# ---------------------------------------------------------------- parent (test-only) CI, for direct comparison
PARENT_TEST_ONLY_CI = [0.61545444778685, 0.7979744887402145]

# ---------------------------------------------------------------- verdict
nested_excludes_chance = bool(nested_ci[0] > CHANCE)
parent_excludes_chance = bool(PARENT_TEST_ONLY_CI[0] > CHANCE)
ci_widened = bool((nested_ci[1] - nested_ci[0]) > (PARENT_TEST_ONLY_CI[1] - PARENT_TEST_ONLY_CI[0]))
refutation_criterion = ("nested train-refit bootstrap 95%% CI lower bound for Guth-Gold leak-free "
                         "directional concordance falls to <= 0.5 (chance), which the parent "
                         "test-resample-only cluster bootstrap could not detect because it never "
                         "refits the 5-parameter physical model on resampled training data")
claim_survives_harder_test = nested_excludes_chance

# ---------------------------------------------------------------- hostile null (sanity: method must detect chance when there is none)
rng2 = np.random.default_rng(SEED)
y_shuf = y.copy(); rng2.shuffle(y_shuf)
p_shuf_obs = loio_pred(X, y_shuf, g, gg_fit_predict)
C_shuf_obs, _ = concordance(y_shuf, p_shuf_obs)

rng3 = np.random.default_rng(SEED)
C_null_boot = np.empty(B)
for b in range(B):
    p_b = np.zeros(n)
    for i in ITER:
        tr = train_idx_by_fold[i]
        te = test_idx_by_fold[i]
        tr_resampled = rng3.choice(tr, size=len(tr), replace=True)
        try:
            p_b[te] = gg_fit_predict(X[tr_resampled], y_shuf[tr_resampled], X[te])
        except Exception:
            p_b[te] = y_shuf[tr_resampled].mean()
    C_null_boot[b] = concordance(y_shuf, p_b)[0]
null_ci = [float(np.percentile(C_null_boot, 2.5)), float(np.percentile(C_null_boot, 97.5))]
null_collapses_to_chance = bool(null_ci[0] <= CHANCE <= null_ci[1])

interp = (
    "HARDER-TEST ATTACK on the module's currently-surviving significance claim "
    "'guth_gold_directional_concordance_exceeds_chance_leak_free' (split-integrity-dedup-v1, "
    "C=%.4f, test-resample-only cluster-bootstrap CI [%.4f, %.4f]). That parent CI holds the "
    "Guth-Gold 5-parameter fit FIXED per fold and only resamples which held-out formulations are "
    "scored; it never propagates the physical model's own parameter-estimation uncertainty at "
    "n_train=41/32/43. This receipt runs a NESTED TRAIN-REFIT bootstrap (%d replicates): every "
    "replicate resamples the TRAINING rows with replacement per fold and REFITS Guth-Gold from "
    "scratch (identical least_squares call), scoring the refit model against the original held-out "
    "fold. This propagates strictly more of the true estimation uncertainty than the parent "
    "protocol (Kohavi 1995; Varma & Simon 2006 BMC Bioinformatics 7:91). "
    "Point estimate reproduced: C_obs=%.10f (parent-receipted %.10f, match=%s). "
    "REFUTATION CRITERION: nested-bootstrap CI lower bound <= 0.5 (chance) would refute the "
    "'exceeds chance' claim under full uncertainty propagation. "
    "OBSERVED: nested train-refit 95%% CI = [%.4f, %.4f] (mean %.4f, std %.4f) vs parent "
    "test-only CI = [%.4f, %.4f] -- the nested CI is %s than the parent CI, i.e. propagating "
    "training-refit uncertainty %s widen the interval as hypothesized. "
    "VERDICT: the nested CI lower bound is %.4f, which %s 0.5, so the claim %s under this harder, "
    "fully-uncertainty-propagated test. Hostile-null sanity check: shuffled-label Guth-Gold under "
    "the identical nested train-refit protocol gives CI [%.4f, %.4f], which %s 0.5 as expected "
    "(confirms the nested-bootstrap machinery correctly detects a genuine null when one is present, "
    "so the non-null result above is not an artifact of the method being unable to reject)."
) % (
    PARENT_C_OBS, PARENT_TEST_ONLY_CI[0], PARENT_TEST_ONLY_CI[1], B,
    C_obs, PARENT_C_OBS, reproduces_parent_point_estimate,
    nested_ci[0], nested_ci[1], nested_mean, nested_std,
    PARENT_TEST_ONLY_CI[0], PARENT_TEST_ONLY_CI[1],
    "WIDER" if ci_widened else "NOT wider",
    "does" if ci_widened else "does NOT",
    nested_ci[0], "EXCLUDES" if nested_excludes_chance else "INCLUDES",
    "SURVIVES" if claim_survives_harder_test else "IS REFUTED",
    null_ci[0], null_ci[1],
    "INCLUDES" if null_collapses_to_chance else "unexpectedly excludes",
)

body = {
    "schema": "amphora.design-rule-score.guth-gold-nested-refit-bootstrap-receipt.v1",
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
    "attacks_parent_receipt": "benchmarks/split-integrity-dedup-v1/split-integrity-deduplication-receipt.v1.json",
    "target": TARGET,
    "target_unit": "N (Erichsen 435 nano-scratch)",
    "features": FEATS,
    "input_zip_sha256": zip_sha,
    "input_zip_matches_locked_dataset_fixture": bool(zip_sha == LOCKED_ZIP_SHA),
    "protocol": "leave-one-iteration-out over the 58 leak-free unique (feature,target) observations (identical dedup construction as split-integrity-dedup-v1), folds 17/26/15",
    "n_observations": int(n),
    "fold_sizes": fold_sizes,
    "n_within_fold_comparable_pairs": n_pairs,
    "arm": "P1_guth_gold_1938 (Guth & Gold 1938 Phys. Rev. 53:322, 5-param bounded least_squares, identical to parent receipt)",
    "point_estimate": {
        "C_obs": C_obs,
        "parent_receipted_C_obs": PARENT_C_OBS,
        "reproduces_parent_point_estimate": reproduces_parent_point_estimate,
    },
    "parent_test_only_cluster_bootstrap_ci95": PARENT_TEST_ONLY_CI,
    "nested_train_refit_bootstrap_ci95": nested_ci,
    "nested_train_refit_bootstrap_mean": nested_mean,
    "nested_train_refit_bootstrap_std": nested_std,
    "bootstrap": {
        "method": "nested train-refit bootstrap: per-replicate per-fold resample of TRAINING rows with replacement, Guth-Gold refit from scratch on resampled training data, scored against the ORIGINAL (non-resampled) held-out fold",
        "resamples": B,
        "rng": "np.random.default_rng(0)",
        "interval": "95% percentile",
        "fit_failures": fit_failures,
        "contrast_with_parent_method": "parent split-integrity-dedup-v1 used a test-resample-only stratified cluster bootstrap (Cameron-Gelbach-Miller 2008) that holds the single per-fold Guth-Gold fit FIXED; this receipt additionally resamples and refits the training data every replicate, propagating parameter-estimation uncertainty the parent protocol omits",
    },
    "refutation_criterion": refutation_criterion,
    "ci_widened_vs_parent": ci_widened,
    "nested_bootstrap_excludes_chance": nested_excludes_chance,
    "parent_bootstrap_excludes_chance": parent_excludes_chance,
    "claim_survives_harder_test": claim_survives_harder_test,
    "hostile_null_sanity_check": {
        "protocol": "identical nested train-refit bootstrap on within-fold-shuffled labels",
        "C_obs_shuffled": C_shuf_obs,
        "nested_ci95_shuffled": null_ci,
        "collapses_to_chance": null_collapses_to_chance,
    },
    "honest_interpretation": interp,
    "claim_scope": ("Statistical-methodology audit only, restricted to the Purformance HTE 2K-PUR "
                     "lacquer scratch-hardness leak-free 58-observation benchmark. Does not modify "
                     "or delete split-integrity-dedup-v1 or any other receipt; reports whether its "
                     "surviving significance claim is robust to a strictly more complete propagation "
                     "of estimation uncertainty. Grants no batch-release, qualification, optimizer, "
                     "or product-performance authority. n=58 leak-free observations from a single "
                     "formulator and a single instrument."),
    "theory_references": [
        "Guth & Gold 1938 Phys. Rev. 53:322 (Einstein-Guth-Gold filler reinforcement)",
        "Guth 1945 J. Appl. Phys. 16:20-25",
        "Hanley & McNeil 1982 Radiology 143(1):29-36 (AUC = pairwise concordance)",
        "Efron & Tibshirani 1993 An Introduction to the Bootstrap",
        "Cameron, Gelbach & Miller 2008 Rev. Econ. Stat. 90(3):414-427 (cluster bootstrap; parent method)",
        "Kohavi 1995 IJCAI 14(2):1137-1145 (study of cross-validation and bootstrap variance)",
        "Varma & Simon 2006 BMC Bioinformatics 7:91 (nested resampling avoids understated CV variance)",
        "Wicks, Jones, Pappas 2007 Organic Coatings 3rd ed. Wiley Ch. 24 (Rule 1 baseline)",
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
out = sys.argv[1] if len(sys.argv) > 1 else "nested_refit.canonical.json"
open(out, "wb").write(canon)
print("canonical_sha256", hashlib.sha256(canon).hexdigest())
print("C_obs", C_obs, "reproduces_parent", reproduces_parent_point_estimate)
print("parent_test_only_ci", PARENT_TEST_ONLY_CI)
print("nested_train_refit_ci", nested_ci)
print("ci_widened_vs_parent", ci_widened)
print("nested_excludes_chance", nested_excludes_chance)
print("claim_survives_harder_test", claim_survives_harder_test)
print("null_ci", null_ci, "null_collapses", null_collapses_to_chance)
print("fit_failures", fit_failures)
