#!/usr/bin/env python3
"""amphora-design-rule-score  AUDIT_ONLY scientific increment (MODEL-VALIDITY axis).

PROSPECTIVE (forward-chained) transfer benchmark for the receipted Guth-Gold
design-rule baseline on the Purformance HTE 2K-PUR scratch-hardness DoE
(Zenodo 13742098, CC-BY-4.0). The three DoE iterations are SEQUENTIAL
Bayesian-optimization rounds (Cordts et al. 2024): iteration i+1's design
region is chosen by an optimizer conditioned on iterations <= i. Every
existing receipt for this module evaluates leave-one-iteration-out (LOIO),
whose iteration-2 fold trains on {1,3} -- i.e. it conditions on FUTURE data
that would not exist at decision time. The module's stated decision unit is
"which within-study directional hypotheses deserve the NEXT experiment",
which is a prospective task.

Falsifiable H0 (optimism): pooled LOIO evaluation is NOT optimistic relative
to forward-chained evaluation on the identical prospective test points
(iterations 2 and 3, n=69); i.e. the paired Delta-R2 (LOIO minus forward)
bootstrap CI includes 0. Fold structure note (stated for honesty): the
train{1,2}->test{3} fold is IDENTICAL under both schemes, so any optimism is
driven entirely by the iteration-2 fold (train{1,3} vs train{1} only).

Falsifiable H0 (form under shift): under the BO-induced covariate shift, the
mechanistic Guth-Gold law does NOT differ prospectively from the strictly
more flexible 4-feature linear model (paired Delta-R2 CI includes 0).

Covariate shift is quantified, not assumed: per-feature standardized mean
difference (Cohen's d, pooled-SD denominator) between train and test for
each forward fold, plus the fraction of test formulations OUTSIDE the convex
hull of the training design (exact LP membership test, scipy linprog/HiGHS,
deterministic) -- hull exit = true extrapolation (Sheridan 2013 time-split
applicability domain).

Theory / method references:
  * Bergmeir & Benitez 2012 Inf. Sci. 191:192-213,
    doi:10.1016/j.ins.2011.12.028 (forward-chaining / out-of-sample order)
  * Sheridan 2013 J. Chem. Inf. Model. 53(4):783-790, doi:10.1021/ci400084k
    (time-split validation is the honest estimate for prospective QSAR use)
  * Shimodaira 2000 J. Stat. Plann. Inference 90(2):227-244,
    doi:10.1016/S0378-3758(00)00115-4 (covariate shift)
  * Cohen 1988 Statistical Power Analysis 2nd ed. (standardized mean diff.)
  * Guth & Gold 1938 Phys. Rev. 53:322; Guth 1945 J. Appl. Phys. 16:20-25
  * Efron & Tibshirani 1993 An Introduction to the Bootstrap
  * Cordts et al. 2024 Chem. Mater. (Purformance dataset, Zenodo 13742098)

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
SEED = 0
B = 10000

def load():
    z = zipfile.ZipFile(ZIP)
    X, y, it = [], [], []
    for i in (1, 2, 3):
        df = pd.read_excel(io.BytesIO(z.read(f"Experiment/iteration_{i}_doe_actual.xlsx")))
        X.append(df[FEATS].to_numpy(float)); y.append(df["Kratzhärte"].to_numpy(float)); it += [i] * len(df)
    zbytes = open(ZIP, "rb").read()
    return np.vstack(X), np.concatenate(y), np.array(it), hashlib.sha256(zbytes).hexdigest()

X, y, it, zip_sha = load()
V, H, M, P = X[:, 0], X[:, 1], X[:, 2], X[:, 3]

# fold schemes over the SAME prospective test region (iterations 2 and 3)
FOLDS_FORWARD = [((1,), 2), ((1, 2), 3)]
FOLDS_LOIO23 = [((1, 3), 2), ((1, 2), 3)]

def p_const(tr, te, yy): return np.full(te.sum(), yy[tr].mean())
def p_lin4(tr, te, yy):
    return LinearRegression().fit(X[tr], yy[tr]).predict(X[te])

def R_gg(phi):
    return 1 + 2.5 * phi + 14.1 * phi * phi

def p_gg(tr, te, yy):
    """Guth-Gold reinforced network, identical structure/bounds/init to the
    parent physical-baseline and alt-law receipts."""
    Vt, Ht, Mt, Pt, yt = V[tr], H[tr], M[tr], P[tr], yy[tr]
    def resid(th):
        H0, a, b, cm, cp = th
        phi = cm * Mt + cp * Pt
        return H0 * (1 + a * Vt + b * Ht) * R_gg(phi) - yt
    sol = least_squares(resid, [yt.mean(), 0.1, 0.1, 0.05, 0.05],
                        bounds=([0, -2, -2, 0, 0], [np.inf, 5, 5, 0.3, 0.3]),
                        max_nfev=20000)
    H0, a, b, cm, cp = sol.x
    phi = cm * M[te] + cp * P[te]
    return H0 * (1 + a * V[te] + b * H[te]) * R_gg(phi)

MODELS = {"B0_constant_mean": p_const, "B2_linear_all_4_features": p_lin4,
          "P1_guth_gold_1938": p_gg}

TEST23 = (it == 2) | (it == 3)
y23 = y[TEST23]
it23 = it[TEST23]

def run_scheme(folds, predfun, target=None):
    yy = y if target is None else target
    pred = np.zeros(TEST23.sum())
    for trs, tei in folds:
        tr = np.isin(it, trs); te = it == tei
        pred[it23 == tei] = predfun(tr, te, yy)
    return pred

def metr(pred, yy):
    return dict(r2=float(r2_score(yy, pred)), rmse=float(mean_squared_error(yy, pred) ** 0.5),
                mae=float(mean_absolute_error(yy, pred)))

fwd = {k: run_scheme(FOLDS_FORWARD, f) for k, f in MODELS.items()}
loi = {k: run_scheme(FOLDS_LOIO23, f) for k, f in MODELS.items()}

def per_fold(preds):
    return {f"iteration_{i}": metr(preds[it23 == i], y23[it23 == i]) for i in (2, 3)}

forward_results = {k: dict(pooled=metr(p, y23), **per_fold(p)) for k, p in fwd.items()}
loio23_results = {k: dict(pooled=metr(p, y23), **per_fold(p)) for k, p in loi.items()}

# ---- covariate-shift quantification per forward fold ----
def smd(a, b):
    """Cohen's d with pooled SD (ddof=1)."""
    na, nb = len(a), len(b)
    sp = np.sqrt(((na - 1) * a.var(ddof=1) + (nb - 1) * b.var(ddof=1)) / (na + nb - 2))
    return float((b.mean() - a.mean()) / sp) if sp > 0 else 0.0

def in_hull(Xtr, x):
    """Exact convex-hull membership via LP feasibility (deterministic HiGHS)."""
    n = len(Xtr)
    A_eq = np.vstack([Xtr.T, np.ones(n)])
    b_eq = np.concatenate([x, [1.0]])
    res = linprog(np.zeros(n), A_eq=A_eq, b_eq=b_eq, bounds=[(0, None)] * n,
                  method="highs")
    return bool(res.status == 0)

covariate_shift = {}
for trs, tei in FOLDS_FORWARD:
    tr = np.isin(it, trs); te = it == tei
    smds = {f: smd(X[tr][:, j], X[te][:, j]) for j, f in enumerate(FEATS)}
    outside = [not in_hull(X[tr], xrow) for xrow in X[te]]
    covariate_shift[f"train_{'_'.join(map(str, trs))}__test_{tei}"] = dict(
        n_train=int(tr.sum()), n_test=int(te.sum()),
        standardized_mean_difference_cohens_d=smds,
        max_abs_smd=float(max(abs(v) for v in smds.values())),
        n_test_outside_train_convex_hull=int(sum(outside)),
        fraction_test_outside_train_convex_hull=float(sum(outside) / te.sum()))

# ---- paired percentile bootstrap, stratified by iteration ----
rng = np.random.default_rng(SEED)
blocks = [np.where(it23 == i)[0] for i in (2, 3)]
idx = np.hstack([blk[rng.integers(0, len(blk), size=(B, len(blk)))] for blk in blocks])

def boot_r2(pred):
    yb = y23[idx]; pb = pred[idx]
    ybar = yb.mean(axis=1, keepdims=True)
    return 1.0 - ((yb - pb) ** 2).sum(axis=1) / ((yb - ybar) ** 2).sum(axis=1)

def ci(v):
    lo, hi = np.percentile(v, [2.5, 97.5]); return [float(lo), float(hi)]

forward_r2_ci = {k: ci(boot_r2(p)) for k, p in fwd.items()}

def delta(pa, pb, point):
    d = boot_r2(pa) - boot_r2(pb)
    lo, hi = np.percentile(d, [2.5, 97.5])
    return dict(point=float(point), ci95=[float(lo), float(hi)],
                excludes_zero=bool(lo > 0 or hi < 0))

optimism = {k: delta(loi[k], fwd[k],
                     loio23_results[k]["pooled"]["r2"] - forward_results[k]["pooled"]["r2"])
            for k in MODELS}
gg_vs_lin_forward = delta(
    fwd["P1_guth_gold_1938"], fwd["B2_linear_all_4_features"],
    forward_results["P1_guth_gold_1938"]["pooled"]["r2"]
    - forward_results["B2_linear_all_4_features"]["pooled"]["r2"])

# ---- hostile-null falsifiability: global label shuffle, forward Guth-Gold ----
rng2 = np.random.default_rng(SEED)
y_shuf = y.copy(); rng2.shuffle(y_shuf)
gg_null = run_scheme(FOLDS_FORWARD, p_gg, target=y_shuf)
null = dict(model="P1_guth_gold_1938",
            r2_on_shuffled_labels=float(r2_score(y_shuf[TEST23], gg_null)),
            r2_on_real_labels=float(forward_results["P1_guth_gold_1938"]["pooled"]["r2"]))
null["signal_collapses_under_shuffle"] = bool(null["r2_on_shuffled_labels"] < 0.10)

gg_opt = optimism["P1_guth_gold_1938"]
interp = (
    "Forward-chained (prospective) evaluation of the receipted Guth-Gold design-rule "
    "baseline on the Purformance HTE 2K-PUR sequential-BO DoE, on the identical "
    "prospective test region (iterations 2+3, n=%d) as a paired LOIO evaluation. "
    "Covariate shift between BO rounds is real: max |Cohen's d| per forward fold is "
    "%.3f (train 1 -> test 2) and %.3f (train 1+2 -> test 3), and %.0f%% / %.0f%% of "
    "prospective test formulations fall OUTSIDE the training convex hull, i.e. true "
    "extrapolation. Prospective pooled R2: Guth-Gold %.4f (LOIO-restricted %.4f), "
    "linear-4 %.4f, constant %.4f. The paired LOIO-minus-forward optimism Delta-R2 for "
    "Guth-Gold is %.4f with 95%% CI [%.4f, %.4f], which %s zero -- LOIO %s materially "
    "optimistic for this module's prospective decision task (any optimism is driven "
    "entirely by the iteration-2 fold, since the iteration-3 fold coincides under both "
    "schemes). Prospectively, Guth-Gold minus linear-4 Delta-R2 = %.4f, CI [%.4f, %.4f] "
    "(%s zero): the mechanistic law %s the flexible linear form under BO-induced "
    "extrapolation. The hostile-null label shuffle collapses forward Guth-Gold R2 to "
    "%.4f (<0.10 gate %s), confirming the prospective signal is not an artifact of the "
    "evaluation plumbing."
) % (
    len(y23),
    covariate_shift["train_1__test_2"]["max_abs_smd"],
    covariate_shift["train_1_2__test_3"]["max_abs_smd"],
    100 * covariate_shift["train_1__test_2"]["fraction_test_outside_train_convex_hull"],
    100 * covariate_shift["train_1_2__test_3"]["fraction_test_outside_train_convex_hull"],
    forward_results["P1_guth_gold_1938"]["pooled"]["r2"],
    loio23_results["P1_guth_gold_1938"]["pooled"]["r2"],
    forward_results["B2_linear_all_4_features"]["pooled"]["r2"],
    forward_results["B0_constant_mean"]["pooled"]["r2"],
    gg_opt["point"], gg_opt["ci95"][0], gg_opt["ci95"][1],
    "EXCLUDES" if gg_opt["excludes_zero"] else "INCLUDES",
    "IS" if (gg_opt["excludes_zero"] and gg_opt["point"] > 0) else "is NOT demonstrably",
    gg_vs_lin_forward["point"], gg_vs_lin_forward["ci95"][0], gg_vs_lin_forward["ci95"][1],
    "EXCLUDES" if gg_vs_lin_forward["excludes_zero"] else "INCLUDES",
    ("significantly beats" if gg_vs_lin_forward["point"] > 0 else "is significantly beaten by")
    if gg_vs_lin_forward["excludes_zero"] else "is statistically indistinguishable from",
    null["r2_on_shuffled_labels"],
    "PASS" if null["signal_collapses_under_shuffle"] else "FAIL",
)

body = {
    "schema": "amphora.design-rule-score.purformance-scratch-hardness-prospective-transfer-receipt.v1",
    "module": "amphora-design-rule-score",
    "authority": "AUDIT_ONLY",
    "promotes_authority": False,
    "closes_gate": None,
    "modifies_existing_receipts": False,
    "target": "Kratzhärte",
    "target_unit": "N (Erichsen 435 nano-scratch)",
    "features": FEATS,
    "n_formulations_total": int(len(y)),
    "n_prospective_test": int(len(y23)),
    "split_forward": "forward-chained: train{1}->test{2} (n=17->27), train{1,2}->test{3} (n=44->42); Bergmeir-Benitez 2012 / Sheridan 2013 time-split",
    "split_loio_restricted": "LOIO folds restricted to the same test region: train{1,3}->test{2}, train{1,2}->test{3}",
    "fold_coincidence_note": ("The train{1,2}->test{3} fold is identical under both schemes; "
                              "the paired optimism contrast is therefore driven entirely by the "
                              "iteration-2 fold (train{1,3} vs train{1}). Stated for honesty; "
                              "the pairing is exact and the bootstrap is over identical test points."),
    "input_zip_sha256": zip_sha,
    "input_zip_matches_locked_dataset_fixture": bool(
        zip_sha == "b6e89fe900b1aaf73beb882eeb07dfaf702e0818c9f443de6e84aaa8e32b0036"),
    "parent_receipt_notes": (
        "Extends benchmarks/guth-gold-physical-baseline-v1 (pooled LOIO R2=0.3345), "
        "benchmarks/directional-concordance-v1 and benchmarks/alt-reinforcement-law-v1, all of "
        "which evaluate LOIO only. The iteration-2 LOIO fold conditions on future iteration-3 "
        "data that would not exist at decision time; no prior receipt evaluates the prospective "
        "(deployment-order) setting the mission's decision unit actually requires."),
    "sequential_design_provenance": (
        "Iterations are sequential Bayesian-optimization rounds (Cordts et al. 2024): each "
        "round's design region is proposed by an optimizer conditioned on all earlier rounds, "
        "inducing covariate shift between train and prospective test."),
    "covariate_shift": covariate_shift,
    "shared_model_structure": "H = H0*(1 + a*Vernetzung + b*HDI_IPDI)*R_GG(phi); phi = cm*Mattierungsmittel + cp*Pigmentpaste; R_GG = 1 + 2.5*phi + 14.1*phi^2; least_squares TRF, bounded, identical init/bounds to parent receipts; deterministic.",
    "forward_results": forward_results,
    "loio_restricted_results": loio23_results,
    "forward_r2_bootstrap_ci95": forward_r2_ci,
    "loio_minus_forward_optimism_delta_r2": optimism,
    "guth_gold_minus_linear4_forward_delta_r2": gg_vs_lin_forward,
    "hostile_null_falsifiability": null,
    "bootstrap": {"method": "Efron-Tibshirani 1993 paired percentile bootstrap, stratified by DoE iteration",
                  "resamples": B, "rng": "np.random.default_rng(0)", "interval": "95% percentile"},
    "convex_hull_membership_test": "exact LP feasibility (lambda>=0, sum lambda=1, X_train^T lambda = x_test), scipy.optimize.linprog method=highs, deterministic",
    "honest_interpretation": interp,
    "claim_scope": ("Prospective-transfer validity attestation for the Guth-Gold scratch-hardness "
                    "design-rule baseline on Purformance HTE 2K-PUR lacquer only, normalized "
                    "feature domain [0,1]^4, 3 sequential BO iterations. Quantifies but does not "
                    "correct covariate shift. Grants no batch-release, qualification, optimizer, "
                    "or product-performance authority. Intervals are marginal not conditional. "
                    "Phase-1 would require independent wet-lab validation on a NEW prospective "
                    "iteration and a cross-formulator dataset."),
    "theory_references": [
        "Bergmeir & Benitez 2012 Inf. Sci. 191:192-213 doi:10.1016/j.ins.2011.12.028 (forward-chained evaluation)",
        "Sheridan 2013 J. Chem. Inf. Model. 53(4):783-790 doi:10.1021/ci400084k (time-split is the honest prospective estimate)",
        "Shimodaira 2000 J. Stat. Plann. Inference 90(2):227-244 doi:10.1016/S0378-3758(00)00115-4 (covariate shift)",
        "Cohen 1988 Statistical Power Analysis for the Behavioral Sciences 2nd ed. ISBN 0-8058-0283-5 (standardized mean difference)",
        "Guth & Gold 1938 Phys. Rev. 53:322; Guth 1945 J. Appl. Phys. 16:20-25 (filler reinforcement law)",
        "Efron & Tibshirani 1993 An Introduction to the Bootstrap ISBN 0-412-04231-2 (percentile CI)",
        "Cordts, Sassmannshausen, Rendel, Klein, Reddemann, Berge 2024 Chem. Mater. (Purformance dataset, Zenodo 13742098, CC-BY-4.0)",
        "Erichsen 435 nano-scratch method",
    ],
    "license": "CC-BY-4.0 (dataset)",
    "toolkit": {"name": "scikit-learn+scipy+openpyxl", "python_version": "%d.%d.%d" % sys.version_info[:3],
                "sklearn_version": sklearn.__version__, "scipy_version": scipy.__version__,
                "numpy_version": np.__version__, "openpyxl_version": openpyxl.__version__},
}

canon = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
out = sys.argv[1] if len(sys.argv) > 1 else "prospective_transfer.canonical.json"
open(out, "wb").write(canon)
print("canonical_sha256", hashlib.sha256(canon).hexdigest())
print("forward R2  GG %.6f  lin4 %.6f  const %.6f" % (
    forward_results["P1_guth_gold_1938"]["pooled"]["r2"],
    forward_results["B2_linear_all_4_features"]["pooled"]["r2"],
    forward_results["B0_constant_mean"]["pooled"]["r2"]))
print("LOIO23  R2  GG %.6f  lin4 %.6f" % (
    loio23_results["P1_guth_gold_1938"]["pooled"]["r2"],
    loio23_results["B2_linear_all_4_features"]["pooled"]["r2"]))
print("optimism GG", optimism["P1_guth_gold_1938"])
print("GG-lin4 fwd", gg_vs_lin_forward)
print("shift", {k: (v["max_abs_smd"], v["fraction_test_outside_train_convex_hull"]) for k, v in covariate_shift.items()})
print("hostile_null", null)
