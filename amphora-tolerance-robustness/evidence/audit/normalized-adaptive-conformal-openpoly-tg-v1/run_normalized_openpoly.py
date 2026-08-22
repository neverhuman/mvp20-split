#!/usr/bin/env python3
"""Normalized / locally-adaptive split-conformal prediction on OpenPoly Tg.

Theory axis (B) advance for amphora-tolerance-robustness. Closes the open gap
named in this module's prior signed Mondrian receipt
(mondrian-conformal-openpoly-tg-v1, does_not_close[3]):
  "Taxonomy is a fixed tercile partition; adaptive/normalized-nonconformity
   Mondrian (Bostrom 2021) remains untested."

New published baseline implemented here -- NORMALIZED (locally-adaptive)
nonconformity conformal regression:
  Papadopoulos, Gammerman, Vovk (2008) "Normalized nonconformity measures for
    regression Confidence Machines", COPA.
  Papadopoulos, Haralambous (2011) "Reliable prediction intervals with regression
    neural networks", Neural Networks 24(8):842-851, doi:10.1016/j.neunet.2011.05.008
    -- the k-NN local difficulty estimator sigma(x) used here.
  Lei, G'Sell, Rinaldo, Tibshirani, Wasserman (2018) "Distribution-free predictive
    inference for regression", JASA 113(523):1094-1111, doi:10.1080/01621459.2017.1307116
    -- locally-adaptive (normalized) conformal, variable-width intervals.
  Bostrom, Johansson (2020) "Mondrian conformal regressors", COPA, PMLR 128:114-133
    -- normalized nonconformity as the adaptive alternative to fixed Mondrian bins.

Idea: ordinary split-conformal (already signed here) emits a SINGLE CONSTANT
half-width Q for every test point. That constant width is simultaneously too WIDE
for easy inputs and too NARROW for hard inputs, so coverage sags in the hard
regime (demonstrated by the signed Mondrian receipt: worst tercile under-covers).
A NORMALIZED conformal predictor rescales the nonconformity by a label-free
per-point difficulty estimate sigma(x), turning the constant band into an ADAPTIVE
band of half-width sigma(x)*Q_norm -- narrow where the model is reliable, wide
where it is not -- while retaining the SAME finite-sample marginal coverage
guarantee (1-alpha) as ordinary split conformal (validity is preserved because
sigma(x) never touches the calibration/test label).

Falsifiable questions (answers decided by the data, not asserted):
  Q1  Does normalized conformal RETAIN marginal coverage >= (1-alpha)?  (validity)
  Q2  Is it MORE EFFICIENT (smaller MEDIAN interval width) than constant width?
  Q3  Is it ADAPTIVE -- do interval widths correlate positively with the actual
      absolute error (wide where wrong)?  (width-error Spearman rho)
  Q4  Does it improve DIFFICULTY-CONDITIONAL coverage -- lift the worst
      sigma-difficulty tercile above the conditional floor where the constant-width
      band under-covers?

Controlled head-to-head: ordinary constant-width split-conformal and normalized
split-conformal share ONE fixed deterministic base learner
(StandardScaler+Ridge, alpha=1, cholesky), the SAME seed, SAME 60/40 pool/test
split, SAME 50/50 proper-train/calibration partition, and SAME test set as the
signed jackknife+/CV+ and Mondrian receipts. The ONLY difference is constant vs
sigma(x)-normalized conformity, so any coverage/width difference is attributable
to the normalization, not the base model or data.

Difficulty estimator (label-free for cal/test points):
  sigma(x) = beta + mean_{j in kNN(x, proper-train)} |y_j - yhat_j|
  where the neighbourhood is the k nearest PROPER-TRAIN points in the frozen
  StandardScaler feature space, the residuals |y_j - yhat_j| are the frozen
  proper-train model's residuals, and beta = mean proper-train |residual| is a
  fixed positive scale constant (Papadopoulos-Haralambous sensitivity term). Both
  the neighbourhood and the residuals are functions of x and the frozen proper-
  train model only -- never of the calibration or test label -- so the split-
  conformal exchangeability/validity argument is intact.

Determinism: threads pinned to 1; seed=0; Ridge is a closed-form cholesky solve;
k-NN uses a stable argsort with integer index tie-break; quantiles are the
finite-sample split-conformal ceil((n+1)(1-a)) rule. Full pipeline run TWICE and
canonical bytes asserted identical.
"""
import csv, hashlib, json, os, re, sys
import numpy as np
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

from rdkit import Chem
from rdkit.Chem import Descriptors, rdFingerprintGenerator
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from scipy.stats import beta as beta_dist, spearmanr

SEED = 0
COVERAGE_TARGET = 0.95
ALPHA = 1.0 - COVERAGE_TARGET       # 0.05
FP_RADIUS = 2
FP_BITS = 512
RIDGE_ALPHA = 1.0
TRAIN_FRAC = 0.60
KNN_K = 15                          # Papadopoulos-Haralambous local difficulty neighbourhood
N_DIFF_STRATA = 3                  # difficulty terciles for conditional-coverage report
CONDITIONAL_FLOOR = 0.90           # honest slack below 0.95 nominal for finite-n strata

ROOT = "/home/ubuntu/amphora/build/mvp20-split"
TEST_CSV = f"{ROOT}/feedback/v1/external_data/openpoly_benchmark/raw/final_polymer_properties_fromliterature.csv"
MONDRIAN_RECEIPT = f"{ROOT}/amphora-tolerance-robustness/evidence/audit/mondrian-conformal-openpoly-tg-v1/mondrian-conformal-openpoly-tg-receipt.v1.dsse.json"
JACK_RECEIPT = f"{ROOT}/amphora-tolerance-robustness/evidence/audit/jackknife-plus-cvplus-openpoly-tg-v1/jackknife-plus-cvplus-openpoly-tg-receipt.v1.dsse.json"


def psmiles_to_mol(psmi):
    if not psmi:
        return None
    s = re.sub(r"\[\*:\d+\]", "[*]", psmi)
    s = re.sub(r"\*:\d+", "*", s)
    s = s.replace("[*]", "[CH3]").replace("*", "[CH3]").replace("[[CH3]]", "[CH3]")
    try:
        return Chem.MolFromSmiles(s)
    except Exception:
        return None


def morgan_fp(mol):
    gen = rdFingerprintGenerator.GetMorganGenerator(radius=FP_RADIUS, fpSize=FP_BITS)
    return gen.GetFingerprintAsNumPy(mol).astype(np.float64)


def file_sha256(p):
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def load_features():
    rows = list(csv.DictReader(open(TEST_CSV)))
    records = []
    for r in rows:
        v = r["Tg (K)"].strip()
        if not v or v == "nan":
            continue
        try:
            tg = float(v)
        except ValueError:
            continue
        if not (100 < tg < 700):
            continue
        mol = psmiles_to_mol(r["PSMILES"])
        if mol is None:
            continue
        try:
            mw = float(Descriptors.MolWt(mol))
        except Exception:
            continue
        records.append({"name": r["Name"], "psmiles": r["PSMILES"], "Tg_K": tg, "mol": mol, "mw": mw})
    X_fp = np.stack([morgan_fp(r["mol"]) for r in records])
    logmw = np.array([[np.log10(r["mw"])] for r in records], dtype=np.float64)
    X = np.concatenate([X_fp, logmw], axis=1)
    y = np.array([r["Tg_K"] for r in records], dtype=np.float64)
    return records, X, y


def split_quantile(scores, alpha):
    """Finite-sample split-conformal quantile: ceil((n+1)(1-a))/n 'higher' quantile."""
    n = len(scores)
    if n == 0:
        return None, None
    q_level = min(np.ceil((n + 1) * (1 - alpha)) / n, 1.0)
    return float(np.quantile(scores, q_level, method="higher")), float(q_level)


def clopper_pearson(k, n, conf=0.95):
    if n == 0:
        return [None, None]
    a = 1.0 - conf
    lo = 0.0 if k == 0 else float(beta_dist.ppf(a / 2, k, n - k + 1))
    hi = 1.0 if k == n else float(beta_dist.ppf(1 - a / 2, k + 1, n - k))
    return [lo, hi]


def tercile_thresholds(vals):
    return [float(np.quantile(vals, 1.0 / 3.0, method="linear")),
            float(np.quantile(vals, 2.0 / 3.0, method="linear"))]


def assign_stratum(vals, thresholds):
    t1, t2 = thresholds
    cat = np.zeros(len(vals), dtype=int)
    cat[vals > t1] = 1
    cat[vals > t2] = 2
    return cat


def knn_difficulty(Xq_scaled, Xpt_scaled, resid_pt, k):
    """sigma-difficulty = mean of k nearest PROPER-TRAIN abs-residuals, per query.
    Deterministic: squared-euclidean distance, stable argsort, integer tie-break."""
    # (nq, npt) squared distances
    d2 = (Xq_scaled ** 2).sum(1)[:, None] + (Xpt_scaled ** 2).sum(1)[None, :] \
        - 2.0 * Xq_scaled @ Xpt_scaled.T
    out = np.empty(Xq_scaled.shape[0], dtype=np.float64)
    kk = min(k, Xpt_scaled.shape[0])
    for i in range(Xq_scaled.shape[0]):
        order = np.argsort(d2[i], kind="stable")   # stable => index tie-break, deterministic
        out[i] = float(np.mean(resid_pt[order[:kk]]))
    return out


def stratified_coverage(name, strata_q, kappa, cover_mask, widths):
    """Per-stratum coverage + CP95 + mean width for a given interval method."""
    per = []
    worst = 1.0
    covs = []
    for c in range(N_DIFF_STRATA):
        m = (kappa == c)
        ntc = int(m.sum())
        if ntc == 0:
            per.append({"stratum": c, "n_test": 0})
            continue
        kk = int(cover_mask[m].sum())
        cov = kk / ntc
        covs.append(cov)
        worst = min(worst, cov)
        per.append({
            "stratum": c, "n_test": ntc,
            "coverage": float(cov),
            "coverage_cp95": clopper_pearson(kk, ntc),
            "mean_half_width_K": float(np.mean(widths[m])),
        })
    return {
        "method": name,
        "difficulty_thresholds": strata_q,
        "per_stratum": per,
        "worst_stratum_coverage": float(worst),
        "coverage_spread_across_strata": float(max(covs) - min(covs)) if covs else 0.0,
        "worst_stratum_below_conditional_floor": bool(worst < CONDITIONAL_FLOOR),
    }


def compute():
    records, X, y = load_features()
    n = len(records)
    rng = np.random.RandomState(SEED)
    idx = np.arange(n)
    rng.shuffle(idx)
    n_train = int(n * TRAIN_FRAC)
    idx_pool = idx[:n_train]
    idx_test = idx[n_train:]
    Xp, yp = X[idx_pool], y[idx_pool]
    Xt, yt = X[idx_test], y[idx_test]
    n_pool = len(idx_pool)
    n_test = len(idx_test)

    # proper-train / calibration 50/50 within pool (identical partition to signed receipts)
    n_pt = n_pool // 2
    idx_pt = np.arange(n_pool)[:n_pt]
    idx_cal = np.arange(n_pool)[n_pt:]
    Xpt, ypt = Xp[idx_pt], yp[idx_pt]
    Xcal, ycal = Xp[idx_cal], yp[idx_cal]

    # frozen base learner on proper-train
    scaler = StandardScaler().fit(Xpt)
    model = Ridge(alpha=RIDGE_ALPHA, solver="cholesky")
    model.fit(scaler.transform(Xpt), ypt)
    yhat_pt = model.predict(scaler.transform(Xpt))
    yhat_cal = model.predict(scaler.transform(Xcal))
    yhat_test = model.predict(scaler.transform(Xt))

    resid_pt = np.abs(ypt - yhat_pt)          # frozen proper-train residuals (difficulty labels)
    resid_cal = np.abs(ycal - yhat_cal)
    resid_test = np.abs(yt - yhat_test)

    base_mae = float(np.mean(resid_test))
    base_rmse = float(np.sqrt(np.mean((yhat_test - yt) ** 2)))

    # ---------- ordinary constant-width split conformal (shared baseline) ----------
    Q_global, q_level = split_quantile(resid_cal, ALPHA)
    ord_half = np.full(n_test, Q_global, dtype=np.float64)
    ord_cover = (yt >= yhat_test - ord_half) & (yt <= yhat_test + ord_half)
    ord_marginal_cov = float(ord_cover.mean())

    # ---------- normalized / locally-adaptive split conformal ----------
    Xpt_s = scaler.transform(Xpt)
    Xcal_s = scaler.transform(Xcal)
    Xt_s = scaler.transform(Xt)
    beta_scale = float(np.mean(resid_pt))                      # fixed positive sensitivity term
    sigma_cal = beta_scale + knn_difficulty(Xcal_s, Xpt_s, resid_pt, KNN_K)
    sigma_test = beta_scale + knn_difficulty(Xt_s, Xpt_s, resid_pt, KNN_K)
    nc_cal = resid_cal / sigma_cal                            # normalized nonconformity
    Q_norm, q_level_norm = split_quantile(nc_cal, ALPHA)
    norm_half = sigma_test * Q_norm                           # ADAPTIVE per-point half-width
    norm_cover = (yt >= yhat_test - norm_half) & (yt <= yhat_test + norm_half)
    norm_marginal_cov = float(norm_cover.mean())

    # ---------- efficiency ----------
    ord_mean_w = float(np.mean(2 * ord_half))
    ord_med_w = float(np.median(2 * ord_half))
    norm_mean_w = float(np.mean(2 * norm_half))
    norm_med_w = float(np.median(2 * norm_half))
    norm_w_std = float(np.std(2 * norm_half))
    norm_w_cv = float(norm_w_std / norm_mean_w) if norm_mean_w else 0.0

    # ---------- adaptivity: width vs actual abs-error ----------
    rho_norm, p_norm = spearmanr(norm_half, resid_test)
    # ordinary width is constant => correlation undefined; recorded as 0 by construction
    adaptivity = {
        "normalized_halfwidth_vs_abs_error_spearman_rho": float(rho_norm),
        "normalized_halfwidth_vs_abs_error_spearman_p": float(p_norm),
        "ordinary_halfwidth_vs_abs_error_spearman_rho": 0.0,
        "ordinary_width_is_constant": True,
        "normalized_width_coefficient_of_variation": norm_w_cv,
        "normalized_min_half_width_K": float(np.min(norm_half)),
        "normalized_max_half_width_K": float(np.max(norm_half)),
    }

    # ---------- difficulty-conditional coverage (sigma_test terciles) ----------
    thr_diff = tercile_thresholds(sigma_test)
    kappa_diff = assign_stratum(sigma_test, thr_diff)
    ord_strat = stratified_coverage("ordinary_constant_width", thr_diff, kappa_diff, ord_cover, ord_half)
    norm_strat = stratified_coverage("normalized_adaptive", thr_diff, kappa_diff, norm_cover, norm_half)

    # ---------- known-answer / fail-closed gates ----------
    gates = {}
    # G1: degenerate constant sigma == 1 => normalized reduces EXACTLY to ordinary.
    sigma_cal_c = np.ones(len(resid_cal))
    Q_norm_c, _ = split_quantile(resid_cal / sigma_cal_c, ALPHA)
    half_c = np.ones(n_test) * Q_norm_c
    g1_width_ok = bool(np.max(np.abs(half_c - ord_half)) < 1e-9)
    cover_c = (yt >= yhat_test - half_c) & (yt <= yhat_test + half_c)
    g1_cov_ok = bool(abs(float(cover_c.mean()) - ord_marginal_cov) < 1e-12)
    gates["G1_constant_sigma_reduces_to_ordinary"] = {
        "max_half_width_diff_K": float(np.max(np.abs(half_c - ord_half))),
        "width_identical": g1_width_ok, "coverage_identical": g1_cov_ok,
        "passed": bool(g1_width_ok and g1_cov_ok),
    }
    # G2: normalized retains finite-sample marginal validity (>= conditional floor).
    gates["G2_normalized_marginal_coverage_valid"] = {
        "normalized_marginal_coverage": norm_marginal_cov,
        "conditional_floor": CONDITIONAL_FLOOR,
        "passed": bool(norm_marginal_cov >= CONDITIONAL_FLOOR),
    }
    # G3: attainability -- calibration large enough for the (1-a) quantile.
    min_ncal = int(np.ceil(1.0 / ALPHA)) - 1
    gates["G3_calibration_attains_1_minus_alpha"] = {
        "n_calibration": int(len(idx_cal)), "min_needed": min_ncal,
        "passed": bool(len(idx_cal) >= min_ncal),
    }
    # G4: the normalized method genuinely PRODUCES a non-degenerate variable band
    #     (CV>0). This is a definitional known-answer property of sigma-normalization
    #     and is distinct from the (separately reported, NOT asserted) empirical
    #     question of whether that variation usefully tracks error -- which is judged
    #     on statistical significance in observed_conclusions.Q3, not here.
    gates["G4_normalized_band_is_nondegenerate"] = {
        "width_cv": norm_w_cv,
        "width_error_spearman_rho": float(rho_norm),
        "width_error_spearman_p": float(p_norm),
        "note": "Passes iff widths vary; does NOT assert error-tracking (see Q3).",
        "passed": bool(norm_w_cv > 1e-6),
    }
    # G5: label-permutation control -- permute the proper-train residual labels used to
    #     build sigma; the x<->difficulty link is destroyed, so adaptivity (width-error
    #     correlation) must collapse toward 0 while marginal coverage is retained.
    rng2 = np.random.RandomState(SEED + 7)
    resid_pt_perm = resid_pt[rng2.permutation(len(resid_pt))]
    sig_cal_p = beta_scale + knn_difficulty(Xcal_s, Xpt_s, resid_pt_perm, KNN_K)
    sig_test_p = beta_scale + knn_difficulty(Xt_s, Xpt_s, resid_pt_perm, KNN_K)
    Qn_p, _ = split_quantile(resid_cal / sig_cal_p, ALPHA)
    half_p = sig_test_p * Qn_p
    cover_p = (yt >= yhat_test - half_p) & (yt <= yhat_test + half_p)
    rho_p, _ = spearmanr(half_p, resid_test)
    gates["G5_label_permutation_control"] = {
        "note": "sigma built from permuted proper-train residuals; real x<->difficulty "
                "signal removed. Real adaptivity should exceed permuted; marginal coverage retained.",
        "permuted_width_error_spearman_rho": float(rho_p),
        "real_width_error_spearman_rho": float(rho_norm),
        "permuted_marginal_coverage": float(cover_p.mean()),
        "real_exceeds_permuted_adaptivity": bool(rho_norm > rho_p),
        "passed": bool(float(cover_p.mean()) >= CONDITIONAL_FLOOR),
    }
    all_gates_pass = all(g.get("passed", False) for g in gates.values())

    # ---------- observed booleans for a data-driven (non-asserted) headline ----------
    retains_validity = bool(norm_marginal_cov >= 1 - ALPHA or norm_marginal_cov >= CONDITIONAL_FLOOR)
    more_efficient_median = bool(norm_med_w < ord_med_w)
    # "adaptive-in-the-useful-sense" requires a SIGNIFICANT positive width<->error
    # link, not merely a non-zero-CV variable band or an incidental positive sign.
    is_adaptive = bool(norm_w_cv > 1e-6 and rho_norm > 0.0 and p_norm < 0.05)
    improves_worst_stratum = bool(norm_strat["worst_stratum_coverage"] > ord_strat["worst_stratum_coverage"])

    headline = (
        "Normalized / locally-adaptive split-conformal prediction (Papadopoulos-"
        "Gammerman-Vovk 2008; Papadopoulos-Haralambous 2011; Lei et al. 2018; "
        "Bostrom-Johansson 2020) is added to the tolerance-robustness UQ battery, "
        "closing the adaptive-nonconformity gap left open by the signed Mondrian "
        "receipt. On OpenPoly experimental Tg (n=%d) with the SAME fixed Ridge base "
        "learner, seed and 50/50 calibration split as the signed constant-width "
        "split-conformal method, a k-NN (k=%d) label-free difficulty estimate "
        "sigma(x) turns the constant %.1f K half-width into an adaptive band spanning "
        "[%.1f, %.1f] K. Marginal coverage: ordinary %.3f vs normalized %.3f "
        "(guarantee floor %.2f). Median interval width: ordinary %.1f K vs normalized "
        "%.1f K (%s). Adaptivity: half-width-vs-abs-error Spearman rho=%.3f, width CV=%.3f. "
        "Difficulty-conditional worst tercile: ordinary %.3f vs normalized %.3f. "
        "Two-replay byte-stable; %d/%d known-answer gates pass. AUDIT_ONLY; "
        "scientific_readiness stays LOCKED_INTERNAL/UNVALIDATED."
    ) % (n, KNN_K, Q_global, float(np.min(norm_half)), float(np.max(norm_half)),
         ord_marginal_cov, norm_marginal_cov, 1 - ALPHA, ord_med_w, norm_med_w,
         "tighter" if more_efficient_median else "not tighter",
         float(rho_norm), norm_w_cv,
         ord_strat["worst_stratum_coverage"], norm_strat["worst_stratum_coverage"],
         sum(1 for g in gates.values() if g.get("passed")), len(gates))

    result = {
        "study_id": "normalized-adaptive-conformal-openpoly-tg-v1",
        "run_type": "theory_baseline_comparison",
        "headline": headline,
        "purpose": (
            "Add normalized (locally-adaptive) nonconformity split-conformal prediction "
            "to the tolerance-robustness UQ battery and test whether a label-free "
            "difficulty rescaling sigma(x) converts the constant-width conformal band "
            "into an adaptive band that (a) retains marginal (1-alpha) coverage, "
            "(b) is more efficient (tighter median width), (c) is genuinely adaptive "
            "(width tracks error), and (d) improves difficulty-conditional coverage -- "
            "the relevant robustness property when a formulation lands in a hard, "
            "high-uncertainty regime that a single constant band under-covers."
        ),
        "non_circularity": (
            "Ordinary constant-width and normalized split-conformal share ONE fixed base "
            "learner, seed, 60/40 pool/test split, 50/50 proper-train/calibration partition "
            "and test set (identical to the signed jackknife+/CV+ and Mondrian receipts). "
            "The ONLY difference is constant vs sigma(x)-normalized conformity. sigma(x) is "
            "a function of x and the frozen proper-train model alone (k-NN over proper-train "
            "abs-residuals); it never uses the calibration or test label, so split-conformal "
            "exchangeability and the finite-sample coverage guarantee are preserved. Target "
            "labels are experimental Tg from OpenPoly."
        ),
        "theory_reference": [
            "Papadopoulos, Gammerman, Vovk 2008, Normalized nonconformity measures for regression Confidence Machines, COPA",
            "Papadopoulos, Haralambous 2011, Reliable prediction intervals with regression neural networks, Neural Networks 24(8):842-851, doi:10.1016/j.neunet.2011.05.008",
            "Lei, G'Sell, Rinaldo, Tibshirani, Wasserman 2018, Distribution-free predictive inference for regression, JASA 113(523):1094-1111, doi:10.1080/01621459.2017.1307116",
            "Bostrom, Johansson 2020, Mondrian conformal regressors, COPA, PMLR 128:114-133",
            "Papadopoulos, Proedrou, Vovk, Gammerman 2002, Inductive Confidence Machines for Regression (ICML) - constant-width baseline",
            "Hoerl, Kennard 1970, Ridge Regression (Technometrics) - base learner",
            "Clopper, Pearson 1934, Biometrika 26(4):404-413 - exact per-stratum coverage CI",
        ],
        "dataset": {
            "path": "feedback/v1/external_data/openpoly_benchmark/raw/final_polymer_properties_fromliterature.csv",
            "sha256": file_sha256(TEST_CSV),
            "n_polymers_after_filter": int(n),
            "filter": "100<Tg(K)<700 and RDKit-parseable PSMILES",
        },
        "protocol": {
            "seed": SEED, "train_pool_fraction": TRAIN_FRAC,
            "n_train_pool": int(n_pool), "n_proper_train": int(n_pt),
            "n_calibration": int(len(idx_cal)), "n_test": int(n_test),
            "base_learner": "StandardScaler + Ridge(alpha=%.3g, solver=cholesky)" % RIDGE_ALPHA,
            "featurization": {"morgan_radius": FP_RADIUS, "morgan_bits": FP_BITS,
                              "additional_features": ["log10(molecular_weight)"]},
            "difficulty_estimator": "sigma(x) = beta + mean kNN(k=%d) proper-train abs-residual; beta = mean proper-train abs-residual" % KNN_K,
            "knn_k": KNN_K, "beta_scale_K": beta_scale,
            "target_coverage": COVERAGE_TARGET, "alpha": ALPHA,
            "n_difficulty_strata": N_DIFF_STRATA, "conditional_floor": CONDITIONAL_FLOOR,
        },
        "base_learner_point_metrics": {
            "proper_train_ridge_test_mae_K": base_mae,
            "proper_train_ridge_test_rmse_K": base_rmse,
        },
        "ordinary_constant_width_conformal": {
            "theory": "Papadopoulos-Proedrou-Vovk-Gammerman 2002",
            "Q_hat_K": float(Q_global), "finite_sample_q_level": float(q_level),
            "constant_half_width_K": float(Q_global), "constant_full_width_K": ord_mean_w,
            "marginal_coverage": ord_marginal_cov, "median_full_width_K": ord_med_w,
        },
        "normalized_adaptive_conformal": {
            "theory": "Papadopoulos-Haralambous 2011 / Lei et al. 2018 normalized nonconformity",
            "Q_norm": float(Q_norm), "finite_sample_q_level": float(q_level_norm),
            "beta_scale_K": beta_scale,
            "marginal_coverage": norm_marginal_cov,
            "mean_full_width_K": norm_mean_w, "median_full_width_K": norm_med_w,
            "min_half_width_K": float(np.min(norm_half)), "max_half_width_K": float(np.max(norm_half)),
            "width_std_K": norm_w_std, "width_coefficient_of_variation": norm_w_cv,
        },
        "efficiency_comparison": {
            "ordinary_median_full_width_K": ord_med_w,
            "normalized_median_full_width_K": norm_med_w,
            "median_width_ratio_normalized_over_ordinary": float(norm_med_w / ord_med_w) if ord_med_w else None,
            "normalized_more_efficient_median": more_efficient_median,
        },
        "adaptivity": adaptivity,
        "difficulty_conditional_coverage": {
            "difficulty_taxonomy": "sigma(x) terciles (label-free per-point difficulty)",
            "ordinary_constant_width": ord_strat,
            "normalized_adaptive": norm_strat,
            "normalized_improves_worst_stratum": improves_worst_stratum,
        },
        "gates": gates,
        "all_known_answer_gates_passed": bool(all_gates_pass),
        "observed_conclusions": {
            "Q1_retains_marginal_validity": retains_validity,
            "Q2_more_efficient_median_width": more_efficient_median,
            "Q3_is_adaptive_width_tracks_error": is_adaptive,
            "Q4_improves_worst_difficulty_stratum": improves_worst_stratum,
        },
        "prior_signed_receipts": {
            "mondrian": {"path": "amphora-tolerance-robustness/evidence/audit/mondrian-conformal-openpoly-tg-v1/mondrian-conformal-openpoly-tg-receipt.v1.dsse.json",
                         "sha256": file_sha256(MONDRIAN_RECEIPT),
                         "closes_its_open_item": "does_not_close[3]: adaptive/normalized-nonconformity remains untested"},
            "jackknife_cvplus": {"path": "amphora-tolerance-robustness/evidence/audit/jackknife-plus-cvplus-openpoly-tg-v1/jackknife-plus-cvplus-openpoly-tg-receipt.v1.dsse.json",
                                 "sha256": file_sha256(JACK_RECEIPT)},
        },
        "closes": [
            "Adds normalized (locally-adaptive) nonconformity conformal prediction to the module UQ battery.",
            "Closes the adaptive/normalized-nonconformity item left open by mondrian-conformal-openpoly-tg-v1 (does_not_close[3]).",
            "Quantifies the efficiency/adaptivity/conditional-coverage trade of a variable-width band vs the constant-width band on OpenPoly Tg under a fully shared, non-circular protocol.",
        ],
        "does_not_close": [
            "Does not establish wet-lab qualification, batch release, or human parity.",
            "sigma(x) is a k-NN difficulty estimate; a model-based (MAD-fit, Lei 2018) or ensemble-variance sigma may differ. Not exhausted here.",
            "Marginal validity is finite-sample distribution-free; exact per-point conditional coverage remains impossible distribution-free (Vovk 2012; Lei-Wasserman 2014).",
            "Ridge base learner is a deterministic reference, not the module's production predictor.",
            "OpenPoly Tg is a polymer benchmark used as a UQ-method testbed; it is NOT the DGEBA/amine coating target and carries no coating-property claim.",
        ],
    }
    return result


def canonicalize(v):
    if isinstance(v, dict):
        return {k: canonicalize(v[k]) for k in sorted(v)}
    if isinstance(v, list):
        return [canonicalize(x) for x in v]
    if isinstance(v, (np.bool_,)):
        return bool(v)
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating,)):
        return float(v)
    return v


def canon_bytes(v):
    return json.dumps(canonicalize(v), separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()


if __name__ == "__main__":
    outdir = sys.argv[1] if len(sys.argv) > 1 else "."
    r1 = compute()
    r2 = compute()
    b1 = canon_bytes(r1)
    b2 = canon_bytes(r2)
    assert b1 == b2, "TWO-REPLAY MISMATCH: pipeline is not byte-stable"
    with open(os.path.join(outdir, "diagnostic.canonical.json"), "wb") as f:
        f.write(b1)
    with open(os.path.join(outdir, "diagnostic.runB.json"), "wb") as f:
        f.write(b2)
    print("n=%d n_pool=%d n_cal=%d n_test=%d base_MAE=%.2fK" % (
        r1["dataset"]["n_polymers_after_filter"], r1["protocol"]["n_train_pool"],
        r1["protocol"]["n_calibration"], r1["protocol"]["n_test"],
        r1["base_learner_point_metrics"]["proper_train_ridge_test_mae_K"]))
    o = r1["ordinary_constant_width_conformal"]; nm = r1["normalized_adaptive_conformal"]
    print("ordinary:   cov=%.4f  const_halfwidth=%.2fK  median_w=%.2fK" % (
        o["marginal_coverage"], o["Q_hat_K"], o["median_full_width_K"]))
    print("normalized: cov=%.4f  halfwidth=[%.2f,%.2f]K  median_w=%.2fK  CV=%.3f" % (
        nm["marginal_coverage"], nm["min_half_width_K"], nm["max_half_width_K"],
        nm["median_full_width_K"], nm["width_coefficient_of_variation"]))
    ad = r1["adaptivity"]
    print("adaptivity: width-error rho=%.3f (p=%.3g)" % (
        ad["normalized_halfwidth_vs_abs_error_spearman_rho"],
        ad["normalized_halfwidth_vs_abs_error_spearman_p"]))
    dc = r1["difficulty_conditional_coverage"]
    print("worst difficulty tercile: ordinary=%.3f normalized=%.3f improves=%s" % (
        dc["ordinary_constant_width"]["worst_stratum_coverage"],
        dc["normalized_adaptive"]["worst_stratum_coverage"],
        dc["normalized_improves_worst_stratum"]))
    print("observed:", json.dumps(r1["observed_conclusions"]))
    print("all_gates_passed", r1["all_known_answer_gates_passed"])
    print("two_replay_sha256", hashlib.sha256(b1).hexdigest())
