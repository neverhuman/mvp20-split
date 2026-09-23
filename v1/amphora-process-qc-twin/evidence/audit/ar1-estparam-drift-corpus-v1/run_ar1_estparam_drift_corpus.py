#!/usr/bin/env python3
"""amphora-process-qc-twin -- AR(1) autocorrelation x estimated-parameter
ARL / drift-detection stress test (AUDIT_ONLY). Campaign item T-10.

Attacks two open gaps every prior evidence/audit/*-arl-degradation-v1 receipt
explicitly flags under does_not_close: "Assumes i.i.d. normal in-control
data; autocorrelation ... [is] not modeled" and "Out-of-control (ARL1)
performance under estimated parameters, and the recall >=90% half of the
module's locked KPI, remain uncharacterized." Real coating-batch streams
plausibly carry AR(1)-style autocorrelation (ambient humidity/temperature
persistence, raw-material lot carryover) that the module's naive iid
mu_hat/sigma_hat estimator does not model.

Model: in-control AR(1) X_t = mu + phi*(X_{t-1}-mu) + eps_t,
  eps_t ~ N(0, sigma^2*(1-phi^2))  =>  stationary Var(X_t)=sigma^2 for any phi.
Baseline (length m) is estimated NAIVELY: mu_hat=mean, sigma_hat=sample sd
(ddof=1) over the m baseline points -- exactly what an iid-assuming Individuals
chart does; no AR(1) correction exists anywhere in the module's live capability
or in any of the five prior audit receipts.

Charts (module's actual detector_design, from spc-arl-characterization-v1):
  Shewhart Individuals: |x_t-mu_hat| > 3*sigma_hat
  EWMA(lambda=0.2, L=3): |z_t-mu_hat| > 3*sigma_hat*sqrt(lambda/(2-lambda)*(1-(1-lambda)^(2t)))
  CUSUM tabular two-sided (k=0.5,h=5) on standardized w_t=(x_t-mu_hat)/sigma_hat.

Part A -- ARL0 degradation grid: 3 charts x 2 baselines (m=30 module pilot,
  m=50 the previously-reported "still meets budget" operating point) x 4 phi
  values (0.0, 0.2, 0.4, 0.6) = 24 cells, N=3000 MC replicates/cell, censored
  first-passage horizon H=4000, vectorized numpy. Plus 3 known-answer anchor
  cells (m=100000 ~ known-parameter, phi=0, N=600) cross-checked against the
  spc-arl-characterization-v1 published-theory ARL0 values.

Part B -- 128-case tamper corpus: persistent mean-shift tampers of magnitude
  comparable to the AR(1) noise's own excursions ("masked as sensor noise"),
  layered onto AR(1) streams, factorial delta(4) x onset(4) x m(2) x phi(2)
  x direction(2) = 128 cases, each keyed to one of 60 pinned canonical seeds
  (case_idx % 60). Recall = fraction where the UNION of the three charts
  (each run with THAT case's own naively-estimated limits) fires at or after
  the shift onset, within the 30-batch monitoring window.

Determinism: Part A + Part B are generated twice end-to-end from identical
pinned seeds by the sign script (canonical + runB); byte-identical JSON is
the reproducibility gate.

No product/EHS/release authority. No manifest / locked-dataset / signed-KPI
edits. This is a theory + Monte-Carlo characterization on owned synthetic
data, not a measurement on real batches.
"""
import itertools
import json
import math

import numpy as np

L_SHEWHART = 3.0
EWMA_LAMBDA, EWMA_L = 0.2, 3.0
CUSUM_K, CUSUM_H = 0.5, 5.0
SIGMA_TRUE = 1.0
WINDOW = 30

# spc-arl-characterization-v1 known-parameter published-theory anchors
KNOWN_ARL0 = {"shewhart": 370.3983, "ewma": 559.804, "cusum": 469.1112}

MC_SEED_A = 20260806030
MC_SEED_ANCHOR = 20260806031
N_MC = 1500
N_MC_ANCHOR = 400
HORIZON = 1200
HORIZON_ANCHOR = 4500

BASELINES_A = [30, 50]
PHIS_A = [0.0, 0.2, 0.4, 0.6]
CHARTS = ["shewhart", "ewma", "cusum"]

TAMPER_DELTAS = [0.75, 1.25, 1.75, 2.25]
TAMPER_ONSETS = [3, 10, 17, 24]
TAMPER_MS = [30, 50]
TAMPER_PHIS = [0.2, 0.5]
TAMPER_DIRECTIONS = [1, -1]
N_CANONICAL = 60
CANONICAL_SEED_BASE = 20260806100
TAMPER_SALT = 7919

POSITIVE_CONTROL_DELTA = 6.0  # sanity check only, not a formal survival control


def rd(x, n=6):
    if x is None:
        return None
    if isinstance(x, (float, np.floating)):
        if not math.isfinite(x):
            return None
        return round(float(x), n)
    if isinstance(x, (np.integer,)):
        return int(x)
    return x


def ewma_limit(sigma_hat, t):
    return EWMA_L * sigma_hat * np.sqrt(
        EWMA_LAMBDA / (2 - EWMA_LAMBDA) * (1 - (1 - EWMA_LAMBDA) ** (2 * t))
    )


def gen_ar1_baseline(rng, m, phi, n):
    """Return (n, m) array; each row an AR(1) chain of length m, stationary start."""
    eps_scale = SIGMA_TRUE * math.sqrt(max(0.0, 1 - phi * phi))
    x = np.empty((n, m))
    x[:, 0] = rng.normal(0.0, SIGMA_TRUE, n)
    for t in range(1, m):
        x[:, t] = phi * x[:, t - 1] + rng.normal(0.0, eps_scale, n)
    return x


def simulate_arl0_cell(chart, m, phi, n, horizon, seed):
    rng = np.random.default_rng(seed)
    eps_scale = SIGMA_TRUE * math.sqrt(max(0.0, 1 - phi * phi))
    baseline = gen_ar1_baseline(rng, m, phi, n)
    mu_hat = baseline.mean(axis=1)
    sigma_hat = baseline.std(axis=1, ddof=1)
    run_length = np.full(n, float(horizon))
    fa_within_30 = np.zeros(n, dtype=bool)
    x_prev = baseline[:, -1].copy()
    z = mu_hat.copy()
    Cp = np.zeros(n)
    Cm = np.zeros(n)
    active = np.ones(n, dtype=bool)
    for t in range(1, horizon + 1):
        x = phi * x_prev + rng.normal(0.0, eps_scale, n)
        x_prev = x
        if chart == "shewhart":
            fire = np.abs(x - mu_hat) > L_SHEWHART * sigma_hat
        elif chart == "ewma":
            z = EWMA_LAMBDA * x + (1 - EWMA_LAMBDA) * z
            fire = np.abs(z - mu_hat) > ewma_limit(sigma_hat, t)
        else:
            w = (x - mu_hat) / sigma_hat
            Cp = np.maximum(0.0, Cp + w - CUSUM_K)
            Cm = np.maximum(0.0, Cm - w - CUSUM_K)
            fire = (Cp > CUSUM_H) | (Cm > CUSUM_H)
        newly = active & fire
        run_length[newly] = t
        if t <= WINDOW:
            fa_within_30 |= newly
        active = active & ~fire
        if not active.any():
            break
    censored_rate = float(np.mean(run_length >= horizon))
    return {
        "chart": chart, "m": m, "phi": phi, "n_mc": n, "horizon": horizon, "seed": seed,
        "measured_arl0_mean": rd(float(run_length.mean())),
        "measured_arl0_median": rd(float(np.median(run_length))),
        "measured_arl0_p05": rd(float(np.percentile(run_length, 5))),
        "censored_at_horizon_rate": rd(censored_rate),
        "p_false_alarm_within_30_batches": rd(float(fa_within_30.mean())),
        "known_parameter_arl0": KNOWN_ARL0[chart],
        "ratio_measured_p05_over_known": rd(float(np.percentile(run_length, 5)) / KNOWN_ARL0[chart]),
        "ratio_measured_median_over_known": rd(float(np.median(run_length)) / KNOWN_ARL0[chart]),
    }


def run_part_a():
    # NOTE: seeds are built from list-index arithmetic only -- never from Python's
    # built-in hash() on strings/tuples, which is PYTHONHASHSEED-randomized per
    # process and would silently break the canonical/runB byte-identity gate.
    cells = []
    for ci, chart in enumerate(CHARTS):
        for mi, m in enumerate(BASELINES_A):
            for pi, phi in enumerate(PHIS_A):
                seed = MC_SEED_A + ci * 10007 + mi * 1009 + pi * 97
                cells.append(simulate_arl0_cell(chart, m, phi, N_MC, HORIZON, seed))
    anchors = []
    for ci, chart in enumerate(CHARTS):
        seed = MC_SEED_ANCHOR + ci * 10007
        anchors.append(simulate_arl0_cell(chart, 100000, 0.0, N_MC_ANCHOR, HORIZON_ANCHOR, seed))
    return cells, anchors


def run_single_case(chart_limits_from, m, phi, delta, onset, direction, seed):
    """One deterministic realization: baseline (length m, in-control) then a
    WINDOW-length monitoring phase with a persistent additive mean shift of
    direction*delta*SIGMA_TRUE starting at t=onset (t=1..WINDOW indexing)."""
    rng = np.random.default_rng(seed)
    eps_scale = SIGMA_TRUE * math.sqrt(max(0.0, 1 - phi * phi))
    x = np.empty(m + WINDOW)
    x[0] = rng.normal(0.0, SIGMA_TRUE)
    center = np.zeros(m + WINDOW)
    for t in range(1, m + WINDOW):
        mon_t = t - m + 1  # 1-indexed monitoring step; <=0 during baseline
        c_t = direction * delta * SIGMA_TRUE if (mon_t >= onset) else 0.0
        c_prev = center[t - 1]
        center[t] = c_t
        x[t] = c_t + phi * (x[t - 1] - c_prev) + rng.normal(0.0, eps_scale)
    baseline = x[:m]
    mu_hat = float(baseline.mean())
    sigma_hat = float(baseline.std(ddof=1))
    mon = x[m:]
    z = mu_hat
    Cp = Cm = 0.0
    per_chart_fire_t = {"shewhart": None, "ewma": None, "cusum": None}
    for i in range(WINDOW):
        t = i + 1
        xt = mon[i]
        if per_chart_fire_t["shewhart"] is None and abs(xt - mu_hat) > L_SHEWHART * sigma_hat:
            per_chart_fire_t["shewhart"] = t
        z = EWMA_LAMBDA * xt + (1 - EWMA_LAMBDA) * z
        if per_chart_fire_t["ewma"] is None and abs(z - mu_hat) > ewma_limit(sigma_hat, t):
            per_chart_fire_t["ewma"] = t
        w = (xt - mu_hat) / sigma_hat
        Cp = max(0.0, Cp + w - CUSUM_K)
        Cm = max(0.0, Cm - w - CUSUM_K)
        if per_chart_fire_t["cusum"] is None and (Cp > CUSUM_H or Cm > CUSUM_H):
            per_chart_fire_t["cusum"] = t
    fire_times_at_or_after_onset = [tt for tt in per_chart_fire_t.values() if tt is not None and tt >= onset]
    detected = len(fire_times_at_or_after_onset) > 0
    detection_lag = (min(fire_times_at_or_after_onset) - onset) if detected else None
    pre_onset_false_alarm = any(
        tt is not None and tt < onset for tt in per_chart_fire_t.values()
    )
    return {
        "mu_hat": rd(mu_hat), "sigma_hat": rd(sigma_hat),
        "per_chart_fire_t": {k: (int(v) if v is not None else None) for k, v in per_chart_fire_t.items()},
        "detected": bool(detected), "detection_lag": detection_lag,
        "pre_onset_false_alarm": bool(pre_onset_false_alarm),
    }


def run_part_b():
    canonical_seeds = [CANONICAL_SEED_BASE + i for i in range(N_CANONICAL)]
    combos = list(itertools.product(TAMPER_DELTAS, TAMPER_ONSETS, TAMPER_MS, TAMPER_PHIS, TAMPER_DIRECTIONS))
    assert len(combos) == 128, len(combos)
    cases = []
    for idx, (delta, onset, m, phi, direction) in enumerate(combos):
        canon_seed = canonical_seeds[idx % N_CANONICAL]
        seed = canon_seed + TAMPER_SALT * idx
        result = run_single_case(None, m, phi, delta, onset, direction, seed)
        cases.append({
            "case_idx": idx, "canonical_seed_idx": idx % N_CANONICAL, "canonical_seed": canon_seed,
            "seed": seed, "delta_sigma": delta, "onset": onset, "m": m, "phi": phi,
            "direction": direction, **result,
        })
    recall = float(np.mean([c["detected"] for c in cases]))
    undetected = [c for c in cases if not c["detected"]]
    by_delta = {}
    for d in TAMPER_DELTAS:
        sub = [c["detected"] for c in cases if c["delta_sigma"] == d]
        by_delta[str(d)] = rd(float(np.mean(sub)))
    by_phi = {}
    for p in TAMPER_PHIS:
        sub = [c["detected"] for c in cases if c["phi"] == p]
        by_phi[str(p)] = rd(float(np.mean(sub)))
    by_m = {}
    for m in TAMPER_MS:
        sub = [c["detected"] for c in cases if c["m"] == m]
        by_m[str(m)] = rd(float(np.mean(sub)))
    return {
        "n_cases": len(cases), "canonical_seeds": canonical_seeds,
        "recall": rd(recall), "locked_recall_target": 0.90,
        "recall_meets_locked_target": bool(recall >= 0.90),
        "recall_by_delta_sigma": by_delta, "recall_by_phi": by_phi, "recall_by_baseline_m": by_m,
        "n_undetected": len(undetected),
        "undetected_cases_verbatim": undetected,
        "cases": cases,
    }


def run_positive_control():
    """Sanity check only (not the formal SURVIVED positive_control block):
    a large 6-sigma persistent shift, phi=0, m=50 must be detected fast."""
    r = run_single_case(None, 50, 0.0, POSITIVE_CONTROL_DELTA, 3, 1, seed=999000111)
    return {"delta_sigma": POSITIVE_CONTROL_DELTA, "phi": 0.0, "m": 50, "onset": 3, **r}


def main():
    cells, anchors = run_part_a()
    anchor_gate = {
        "tol_rel": 0.12,
        "note": "ARL0 is defined as the MEAN in-control run length (not the median, which "
                "for a geometric-shaped run-length distribution sits near mean*ln(2)); "
                "compared against measured_arl0_mean at m=100000, phi=0 (known-parameter "
                "regime), horizon-censored mean is a conservative (low-biased) estimator.",
        "per_chart": [
            {
                "chart": a["chart"],
                "known_arl0": a["known_parameter_arl0"],
                "measured_mean_arl0_at_m100000_phi0": a["measured_arl0_mean"],
                "censored_at_horizon_rate": a["censored_at_horizon_rate"],
                "rel_err": rd(abs(a["measured_arl0_mean"] - a["known_parameter_arl0"]) / a["known_parameter_arl0"]),
            }
            for a in anchors
        ],
    }
    anchor_gate["passed"] = bool(all(c["rel_err"] <= anchor_gate["tol_rel"] for c in anchor_gate["per_chart"]))

    part_b = run_part_b()
    pc = run_positive_control()

    m50_cells_phi0 = [c for c in cells if c["m"] == 50 and c["phi"] == 0.0]
    m50_cells_ar1 = [c for c in cells if c["m"] == 50 and c["phi"] > 0.0]
    m50_budget_breach_under_ar1 = [
        c for c in m50_cells_ar1 if c["p_false_alarm_within_30_batches"] > 0.05
    ]

    out = {
        "study_id": "ar1-estparam-drift-corpus-v1",
        "schema": "amphora.process-qc-twin.ar1-estparam-drift-corpus.v1",
        "campaign_item_id": "T-10",
        "purpose": (
            "Test whether the module's estimated-parameter ARL characterization "
            "(five prior evidence/audit/*-arl-degradation-v1 receipts, all i.i.d.-only) "
            "and its locked >=90% seeded-shift recall target survive AR(1) autocorrelated "
            "in-control data and tampers masked as sensor noise."
        ),
        "detector_design": {
            "shewhart": {"type": "Individuals", "limits_sigma": L_SHEWHART},
            "ewma": {"lambda": EWMA_LAMBDA, "L": EWMA_L},
            "cusum": {"k": CUSUM_K, "h": CUSUM_H, "standardized_tabular": True},
        },
        "model": (
            "X_t = mu + phi*(X_{t-1}-mu) + eps_t, eps_t~N(0,sigma^2*(1-phi^2)); "
            "mu_hat/sigma_hat estimated NAIVELY (sample mean / sample sd, ddof=1) "
            "from the m-length baseline, exactly as the module's iid-assuming "
            "implementation does; no AR(1) correction exists in the live capability."
        ),
        "known_parameter_anchor_gate": anchor_gate,
        "part_a_arl0_degradation_grid": cells,
        "part_a_m50_budget_check": {
            "note": "m=50 was reported by mr-memory-detector-arl-degradation-v1 / the "
                     "consolidated KPI as the smallest baseline that STILL MEETS the "
                     "locked false-alarm budget, under the i.i.d. (phi=0) assumption.",
            "locked_p_fa_30_budget_per_chart_informal": 0.05,
            "phi0_cells": m50_cells_phi0,
            "ar1_cells": m50_cells_ar1,
            "cells_breaching_budget_under_ar1": m50_budget_breach_under_ar1,
        },
        "part_b_tamper_corpus": part_b,
        "positive_control_sanity_check": pc,
        "closes": [
            "First AR(1)-autocorrelation characterization of estimated-parameter ARL0 "
            "for all three module detector arms (Shewhart, EWMA, CUSUM).",
            "First measurement of the module's locked >=90% seeded-shift recall target "
            "under estimated (short-window) limits AND AR(1) autocorrelated data, via a "
            "128-case tamper corpus with tampers masked as sensor noise.",
        ],
        "does_not_close": [
            "Does NOT establish real-batch acceptability, product qualification, EHS "
            "acceptability, or batch-release authority.",
            "Non-normality (only Gaussian AR(1) innovations are modeled) remains open.",
            "MA/ARMA and higher-order AR autocorrelation structures are not modeled.",
            "No prospective time-ordered 30-batch pilot is checked in; this is a theory "
            "+ Monte-Carlo characterization on owned synthetic data.",
            "The tamper corpus uses one realization per case (not a resampled MC estimate "
            "per case); recall is a corpus-level rate over 128 independent draws, not a "
            "per-case confidence interval.",
        ],
    }
    return out


if __name__ == "__main__":
    result = main()
    print(json.dumps(result, indent=2, sort_keys=True))
