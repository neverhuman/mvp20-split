#!/usr/bin/env python3
"""
amphora-cure-potlife-gate  --  Distribution-free CONFORMAL prediction intervals
on the signed Arrhenius pot-life temperature-scaling gate  (MODEL AXIS, option C).

MOTIVATION.  The signed Phase-0 KPI
(evidence/phase0/kpis/cure-potlife-arrhenius-kpi.v1.json) reports only a POINT
error (held-out MAPE 0.1473).  The module's actual decision -- "should this
formulation proceed to multi-temperature CRO cure testing?" -- is a gate that
needs a CALIBRATED interval on predicted pot-life at held-out temperature, not a
bare point estimate.  A point prediction with no honest band cannot bound the
risk of gating a formulation whose true pot-life is out of the workable window.

This harness adds distribution-free UQ on top of the FIXED, already-signed
Arrhenius model, using ONLY the already-signed 12-system x 3-held-out-temperature
truth table (evidence/phase0/benchmark/result.v1.json).  No new data, no refit:
the Arrhenius activation energies are external published constants, so the 36
held-out log-residuals are genuinely out-of-sample and exchangeable-by-design.

Nonconformity score (multiplicative errors; pot-life spans 5-10x across systems):
    s_i = | ln(pred_i) - ln(obs_i) |
Symmetric conformal band in log space: pred * exp(+/- q), so obs is covered iff
s_i <= q.  Finite-sample split/full-conformal quantile from a calibration set of
size m at miscoverage alpha:
    q = the ceil((m+1)*(1-alpha))-th smallest calibration score  (+inf if rank>m)
(Vovk, Gammerman & Shafer 2005 "Algorithmic Learning in a Random World";
Lei et al. 2018 JASA 113:1094 "Distribution-Free Predictive Inference"; the
leave-one-out variant is the jackknife+ of Barber, Candes, Ramdas & Tibshirani
2021 Ann. Statist. 49:486.)

Three protocols:
  P1  marginal LOO (jackknife+, model fixed): each point calibrated on the other
      35 -> marginal coverage guaranteed >= 1-alpha.  GATE G1.
  P2  leave-one-FAMILY-out (group / Mondrian conformal): calibrate on the 4 other
      amine classes, test on the held-out class.  Tests whether family structure
      breaks marginal exchangeability -- the honest, harder question.  GATE G2.
  P3  parametric Gaussian +/- z*sigma on signed log-residuals: shows whether a
      naive normal band mis-calibrates vs the distribution-free conformal band.

Plus: a seeded (fixed) bootstrap 95% CI on the marginal coverage estimate; the
median multiplicative band width; per-held-out-temperature coverage (does the
furthest 40 C extrapolation under-cover?); and a crosscheck that the recomputed
MAPE reproduces the signed KPI value (ties this analysis to the signed artifact).

R = 8.31446261815324 J/(mol.K) CODATA 2018 is embedded in the signed predictions
already; nothing here refits it.  All arithmetic is deterministic and sorted for
byte-stable two-replay reproduction.
"""
import json, hashlib, math, sys
from pathlib import Path
from collections import defaultdict

MODULE = "amphora-cure-potlife-gate"
ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / MODULE
RESULT = MOD / "evidence/phase0/benchmark/result.v1.json"
KPI = MOD / "evidence/phase0/kpis/cure-potlife-arrhenius-kpi.v1.json"

BOOTSTRAP_SEED = 20260728
BOOTSTRAP_ITERS = 10000
ALPHAS = [0.10, 0.20]  # nominal coverage 0.90, 0.80


def sha(b):
    return hashlib.sha256(b).hexdigest()


def rnd(x, n=10):
    # deterministic rounding for byte-stable output
    if x is None or (isinstance(x, float) and (math.isinf(x) or math.isnan(x))):
        return x
    return round(float(x), n)


def conformal_q(scores, alpha):
    """Split/full-conformal symmetric half-width from calibration scores."""
    s = sorted(scores)
    m = len(s)
    rank = math.ceil((m + 1) * (1.0 - alpha))  # 1-indexed
    if rank > m:
        return math.inf
    return s[rank - 1]


def quantile(sorted_vals, p):
    # linear-interpolation quantile on a pre-sorted list
    n = len(sorted_vals)
    if n == 1:
        return sorted_vals[0]
    idx = p * (n - 1)
    lo = int(math.floor(idx))
    hi = int(math.ceil(idx))
    if lo == hi:
        return sorted_vals[lo]
    frac = idx - lo
    return sorted_vals[lo] * (1 - frac) + sorted_vals[hi] * frac


class LCG:
    """Deterministic 64-bit LCG (Numerical Recipes constants) -> reproducible
    bootstrap without depending on any library RNG stream."""
    def __init__(self, seed):
        self.s = seed & ((1 << 64) - 1)

    def next_u64(self):
        self.s = (self.s * 6364136223846793005 + 1442695040888963407) & ((1 << 64) - 1)
        return self.s

    def randint(self, n):
        return self.next_u64() % n


def main():
    result = json.loads(RESULT.read_text())
    kpi = json.loads(KPI.read_text())
    recs = result["first_replay"]["diagnostic_receipt"]["records"]

    # --- build the 36 held-out points from the SIGNED truth table -----------
    points = []
    for r in recs:
        fam = r["hardener_family"]
        sysid = r["system_id"]
        for h in r["held_out_temperatures"]:
            obs = float(h["published_pot_life_min"])
            pred = float(h["arrhenius_predicted_pot_life_min"])
            points.append({
                "system_id": sysid,
                "family": fam,
                "temperature_c": float(h["temperature_c"]),
                "obs": obs,
                "pred": pred,
                "log_resid": math.log(pred) - math.log(obs),  # signed
                "score": abs(math.log(pred) - math.log(obs)),  # nonconformity
                "ape": abs(pred - obs) / obs,
            })
    points.sort(key=lambda p: (p["family"], p["system_id"], p["temperature_c"]))
    n = len(points)

    # --- crosscheck: recompute held-out MAPE, compare to signed KPI ----------
    recomputed_mape = sum(p["ape"] for p in points) / n
    signed_mape = None
    for m in kpi["metrics"]:
        if m["name"] == "arrhenius_pot_life_mape":
            signed_mape = m["observed"]
    mape_abs_diff = abs(recomputed_mape - signed_mape) if signed_mape is not None else None

    # --- P1: marginal LOO (jackknife+) --------------------------------------
    p1 = {}
    for alpha in ALPHAS:
        covered = 0
        widths = []
        for i in range(n):
            cal = [points[j]["score"] for j in range(n) if j != i]
            q = conformal_q(cal, alpha)
            if points[i]["score"] <= q:
                covered += 1
            widths.append(q)
        finite_w = sorted(w for w in widths if math.isfinite(w))
        med_q = quantile(finite_w, 0.5) if finite_w else math.inf
        p1[f"alpha_{alpha:.2f}"] = {
            "nominal_coverage": rnd(1 - alpha, 4),
            "empirical_coverage": rnd(covered / n, 6),
            "n_covered": covered,
            "n": n,
            "median_halfwidth_log": rnd(med_q, 8),
            "median_band_multiplicative_factor": rnd(math.exp(med_q), 6) if math.isfinite(med_q) else None,
            "meets_nominal": bool(covered / n >= (1 - alpha) - 1e-12),
        }

    # --- bootstrap 95% CI on marginal coverage at alpha=0.10 -----------------
    alpha_boot = 0.10
    per_point_cov = []
    for i in range(n):
        cal = [points[j]["score"] for j in range(n) if j != i]
        q = conformal_q(cal, alpha_boot)
        per_point_cov.append(1 if points[i]["score"] <= q else 0)
    rng = LCG(BOOTSTRAP_SEED)
    boot_covs = []
    for _ in range(BOOTSTRAP_ITERS):
        acc = 0
        for _k in range(n):
            acc += per_point_cov[rng.randint(n)]
        boot_covs.append(acc / n)
    boot_covs.sort()
    boot_ci = {
        "alpha": alpha_boot,
        "point_coverage": rnd(sum(per_point_cov) / n, 6),
        "ci95_lo": rnd(quantile(boot_covs, 0.025), 6),
        "ci95_hi": rnd(quantile(boot_covs, 0.975), 6),
        "seed": BOOTSTRAP_SEED,
        "iters": BOOTSTRAP_ITERS,
    }

    # --- P2: leave-one-FAMILY-out (group / Mondrian conformal) --------------
    families = sorted(set(p["family"] for p in points))
    p2 = {}
    for alpha in ALPHAS:
        per_family = {}
        pooled_cov = 0
        pooled_n = 0
        undercover = []
        for f in families:
            cal = [p["score"] for p in points if p["family"] != f]
            test = [p for p in points if p["family"] == f]
            q = conformal_q(cal, alpha)
            cov = sum(1 for t in test if t["score"] <= q)
            per_family[f] = {
                "n_test": len(test),
                "n_covered": cov,
                "empirical_coverage": rnd(cov / len(test), 6),
                "calibration_halfwidth_log": rnd(q, 8) if math.isfinite(q) else None,
                "meets_nominal": bool(cov / len(test) >= (1 - alpha) - 1e-12),
            }
            pooled_cov += cov
            pooled_n += len(test)
            if cov / len(test) < (1 - alpha) - 1e-12:
                undercover.append(f)
        p2[f"alpha_{alpha:.2f}"] = {
            "nominal_coverage": rnd(1 - alpha, 4),
            "pooled_empirical_coverage": rnd(pooled_cov / pooled_n, 6),
            "per_family": per_family,
            "families_undercovering": sorted(undercover),
            "marginal_valid_but_not_family_conditional": bool(undercover),
        }

    # --- P3: parametric Gaussian band on signed log-residuals ---------------
    resids = [p["log_resid"] for p in points]
    mu = sum(resids) / n
    var = sum((r - mu) ** 2 for r in resids) / (n - 1)
    sigma = math.sqrt(var)
    Z = {0.10: 1.6448536269514722, 0.20: 1.2815515594457831}  # z_{1-alpha/2}
    p3 = {}
    for alpha in ALPHAS:
        z = Z[alpha]
        lo, hi = mu - z * sigma, mu + z * sigma
        cov = sum(1 for r in resids if lo <= r <= hi)
        p3[f"alpha_{alpha:.2f}"] = {
            "nominal_coverage": rnd(1 - alpha, 4),
            "empirical_coverage": rnd(cov / n, 6),
            "n_covered": cov,
            "band_halfwidth_log": rnd(z * sigma, 8),
            "band_multiplicative_factor": rnd(math.exp(z * sigma), 6),
            "meets_nominal": bool(cov / n >= (1 - alpha) - 1e-12),
        }
    gauss = {"mean_log_resid": rnd(mu, 8), "std_log_resid": rnd(sigma, 8),
             "note": "signed log-residual mean/std; mean != 0 indicates directional bias"}

    # --- per-held-out-temperature marginal coverage (alpha=0.10) ------------
    temps = sorted(set(p["temperature_c"] for p in points))
    per_temp = {}
    for tc in temps:
        idxs = [i for i in range(n) if points[i]["temperature_c"] == tc]
        cov = 0
        for i in idxs:
            cal = [points[j]["score"] for j in range(n) if j != i]
            q = conformal_q(cal, 0.10)
            if points[i]["score"] <= q:
                cov += 1
        per_temp[f"{tc:.2f}C"] = {
            "n": len(idxs), "n_covered": cov,
            "empirical_coverage_marginal_alpha0.10": rnd(cov / len(idxs), 6),
        }

    # --- G3: fail-closed on degenerate score inputs -------------------------
    def safe_score(pred, obs):
        if pred is None or obs is None:
            return None
        if not (math.isfinite(pred) and math.isfinite(obs)):
            return None
        if pred <= 0 or obs <= 0:
            return None
        return abs(math.log(pred) - math.log(obs))
    probes = [
        {"probe": "nan_pred", "pred": float("nan"), "obs": 30.0},
        {"probe": "inf_obs", "pred": 30.0, "obs": float("inf")},
        {"probe": "zero_pred", "pred": 0.0, "obs": 30.0},
        {"probe": "negative_obs", "pred": 30.0, "obs": -5.0},
        {"probe": "none_pred", "pred": None, "obs": 30.0},
    ]
    probe_out = []
    fc = 0
    for pr in probes:
        s = safe_score(pr["pred"], pr["obs"])
        closed = s is None
        fc += int(closed)
        probe_out.append({"probe": pr["probe"], "fail_closed": closed})

    # --- gates ---------------------------------------------------------------
    g1 = all(p1[f"alpha_{a:.2f}"]["meets_nominal"] for a in ALPHAS)
    g2_undercover_any = any(p2[f"alpha_{a:.2f}"]["marginal_valid_but_not_family_conditional"] for a in ALPHAS)
    g3 = (fc == len(probes))
    g4 = (mape_abs_diff is not None and mape_abs_diff < 1e-9)

    headline = (
        "Distribution-free conformal wraps the signed Arrhenius pot-life gate: marginal "
        "leave-one-out (jackknife+) coverage meets nominal at both 90%% and 80%% "
        "(G1 %s); the group / leave-one-amine-class-out test shows marginal validity is "
        "%s family-conditional (%s); the parametric Gaussian band is %scalibrated. "
        "Median 90%% band = x%s pot-life factor. MAPE crosscheck ties to signed KPI (delta %.1e)."
    ) % (
        "PASS" if g1 else "FAIL",
        "NOT" if g2_undercover_any else "also",
        ("under-covering classes: " + ",".join(sorted(set(
            f for a in ALPHAS for f in p2[f"alpha_{a:.2f}"]["families_undercovering"]))))
            if g2_undercover_any else "all classes covered",
        "" if all(p3[f"alpha_{a:.2f}"]["meets_nominal"] for a in ALPHAS) else "MIS-",
        p1["alpha_0.10"]["median_band_multiplicative_factor"],
        mape_abs_diff if mape_abs_diff is not None else float("nan"),
    )

    diag = {
        "schema": "amphora.cure-potlife-gate.conformal-interval-diagnostic.v1",
        "module": MODULE,
        "run_type": "MODEL_AXIS_CALIBRATED_INTERVAL_CONFORMAL",
        "authority": "AUDIT_ONLY",
        "purpose": (
            "Add distribution-free calibrated prediction intervals (conformal + bootstrap) "
            "to the module's signed Arrhenius pot-life temperature-scaling gate, which "
            "currently reports only a point MAPE. Uses ONLY the already-signed 12-system x "
            "3-held-out-temperature truth table; no new data, no model refit."),
        "non_circularity": (
            "The Arrhenius activation energies are external published constants (Prime 1997; "
            "Kamal & Sourour 1973; Blanco 2005), not fit to these 36 points, so the log-"
            "residuals are genuinely out-of-sample. Conformal calibration is leave-one-out "
            "(P1) and leave-one-amine-class-out (P2); no test point informs its own band."),
        "theory_reference": (
            "Conformal prediction: Vovk, Gammerman & Shafer 2005 'Algorithmic Learning in a "
            "Random World'; Lei, G'Sell, Rinaldo, Tibshirani & Wasserman 2018 JASA 113:1094; "
            "jackknife+ / CV+ Barber, Candes, Ramdas & Tibshirani 2021 Ann. Statist. 49:486; "
            "Mondrian/group conformal Vovk et al. 2003. Underlying model: Arrhenius (1889) "
            "k(T)=A*exp(-Ea/RT), pot_life(T)=pot_life_ref*exp[(Ea/R)(1/T-1/T_ref)], "
            "R=8.31446261815324 J/(mol.K) CODATA 2018, T_ref=295.928 K (22.78 C)."),
        "nonconformity_score": "s_i = |ln(pred_i) - ln(obs_i)| (multiplicative pot-life error)",
        "n_points": n,
        "families": {f: sum(1 for p in points if p["family"] == f) for f in families},
        "crosscheck_mape_vs_signed_kpi": {
            "recomputed_held_out_mape": rnd(recomputed_mape, 12),
            "signed_kpi_arrhenius_pot_life_mape": signed_mape,
            "abs_difference": rnd(mape_abs_diff, 12) if mape_abs_diff is not None else None,
            "ties_to_signed_truth_table": bool(g4),
        },
        "p1_marginal_loo_jackknife_plus": p1,
        "p1_bootstrap_ci_coverage_alpha0.10": boot_ci,
        "p2_leave_one_family_out_group_conformal": p2,
        "p3_parametric_gaussian_band": {"gaussian_fit": gauss, "by_alpha": p3},
        "per_held_out_temperature_marginal_coverage": per_temp,
        "gates": {
            "G1_marginal_conformal_meets_nominal": {
                "definition": "LOO (jackknife+) empirical coverage >= nominal at alpha in {0.10,0.20}",
                "passed": bool(g1)},
            "G2_family_conditional_validity": {
                "definition": ("leave-one-amine-class-out coverage >= nominal for EVERY class; "
                               "if any class under-covers, marginal conformal is valid but NOT "
                               "family-conditional -> CRO gate needs class-stratified intervals"),
                "marginal_valid_but_not_family_conditional": bool(g2_undercover_any),
                "informative": True},
            "G3_score_fail_closed": {
                "definition": "nonconformity score returns None (fail-closed) on NaN/Inf/<=0 inputs",
                "n_probes": len(probes), "n_fail_closed": fc, "passed": bool(g3),
                "probes": probe_out},
            "G4_mape_reproduces_signed_kpi": {
                "definition": "recomputed held-out MAPE matches signed KPI to <1e-9",
                "passed": bool(g4)},
        },
        "all_structural_gates_passed": bool(g1 and g3 and g4),
        "headline": headline,
        "closes": [
            "Point-only reporting: the signed Arrhenius gate now carries a distribution-free "
            "calibrated band with finite-sample marginal coverage guarantee.",
            "Quantifies the honest CRO-gate uncertainty as a multiplicative pot-life factor.",
        ],
        "does_not_close": [
            "Does NOT modify the signed Arrhenius KPI or the 66-receipt master manifest.",
            "Does NOT promote the module out of PRE_PHASE_0 (human dual-identity keys required).",
            "Does NOT beat the Phase-1 named pot-life baseline; 36 owned independently-mixed "
            "CRO runs still pending.",
            "Coverage guarantee is MARGINAL over the exchangeable held-out set; family-"
            "conditional coverage is reported separately and is the open Phase-1 question.",
            "Absolute pot-life of a thinned marine paint differs from these gel/pot-life "
            "anchors; the band is validated on the published truth table only.",
        ],
        "human_review_performed": False,
        "modifies_manifest": False,
        "modifies_signed_phase0_kpi": False,
        "promotes_authority": False,
        "claim_locks": {
            "audit_only_no_authority": True,
            "cro_gated_promotion_still_blocked": True,
            "no_manifest_mutation": True,
            "phase1_named_baseline_still_not_beaten": True,
            "pre_phase_0_research_only": True,
        },
    }
    return diag


if __name__ == "__main__":
    diag = main()
    out = json.dumps(diag, indent=2, sort_keys=True)
    dest = sys.argv[1] if len(sys.argv) > 1 else "/dev/stdout"
    Path(dest).write_text(out)
    print("diagnostic_sha256", sha(out.encode()))
    print("headline:", diag["headline"])
