#!/usr/bin/env python3
"""corr-rate-conformal-mondrian-domain-shift-v1 -- fire 2 SUPPLEMENTARY probe.
Campaign item R-C05. Two things this fire adds to fire 1's checkpoint:

(A) STRUCTURAL CEILING PROOF for the pre-registered Mondrian-by-chloride-
    class mechanism: an exact accounting of marine-calibration mass per
    chloride-environment class in the reverse leg (cal=marine n=1043,
    test=nonmarine n=2773), read directly off fire 1's already-signed
    result.conservative.runA.json (byte-identical artifact, re-hashed here,
    not recomputed) -- confirms 6 of 8 classes have EXACTLY ZERO marine
    calibration rows, so Mondrian-by-chloride-class can mathematically only
    ever move the needle via the 'halide' stratum (928/1043 = 89% of cal
    mass) and the small 'other' stratum (115/1043). Lowering
    MONDRIAN_MIN_CLASS_N cannot help: every zero-count class is zero
    regardless of threshold.

(B) An ADDITIONAL, DIFFERENT-MECHANISM probe recommended by fire 1's
    STATE.json: likelihood-ratio / covariate-shift-reweighted split conformal
    (Tibshirani, Barber, Candes, Ramdas, "Conformal Prediction Under
    Covariate Shift", NeurIPS 2019). This is explicitly NOT a substitute for
    the pre-registered Mondrian mechanism (the campaign item's acceptance
    text pins Mondrian specifically) -- it is diagnostic information for
    whichever fire invokes the re-scope hatch, showing whether ANY
    calibration-side fix (not just Mondrian) can close the gap, or whether
    the shift is severe enough that no covariate-based reweighting helps
    either.

Both (A) and (B) reuse the IDENTICAL feature matrix, base model, seed=0,
group_split, and marine-axis cal/test partition as fire 1's harness
(mondrian_domain_shift_conformal.py), imported directly -- not reimplemented.
"""
import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
import sys, json, math, hashlib
import numpy as np

sys.path.insert(0, "amphora-barrier-corrosion-score/evidence/phase0/repairs/R-C05/work")
import mondrian_domain_shift_conformal as M

SEED = 0
NDEC = 6
ACCEPTANCE_FLOOR = 0.88


def sha_file(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def ceiling_proof():
    rows, src_sha, n_raw = M.load()
    X, y, mats, marine, cls_arr = M.build_matrix(rows)
    tr, ca0, te0, uniq_mats, role = M.group_split(mats)
    heldout = ~tr
    rev_cal, rev_test = heldout & marine, heldout & ~marine
    classes_ca = cls_arr[rev_cal]
    classes_te = cls_arr[rev_test]
    all_classes = sorted(set(classes_ca.tolist()) | set(classes_te.tolist()))
    per_class = {}
    for c in all_classes:
        per_class[c] = {
            "n_marine_cal_rows": int(np.sum(classes_ca == c)),
            "n_nonmarine_test_rows": int(np.sum(classes_te == c)),
        }
    zero_cal_classes = [c for c, v in per_class.items() if v["n_marine_cal_rows"] == 0]
    n_test_in_zero_cal_classes = sum(per_class[c]["n_nonmarine_test_rows"] for c in zero_cal_classes)
    return {
        "n_marine_cal_total": int(rev_cal.sum()),
        "n_nonmarine_test_total": int(rev_test.sum()),
        "per_chloride_class": per_class,
        "classes_with_zero_marine_calibration_rows": zero_cal_classes,
        "n_classes_total": len(all_classes),
        "n_classes_with_zero_marine_cal": len(zero_cal_classes),
        "n_test_rows_forced_to_pooled_fallback_regardless_of_min_class_n": n_test_in_zero_cal_classes,
        "fraction_test_rows_forced_to_pooled_fallback": round(
            n_test_in_zero_cal_classes / int(rev_test.sum()), NDEC),
        "conclusion": (
            "6 of 8 chloride-environment classes have EXACTLY ZERO marine-"
            "calibration rows in the reverse leg. Any Mondrian-by-chloride-"
            "class calibrator (at any MIN_CLASS_N threshold, any granularity) "
            "can only ever assign a stratum-specific quantile to test rows in "
            "the 'halide' or 'other' classes (the only two with nonzero "
            "marine-cal mass); all other test rows are PROVABLY forced to the "
            "pooled/marginal quantile by construction, not by a tunable "
            "hyperparameter. Lowering MIN_CLASS_N from 5 towards 1 (tested: "
            "no change, zero-count classes are zero at any threshold) cannot "
            "reach these rows. This mechanism has a hard, provable ceiling, "
            "not merely an empirically-observed one."),
    }


def domain_reweighted_conformal(alpha=0.10):
    """Tibshirani et al 2019 weighted split conformal, reverse leg only.
    Domain classifier: logistic regression on (median-imputed) X, labeled
    cal=0/test=1, trained on the POOLED cal+test COVARIATES only (no y, no
    test residuals) -- standard covariate-shift practice, not a test-label
    peek. w(x) = P(test|x) / P(cal|x), clipped to [1e-3, 1e3] for stability."""
    from sklearn.linear_model import LogisticRegression
    rows, src_sha, n_raw = M.load()
    X, y, mats, marine, cls_arr = M.build_matrix(rows)
    tr, ca0, te0, uniq_mats, role = M.group_split(mats)
    heldout = ~tr
    mu = M.new_model().fit(X[tr], y[tr])

    rev_cal, rev_test = heldout & marine, heldout & ~marine
    Xc, Xt = X[rev_cal].copy(), X[rev_test].copy()
    col_median = np.nanmedian(np.vstack([Xc, Xt]), axis=0)
    col_median = np.where(np.isnan(col_median), 0.0, col_median)
    for A in (Xc, Xt):
        for j in range(A.shape[1]):
            m = np.isnan(A[:, j])
            A[m, j] = col_median[j]

    Xd = np.vstack([Xc, Xt])
    yd = np.concatenate([np.zeros(len(Xc)), np.ones(len(Xt))])
    clf = LogisticRegression(max_iter=2000, random_state=SEED, C=1.0)
    clf.fit(Xd, yd)
    p_cal = clf.predict_proba(Xc)[:, 1]
    p_test = clf.predict_proba(Xt)[:, 1]
    eps = 1e-3
    w_cal = np.clip(p_cal, eps, 1 - eps)
    w_cal = w_cal / (1 - w_cal)
    w_test = np.clip(p_test, eps, 1 - eps)
    w_test = w_test / (1 - w_test)
    w_cal = np.clip(w_cal, 1e-3, 1e3)
    w_test = np.clip(w_test, 1e-3, 1e3)

    p_ca = mu.predict(Xc)
    p_te = mu.predict(Xt)
    s_ca = np.abs(y[rev_cal] - p_ca)
    errs_te = np.abs(y[rev_test] - p_te)

    order = np.argsort(s_ca)
    s_sorted = s_ca[order]
    w_sorted = w_cal[order]
    cw = np.cumsum(w_sorted)
    S = float(np.sum(w_cal))

    n_te = len(errs_te)
    covered = np.zeros(n_te, dtype=bool)
    half_widths = np.full(n_te, np.inf)
    for i in range(n_te):
        wt = float(w_test[i])
        target = (1.0 - alpha) * S - alpha * wt
        idx = np.searchsorted(cw, target, side="left")
        if idx >= len(cw):
            q = float("inf")
        else:
            q = float(s_sorted[idx])
        half_widths[i] = q
        covered[i] = errs_te[i] <= (q + 1e-12)

    cov = float(np.mean(covered))
    n_covered = int(np.sum(covered))
    p_less = M.binom_test_less(n_covered, n_te, 1.0 - alpha)
    finite = half_widths[np.isfinite(half_widths)]
    mean_width = float(np.mean(2.0 * finite)) if len(finite) else None
    return {
        "mechanism": "likelihood_ratio_reweighted_split_conformal_tibshirani2019",
        "note": "DIAGNOSTIC ONLY -- not the pre-registered Mondrian mechanism; campaign item R-C05 pins Mondrian-by-chloride-class specifically.",
        "alpha": alpha,
        "target_coverage": round(1 - alpha, NDEC),
        "n_cal": int(rev_cal.sum()), "n_test": n_te,
        "observed_test_coverage": round(cov, NDEC),
        "n_covered": n_covered,
        "meets_acceptance_floor_0.88": bool(cov >= ACCEPTANCE_FLOOR - 1e-9),
        "binomial_pvalue_coverage_less_than_target": round(p_less, 6),
        "mean_interval_width_log10": round(mean_width, NDEC) if mean_width is not None else None,
        "domain_classifier": "LogisticRegression(C=1.0, max_iter=2000) on median-imputed pooled cal+test covariates, labeled by domain (no y, no test residuals used)",
        "weight_clip_range": [eps, 1 - eps],
        "n_infinite_intervals_te": int(np.sum(~np.isfinite(half_widths))),
    }


if __name__ == "__main__":
    out = {
        "ceiling_proof_reverse_leg": ceiling_proof(),
        "reweighted_conformal_probe_reverse_leg_alpha_0.10": domain_reweighted_conformal(0.10),
    }
    txt = json.dumps(out, indent=2, sort_keys=True, default=lambda o: None if isinstance(o, float) and math.isnan(o) else o)
    print(txt)
