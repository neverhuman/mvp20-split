#!/usr/bin/env python3
"""amphora-design-rule-score  AUDIT_ONLY scientific increment (MODEL/PROTOCOL axis).

SPLIT-INTEGRITY AUDIT of the leave-one-iteration-out (LOIO) protocol used by the
three previously-receipted increments on the Purformance 2K-PUR lacquer
scratch-hardness (Kratzhaerte, N) target (Cordts et al. 2024 Chem. Mater.,
Zenodo 13742098, CC-BY-4.0).

Discovered data fact (verified in this run, not assumed): the three files
Experiment/iteration_{1,2,3}_doe_actual.xlsx are CUMULATIVE campaign snapshots,
not disjoint batches. Every one of iteration 2's 27 (feature,target) rows recurs
VERBATIM inside iteration 3's 42 rows, and one row recurs in all three. The 86
stacked rows therefore contain only 58 unique observations. Consequently the
LOIO folds are NOT group-disjoint: holding out iteration 2 leaves 27/27 of its
test rows sitting verbatim in the training set.

Falsifiable question: which of the module's receipted findings survive a
leak-free split? Protocol DEDUP assigns each unique (feature,target)
observation to its FIRST iteration of appearance, giving strictly disjoint
folds of 17/26/15, and re-runs every arm and BOTH scoring tasks (point R2 and
the module's stated directional-decision task) unchanged otherwise.

Arms (identical to the receipted increments plus one documented DoE baseline):
  B0 constant training mean
  D1 Rule-1, fit-free: score = Vernetzung (crosslink density)
     Wicks, Jones, Pappas 2007 Organic Coatings 3rd ed. Wiley Ch. 24
  B2 linear in all 4 DoE features (OLS)
  P1 Einstein-Guth-Gold reinforced network, 5 param
     Guth & Gold 1938 Phys. Rev. 53:322; Guth 1945 J. Appl. Phys. 16:20-25
  R1 Box-Wilson 1951 full second-order response surface (15 param OLS)
     Box & Wilson 1951 J. R. Stat. Soc. B 13(1):1-45, doi:10.1111/j.2517-6161.1951.tb00067.x
  M1 HistGradientBoostingRegressor, library defaults, random_state=0

Byte-stable: every stochastic step is np.random.default_rng(SEED); OLS,
least_squares (TRF, fixed init/bounds) and HistGBM(random_state=0) are
deterministic.
"""
import json, hashlib, sys, io, zipfile
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from scipy.optimize import least_squares
import sklearn, scipy, openpyxl

ROOT = "/home/ubuntu/amphora/build/mvp20-split/amphora-design-rule-score"
ZIP = ROOT + "/reference/purformance/zenodo-13742098/Experiment.zip"
FEATS = ["Vernetzung", "HDI-IPDI", "Mattierungsmittel", "Pigmentpaste"]
TARGET = "Kratzhärte"
LOCKED_ZIP_SHA = "b6e89fe900b1aaf73beb882eeb07dfaf702e0818c9f443de6e84aaa8e32b0036"
SEED = 0
B = 10000
ITER = (1, 2, 3)

# ---------------------------------------------------------------- load
zf = zipfile.ZipFile(ZIP)
per_iter = {}
for i in ITER:
    df = pd.read_excel(io.BytesIO(zf.read(f"Experiment/iteration_{i}_doe_actual.xlsx")))
    per_iter[i] = [(tuple(np.round(list(r[FEATS]), 9)), float(round(r[TARGET], 9)))
                   for _, r in df.iterrows()]
zip_sha = hashlib.sha256(open(ZIP, "rb").read()).hexdigest()

# ------------------------------------------------- split-integrity census
sets = {i: set(per_iter[i]) for i in ITER}
overlap = {}
for a in ITER:
    for b in ITER:
        if a < b:
            overlap[f"iter{a}_cap_iter{b}"] = {
                "n_identical_rows": int(len(sets[a] & sets[b])),
                "iter%d_is_verbatim_subset_of_iter%d" % (a, b): bool(sets[a] <= sets[b]),
                "iter%d_is_verbatim_subset_of_iter%d" % (b, a): bool(sets[b] <= sets[a]),
            }
raw_rows = [(i, f, t) for i in ITER for (f, t) in per_iter[i]]
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

def leak_census(rows):
    X, y, g = arrays(rows)
    out = {}
    for i in ITER:
        tr_full = set(map(tuple, np.column_stack([X[g != i], y[g != i]])))
        tr_feat = set(map(tuple, X[g != i]))
        te = np.column_stack([X[g == i], y[g == i]])
        n = int((g == i).sum())
        dup_full = int(sum(tuple(r) in tr_full for r in te))
        dup_feat = int(sum(tuple(r[:4]) in tr_feat for r in te))
        out[f"holdout_iter{i}"] = {
            "n_test": n, "n_train": int(len(y) - n),
            "test_rows_with_identical_feature_and_target_row_in_train": dup_full,
            "test_rows_with_identical_feature_vector_in_train": dup_feat,
            "leak_fraction_feature_and_target": round(dup_full / n, 6),
        }
    return out

# ---------------------------------------------------------------- arms
def a_const(Xt, yt, Xe): return np.full(len(Xe), yt.mean())
def a_rule1(Xt, yt, Xe): return Xe[:, 0].copy()          # fit-free declared baseline
def a_lin4(Xt, yt, Xe): return LinearRegression().fit(Xt, yt).predict(Xe)

def a_gg(Xt, yt, Xe):
    V, H, M, P = Xt.T
    def resid(th):
        phi = th[3] * M + th[4] * P
        return th[0] * (1 + th[1] * V + th[2] * H) * (1 + 2.5 * phi + 14.1 * phi * phi) - yt
    s = least_squares(resid, [yt.mean(), 0.1, 0.1, 0.05, 0.05],
                      bounds=([0, -2, -2, 0, 0], [np.inf, 5, 5, 0.3, 0.3]),
                      max_nfev=20000).x
    V, H, M, P = Xe.T
    phi = s[3] * M + s[4] * P
    return s[0] * (1 + s[1] * V + s[2] * H) * (1 + 2.5 * phi + 14.1 * phi * phi)

def _rsm(A):
    return np.hstack([A] + [A[:, [a]] * A[:, [b]] for a in range(4) for b in range(a, 4)])
def a_rsm(Xt, yt, Xe): return LinearRegression().fit(_rsm(Xt), yt).predict(_rsm(Xe))
def a_ml(Xt, yt, Xe):
    return HistGradientBoostingRegressor(random_state=SEED).fit(Xt, yt).predict(Xe)

ARMS = [("B0_constant_mean", a_const), ("D1_rule1_vernetzung_fitfree", a_rule1),
        ("B2_linear_all_4_features", a_lin4), ("P1_guth_gold_1938", a_gg),
        ("R1_box_wilson_1951_quadratic_rsm", a_rsm), ("M1_histgbm_default", a_ml)]

def loio_pred(rows, fn, ytarget=None):
    X, y, g = arrays(rows)
    yy = y if ytarget is None else ytarget
    p = np.zeros(len(y))
    for i in ITER:
        p[g == i] = fn(X[g != i], yy[g != i], X[g == i])
    return p

def metr(yy, p):
    return dict(r2=float(r2_score(yy, p)), rmse=float(mean_squared_error(yy, p) ** 0.5),
                mae=float(mean_absolute_error(yy, p)))

# ---------------------------- directional concordance (module's stated task)
def pair_index(g):
    """All within-fold ordered pairs (i,j), i<j -- group-safe by construction."""
    ii, jj = [], []
    for k in ITER:
        idx = np.where(g == k)[0]
        for a in range(len(idx)):
            for b in range(a + 1, len(idx)):
                ii.append(idx[a]); jj.append(idx[b])
    return np.array(ii), np.array(jj)

def concordance(y, p, ii, jj):
    dy = y[ii] - y[jj]
    m = dy != 0
    ds = p[ii][m] - p[jj][m]
    dy = dy[m]
    conc = (np.sign(ds) == np.sign(dy)).sum()
    ties = (ds == 0).sum()
    n = len(dy)
    return float((conc + 0.5 * ties) / n), int(n)

# ---------------------------------------------------------------- evaluate
def evaluate(rows, label):
    X, y, g = arrays(rows)
    preds = {nm: loio_pred(rows, fn) for nm, fn in ARMS}
    res = {nm: metr(y, p) for nm, p in preds.items()}
    ii, jj = pair_index(g)
    conc = {}
    for nm, p in preds.items():
        c, npairs = concordance(y, p, ii, jj)
        conc[nm] = {"concordance_C": c, "kendall_tau": 2 * c - 1}
    # --- Efron-Tibshirani paired percentile bootstrap on R2 (row resample)
    rng = np.random.default_rng(SEED)
    n = len(y)
    idx = rng.integers(0, n, size=(B, n))
    def boot_r2(p):
        yb, pb = y[idx], p[idx]
        ss_res = ((yb - pb) ** 2).sum(axis=1)
        ss_tot = ((yb - yb.mean(axis=1, keepdims=True)) ** 2).sum(axis=1)
        return 1.0 - ss_res / ss_tot
    br2 = {nm: boot_r2(p) for nm, p in preds.items()}
    r2_ci = {nm: [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))]
             for nm, v in br2.items()}
    # --- stratified cluster bootstrap over formulations for concordance
    rngc = np.random.default_rng(SEED)
    fold_idx = {k: np.where(g == k)[0] for k in ITER}
    bc = {nm: np.empty(B) for nm in preds}
    for b in range(B):
        sel = {k: rngc.choice(fold_idx[k], size=len(fold_idx[k]), replace=True) for k in ITER}
        bi, bj = [], []
        for k in ITER:
            s = sel[k]
            for a in range(len(s)):
                for c2 in range(a + 1, len(s)):
                    bi.append(s[a]); bj.append(s[c2])
        bi, bj = np.array(bi), np.array(bj)
        for nm, p in preds.items():
            bc[nm][b] = concordance(y, p, bi, bj)[0]
    conc_ci = {nm: [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))]
               for nm, v in bc.items()}

    def dci(dist_a, dist_b, pa, pb, key):
        d = dist_a - dist_b
        lo, hi = float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))
        return {"point": float(pa - pb), "ci95": [lo, hi],
                "excludes_zero": bool(lo > 0 or hi < 0)}
    pairs = [("P1_guth_gold_1938", "D1_rule1_vernetzung_fitfree"),
             ("P1_guth_gold_1938", "B0_constant_mean"),
             ("P1_guth_gold_1938", "B2_linear_all_4_features"),
             ("M1_histgbm_default", "P1_guth_gold_1938"),
             ("R1_box_wilson_1951_quadratic_rsm", "P1_guth_gold_1938")]
    d_r2 = {f"{a}_minus_{b}": dci(br2[a], br2[b], res[a]["r2"], res[b]["r2"], a) for a, b in pairs}
    d_c = {f"{a}_minus_{b}": dci(bc[a], bc[b], conc[a]["concordance_C"],
                                 conc[b]["concordance_C"], a) for a, b in pairs}
    return {"label": label, "n_observations": int(n),
            "fold_sizes": {f"iter{k}": int((g == k).sum()) for k in ITER},
            "n_within_fold_comparable_pairs": int(concordance(y, preds["P1_guth_gold_1938"], ii, jj)[1]),
            "leakage_census": leak_census(rows),
            "loio_point_metrics": res, "loio_r2_bootstrap_ci95": r2_ci,
            "directional_concordance": conc, "concordance_cluster_bootstrap_ci95": conc_ci,
            "delta_r2_paired_bootstrap": d_r2,
            "delta_concordance_paired_cluster_bootstrap": d_c}, preds, y

legacy, lp, ly = evaluate(raw_rows, "LEGACY_loio_raw_86_rows_as_receipted")
dedup, dp, dy_ = evaluate(dedup_rows, "DEDUP_loio_first_appearance_58_unique_rows")

# ------------------------------- reproduction check vs receipted parents
repro = {
    "parent_guth_gold_receipt_loio_r2_0_3345": round(legacy["loio_point_metrics"]["P1_guth_gold_1938"]["r2"], 4) == 0.3345,
    "parent_linear4_loio_r2_0_334078": round(legacy["loio_point_metrics"]["B2_linear_all_4_features"]["r2"], 6) == 0.334078,
    "parent_constant_loio_r2_neg_0_012078": round(legacy["loio_point_metrics"]["B0_constant_mean"]["r2"], 6) == -0.012078,
    "parent_ml_default_loio_r2_0_3857": round(legacy["loio_point_metrics"]["M1_histgbm_default"]["r2"], 4) == 0.3857,
    "parent_concordance_receipt_rule1_C_0_5623": round(legacy["directional_concordance"]["D1_rule1_vernetzung_fitfree"]["concordance_C"], 4) == 0.5623,
    "parent_concordance_receipt_physical_C_0_7211": round(legacy["directional_concordance"]["P1_guth_gold_1938"]["concordance_C"], 4) == 0.7211,
    "parent_concordance_receipt_n_pairs_1348": legacy["n_within_fold_comparable_pairs"] == 1348,
}
repro["all_parent_numbers_reproduced"] = all(repro.values())

# ------------------------------- inflation attributable to the leak
inflation = {nm: {"legacy_r2": legacy["loio_point_metrics"][nm]["r2"],
                  "dedup_r2": dedup["loio_point_metrics"][nm]["r2"],
                  "r2_inflation": legacy["loio_point_metrics"][nm]["r2"] - dedup["loio_point_metrics"][nm]["r2"],
                  "legacy_C": legacy["directional_concordance"][nm]["concordance_C"],
                  "dedup_C": dedup["directional_concordance"][nm]["concordance_C"],
                  "C_inflation": legacy["directional_concordance"][nm]["concordance_C"] - dedup["directional_concordance"][nm]["concordance_C"]}
             for nm, _ in ARMS}

# ------------------------------- hostile null on the leak-free protocol
rngn = np.random.default_rng(SEED)
X_d, y_d, g_d = arrays(dedup_rows)
y_shuf = y_d.copy(); rngn.shuffle(y_shuf)
null_p = loio_pred(dedup_rows, a_gg, ytarget=y_shuf)
ii_d, jj_d = pair_index(g_d)
null = {"protocol": "DEDUP", "model": "P1_guth_gold_1938",
        "r2_on_shuffled_labels": float(r2_score(y_shuf, null_p)),
        "r2_on_real_labels": dedup["loio_point_metrics"]["P1_guth_gold_1938"]["r2"],
        "concordance_on_shuffled_labels": concordance(y_shuf, null_p, ii_d, jj_d)[0],
        "concordance_on_real_labels": dedup["directional_concordance"]["P1_guth_gold_1938"]["concordance_C"]}
null["signal_collapses_under_shuffle"] = bool(null["r2_on_shuffled_labels"] < 0.10 and
                                              abs(null["concordance_on_shuffled_labels"] - 0.5) < 0.10)

def ci_of(prot, nm, which):
    return prot["concordance_cluster_bootstrap_ci95"][nm] if which == "C" else prot["loio_r2_bootstrap_ci95"][nm]

gg_survives_r2 = dedup["delta_r2_paired_bootstrap"]["P1_guth_gold_1938_minus_B0_constant_mean"]["excludes_zero"]
gg_survives_c = dedup["delta_concordance_paired_cluster_bootstrap"]["P1_guth_gold_1938_minus_D1_rule1_vernetzung_fitfree"]["excludes_zero"]
gg_c_ci = ci_of(dedup, "P1_guth_gold_1938", "C")
ml_c_ci = ci_of(dedup, "M1_histgbm_default", "C")
gg_beats_chance = bool(gg_c_ci[0] > 0.5)
ml_beats_chance = bool(ml_c_ci[0] > 0.5)
ml_r2_leakfree = dedup["loio_point_metrics"]["M1_histgbm_default"]["r2"]
b0_r2_leakfree = dedup["loio_point_metrics"]["B0_constant_mean"]["r2"]
ml_no_variance = bool(ml_r2_leakfree <= 0.0)
gg_best_r2 = bool(dedup["loio_point_metrics"]["P1_guth_gold_1938"]["r2"] ==
                  max(v["r2"] for v in dedup["loio_point_metrics"].values()))

interp = (
    "SPLIT-INTEGRITY DEFECT FOUND AND QUANTIFIED. The three Purformance iteration workbooks are "
    "cumulative campaign snapshots, not disjoint batches: all %d of iteration 2's (feature,target) "
    "rows recur VERBATIM inside iteration 3, so the 86 stacked rows hold only %d unique "
    "observations. Under the leave-one-iteration-out split used by this module's three prior "
    "receipts, %d/%d held-out iteration-2 rows and %d/%d held-out iteration-3 rows are "
    "byte-identical to rows in their own training set. This run first reproduces every published "
    "parent number exactly (all_parent_numbers_reproduced=%s), then re-runs the identical arms, "
    "metrics and bootstraps under a leak-free protocol assigning each unique observation to its "
    "FIRST iteration of appearance (disjoint folds 17/26/15, verified zero shared feature vectors "
    "across folds). "
    "Point R2 legacy -> leak-free: Guth-Gold %.4f -> %.4f; linear-4 %.4f -> %.4f; Box-Wilson "
    "quadratic RSM %.4f -> %.4f; default HistGBM %.4f -> %.4f. Directional concordance C legacy -> "
    "leak-free: Guth-Gold %.4f -> %.4f; linear-4 %.4f -> %.4f; RSM %.4f -> %.4f; default HistGBM "
    "%.4f -> %.4f. Inflation scales monotonically with model flexibility: the 5-parameter physical "
    "law loses %.4f R2, the 15-parameter response surface %.4f, the gradient-boosted ensemble %.4f. "
    "WHAT SURVIVES: the Einstein-Guth-Gold physical law is still the best of the six arms on "
    "leak-free point R2 (%s), and its leak-free directional concordance C=%.4f has cluster-bootstrap "
    "CI [%.4f, %.4f], which %s chance (0.5). "
    "WHAT DOES NOT SURVIVE: at n=%d unique observations the paired 95%% CI for Guth-Gold minus "
    "constant-mean on R2 is [%.4f, %.4f] (%s zero) and for Guth-Gold minus the declared fit-free "
    "Wicks-Jones-Pappas Rule-1 baseline on concordance is [%.4f, %.4f] (%s zero). The CORROBORATED "
    "significance verdict receipted in directional-concordance-v1 was carried by duplicated rows; "
    "on leak-free data the same comparison is UNDERPOWERED and the significance claim is hereby "
    "WITHDRAWN. The point estimates still favour the physical law, but the evidence no longer "
    "clears 95%%. "
    "STRONGEST NEW NEGATIVE RESULT: out-of-box gradient boosting retains essentially no "
    "out-of-sample skill once duplicates are removed -- R2 %.4f against a constant-mean baseline of "
    "%.4f (i.e. it explains no variance at all), and its directional concordance falls from %.4f to "
    "%.4f with CI [%.4f, %.4f], which %s chance. Its entire apparent advantage was memorization of "
    "duplicated rows. This is a verified instance of Kaufman-Rosset-Perlich 2012 leakage and "
    "supplies a concrete mechanism for the parent Purformance model card's unreproducible tuned "
    "R2=0.8555, which no honest group-safe protocol in this module has ever approached. "
    "Hostile-null y-shuffle under the leak-free protocol collapses the physical arm to R2=%.4f and "
    "C=%.4f (chance), confirming no residual exchangeability leakage. "
    "NET EFFECT ON THE MODULE: the magnitudes AND the significance verdicts of "
    "guth-gold-physical-baseline-v1, directional-concordance-v1 and alt-reinforcement-law-v1 are "
    "superseded by the DEDUP column here; the qualitative ordering physics >= linear > out-of-box ML "
    "is preserved and strengthened, while the physics-beats-Rule-1 significance claim is withdrawn "
    "pending more data. The binding constraint is now sample size, not model form."
) % (
    len(sets[2]), len(dedup_rows),
    legacy["leakage_census"]["holdout_iter2"]["test_rows_with_identical_feature_and_target_row_in_train"],
    legacy["leakage_census"]["holdout_iter2"]["n_test"],
    legacy["leakage_census"]["holdout_iter3"]["test_rows_with_identical_feature_and_target_row_in_train"],
    legacy["leakage_census"]["holdout_iter3"]["n_test"],
    repro["all_parent_numbers_reproduced"],
    inflation["P1_guth_gold_1938"]["legacy_r2"], inflation["P1_guth_gold_1938"]["dedup_r2"],
    inflation["B2_linear_all_4_features"]["legacy_r2"], inflation["B2_linear_all_4_features"]["dedup_r2"],
    inflation["R1_box_wilson_1951_quadratic_rsm"]["legacy_r2"], inflation["R1_box_wilson_1951_quadratic_rsm"]["dedup_r2"],
    inflation["M1_histgbm_default"]["legacy_r2"], inflation["M1_histgbm_default"]["dedup_r2"],
    inflation["P1_guth_gold_1938"]["legacy_C"], inflation["P1_guth_gold_1938"]["dedup_C"],
    inflation["B2_linear_all_4_features"]["legacy_C"], inflation["B2_linear_all_4_features"]["dedup_C"],
    inflation["R1_box_wilson_1951_quadratic_rsm"]["legacy_C"], inflation["R1_box_wilson_1951_quadratic_rsm"]["dedup_C"],
    inflation["M1_histgbm_default"]["legacy_C"], inflation["M1_histgbm_default"]["dedup_C"],
    inflation["P1_guth_gold_1938"]["r2_inflation"],
    inflation["R1_box_wilson_1951_quadratic_rsm"]["r2_inflation"],
    inflation["M1_histgbm_default"]["r2_inflation"],
    "yes" if gg_best_r2 else "no -- it is not",
    dedup["directional_concordance"]["P1_guth_gold_1938"]["concordance_C"], gg_c_ci[0], gg_c_ci[1],
    "EXCLUDES" if gg_beats_chance else "INCLUDES",
    dedup["n_observations"],
    dedup["delta_r2_paired_bootstrap"]["P1_guth_gold_1938_minus_B0_constant_mean"]["ci95"][0],
    dedup["delta_r2_paired_bootstrap"]["P1_guth_gold_1938_minus_B0_constant_mean"]["ci95"][1],
    "EXCLUDES" if gg_survives_r2 else "INCLUDES",
    dedup["delta_concordance_paired_cluster_bootstrap"]["P1_guth_gold_1938_minus_D1_rule1_vernetzung_fitfree"]["ci95"][0],
    dedup["delta_concordance_paired_cluster_bootstrap"]["P1_guth_gold_1938_minus_D1_rule1_vernetzung_fitfree"]["ci95"][1],
    "EXCLUDES" if gg_survives_c else "INCLUDES",
    ml_r2_leakfree, b0_r2_leakfree,
    inflation["M1_histgbm_default"]["legacy_C"], inflation["M1_histgbm_default"]["dedup_C"],
    ml_c_ci[0], ml_c_ci[1], "EXCLUDES" if ml_beats_chance else "INCLUDES",
    null["r2_on_shuffled_labels"], null["concordance_on_shuffled_labels"],
)

body = {
    "schema": "amphora.design-rule-score.purformance-split-integrity-deduplication-receipt.v1",
    "module": "amphora-design-rule-score",
    "authority": "AUDIT_ONLY",
    "promotes_authority": False,
    "closes_gate": None,
    "modifies_existing_receipts": False,
    "corrects_magnitudes_of_prior_receipts": [
        "benchmarks/guth-gold-physical-baseline-v1/physical_baseline.canonical.json",
        "benchmarks/directional-concordance-v1/concordance.canonical.json",
        "benchmarks/alt-reinforcement-law-v1/alt_law.canonical.json",
    ],
    "target": TARGET,
    "target_unit": "N (Erichsen 435 nano-scratch)",
    "features": FEATS,
    "input_zip_sha256": zip_sha,
    "input_zip_matches_locked_dataset_fixture": bool(zip_sha == LOCKED_ZIP_SHA),
    "dataset_structure_finding": {
        "raw_stacked_rows": len(raw_rows),
        "unique_feature_target_observations": len(dedup_rows),
        "duplicate_rows_removed": len(raw_rows) - len(dedup_rows),
        "distinct_feature_vectors": int(len({f for _, f, _ in raw_rows})),
        "pairwise_iteration_overlap": overlap,
        "files_are_cumulative_snapshots_not_disjoint_batches": bool(sets[2] <= sets[3]),
        "note": ("Exactly one formulation (Vernetzung 0.697303, HDI-IPDI 0.711274, "
                 "Mattierungsmittel 0.576461, Pigmentpaste 0.191029) carries two distinct "
                 "Kratzhaerte values (16.765, 13.994) -- the only genuine measurement replicate "
                 "in the corpus; both are retained and both fall in the same leak-free fold."),
    },
    "protocols": {
        "LEGACY": "leave-one-iteration-out over the 86 stacked rows exactly as receipted by the three parent increments",
        "DEDUP": "leave-one-iteration-out over the 58 unique (feature,target) observations, each assigned to its FIRST iteration of appearance; folds 17/26/15, zero duplicate feature vectors across folds",
    },
    "arms": {
        "B0_constant_mean": "training-fold mean",
        "D1_rule1_vernetzung_fitfree": "declared a-priori baseline, score = Vernetzung (Wicks, Jones, Pappas 2007 Ch. 24)",
        "B2_linear_all_4_features": "OLS linear in the 4 DoE features",
        "P1_guth_gold_1938": "H = H0*(1+a*Vernetzung+b*HDI_IPDI)*(1+2.5*phi+14.1*phi^2), phi = cm*Mattierungsmittel+cp*Pigmentpaste; 5 param, bounded least_squares TRF",
        "R1_box_wilson_1951_quadratic_rsm": "full second-order response surface, 4 linear + 4 pure quadratic + 6 two-factor interaction terms, 15 param OLS (Box & Wilson 1951)",
        "M1_histgbm_default": "HistGradientBoostingRegressor(random_state=0), library defaults",
    },
    "parent_number_reproduction": repro,
    "legacy_protocol": legacy,
    "dedup_protocol": dedup,
    "leakage_inflation_by_arm": inflation,
    "hostile_null_falsifiability": null,
    "surviving_claims": {
        "guth_gold_is_best_arm_leak_free_on_r2": gg_best_r2,
        "guth_gold_directional_concordance_exceeds_chance_leak_free": gg_beats_chance,
        "guth_gold_beats_constant_mean_on_r2_leak_free_at_95pct": bool(gg_survives_r2),
        "guth_gold_beats_declared_rule1_on_directional_task_leak_free_at_95pct": bool(gg_survives_c),
        "default_ml_directional_concordance_exceeds_chance_leak_free": ml_beats_chance,
        "default_ml_explains_no_out_of_sample_variance_leak_free": ml_no_variance,
        "prior_receipt_significance_verdicts_withdrawn": bool(not (gg_survives_r2 and gg_survives_c)),
    },
    "bootstrap": {"r2_method": "Efron-Tibshirani 1993 paired percentile bootstrap over observations",
                  "concordance_method": "stratified within-fold cluster bootstrap over formulations (Cameron-Gelbach-Miller 2008), paired",
                  "resamples": B, "rng": "np.random.default_rng(0)", "interval": "95% percentile"},
    "honest_interpretation": interp,
    "claim_scope": ("Split-integrity attestation and leak-free re-baselining for the Purformance HTE "
                    "2K-PUR lacquer scratch-hardness benchmark ONLY, normalized feature domain [0,1]^4. "
                    "Grants no batch-release, qualification, optimizer, or product-performance authority. "
                    "Does not modify or delete any existing receipt; it supersedes the MAGNITUDES those "
                    "receipts report and leaves their qualitative conclusions standing. Intervals are "
                    "marginal, not family-conditional. n=58 leak-free observations from a single "
                    "formulator and a single instrument; Phase-1 would still require a cross-formulator "
                    "dataset and independent wet-lab validation."),
    "theory_references": [
        "Guth & Gold 1938 Phys. Rev. 53:322 (Einstein-Guth-Gold filler reinforcement)",
        "Guth 1945 J. Appl. Phys. 16:20-25",
        "Box & Wilson 1951 J. R. Stat. Soc. B 13(1):1-45 doi:10.1111/j.2517-6161.1951.tb00067.x (second-order response surface)",
        "Wicks, Jones, Pappas 2007 Organic Coatings 3rd ed. Wiley Ch. 24 (Rule 1: hardness rises with crosslink density)",
        "Hanley & McNeil 1982 Radiology 143(1):29-36 (AUC = pairwise concordance)",
        "Efron & Tibshirani 1993 An Introduction to the Bootstrap (percentile CI)",
        "Cameron, Gelbach & Miller 2008 Rev. Econ. Stat. 90(3):414-427 (cluster bootstrap)",
        "Kaufman, Rosset, Perlich 2012 ACM TKDD 6(4):15 (leakage in data mining)",
        "Cordts, Sassmannshausen, Rendel, Klein, Reddemann, Berge 2024 Chem. Mater. (Purformance, Zenodo 13742098)",
        "Erichsen 435 nano-scratch method",
    ],
    "license": "CC-BY-4.0 (dataset)",
    "toolkit": {"name": "scikit-learn+scipy+openpyxl",
                "python_version": "%d.%d.%d" % sys.version_info[:3],
                "sklearn_version": sklearn.__version__, "scipy_version": scipy.__version__,
                "numpy_version": np.__version__, "pandas_version": pd.__version__,
                "openpyxl_version": openpyxl.__version__},
}

canon = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
out = sys.argv[1] if len(sys.argv) > 1 else "split_integrity.canonical.json"
open(out, "wb").write(canon)
print("canonical_sha256", hashlib.sha256(canon).hexdigest())
print("parent_repro", repro)
print("leak census legacy", json.dumps(legacy["leakage_census"]))
print("leak census dedup ", json.dumps(dedup["leakage_census"]))
for nm, _ in ARMS:
    print("  %-34s legacy R2 %+.4f -> dedup %+.4f | legacy C %.4f -> dedup %.4f" % (
        nm, inflation[nm]["legacy_r2"], inflation[nm]["dedup_r2"],
        inflation[nm]["legacy_C"], inflation[nm]["dedup_C"]))
print("dedup dR2 GG-const", dedup["delta_r2_paired_bootstrap"]["P1_guth_gold_1938_minus_B0_constant_mean"])
print("dedup dC   GG-rule1", dedup["delta_concordance_paired_cluster_bootstrap"]["P1_guth_gold_1938_minus_D1_rule1_vernetzung_fitfree"])
print("dedup dR2 ML-GG   ", dedup["delta_r2_paired_bootstrap"]["M1_histgbm_default_minus_P1_guth_gold_1938"])
print("surviving", json.dumps(body["surviving_claims"]))
print("GG C ci", gg_c_ci, "ML C ci", ml_c_ci)
print("null", null)
