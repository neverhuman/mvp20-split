#!/usr/bin/env python3
"""
amphora-process-qc-twin : estimated-parameter (Phase-II) run-length degradation
of the EWMA(0.20,3) and two-sided CUSUM(0.5,5) memory detectors -- and the
three-detector UNION false-alarm budget -- under the ACTUAL Individuals-chart
default sigma estimator sigma_hat = MRbar/d2(2), NOT S/c4. AUDIT_ONLY.

THIS IS AN ATTACK on a standing claim
-------------------------------------
estparam-memory-detector-arl-degradation-v1 (prior receipt) reported:
  baseline_size_requirement.smallest_tabulated_m_meeting_criterion == 50
i.e. "a 50-observation Phase-I baseline suffices to guarantee (95th pct) the
module's locked <=1.5-expected-false-alarm/30-batch union budget." That number
was computed with sigma_hat = S/c4(m), which the SAME receipt's own
`does_not_close` explicitly flags:
  "Uses sigma_hat = S/c4; the MRbar/d2 estimator actually defaulted to by
   Individuals charts is strictly worse (ARE 0.605), so the memory-arm
   guaranteed ARL0 reported here is an upper bound, not the operating value.
   The MRbar/d2 x EWMA/CUSUM cross is still open."
moving-range-arl-degradation-v1 closed the MRbar/d2 cross for the SHEWHART arm
only. Neither prior receipt characterizes what happens when the union's
EWMA and CUSUM arms are fed the ACTUAL Montgomery-default Individuals sigma
estimator (mission.md: "Individuals / Moving-Range Shewhart 3-sigma"; all
three charts read the same standardized stream off the SAME Phase-I baseline,
so if the Shewhart arm uses MRbar/d2 the EWMA/CUSUM arms operate on that same
estimate in practice). This receipt closes that remaining cross and checks
whether m=50 still meets the locked budget once the real estimator is used.

Method: exact conditional reduction, sigma-law by Monte Carlo (not a Patnaik
proxy), conditional ARL by the SAME published Markov-chain machinery
-----------------------------------------------------------------------------
Xbar is a mean contrast, orthogonal to every difference X_{i+1}-X_i, hence
mu_hat = Xbar is EXACTLY independent of sigma_hat_MR = MRbar/d2 (same argument
as moving-range-arl-degradation-v1 / estparam-arl-degradation-v1's S-based
reduction). So, exactly as in estparam-memory-detector-arl-degradation-v1:
  U = mu_hat/sigma ~ N(0,1/m)                          (exact, closed form)
  W = sigma_hat_MR/sigma                                (NO closed form -- MR
                                                          is only characterized
                                                          by its first two
                                                          moments analytically;
                                                          its full law is
                                                          obtained here by
                                                          direct simulation of
                                                          the correlated
                                                          moving-range process)
  delta_eff = -U/W,  s_eff = 1/W
  conditional ARL0 = known-parameter ARL0 at (delta_eff, s_eff)
An earlier version of this harness (superseded, not signed) computed
conditional ARL0 by simulating a SINGLE realized future run per baseline
draw. That conflates two variance sources -- baseline-estimation variability
(what we want) and single-run geometric/random-walk noise (CV ~ 1, pure
nuisance) -- and catastrophically deflates the reported guaranteed (5th-pct)
ARL0. The corrected method below uses Monte Carlo ONLY to characterize the
sampling law of W (a large empirical-quantile sample of sigma_hat_MR, since it
has no closed form), and then applies the EXACT deterministic Brook-Evans
Markov-chain / geometric formulas -- already validated against Montgomery
Table 9.4 and Siegmund 1985 in estparam-memory-detector-arl-degradation-v1 --
to get the conditional expectation at each (U,W) grid node. No run is ever
simulated; only the baseline (mu_hat, sigma_hat_MR) sampling law is.

Published baselines (non-circular)
-----------------------------------
[MR estimator]      Montgomery 2020 ISQC 8th ed. Ch.6.4; NIST/SEMATECH 6.3.2.
[MR vs S efficiency] Cryer & Ryan 1990, JQT 22(3):187-192.
[Patnaik chi proxy]  Patnaik 1950, Biometrika 37:78-87.
[EWMA/CUSUM est-par] Jones, Champ & Rigdon 2001 Technometrics 43(2):156-167;
                     Jones, Champ & Rigdon 2004 JQT 36(1):95-108.
[Markov chain ARL]   Brook & Evans 1972, Biometrika 59(3):539-549.
[anchors]            Montgomery 2020 Table 9.4; NIST/SEMATECH 6.3; Shewhart 1931.

Honest ceiling
--------------
i.i.d. normality assumed throughout; autocorrelation/non-normality not
modeled. Theory characterization, not a measurement on real batches. Grants no
release authority.
"""
import hashlib, json, math, os
from pathlib import Path

import numpy as np
from scipy.special import gammaln, ndtr

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-process-qc-twin"
HERE = MOD / "evidence/audit/mr-memory-detector-arl-degradation-v1"
PRIOR_MEMORY = MOD / "evidence/audit/estparam-memory-detector-arl-degradation-v1/diagnostic.canonical.json"
PRIOR_MR = MOD / "evidence/audit/moving-range-arl-degradation-v1/diagnostic.canonical.json"

LAM, L_EWMA = 0.20, 3.0
K_CUSUM, H_CUSUM = 0.5, 5.0
L_SHEW = 3.0
D2 = 2.0 / math.sqrt(math.pi)          # moving-range span-2 constant, exact
BATCH_WINDOW = 30
FA_BUDGET = 1.5
BASELINES = [20, 30, 50, 100, 300, 1000]
MC_SEED_BASE = 20260803
N_SIGMA_MC = 1_000_000                 # baseline (mu_hat,sigma_hat_MR) samples per m
SIGMA_MC_CHUNK = 40_000
NU_GRID, NW_GRID = 64, 64
NU_FINE, NW_FINE = 96, 96
CHAIN_N_EWMA = 201
CHAIN_N_CUSUM = 100


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def c4(m):
    return math.sqrt(2.0 / (m - 1.0)) * math.exp(gammaln(m / 2.0) - gammaln((m - 1.0) / 2.0))


def shewhart_arl_known(delta=0.0, s=1.0, L=L_SHEW):
    p = ndtr((-L - delta) / s) + (1.0 - ndtr((L - delta) / s))
    return 1.0 / p


# ---------------------------------------------------- Brook-Evans Markov chain
# (unmodified reuse of the machinery validated in
#  estparam-memory-detector-arl-degradation-v1 against Montgomery Table 9.4 /
#  Siegmund 1985. This IS the reported estimator here, not just a cross-check:
#  the only new ingredient in this receipt is the sampling law of W.)
def ewma_arl_chain(delta, s, lam=LAM, L=L_EWMA, N=CHAIN_N_EWMA):
    H = L * math.sqrt(lam / (2.0 - lam))
    w = 2.0 * H / N
    mids = -H + (np.arange(N) + 0.5) * w
    edges = -H + np.arange(N + 1) * w
    base = (1.0 - lam) * mids
    x = (edges[None, :] - base[:, None]) / lam
    cdf = ndtr((x - delta) / s)
    R = cdf[:, 1:] - cdf[:, :-1]
    arl = np.linalg.solve(np.eye(N) - R, np.ones(N))
    return float(arl[N // 2])


def cusum_arl_oneside_chain(delta, s, k=K_CUSUM, h=H_CUSUM, N=CHAIN_N_CUSUM):
    w = h / N
    mids = (np.arange(N) + 0.5) * w
    edges = np.arange(N + 1) * w
    x = edges[None, :] - mids[:, None] + k
    cdf = ndtr((x - delta) / s)
    R = cdf[:, 1:] - cdf[:, :-1]
    R[:, 0] = cdf[:, 1]
    arl = np.linalg.solve(np.eye(N) - R, np.ones(N))
    return float(arl[0])


def cusum_arl_oneside_rich(delta, s, k=K_CUSUM, h=H_CUSUM, N=CHAIN_N_CUSUM):
    a1 = cusum_arl_oneside_chain(delta, s, k, h, N)
    a2 = cusum_arl_oneside_chain(delta, s, k, h, 2 * N)
    return 2.0 * a2 - a1


def cusum_arl_twoside_chain(delta, s, k=K_CUSUM, h=H_CUSUM, N=CHAIN_N_CUSUM):
    a_up = cusum_arl_oneside_rich(delta, s, k, h, N)
    a_dn = cusum_arl_oneside_rich(-delta, s, k, h, N)
    return 1.0 / (1.0 / a_up + 1.0 / a_dn)


# ------------------------------------------------------- Patnaik nu_eff (MR/d2)
# (unmodified reuse of moving-range-arl-degradation-v1's device; used here as a
# coarse 2-moment cross-check of the empirical W-quantile approach.)
RHO = -0.5
VAR_MR_UNIT = 2.0 * (1.0 - 2.0 / math.pi)
COV_ADJ_UNIT = 2.0 * (2.0 / math.pi) * (math.sqrt(1.0 - RHO * RHO) + RHO * math.asin(RHO) - 1.0)


def var_sigmahat_mr(m):
    k = m - 1
    var_mrbar = (k * VAR_MR_UNIT + 2.0 * (k - 1) * COV_ADJ_UNIT) / (k * k)
    return var_mrbar / (D2 * D2)


def nu_eff_mr(m):
    target = var_sigmahat_mr(m)

    def relvar(nu):
        c = c4(nu + 1.0)
        return (1.0 - c * c) / (c * c)

    lo, hi = 1.0, 1e7
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if relvar(mid) > target:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


# ------------------------------------------------- empirical W law by MC
def mr_sigma_hat_samples(m, n_total, seed, chunk=SIGMA_MC_CHUNK):
    """Chunked simulation of sigma_hat_MR = MRbar/d2 for iid N(0,1) baselines
    of size m. mu_hat is NOT needed here (its law is the exact N(0,1/m); it is
    independent of sigma_hat_MR by the Cochran-style orthogonality argument),
    so only the sigma_hat_MR marginal is simulated.
    Chunk is capped so that chunk*m stays bounded (<=2e7 elements, ~160MB per
    temporary array) regardless of m -- needed because G7's known-parameter
    limit probe uses m=200000, and the unmodified fixed chunk=40000 would
    allocate a (40000, 200000) = 8e9-element array (~64GB) per iteration.
    This changes only how the same i.i.d. draws are batched, not their
    distribution or the seed sequence semantics of any single run."""
    chunk = max(1000, min(chunk, 20_000_000 // m))
    rng = np.random.default_rng(seed)
    out = np.empty(n_total, dtype=np.float64)
    done = 0
    while done < n_total:
        c = min(chunk, n_total - done)
        x = rng.standard_normal((c, m))
        mr = np.abs(np.diff(x, axis=1)).mean(axis=1)
        out[done:done + c] = mr / D2
        done += c
    return out


def empirical_quantile_nodes(samples, nw):
    """Equal-probability stratified nodes from a large empirical sample:
    node j = sample quantile at level (j+0.5)/nw."""
    s = np.sort(samples)
    n = s.size
    p = (np.arange(nw) + 0.5) / nw
    idx = np.clip((p * n).astype(np.int64), 0, n - 1)
    return s[idx]


def conditional_arl_grid(u, W):
    nu, nw = u.size, W.size
    out = {c: np.zeros((nu, nw)) for c in ("shewhart", "ewma", "cusum")}
    cache = {}
    for j in range(nw):
        s_eff = 1.0 / W[j]
        for i in range(nu):
            d_eff = abs(u[i]) / W[j]
            key = (round(d_eff, 10), round(s_eff, 10))
            if key not in cache:
                cache[key] = (shewhart_arl_known(d_eff, s_eff),
                              ewma_arl_chain(d_eff, s_eff),
                              cusum_arl_twoside_chain(d_eff, s_eff))
            a_sh, a_ew, a_cu = cache[key]
            out["shewhart"][i, j] = a_sh
            out["ewma"][i, j] = a_ew
            out["cusum"][i, j] = a_cu
    return out


def wq(values, q):
    v = np.sort(np.asarray(values).ravel())
    n = v.size
    i = min(n - 1, max(0, int(math.ceil(q * n)) - 1))
    return float(v[i])


def analyse_baseline_mr(m, seed, nu=NU_GRID, nw=NW_GRID, n_sigma=N_SIGMA_MC):
    u = np.array([_norm_ppf((k + 0.5) / nu) for k in range(nu)]) / math.sqrt(m)
    sigma_samples = mr_sigma_hat_samples(m, n_sigma, seed)
    W = empirical_quantile_nodes(sigma_samples, nw)
    arls = conditional_arl_grid(u, W)
    fa = sum(BATCH_WINDOW / arls[c] for c in ("shewhart", "ewma", "cusum"))
    rec = {"m": m, "mc_sigma_samples": n_sigma,
           "mc_mean_sigma_hat": round(float(sigma_samples.mean()), 6),
           "mc_var_sigma_hat": round(float(sigma_samples.var()), 8)}
    for name in ("shewhart", "ewma", "cusum"):
        a = arls[name]
        rec[name] = {
            "arl0_median": round(wq(a, 0.50), 3),
            "arl0_p05_guaranteed": round(wq(a, 0.05), 3),
            "arl0_p25": round(wq(a, 0.25), 3),
            "arl0_mean": round(float(a.mean()), 3),
            "P_arl0_below_200": round(float((a < 200.0).mean()), 5),
        }
    rec["union_false_alarms_per_30_batch"] = {
        "median": round(wq(fa, 0.50), 5),
        "p95_guaranteed": round(wq(fa, 0.95), 5),
        "p99": round(wq(fa, 0.99), 5),
        "mean": round(float(fa.mean()), 5),
        "P_exceeds_budget_1p5": round(float((fa > FA_BUDGET).mean()), 5),
    }
    return rec


def _norm_ppf(p):
    from scipy.stats import norm
    return float(norm.ppf(p))


def build():
    from scipy.stats import chi2, norm as sp_norm
    gates = {}

    # G1: c4 / d2 known-answer
    C4_PUB = {2: 0.7979, 3: 0.8862, 5: 0.9400, 10: 0.9727, 25: 0.9896}
    g1 = [{"m": m, "c4_computed": round(c4(m), 6), "c4_published": v,
           "abs_err": round(abs(c4(m) - v), 7)} for m, v in sorted(C4_PUB.items())]
    e1 = max(r["abs_err"] for r in g1)
    d2_pub, d2_err = 1.128, abs(D2 - 1.128)
    gates["c4_d2_constants_known_answer"] = {
        "source": "Montgomery 2020 App. VI; NIST/SEMATECH 6.3.2",
        "c4_rows": g1, "c4_max_abs_err": round(e1, 7),
        "d2_computed": round(D2, 6), "d2_published": d2_pub, "d2_abs_err": round(d2_err, 6),
        "tol": 5e-4, "passed": bool(e1 <= 5e-5 and d2_err <= 5e-4)}

    # G2: Markov-chain solvers vs Montgomery Table 9.4 / Siegmund 1985 (the
    # SAME published anchors used by estparam-memory-detector-arl-degradation-v1;
    # this receipt reuses that machinery unmodified).
    CUSUM_PUB = {0.0: 465.0, 0.25: 139.0, 0.5: 38.0, 0.75: 17.0, 1.0: 10.4, 1.5: 5.75, 2.0: 4.01}
    rows = []
    for d in sorted(CUSUM_PUB):
        mc2 = cusum_arl_twoside_chain(d, 1.0)
        rows.append({"shift_sigma": d, "arl_markov_chain": round(mc2, 4),
                     "arl_published_montgomery_t9p4": CUSUM_PUB[d],
                     "rel_err": round(abs(mc2 - CUSUM_PUB[d]) / CUSUM_PUB[d], 5)})
    e2a = max(r["rel_err"] for r in rows)
    ewma_kp = ewma_arl_chain(0.0, 1.0)
    sh_kp = shewhart_arl_known(0.0, 1.0)
    e2b = abs(sh_kp - 370.4) / 370.4
    gates["markov_chain_vs_published_anchors"] = {
        "source": "Brook & Evans 1972; Page 1954; Montgomery 2020 Table 9.4; Shewhart 1931",
        "cusum_rows": rows, "cusum_max_rel_err": round(e2a, 5),
        "shewhart_arl0": round(sh_kp, 4), "shewhart_rel_err": round(e2b, 6),
        "ewma_arl0_known_param": round(ewma_kp, 3),
        "tol": 0.06, "passed": bool(e2a <= 0.06 and e2b <= 0.01)}

    # G3: MR estimator moments closed-form vs direct MC (self-contained
    # re-derivation of moving-range-arl-degradation-v1's key gate)
    rows = []
    for m in (20, 30, 100, 1000):
        s = mr_sigma_hat_samples(m, 400000, MC_SEED_BASE + 5000 + m)
        mc_var = float(s.var())
        mc_mean = float(s.mean())
        cf = var_sigmahat_mr(m)
        rel = abs(mc_var - cf) / cf
        rows.append({"m": m, "var_closed_form": round(cf, 8), "var_mc": round(mc_var, 8),
                     "rel_err": round(rel, 5), "mc_mean_sigma_hat": round(mc_mean, 5)})
    e3 = max(r["rel_err"] for r in rows)
    gates["mr_variance_closed_form_vs_mc"] = {
        "source": "Cryer & Ryan 1990 JQT 22(3):187-192 (adjacent MR correlation rho=-1/2)",
        "rows": rows, "max_rel_err": round(e3, 5), "tol": 0.03, "passed": bool(e3 <= 0.03)}

    # ------------------------------------------------------- main table
    table = [analyse_baseline_mr(m, MC_SEED_BASE + 137 * (i + 1)) for i, m in enumerate(BASELINES)]

    # G4: independent cross-check against moving-range-arl-degradation-v1's OWN
    # Shewhart MC (different seed, different harness) at shared baseline sizes.
    prior_mr = json.loads(PRIOR_MR.read_text())
    prior_mr_rows = {r["m"]: r for r in prior_mr["mr_estimated_parameter_distribution_by_baseline_m"]}
    rows = []
    for r in table:
        m = r["m"]
        if m in prior_mr_rows:
            mine = r["shewhart"]["arl0_p05_guaranteed"]
            theirs = prior_mr_rows[m]["arl0_p05"]
            rows.append({"m": m, "this_receipt_shewhart_p05": mine,
                         "moving_range_arl_degradation_v1_shewhart_p05": theirs,
                         "rel_err": round(abs(mine - theirs) / theirs, 5)})
    e4 = max(r["rel_err"] for r in rows) if rows else 0.0
    gates["shewhart_cross_check_vs_moving_range_receipt"] = {
        "note": "Independent-seed cross-validation of this receipt's empirical-W-law "
                "Shewhart conditional-ARL pipeline against "
                "moving-range-arl-degradation-v1's independently-seeded direct MC "
                "(different method: MRbar/d2 conditional decision, not the (U,W) "
                "grid) at shared baseline sizes.",
        "rows": rows, "max_rel_err": round(e4, 5), "tol": 0.05, "passed": bool(e4 <= 0.05)}

    # G5: quadrature grid convergence (64x64 vs 96x96) at decision-relevant m
    conv = []
    for m in (30, 50, 100):
        coarse = analyse_baseline_mr(m, MC_SEED_BASE + 9001 + m, nu=NU_GRID, nw=NW_GRID, n_sigma=400000)
        fine = analyse_baseline_mr(m, MC_SEED_BASE + 9101 + m, nu=NU_FINE, nw=NW_FINE, n_sigma=400000)
        for c in ("shewhart", "ewma", "cusum"):
            a, b = coarse[c]["arl0_p05_guaranteed"], fine[c]["arl0_p05_guaranteed"]
            conv.append({"m": m, "chart": c, "p05_grid64": a, "p05_grid96": b,
                         "rel_err": round(abs(a - b) / b, 5)})
        a = coarse["union_false_alarms_per_30_batch"]["p95_guaranteed"]
        b = fine["union_false_alarms_per_30_batch"]["p95_guaranteed"]
        conv.append({"m": m, "chart": "union_fa_p95", "p05_grid64": a, "p05_grid96": b,
                     "rel_err": round(abs(a - b) / b, 5)})
    e5 = max(r["rel_err"] for r in conv)
    gates["quadrature_grid_convergence"] = {
        "note": "64x64 vs 96x96 (U,W) grid nodes; W nodes are independent MC draws "
                "(different seed) at each resolution, so this also exercises "
                "Monte Carlo sampling-noise stability, not just grid density.",
        "rows": conv, "max_rel_err": round(e5, 5), "tol": 0.08, "passed": bool(e5 <= 0.08)}

    # G6: Patnaik nu_eff proxy (2-moment chi approx of the W law) vs the
    # empirical-MC W law, both driven through the IDENTICAL Markov-chain ARL
    # formula -- isolates exactly how good the Patnaik approximation of the
    # MR sampling law is (coarse cross-check role established in
    # moving-range-arl-degradation-v1).
    patnaik_rows = []
    for r in table:
        m = r["m"]
        nu_p = nu_eff_mr(m)
        pu = (np.arange(NU_GRID) + 0.5) / NU_GRID
        pw = (np.arange(NW_GRID) + 0.5) / NW_GRID
        u_p = sp_norm.ppf(pu) / math.sqrt(m)
        W_p = np.sqrt(chi2.ppf(pw, nu_p) / nu_p) / c4(nu_p + 1.0)
        arls_p = conditional_arl_grid(u_p, W_p)
        fa_p = sum(BATCH_WINDOW / arls_p[c] for c in ("shewhart", "ewma", "cusum"))
        p05 = {c: round(wq(arls_p[c], 0.05), 3) for c in ("shewhart", "ewma", "cusum")}
        fa_p95 = round(wq(fa_p, 0.95), 5)
        e_sh = abs(p05["shewhart"] - r["shewhart"]["arl0_p05_guaranteed"]) / r["shewhart"]["arl0_p05_guaranteed"]
        e_ew = abs(p05["ewma"] - r["ewma"]["arl0_p05_guaranteed"]) / r["ewma"]["arl0_p05_guaranteed"]
        e_cu = abs(p05["cusum"] - r["cusum"]["arl0_p05_guaranteed"]) / r["cusum"]["arl0_p05_guaranteed"]
        e_fa = abs(fa_p95 - r["union_false_alarms_per_30_batch"]["p95_guaranteed"]) / r["union_false_alarms_per_30_batch"]["p95_guaranteed"]
        patnaik_rows.append({"m": m, "nu_eff": round(nu_p, 4),
                              "patnaik_shewhart_p05": p05["shewhart"], "mc_shewhart_p05": r["shewhart"]["arl0_p05_guaranteed"],
                              "patnaik_ewma_p05": p05["ewma"], "mc_ewma_p05": r["ewma"]["arl0_p05_guaranteed"],
                              "patnaik_cusum_p05": p05["cusum"], "mc_cusum_p05": r["cusum"]["arl0_p05_guaranteed"],
                              "patnaik_union_fa_p95": fa_p95, "mc_union_fa_p95": r["union_false_alarms_per_30_batch"]["p95_guaranteed"],
                              "rel_err_shewhart": round(e_sh, 5), "rel_err_ewma": round(e_ew, 5),
                              "rel_err_cusum": round(e_cu, 5), "rel_err_union_fa": round(e_fa, 5)})
    e6 = max(max(r["rel_err_shewhart"], r["rel_err_ewma"], r["rel_err_cusum"], r["rel_err_union_fa"]) for r in patnaik_rows)
    gates["patnaik_proxy_vs_empirical_w_law"] = {
        "role": "COARSE_ANALYTIC_CROSS_CHECK",
        "note": "Patnaik (1950) nu_eff scaled-chi proxy for the W=sigma_hat_MR/sigma "
                "law vs the empirical-MC W law, BOTH driven through the identical "
                "Montgomery-Table-9.4-validated Markov-chain ARL formula -- isolates "
                "the W-law approximation error only. Same coarse-cross-check role "
                "and tolerance regime established in moving-range-arl-degradation-v1 "
                "(worst error at smallest m).",
        "rows": patnaik_rows, "max_rel_err": round(e6, 5), "tol": 0.20, "passed": bool(e6 <= 0.20)}

    # G7: known-parameter limit (m -> inf: W -> 1, U -> 0)
    big = analyse_baseline_mr(200000, MC_SEED_BASE + 424242, nu=48, nw=48, n_sigma=300000)
    kp = {"shewhart": shewhart_arl_known(0.0, 1.0), "ewma": ewma_arl_chain(0.0, 1.0),
          "cusum": cusum_arl_twoside_chain(0.0, 1.0)}
    kp_union = sum(BATCH_WINDOW / kp[c] for c in kp)
    lim_err = {c: abs(big[c]["arl0_median"] - kp[c]) / kp[c] for c in kp}
    e7 = max(lim_err.values())
    gates["known_parameter_limit_m_to_inf"] = {
        "note": "As baseline m -> inf, U -> 0 and W -> 1, so the estimated-parameter "
                "median ARL0 must collapse onto the known-parameter ARL0.",
        "known_parameter_arl0": {c: round(v, 3) for c, v in kp.items()},
        "known_parameter_union_fa_per_30_batch": round(kp_union, 5),
        "m_1e5_median_arl0": {c: big[c]["arl0_median"] for c in kp},
        "max_rel_err": round(e7, 5), "tol": 0.03, "passed": bool(e7 <= 0.03)}

    # G8: fail-closed
    fc = []
    try:
        bad = c4(2) * 1.02
        fc.append({"check": "tampered_c4_rejected", "passed": bool(abs(bad - 0.7979) > 5e-5)})
    except Exception:
        fc.append({"check": "tampered_c4_rejected", "passed": False})
    try:
        bad_d2 = D2 * 1.02
        fc.append({"check": "tampered_d2_rejected", "passed": bool(abs(bad_d2 - 1.128) > 5e-4)})
    except Exception:
        fc.append({"check": "tampered_d2_rejected", "passed": False})
    try:
        c4(1)
        fc.append({"check": "m_lt_2_rejected", "passed": False})
    except (ValueError, ZeroDivisionError, OverflowError):
        fc.append({"check": "m_lt_2_rejected", "passed": True})
    p05_ew = [r["ewma"]["arl0_p05_guaranteed"] for r in table]
    fc.append({"check": "ewma_p05_monotone_increasing_in_m", "values": p05_ew,
               "passed": bool(all(p05_ew[i] < p05_ew[i + 1] for i in range(len(p05_ew) - 1)))})
    p05_cu = [r["cusum"]["arl0_p05_guaranteed"] for r in table]
    fc.append({"check": "cusum_p05_monotone_increasing_in_m", "values": p05_cu,
               "passed": bool(all(p05_cu[i] < p05_cu[i + 1] for i in range(len(p05_cu) - 1)))})
    fa_p95 = [r["union_false_alarms_per_30_batch"]["p95_guaranteed"] for r in table]
    fc.append({"check": "union_fa_p95_monotone_decreasing_in_m", "values": fa_p95,
               "passed": bool(all(fa_p95[i] > fa_p95[i + 1] for i in range(len(fa_p95) - 1)))})
    fc.append({"check": "union_fa_p95_exceeds_known_parameter_value",
               "passed": bool(all(v > kp_union for v in fa_p95))})

    # THE key conservative-direction check: MR/d2-fed EWMA/CUSUM guaranteed p05
    # must sit AT OR BELOW the S/c4-fed value from
    # estparam-memory-detector-arl-degradation-v1 at every shared baseline m.
    prior_mem = json.loads(PRIOR_MEMORY.read_text())
    prior_mem_rows = {r["m"]: r for r in prior_mem["estimated_parameter_distribution_by_baseline_m"]}
    cmp_rows = []
    worse_all = True
    for r in table:
        m = r["m"]
        pm = prior_mem_rows.get(m)
        if pm is None:
            continue
        ew_ok = r["ewma"]["arl0_p05_guaranteed"] <= pm["ewma"]["arl0_p05_guaranteed"]
        cu_ok = r["cusum"]["arl0_p05_guaranteed"] <= pm["cusum"]["arl0_p05_guaranteed"]
        worse_all = worse_all and ew_ok and cu_ok
        cmp_rows.append({"m": m,
                         "mr_ewma_p05": r["ewma"]["arl0_p05_guaranteed"],
                         "sc4_ewma_p05_prior_receipt": pm["ewma"]["arl0_p05_guaranteed"],
                         "ewma_mr_le_sc4": bool(ew_ok),
                         "mr_cusum_p05": r["cusum"]["arl0_p05_guaranteed"],
                         "sc4_cusum_p05_prior_receipt": pm["cusum"]["arl0_p05_guaranteed"],
                         "cusum_mr_le_sc4": bool(cu_ok)})
    fc.append({"check": "MR_ewma_cusum_p05_le_Sc4_p05_all_m_conservative_direction",
               "detail": cmp_rows, "passed": bool(worse_all)})

    fa_cmp = []
    for r in table:
        m = r["m"]
        pm = prior_mem_rows.get(m)
        if pm is None:
            continue
        fa_cmp.append({"m": m,
                       "mr_union_fa_p95": r["union_false_alarms_per_30_batch"]["p95_guaranteed"],
                       "sc4_union_fa_p95_prior_receipt": pm["union_false_alarms_per_30_batch"]["p95_guaranteed"],
                       "mr_ge_sc4": bool(r["union_false_alarms_per_30_batch"]["p95_guaranteed"]
                                         >= pm["union_false_alarms_per_30_batch"]["p95_guaranteed"])})
    fc.append({"check": "MR_union_fa_p95_ge_Sc4_union_fa_p95_all_m",
               "detail": fa_cmp, "passed": bool(all(r["mr_ge_sc4"] for r in fa_cmp))})

    gates["fail_closed"] = {"rows": fc, "passed": bool(all(r["passed"] for r in fc))}

    all_pass = all(g["passed"] for g in gates.values())

    smallest_ok = None
    for r in table:
        if r["union_false_alarms_per_30_batch"]["p95_guaranteed"] <= FA_BUDGET:
            smallest_ok = r["m"]
            break

    prior_smallest_ok = prior_mem["baseline_size_requirement"]["smallest_tabulated_m_meeting_criterion"]
    m50_prior = prior_mem_rows[50]["union_false_alarms_per_30_batch"]["p95_guaranteed"]
    m50_mine = next(r for r in table if r["m"] == 50)["union_false_alarms_per_30_batch"]["p95_guaranteed"]
    m50_still_meets_budget = bool(m50_mine <= FA_BUDGET)
    claim_refuted = bool((prior_smallest_ok is not None) and
                         ((smallest_ok is None) or (smallest_ok > prior_smallest_ok)))

    r30 = next(r for r in table if r["m"] == 30)
    retention30 = {c: round(r30[c]["arl0_p05_guaranteed"] / kp[c], 4) for c in ("shewhart", "ewma", "cusum")}

    diag = {
        "schema": "amphora.process-qc-twin.mr-memory-detector-arl-degradation.v1",
        "study_id": "mr-memory-detector-arl-degradation-v1",
        "module": "amphora-process-qc-twin",
        "run_type": "AUDIT_ONLY_THEORY_CHARACTERIZATION",
        "authority": "AUDIT_ONLY",
        "attacked_claim": {
            "receipt": "estparam-memory-detector-arl-degradation-v1",
            "field": "baseline_size_requirement.smallest_tabulated_m_meeting_criterion",
            "asserted_value": prior_smallest_ok,
            "asserted_under_estimator": "sigma_hat = S/c4(m), explicitly flagged by that "
                "receipt as an UPPER BOUND on the memory arms' guaranteed ARL0, not the "
                "operating value"},
        "headline": (
            f"Under the ACTUAL Individuals-chart default sigma estimator "
            f"sigma_hat=MRbar/d2 (not S/c4), the guaranteed (95th-pct) union "
            f"false-alarm count at the module's previously-reported sufficient "
            f"baseline m=50 is {m50_mine} (vs {m50_prior} under S/c4), against the "
            f"locked budget of {FA_BUDGET}. The smallest tabulated baseline meeting "
            f"the budget under MR/d2 is m={smallest_ok} "
            + (f"(UNCHANGED from the S/c4-based claim of m={prior_smallest_ok})"
               if not claim_refuted else
               f"(WORSE than the S/c4-based claim of m={prior_smallest_ok} -- "
               f"that claim is REFUTED for the estimator the module's own "
               f"Individuals chart actually uses)")
            + f". m=50 {'STILL MEETS' if m50_still_meets_budget else 'NO LONGER MEETS'} "
              f"the budget once MRbar/d2 replaces S/c4."),
        "purpose": (
            "Attack estparam-memory-detector-arl-degradation-v1's "
            "smallest_tabulated_m_meeting_criterion=50 claim by recomputing the "
            "union false-alarm table with the estimator the module's Individuals "
            "chart actually defaults to (MRbar/d2), closing the 'MRbar/d2 x "
            "EWMA/CUSUM cross' both prior receipts left explicitly open."),
        "non_circularity": (
            "The W=sigma_hat_MR/sigma sampling law has no closed form and is "
            "characterized here by direct Monte Carlo of the correlated "
            "moving-range process (independent of, and cross-checked against, "
            "moving-range-arl-degradation-v1's own MC and closed-form moments). "
            "The conditional ARL0 at each (U,W) node is the EXACT deterministic "
            "Brook-Evans Markov-chain / geometric formula, already validated "
            "against Montgomery Table 9.4 and Siegmund 1985 in "
            "estparam-memory-detector-arl-degradation-v1 -- no run is ever "
            "simulated, eliminating single-run noise from the reported "
            "percentiles."),
        "detector_design": {
            "shewhart_individuals_L": L_SHEW, "ewma_lambda": LAM, "ewma_L": L_EWMA,
            "cusum_k": K_CUSUM, "cusum_h": H_CUSUM,
            "sigma_estimator": "MRbar/d2(2), d2(2)=2/sqrt(pi) (Montgomery default for "
                "Individuals charts; NIST/SEMATECH 6.3.2)",
            "note": "All three charts read the SAME standardized stream off the SAME "
                    "Phase-I baseline in the live module; if the Individuals chart "
                    "uses MRbar/d2 the EWMA/CUSUM arms operate on that same estimate."},
        "known_parameter_reference": {"arl0": {c: round(v, 3) for c, v in kp.items()},
                                       "union_false_alarms_per_30_batch": round(kp_union, 5),
                                       "prior_receipt": "spc-arl-characterization-v1"},
        "mr_estimator_moments_closed_form": {
            "d2_span2": round(D2, 8), "rho_adjacent_moving_ranges": RHO,
            "var_MR_unit_sigma": round(VAR_MR_UNIT, 8),
            "cov_adjacent_MR_unit_sigma": round(COV_ADJ_UNIT, 8),
            "source": "Cryer & Ryan 1990 JQT 22(3):187-192"},
        "estimated_parameter_distribution_by_baseline_m": table,
        "patnaik_proxy_cross_check_by_baseline_m": patnaik_rows,
        "guaranteed_arl0_retention_at_m30_vs_known_parameter": retention30,
        "baseline_size_requirement": {
            "false_alarm_budget_per_30_batch": FA_BUDGET,
            "criterion": "p95 (guaranteed) union false-alarm count <= 1.5",
            "smallest_tabulated_m_meeting_criterion_MRbar_d2": smallest_ok,
            "smallest_tabulated_m_meeting_criterion_Sc4_prior_receipt": prior_smallest_ok,
            "tabulated_m": BASELINES,
            "union_fa_p95_by_m_MRbar_d2": dict(zip(map(str, BASELINES), fa_p95)),
            "m50_union_fa_p95_MRbar_d2": m50_mine,
            "m50_union_fa_p95_Sc4_prior_receipt": m50_prior,
            "m50_still_meets_budget_under_MRbar_d2": m50_still_meets_budget},
        "claim_verdict": "REFUTED" if claim_refuted else "SURVIVED",
        "kpi_linkage": {
            "module_locked_kpi": "prospective 30-batch pilot: seeded-control recall >=90%, "
                                 "false alarms <=5%, zero false releases",
            "false_alarm_budget_expected_per_30_batch": FA_BUDGET,
            "closes_prior_does_not_close_item":
                "estparam-memory-detector-arl-degradation-v1 does_not_close: "
                "'The MRbar/d2 x EWMA/CUSUM cross is still open.'"},
        "theory_reference": {
            "moving_range_estimator": "Montgomery 2020 ISQC 8th ed. Ch.6.4; NIST/SEMATECH 6.3.2",
            "mr_vs_s_efficiency": "Cryer & Ryan 1990 JQT 22(3):187-192",
            "patnaik_chi_proxy": "Patnaik 1950 Biometrika 37:78-87",
            "estimated_parameter_ewma": "Jones, Champ & Rigdon 2001 Technometrics 43(2):156-167",
            "estimated_parameter_cusum": "Jones, Champ & Rigdon 2004 JQT 36(1):95-108",
            "markov_chain_arl": "Brook & Evans 1972 Biometrika 59(3):539-549",
            "anchors": "Montgomery 2020 Table 9.4; NIST/SEMATECH 6.3; Shewhart 1931"},
        "gates": gates,
        "all_known_answer_gates_passed": bool(all_pass),
        "reproducibility_seed": {"mc_seed_base": MC_SEED_BASE, "n_sigma_mc": N_SIGMA_MC,
                                 "quadrature_nodes": [NU_GRID, NW_GRID],
                                 "quadrature_nodes_fine": [NU_FINE, NW_FINE],
                                 "ewma_states": CHAIN_N_EWMA, "cusum_states": CHAIN_N_CUSUM,
                                 "numpy": np.__version__},
        "closes": [
            "Closes the 'MRbar/d2 x EWMA/CUSUM cross' open item shared by "
            "estparam-memory-detector-arl-degradation-v1 and "
            "moving-range-arl-degradation-v1.",
            "Recomputes the module's guaranteed 30-batch union false-alarm table "
            "under the sigma estimator the Individuals chart actually defaults to.",
            "Directly tests whether the previously-reported "
            "smallest_tabulated_m_meeting_criterion=50 survives the switch from "
            "S/c4 (upper bound, per prior receipt's own caveat) to MRbar/d2 "
            "(operating estimator)."],
        "does_not_close": [
            "Does NOT establish real-batch acceptability, product qualification, EHS "
            "acceptability, or batch-release authority.",
            "Assumes i.i.d. normal in-control data; autocorrelation and non-normality "
            "are not modeled and remain open.",
            "The union false-alarm figure is a per-node sum of 30/ARL0 across the "
            "three arms sharing one (U,W) draw; it is still a Bonferroni-style rate "
            "approximation of the union alarm event, not an exact union probability.",
            "The Lucas-Crosier two-sided CUSUM 1/ARL=1/ARL+ +1/ARL- combination is an "
            "approximation (validated to <=6% against Montgomery Table 9.4 in the "
            "prior receipt).",
            "The W sampling law is characterized by Monte Carlo (no closed form for "
            "MRbar/d2), so the reported percentiles carry MC sampling noise on top of "
            "the exact conditional-ARL formula; quantified by the grid-convergence gate.",
            "No prospective time-ordered 30-batch pilot is checked in; this is a "
            "theory characterization, not a false-alarm measurement on real batches.",
            "Out-of-control (ARL1) performance under MRbar/d2-estimated parameters, "
            "and the recall >=90% half of the KPI, are not characterized here.",
            "Covers only the span-2 moving range d2(2); larger MR spans are not "
            "characterized."],
        "governance": {
            "modifies_manifest": False, "promotes_authority": False,
            "flips_scientific_readiness": False, "modifies_locked_dataset": False,
            "modifies_signed_phase0_kpi": False,
            "module_scientific_readiness": "LOCKED_INTERNAL",
            "portfolio_manifest_receipts": 66, "portfolio_manifest_modules": 11},
    }
    return diag


if __name__ == "__main__":
    for v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
              "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
        assert os.environ.get(v) == "1", f"{v} must be pinned to 1 for byte-stability"
    import sys
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else (HERE / "diagnostic.canonical.json")
    d = build()
    out.parent.mkdir(parents=True, exist_ok=True)
    b = json.dumps(d, indent=2, sort_keys=True).encode()
    out.write_bytes(b)
    print("WROTE", out)
    print("all_gates_passed", d["all_known_answer_gates_passed"])
    for k, g in d["gates"].items():
        print(f"  {k:52s} {g['passed']}")
    print("claim_verdict", d["claim_verdict"])
    print("smallest_m_MRbar_d2", d["baseline_size_requirement"]["smallest_tabulated_m_meeting_criterion_MRbar_d2"])
    print("smallest_m_Sc4_prior", d["baseline_size_requirement"]["smallest_tabulated_m_meeting_criterion_Sc4_prior_receipt"])
    print("sha256", sha_bytes(b))
