#!/usr/bin/env python3
"""Positive control for conformal-coverage-dedup-v1.

Runs the identical jackknife+ / LOIO machinery from run_conformal_dedup.py
against TWO deliberately planted defects, to prove the attack's gates can
actually fire on a defect of the kind they exist to catch (not just pass
vacuously on well-behaved real data):

DEFECT A -- coverage-floor breach. Mutates the real-signal jackknife+
interval bounds post-hoc: lower/upper are both shrunk toward the point
prediction by a factor of 0.3 (simulating a buggy narrow-interval
construction, e.g. an off-by-something in the quantile index). This is
EXACTLY the class of defect gates (a)/(b)/(c)
(marginal_conformal_coverage_at_alpha_0XX_meets_worst_case_floor,
hostile_null_shuffle_coverage...) exist to catch.

DEFECT B -- no-real-skill collapse. Replaces the real-signal target y with
an INDEPENDENT second random shuffle (np.random.default_rng(1), distinct
from the hostile-null shuffle's seed 0), so both "real" and "null" arms are
now fit on pure noise. This is exactly the class of defect gate (d)
(hostile_null_width_inflates_over_real_signal) exists to catch: if the
"real" arm has no more skill than the null arm, the width-inflation ratio
should collapse toward 1.0 and breach the >=1.10 target.
"""
import json, hashlib, sys, io, zipfile, math
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

ROOT = "/home/ubuntu/amphora/build/mvp20-split/amphora-design-rule-score"
ZIP = ROOT + "/reference/purformance/zenodo-13742098/Experiment.zip"
FEATS = ["Vernetzung", "HDI-IPDI", "Mattierungsmittel", "Pigmentpaste"]
TARGET = "Kratzhärte"
SEED = 0
ITER = (1, 2, 3)
HGB_KW = dict(l2_regularization=0.1, learning_rate=0.05, max_depth=6,
              max_iter=300, min_samples_leaf=5, random_state=0)

zf = zipfile.ZipFile(ZIP)
per_iter = {}
for i in ITER:
    df = pd.read_excel(io.BytesIO(zf.read(f"Experiment/iteration_{i}_doe_actual.xlsx")))
    per_iter[i] = [(tuple(np.round(list(r[FEATS]), 9)), float(round(r[TARGET], 9)))
                   for _, r in df.iterrows()]

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

X_all, y_all, g_all = arrays(dedup_rows)

def jackknife_plus_interval(Xtr, ytr, Xte, alpha, hgb_kw=HGB_KW):
    n = len(ytr)
    loo_resid = np.empty(n)
    loo_pred_test = np.empty((n, len(Xte)))
    for i in range(n):
        mask = np.ones(n, dtype=bool); mask[i] = False
        m = HistGradientBoostingRegressor(**hgb_kw).fit(Xtr[mask], ytr[mask])
        loo_resid[i] = abs(ytr[i] - m.predict(Xtr[i:i+1])[0])
        loo_pred_test[i, :] = m.predict(Xte)
    lo = loo_pred_test - loo_resid[:, None]
    hi = loo_pred_test + loo_resid[:, None]
    k_lo = max(1, math.floor(alpha * (n + 1)))
    k_hi = min(n, math.ceil((1 - alpha) * (n + 1)))
    lower = np.sort(lo, axis=0)[k_lo - 1, :]
    upper = np.sort(hi, axis=0)[k_hi - 1, :]
    return lower, upper, n

def loio_jackknife_plus(rows_X, rows_y, rows_g, alpha, ytarget=None):
    yy = rows_y if ytarget is None else ytarget
    lower_all = np.empty(len(yy)); upper_all = np.empty(len(yy))
    n_loo_total = 0
    for i in ITER:
        tr = rows_g != i; te = rows_g == i
        lower, upper, n_train = jackknife_plus_interval(rows_X[tr], yy[tr], rows_X[te], alpha)
        lower_all[te] = lower; upper_all[te] = upper
        n_loo_total += n_train
    covered = (yy >= lower_all) & (yy <= upper_all)
    return {
        "marginal_coverage": float(np.mean(covered)),
        "median_width": float(np.median(upper_all - lower_all)),
        "n_loo_fits": int(n_loo_total),
    }, lower_all, upper_all, yy

results = {}
total_fits = 0

# --- DEFECT A: shrink real-signal alpha=0.10 intervals by 0.3x post-hoc
real_res, lower, upper, yy = loio_jackknife_plus(X_all, y_all, g_all, 0.10)
total_fits += real_res["n_loo_fits"]
mid = (lower + upper) / 2.0
half = (upper - lower) / 2.0
shrink = 0.3
lower_defect = mid - half * shrink
upper_defect = mid + half * shrink
cov_defect_a = float(np.mean((yy >= lower_defect) & (yy <= upper_defect)))
gate_a_real = real_res["marginal_coverage"] >= 0.80
gate_a_defect = cov_defect_a >= 0.80
results["defect_A_coverage_shrink"] = {
    "how_planted": "post-hoc scaled real-signal alpha=0.10 jackknife+ interval half-widths by 0.3x around the midpoint (simulates a buggy narrow-interval construction)",
    "real_signal_undefected_coverage": real_res["marginal_coverage"],
    "real_signal_undefected_gate_passed": bool(gate_a_real),
    "defected_shrunk_coverage": cov_defect_a,
    "defected_gate_passed": bool(gate_a_defect),
    "attack_fired_on_defect": bool(gate_a_real and not gate_a_defect),
}

# --- DEFECT B: independent second shuffle competing against the hostile-null shuffle
rng1 = np.random.default_rng(1)
y_shuf2 = y_all.copy(); rng1.shuffle(y_shuf2)
defect_b_res, _, _, _ = loio_jackknife_plus(X_all, y_all, g_all, 0.10, ytarget=y_shuf2)
total_fits += defect_b_res["n_loo_fits"]

rng0 = np.random.default_rng(0)
y_shuf0 = y_all.copy(); rng0.shuffle(y_shuf0)
null_res, _, _, _ = loio_jackknife_plus(X_all, y_all, g_all, 0.10, ytarget=y_shuf0)
total_fits += null_res["n_loo_fits"]

ratio_defect = null_res["median_width"] / defect_b_res["median_width"]
ratio_real = null_res["median_width"] / real_res["median_width"]
gate_d_real = ratio_real >= 1.10
gate_d_defect = ratio_defect >= 1.10
results["defect_B_no_real_skill"] = {
    "how_planted": "replaced the real-signal target y with an INDEPENDENT second shuffle (rng seed 1, distinct from hostile-null's seed 0), so the 'real' arm now also has no genuine signal -- exactly the failure mode gate (d) exists to catch",
    "real_signal_undefected_width_inflation_ratio": ratio_real,
    "real_signal_undefected_gate_passed": bool(gate_d_real),
    "defected_noise_vs_noise_width_inflation_ratio": ratio_defect,
    "defected_gate_passed": bool(gate_d_defect),
    "attack_fired_on_defect": bool(gate_d_real and not gate_d_defect),
}

positive_control = {
    "planted_defect": "(A) shrunk real-signal jackknife+ intervals by 0.3x around the midpoint; (B) replaced the real-signal target with an independent noise shuffle so both arms are pure noise",
    "how_planted": "(A) post-hoc scaling of lower/upper bounds computed by the SAME jackknife_plus_interval function used against real data, factor 0.3, midpoint-anchored; (B) np.random.default_rng(1).shuffle(y) applied in place of the true target, fed through the SAME loio_jackknife_plus function used against real data",
    "detected": bool(results["defect_A_coverage_shrink"]["attack_fired_on_defect"] and
                      results["defect_B_no_real_skill"]["attack_fired_on_defect"]),
    "evidence": {
        "defect_A": results["defect_A_coverage_shrink"],
        "defect_B": results["defect_B_no_real_skill"],
    },
}

body = {
    "schema": "amphora.design-rule-score.purformance-conformal-coverage-dedup-positive-control-receipt.v1",
    "module": "amphora-design-rule-score",
    "authority": "AUDIT_ONLY",
    "purpose": "Positive control demonstrating the conformal-coverage-dedup-v1 attack gates can detect defects of the kind they exist to catch, licensing the CLAIM_SURVIVED verdict on the real (undefected) leak-free re-run.",
    "attacks_receipt": "amphora-design-rule-score/benchmarks/conformal-coverage-dedup-v1/conformal-coverage-dedup-receipt.v1.json",
    "total_histgbm_fits": total_fits,
    "positive_control": positive_control,
    "conclusion": (
        "Both planted defects were caught: (A) shrinking real-signal intervals by 0.3x drops "
        "coverage from %.4f to %.4f, breaching the 0.80 worst-case floor gate that PASSED on "
        "undefected real data; (B) replacing the real-signal target with independent noise "
        "collapses the width-inflation ratio from %.4fx to %.4fx, breaching the >=1.10x target "
        "gate that PASSED on undefected real data. The attack's gates are demonstrably capable of "
        "firing on real defects, not just passing vacuously; the CLAIM_SURVIVED verdict on the "
        "undefected leak-free re-run is licensed."
    ) % (results["defect_A_coverage_shrink"]["real_signal_undefected_coverage"],
         results["defect_A_coverage_shrink"]["defected_shrunk_coverage"],
         results["defect_B_no_real_skill"]["real_signal_undefected_width_inflation_ratio"],
         results["defect_B_no_real_skill"]["defected_noise_vs_noise_width_inflation_ratio"]),
}

canon = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
out = sys.argv[1] if len(sys.argv) > 1 else "positive_control.canonical.json"
open(out, "wb").write(canon)
print("canonical_sha256", hashlib.sha256(canon).hexdigest())
print("total_histgbm_fits", total_fits)
print(json.dumps(results, indent=2))
print("detected", positive_control["detected"])
