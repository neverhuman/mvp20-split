#!/usr/bin/env python3
"""amphora-design-rule-score  AUDIT_ONLY scientific increment (MODEL-VALIDITY axis).

LEAK-FREE PROSPECTIVE (forward-chained) transfer benchmark for the receipted
Guth-Gold design-rule baseline on the Purformance HTE 2K-PUR scratch-hardness
DoE (Zenodo 13742098, CC-BY-4.0).

MOTIVATION / GAP THIS CLOSES: benchmarks/split-integrity-dedup-v1 (2026-07-30)
proved the three Purformance iteration workbooks are cumulative campaign
snapshots, not disjoint batches -- all 27 of iteration 2's (feature,target)
rows recur VERBATIM inside iteration 3. That receipt corrected the LOIO-based
guth-gold-physical-baseline-v1, directional-concordance-v1 and
alt-reinforcement-law-v1 receipts (evidence/phase0/kpis/...dedup-superseding-
kpi.v1.json, populated 2026-08-01) but explicitly did NOT touch
benchmarks/prospective-transfer-v1 (2026-07-2x), which remains UNCORRECTED
and STILL STANDING. That receipt's forward-chained fold train{1,2}->test{3}
trains on n=44 rows (17 from iteration 1 + 27 from iteration 2) and tests on
iteration 3's 42 rows -- of which 27 are byte-identical duplicates of the
iteration-2 rows already sitting in the training set. 27/42 = 64% of that
fold's "prospective" test set is memorization, not extrapolation. The
receipted headline (forward pooled R2 = 0.1917, hostile-null gate PASS,
honest_interpretation: "confirming the prospective signal is not an
artifact of the evaluation plumbing") is therefore itself built on the same
leak class (Kaufman, Rosset, Perlich 2012 ACM TKDD 6(4):15) that
split-integrity-dedup-v1 found and corrected everywhere else in this module.

Falsifiable H0: the prospective (forward-chained) Guth-Gold R2 reported by
prospective-transfer-v1 does NOT collapse once the 27 duplicate/memorized
test rows are removed and each unique observation is evaluated only the
FIRST time it is prospectively novel (i.e. genuine forward-chaining over the
DEDUP-first-appearance partition established by split-integrity-dedup-v1:
train on iteration-1 unique rows (n=17) -> test on rows NEW to iteration 2
(n=26); train on iteration-{1,2} unique rows (n=43) -> test on rows NEW to
iteration 3 (n=15". Pooled leak-free prospective n=41, down from the
receipted 69.

Byte-stable: all randomness is np.random.default_rng(SEED); least_squares
(TRF, fixed init/bounds) and linprog (HiGHS) are deterministic.
"""
import json, hashlib, sys
import numpy as np
import pandas as pd
import zipfile, io
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from scipy.optimize import least_squares, linprog
import sklearn, scipy, openpyxl

ROOT = "/home/ubuntu/amphora/build/mvp20-split/amphora-design-rule-score"
ZIP = ROOT + "/reference/purformance/zenodo-13742098/Experiment.zip"
FEATS = ["Vernetzung", "HDI-IPDI", "Mattierungsmittel", "Pigmentpaste"]
TARGET = "Kratzhärte"
SEED = 0
B = 10000
LOCKED_ZIP_SHA = "b6e89fe900b1aaf73beb882eeb07dfaf702e0818c9f443de6e84aaa8e32b0036"
ITER = (1, 2, 3)

# ---------------------------------------------------------------- load (identical to split-integrity-dedup-v1 / prospective-transfer-v1)
zf = zipfile.ZipFile(ZIP)
per_iter = {}
for i in ITER:
    df = pd.read_excel(io.BytesIO(zf.read(f"Experiment/iteration_{i}_doe_actual.xlsx")))
    per_iter[i] = [(tuple(np.round(list(r[FEATS]), 9)), float(round(r[TARGET], 9)))
                   for _, r in df.iterrows()]
zip_sha = hashlib.sha256(open(ZIP, "rb").read()).hexdigest()

raw_rows = [(i, f, t) for i in ITER for (f, t) in per_iter[i]]

# ---------------------------------------- DEDUP first-appearance partition (identical protocol to split-integrity-dedup-v1)
seen, dedup_rows = {}, []
for i, f, t in raw_rows:
    if (f, t) in seen:
        continue
    seen[(f, t)] = i
    dedup_rows.append((i, f, t))

def arrays(rows):
    X = np.array([r[1] for r in rows], float)
    y = np.array([r[2] for r in rows], float)
    g = np.array([r[0] for r in rows], int)
    return X, y, g

X_all, y_all, g_all = arrays(dedup_rows)
fold_sizes = {i: int((g_all == i).sum()) for i in ITER}

# ---------------------------------------------------------------- models (identical structure/bounds/init to prospective-transfer-v1 / parent receipts)
def p_const(Xt, yt, Xe): return np.full(len(Xe), yt.mean())
def p_lin4(Xt, yt, Xe): return LinearRegression().fit(Xt, yt).predict(Xe)

def R_gg(phi): return 1 + 2.5 * phi + 14.1 * phi * phi

def p_gg(Xt, yt, Xe):
    Vt, Ht, Mt, Pt = Xt.T
    def resid(th):
        H0, a, b, cm, cp = th
        phi = cm * Mt + cp * Pt
        return H0 * (1 + a * Vt + b * Ht) * R_gg(phi) - yt
    sol = least_squares(resid, [yt.mean(), 0.1, 0.1, 0.05, 0.05],
                        bounds=([0, -2, -2, 0, 0], [np.inf, 5, 5, 0.3, 0.3]),
                        max_nfev=20000)
    H0, a, b, cm, cp = sol.x
    Ve, He, Me, Pe = Xe.T
    phi = cm * Me + cp * Pe
    return H0 * (1 + a * Ve + b * He) * R_gg(phi)

MODELS = {"B0_constant_mean": p_const, "B2_linear_all_4_features": p_lin4,
          "P1_guth_gold_1938": p_gg}

# ---------------------------------------------------------- LEAK-FREE forward chaining over the DEDUP partition
# fold A: train = dedup rows first-seen in iter 1 ; test = dedup rows first-seen in iter 2 (genuinely NEW at round 2)
# fold B: train = dedup rows first-seen in iter {1,2} ; test = dedup rows first-seen in iter 3 (genuinely NEW at round 3)
FOLDS_FORWARD_DEDUP = [((1,), 2), ((1, 2), 3)]

TEST23 = (g_all == 2) | (g_all == 3)
y23 = y_all[TEST23]
it23 = g_all[TEST23]
n_prospective = int(TEST23.sum())

def run_scheme(folds, predfun, target=None):
    yy = y_all if target is None else target
    pred = np.zeros(n_prospective)
    for trs, tei in folds:
        tr = np.isin(g_all, trs); te = g_all == tei
        pred[it23 == tei] = predfun(X_all[tr], yy[tr], X_all[te])
    return pred

fwd = {k: run_scheme(FOLDS_FORWARD_DEDUP, f) for k, f in MODELS.items()}

def metr(pred, yy):
    return dict(r2=float(r2_score(yy, pred)), rmse=float(mean_squared_error(yy, pred) ** 0.5),
                mae=float(mean_absolute_error(yy, pred)))

def per_fold(preds):
    return {f"iteration_{i}": metr(preds[it23 == i], y23[it23 == i]) for i in (2, 3)}

forward_results_dedup = {k: dict(pooled=metr(p, y23), **per_fold(p)) for k, p in fwd.items()}

# --------------------------------------- leakage census: confirm the fix actually removed the leak
def dup_count(train_rows, test_rows):
    tr_full = set((f, t) for _, f, t in train_rows)
    return sum(1 for _, f, t in test_rows if (f, t) in tr_full)

train_A = [r for r in dedup_rows if r[0] == 1]
test_A = [r for r in dedup_rows if r[0] == 2]
train_B = [r for r in dedup_rows if r[0] in (1, 2)]
test_B = [r for r in dedup_rows if r[0] == 3]
raw_train_B = [r for r in raw_rows if r[0] in (1, 2)]
raw_test_B = [r for r in raw_rows if r[0] == 3]

leakage_fix_census = {
    "legacy_fold_B_train44_test42_duplicate_test_rows_in_train": dup_count(raw_train_B, raw_test_B),
    "legacy_fold_B_leak_fraction": round(dup_count(raw_train_B, raw_test_B) / len(raw_test_B), 6),
    "dedup_fold_A_train17_test26_duplicate_test_rows_in_train": dup_count(train_A, test_A),
    "dedup_fold_B_train43_test15_duplicate_test_rows_in_train": dup_count(train_B, test_B),
    "dedup_folds_are_leak_free": bool(dup_count(train_A, test_A) == 0 and dup_count(train_B, test_B) == 0),
}

# ---------------------------------------------- covariate shift on the leak-free folds (Sheridan 2013 hull-exit)
def smd(a, b):
    na, nb = len(a), len(b)
    sp = np.sqrt(((na - 1) * a.var(ddof=1) + (nb - 1) * b.var(ddof=1)) / (na + nb - 2))
    return float((b.mean() - a.mean()) / sp) if sp > 0 else 0.0

def in_hull(Xtr, x):
    n = len(Xtr)
    A_eq = np.vstack([Xtr.T, np.ones(n)])
    b_eq = np.concatenate([x, [1.0]])
    res = linprog(np.zeros(n), A_eq=A_eq, b_eq=b_eq, bounds=[(0, None)] * n, method="highs")
    return bool(res.status == 0)

covariate_shift = {}
for trs, tei in FOLDS_FORWARD_DEDUP:
    tr = np.isin(g_all, trs); te = g_all == tei
    Xtr, Xte = X_all[tr], X_all[te]
    smds = {f: smd(Xtr[:, j], Xte[:, j]) for j, f in enumerate(FEATS)}
    outside = [not in_hull(Xtr, xrow) for xrow in Xte]
    covariate_shift[f"train_{'_'.join(map(str, trs))}__test_{tei}"] = dict(
        n_train=int(tr.sum()), n_test=int(te.sum()),
        standardized_mean_difference_cohens_d=smds,
        max_abs_smd=float(max(abs(v) for v in smds.values())),
        n_test_outside_train_convex_hull=int(sum(outside)),
        fraction_test_outside_train_convex_hull=float(sum(outside) / te.sum()))

# ---------------------------------------------- paired percentile bootstrap, stratified by iteration
rng = np.random.default_rng(SEED)
blocks = [np.where(it23 == i)[0] for i in (2, 3)]
idx = np.hstack([blk[rng.integers(0, len(blk), size=(B, len(blk)))] for blk in blocks])

def boot_r2(pred):
    yb = y23[idx]; pb = pred[idx]
    ybar = yb.mean(axis=1, keepdims=True)
    denom = ((yb - ybar) ** 2).sum(axis=1)
    denom[denom == 0] = np.nan
    return 1.0 - ((yb - pb) ** 2).sum(axis=1) / denom

def ci(v):
    v = v[~np.isnan(v)]
    lo, hi = np.percentile(v, [2.5, 97.5]); return [float(lo), float(hi)]

forward_r2_ci_dedup = {k: ci(boot_r2(p)) for k, p in fwd.items()}

def delta(pa, pb, point):
    d = boot_r2(pa) - boot_r2(pb)
    d = d[~np.isnan(d)]
    lo, hi = np.percentile(d, [2.5, 97.5])
    return dict(point=float(point), ci95=[float(lo), float(hi)],
                excludes_zero=bool(lo > 0 or hi < 0))

gg_vs_const_dedup = delta(fwd["P1_guth_gold_1938"], fwd["B0_constant_mean"],
                           forward_results_dedup["P1_guth_gold_1938"]["pooled"]["r2"]
                           - forward_results_dedup["B0_constant_mean"]["pooled"]["r2"])
gg_vs_lin4_dedup = delta(fwd["P1_guth_gold_1938"], fwd["B2_linear_all_4_features"],
                          forward_results_dedup["P1_guth_gold_1938"]["pooled"]["r2"]
                          - forward_results_dedup["B2_linear_all_4_features"]["pooled"]["r2"])

# ---------------------------------------------- hostile-null falsifiability: global label shuffle
rng2 = np.random.default_rng(SEED)
y_shuf = y_all.copy(); rng2.shuffle(y_shuf)
gg_null = run_scheme(FOLDS_FORWARD_DEDUP, p_gg, target=y_shuf)
null = dict(model="P1_guth_gold_1938",
            r2_on_shuffled_labels=float(r2_score(y_shuf[TEST23], gg_null)),
            r2_on_real_labels=float(forward_results_dedup["P1_guth_gold_1938"]["pooled"]["r2"]))
null["signal_collapses_under_shuffle"] = bool(null["r2_on_shuffled_labels"] < 0.10)

# ---------------------------------------------- comparison vs the still-standing (uncorrected) prospective-transfer-v1 receipted numbers
LEGACY_RECEIPTED = {
    "forward_pooled_r2_guth_gold": 0.1917424925248703,
    "forward_pooled_r2_linear4": 0.22828305818381323,
    "forward_pooled_r2_constant": -0.011374286019813384,
    "n_prospective_test": 69,
    "hostile_null_r2_shuffled": -0.07544796359268724,
}

gg_point_dedup = forward_results_dedup["P1_guth_gold_1938"]["pooled"]["r2"]
gg_point_legacy = LEGACY_RECEIPTED["forward_pooled_r2_guth_gold"]
gg_beats_const_dedup = bool(gg_vs_const_dedup["excludes_zero"] and gg_vs_const_dedup["point"] > 0)
gg_beats_lin4_dedup = bool(gg_vs_lin4_dedup["excludes_zero"] and gg_vs_lin4_dedup["point"] > 0)
prior_headline_reproducible = bool(round(gg_point_dedup, 2) == round(gg_point_legacy, 2))

interp = (
    "LEAK-FREE RE-RUN OF prospective-transfer-v1 (still standing, uncorrected as of this run). "
    "split-integrity-dedup-v1 (2026-07-30) proved the Purformance iteration workbooks are cumulative "
    "snapshots and corrected the module's LOIO-based receipts, but explicitly left "
    "prospective-transfer-v1 untouched. This run shows prospective-transfer-v1's forward-chained "
    "fold train{1,2}->test{3} (n_train=%d, n_test=%d) contains %d/%d (%.0f%%) duplicate test rows "
    "already present verbatim in its own training set -- the identical Kaufman-Rosset-Perlich 2012 "
    "leakage class split-integrity-dedup-v1 found elsewhere. Re-running genuine forward-chaining "
    "over the DEDUP first-appearance partition (train iter-1 unique (n=%d) -> test rows NEW at "
    "iter-2 (n=%d); train iter-{1,2} unique (n=%d) -> test rows NEW at iter-3 (n=%d); verified "
    "leak-free: %d and %d duplicate test rows respectively in the two folds) pools to n=%d "
    "prospective observations, down from the receipted 69. Guth-Gold leak-free forward pooled "
    "R2 = %.4f versus the still-standing receipted value %.4f (delta %.4f) -- the receipted number "
    "IS %s under a leak-free protocol. Guth-Gold minus constant-mean delta-R2 = %.4f, CI [%.4f, "
    "%.4f] (%s zero): Guth-Gold %s beat the constant baseline prospectively at 95%% once "
    "memorized rows are excluded. Guth-Gold minus linear-4 delta-R2 = %.4f, CI [%.4f, %.4f] (%s "
    "zero). Hostile-null label-shuffle forward R2 = %.4f (<0.10 gate %s). "
    "Binding constraint: pooled prospective n fell from 69 (leaky) to 41 (leak-free), consistent "
    "with split-integrity-dedup-v1's finding that this module's binding constraint is sample size, "
    "not model form. Grants no batch-release, qualification, optimizer, or product-performance "
    "authority."
) % (
    len(raw_train_B), len(raw_test_B),
    leakage_fix_census["legacy_fold_B_train44_test42_duplicate_test_rows_in_train"], len(raw_test_B),
    100 * leakage_fix_census["legacy_fold_B_leak_fraction"],
    fold_sizes[1], len(test_A),
    len(train_B), len(test_B),
    leakage_fix_census["dedup_fold_A_train17_test26_duplicate_test_rows_in_train"],
    leakage_fix_census["dedup_fold_B_train43_test15_duplicate_test_rows_in_train"],
    n_prospective,
    gg_point_dedup, gg_point_legacy, gg_point_dedup - gg_point_legacy,
    "REPRODUCIBLE (within 0.02)" if prior_headline_reproducible else "NOT REPRODUCIBLE leak-free",
    gg_vs_const_dedup["point"], gg_vs_const_dedup["ci95"][0], gg_vs_const_dedup["ci95"][1],
    "EXCLUDES" if gg_vs_const_dedup["excludes_zero"] else "INCLUDES",
    "DOES" if gg_beats_const_dedup else "does NOT",
    gg_vs_lin4_dedup["point"], gg_vs_lin4_dedup["ci95"][0], gg_vs_lin4_dedup["ci95"][1],
    "EXCLUDES" if gg_vs_lin4_dedup["excludes_zero"] else "INCLUDES",
    null["r2_on_shuffled_labels"], "PASS" if null["signal_collapses_under_shuffle"] else "FAIL",
)

body = {
    "schema": "amphora.design-rule-score.purformance-scratch-hardness-prospective-transfer-dedup-receipt.v1",
    "module": "amphora-design-rule-score",
    "authority": "AUDIT_ONLY",
    "promotes_authority": False,
    "closes_gate": None,
    "modifies_existing_receipts": False,
    "corrects_magnitudes_of_prior_receipts": [
        "benchmarks/prospective-transfer-v1/prospective_transfer.canonical.json",
    ],
    "target": TARGET,
    "target_unit": "N (Erichsen 435 nano-scratch)",
    "features": FEATS,
    "input_zip_sha256": zip_sha,
    "input_zip_matches_locked_dataset_fixture": bool(zip_sha == LOCKED_ZIP_SHA),
    "gap_this_closes": (
        "benchmarks/split-integrity-dedup-v1 corrected guth-gold-physical-baseline-v1, "
        "directional-concordance-v1 and alt-reinforcement-law-v1 for duplicate-row leakage under "
        "LOIO, but did not touch benchmarks/prospective-transfer-v1, whose forward-chained "
        "train{1,2}->test{3} fold independently contains the identical leak (27/42 test rows "
        "duplicated verbatim in train). This receipt closes that gap."),
    "legacy_receipted_values": LEGACY_RECEIPTED,
    "leakage_fix_census": leakage_fix_census,
    "dedup_fold_sizes": {f"iter{k}": v for k, v in fold_sizes.items()},
    "split_forward_dedup": (
        "forward-chained over the DEDUP first-appearance partition (split-integrity-dedup-v1 "
        "protocol): train iter-1 unique (n=17) -> test rows first-appearing at iter-2 (n=26); "
        "train iter-{1,2} unique (n=43) -> test rows first-appearing at iter-3 (n=15). "
        "Bergmeir-Benitez 2012 / Sheridan 2013 time-split, leak-free by construction."),
    "n_prospective_test_dedup": n_prospective,
    "shared_model_structure": "H = H0*(1 + a*Vernetzung + b*HDI_IPDI)*R_GG(phi); phi = cm*Mattierungsmittel + cp*Pigmentpaste; R_GG = 1 + 2.5*phi + 14.1*phi^2; least_squares TRF, bounded, identical init/bounds to parent receipts; deterministic.",
    "forward_results_dedup": forward_results_dedup,
    "forward_r2_bootstrap_ci95_dedup": forward_r2_ci_dedup,
    "guth_gold_minus_constant_forward_delta_r2_dedup": gg_vs_const_dedup,
    "guth_gold_minus_linear4_forward_delta_r2_dedup": gg_vs_lin4_dedup,
    "hostile_null_falsifiability": null,
    "covariate_shift_dedup": covariate_shift,
    "surviving_claims": {
        "prior_headline_forward_r2_0_1917_reproducible_leak_free": prior_headline_reproducible,
        "guth_gold_beats_constant_mean_forward_leak_free_at_95pct": gg_beats_const_dedup,
        "guth_gold_beats_linear4_forward_leak_free_at_95pct": gg_beats_lin4_dedup,
        "hostile_null_gate_passed": bool(null["signal_collapses_under_shuffle"]),
    },
    "bootstrap": {"method": "Efron-Tibshirani 1993 paired percentile bootstrap, stratified by DoE iteration",
                  "resamples": B, "rng": "np.random.default_rng(0)", "interval": "95% percentile"},
    "convex_hull_membership_test": "exact LP feasibility (lambda>=0, sum lambda=1, X_train^T lambda = x_test), scipy.optimize.linprog method=highs, deterministic",
    "honest_interpretation": interp,
    "claim_scope": ("Leak-free prospective-transfer validity re-attestation for the Guth-Gold "
                    "scratch-hardness design-rule baseline on Purformance HTE 2K-PUR lacquer only, "
                    "normalized feature domain [0,1]^4, 3 sequential BO iterations. Supersedes the "
                    "MAGNITUDES (not the qualitative conclusions) of prospective-transfer-v1. Grants "
                    "no batch-release, qualification, optimizer, or product-performance authority. "
                    "Intervals are marginal not conditional. n=41 leak-free prospective observations "
                    "from a single formulator and a single instrument; Phase-1 would require a "
                    "cross-formulator dataset and independent wet-lab validation."),
    "theory_references": [
        "Bergmeir & Benitez 2012 Inf. Sci. 191:192-213 doi:10.1016/j.ins.2011.12.028 (forward-chained evaluation)",
        "Sheridan 2013 J. Chem. Inf. Model. 53(4):783-790 doi:10.1021/ci400084k (time-split is the honest prospective estimate)",
        "Shimodaira 2000 J. Stat. Plann. Inference 90(2):227-244 doi:10.1016/S0378-3758(00)00115-4 (covariate shift)",
        "Kaufman, Rosset, Perlich 2012 ACM TKDD 6(4):15 (leakage in data mining)",
        "Guth & Gold 1938 Phys. Rev. 53:322; Guth 1945 J. Appl. Phys. 16:20-25 (filler reinforcement law)",
        "Efron & Tibshirani 1993 An Introduction to the Bootstrap ISBN 0-412-04231-2 (percentile CI)",
        "Cordts, Sassmannshausen, Rendel, Klein, Reddemann, Berge 2024 Chem. Mater. (Purformance dataset, Zenodo 13742098, CC-BY-4.0)",
        "Erichsen 435 nano-scratch method",
    ],
    "license": "CC-BY-4.0 (dataset)",
    "toolkit": {"name": "scikit-learn+scipy+openpyxl", "python_version": "%d.%d.%d" % sys.version_info[:3],
                "sklearn_version": sklearn.__version__, "scipy_version": scipy.__version__,
                "numpy_version": np.__version__, "pandas_version": pd.__version__,
                "openpyxl_version": openpyxl.__version__},
}

canon = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
out = sys.argv[1] if len(sys.argv) > 1 else "prospective_transfer_dedup.canonical.json"
open(out, "wb").write(canon)
print("canonical_sha256", hashlib.sha256(canon).hexdigest())
print("leakage_fix_census", json.dumps(leakage_fix_census))
print("forward R2 dedup  GG %.6f  lin4 %.6f  const %.6f" % (
    forward_results_dedup["P1_guth_gold_1938"]["pooled"]["r2"],
    forward_results_dedup["B2_linear_all_4_features"]["pooled"]["r2"],
    forward_results_dedup["B0_constant_mean"]["pooled"]["r2"]))
print("legacy leaky R2   GG %.6f" % LEGACY_RECEIPTED["forward_pooled_r2_guth_gold"])
print("gg_vs_const", gg_vs_const_dedup)
print("gg_vs_lin4", gg_vs_lin4_dedup)
print("null", null)
print("surviving", json.dumps(body["surviving_claims"]))
