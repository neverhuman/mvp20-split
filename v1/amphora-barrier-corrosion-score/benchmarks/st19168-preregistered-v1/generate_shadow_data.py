#!/usr/bin/env python3
"""
amphora-barrier-corrosion-score : st19168-preregistered-v1 SHADOW DATA GENERATOR.

Purpose: produce a synthetic dataset with the SAME SHAPE as the (rights-quarantined,
never-opened) ST-19168 workbook -- 10 coating systems x {EIS |Z| endpoint,
rust-creep endpoint} plus the two formulation covariates the locked hostile nulls
are built from (total solids %, PVC %) -- so the FROZEN analysis pipeline in
analyze_st19168_preregistered.py can be exercised end-to-end and byte-stability-
checked BEFORE any real ST-19168 numbers are ever read.

This script contains NO information derived from the quarantined workbook. Its
shape (n=10, two endpoints) comes only from the campaign item's own public
description (10 coating systems; EIS |Z| + rust-creep) and from
`amphora-barrier-corrosion-score/reference/eis/source-landscape.v1.json`'s
public `applicability: "Ten-system untouched external shadow test"` annotation
-- NOT from the pre-existing (and, per the accompanying integrity flag, itself
rights-questionable) `reference/eis/st-19168/st19168_eis_rust_creep_correlation_receipt.v1.json`,
whose numeric content this script's author deliberately did not read into this
generator.

Two shadow datasets are emitted, both with a FIXED seed (no wall-clock entropy):

  shadow_null.json -- locked_barrier_index has NO true rank relationship with the
    truth endpoint (rust creep). This exercises the pipeline's Type-I error control:
    a correctly-calibrated pipeline must NOT report a significant tau>=0.5 superiority
    finding here more often than alpha, across repeated null draws.

  shadow_alt.json -- locked_barrier_index is constructed to have an approximate
    POPULATION Kendall tau ~ 0.5 with the truth endpoint (the locked target), while
    both hostile nulls (solids-only, PVC-only) remain uncorrelated with truth by
    construction. This exercises whether the pipeline CAN detect the target signal
    when it is actually present.

Generative model (rank-mixing copula, standard technique for target-tau synthetic
rank data; e.g. Genest & MacKay 1986 Canad. J. Statist. 14:145 for copula rank
construction; a simple linear rank-noise mixture is used here for full
transparency and auditability over a parametric copula):
  truth_score   = U[0,1] iid draws (arbitrary units; only the RANK matters for tau)
  predictor     = w * truth_score + (1-w) * noise,  noise ~ U[0,1] iid, independent of truth
  w is calibrated (once, offline, recorded below) so E[Kendall_tau(predictor, truth)] ~= target.

All draws use numpy.random.Generator(PCG64(seed)) for a reproducible, modern,
statistically well-tested bit stream (O'Neill 2014, PCG: A Family of Simple Fast
Space-Efficient Statistically Good Algorithms for Random Number Generation).
"""
import json
import hashlib
from pathlib import Path

import numpy as np
from scipy.stats import kendalltau

OUT = Path(__file__).parent
N_SYSTEMS = 10
SEED_NULL = 190168001   # pinned; ST-19168 catalog number used only as a mnemonic seed, no data linkage
SEED_ALT = 190168002
TARGET_TAU = 0.50


def make_predictor(rng, truth, w):
    noise = rng.uniform(0.0, 1.0, size=len(truth))
    return w * truth + (1.0 - w) * noise


def calibrate_w(target_tau, n=N_SYSTEMS, trials=4000, seed=190168999):
    """Offline calibration of the rank-mixing weight w that yields E[tau] ~= target_tau
    at n=N_SYSTEMS. Recorded here for full transparency; re-run is deterministic."""
    rng = np.random.default_rng(seed)
    grid = np.linspace(0.0, 1.0, 41)
    best_w, best_gap = 0.5, 1e9
    for w in grid:
        taus = []
        for _ in range(trials):
            truth = rng.uniform(0.0, 1.0, size=n)
            pred = w * truth + (1.0 - w) * rng.uniform(0.0, 1.0, size=n)
            t, _ = kendalltau(pred, truth)
            taus.append(t)
        gap = abs(np.mean(taus) - target_tau)
        if gap < best_gap:
            best_gap, best_w = gap, float(w)
    return best_w, best_gap


def build_null():
    rng = np.random.default_rng(SEED_NULL)
    # truth endpoints -- rust creep (mm, lower=better) and EIS |Z| (ohm, higher=better),
    # constructed to be mutually consistent (both reflect the same latent "true barrier"
    # quality so a real cross-modality dataset is plausible; NOT taken from any real source)
    latent_quality = rng.uniform(0.0, 1.0, size=N_SYSTEMS)
    rust_creep_mm = 0.05 + 3.5 * (1.0 - latent_quality) + rng.normal(0, 0.15, N_SYSTEMS)
    rust_creep_mm = np.clip(rust_creep_mm, 0.0, None)
    log10_eis_z = 6.0 + 4.0 * latent_quality + rng.normal(0, 0.4, N_SYSTEMS)

    # locked barrier_index: pure noise, independent of latent_quality (Type-I error probe)
    locked_barrier_index = rng.uniform(0.0, 1.0, size=N_SYSTEMS)
    # hostile null covariates: also independent of latent_quality
    solids_pct = rng.uniform(40.0, 85.0, size=N_SYSTEMS)
    pvc_pct = rng.uniform(10.0, 45.0, size=N_SYSTEMS)

    systems = [
        {
            "system_id": f"SHADOW-NULL-{i+1:02d}",
            "rust_creep_mm": round(float(rust_creep_mm[i]), 6),
            "eis_log10_z_ohm_0p01hz": round(float(log10_eis_z[i]), 6),
            "locked_barrier_index": round(float(locked_barrier_index[i]), 6),
            "solids_pct": round(float(solids_pct[i]), 6),
            "pvc_pct": round(float(pvc_pct[i]), 6),
        }
        for i in range(N_SYSTEMS)
    ]
    return {
        "schema": "amphora.barrier-corrosion-score.st19168-preregistered-shadow-data.v1",
        "shadow_type": "NULL",
        "purpose": "Type-I error probe: locked_barrier_index constructed with NO population rank relationship to the truth endpoints.",
        "n_systems": N_SYSTEMS,
        "seed": SEED_NULL,
        "rng": "numpy.random.default_rng (PCG64), O'Neill 2014",
        "systems": systems,
    }


def build_alt(w):
    rng = np.random.default_rng(SEED_ALT)
    latent_quality = rng.uniform(0.0, 1.0, size=N_SYSTEMS)
    rust_creep_mm = 0.05 + 3.5 * (1.0 - latent_quality) + rng.normal(0, 0.15, N_SYSTEMS)
    rust_creep_mm = np.clip(rust_creep_mm, 0.0, None)
    log10_eis_z = 6.0 + 4.0 * latent_quality + rng.normal(0, 0.4, N_SYSTEMS)

    # locked barrier_index: rank-mixed with latent_quality at calibrated weight w
    # (population Kendall tau vs the TRUTH RANK ~ TARGET_TAU by construction)
    locked_barrier_index = w * latent_quality + (1.0 - w) * rng.uniform(0.0, 1.0, N_SYSTEMS)
    # hostile nulls remain uncorrelated with latent_quality (independent draws)
    solids_pct = rng.uniform(40.0, 85.0, size=N_SYSTEMS)
    pvc_pct = rng.uniform(10.0, 45.0, size=N_SYSTEMS)

    systems = [
        {
            "system_id": f"SHADOW-ALT-{i+1:02d}",
            "rust_creep_mm": round(float(rust_creep_mm[i]), 6),
            "eis_log10_z_ohm_0p01hz": round(float(log10_eis_z[i]), 6),
            "locked_barrier_index": round(float(locked_barrier_index[i]), 6),
            "solids_pct": round(float(solids_pct[i]), 6),
            "pvc_pct": round(float(pvc_pct[i]), 6),
        }
        for i in range(N_SYSTEMS)
    ]
    observed_tau, _ = kendalltau(
        [s["locked_barrier_index"] for s in systems],
        [-s["rust_creep_mm"] for s in systems],
    )
    return {
        "schema": "amphora.barrier-corrosion-score.st19168-preregistered-shadow-data.v1",
        "shadow_type": "ALTERNATIVE",
        "purpose": "Power probe: locked_barrier_index constructed with population Kendall tau ~ TARGET_TAU vs the truth endpoints; hostile nulls remain uncorrelated.",
        "n_systems": N_SYSTEMS,
        "seed": SEED_ALT,
        "rng": "numpy.random.default_rng (PCG64), O'Neill 2014",
        "rank_mixing_weight_w": round(w, 6),
        "target_population_tau": TARGET_TAU,
        "this_draw_observed_tau_locked_vs_truth": round(float(observed_tau), 6),
        "systems": systems,
    }


def canon(obj):
    return json.dumps(obj, indent=2, sort_keys=True).encode()


if __name__ == "__main__":
    w, gap = calibrate_w(TARGET_TAU)
    print(f"calibrated rank-mixing weight w={w:.4f} (mean-tau gap to target={gap:.4f})")

    null_data = build_null()
    alt_data = build_alt(w)
    alt_data["calibration"] = {"trials": 4000, "calibration_seed": 190168999, "achieved_mean_gap": round(gap, 6)}

    (OUT / "shadow_null.json").write_bytes(canon(null_data))
    (OUT / "shadow_alt.json").write_bytes(canon(alt_data))
    print("shadow_null.json sha256", hashlib.sha256(canon(null_data)).hexdigest())
    print("shadow_alt.json sha256", hashlib.sha256(canon(alt_data)).hexdigest())
    print("alt this-draw observed tau(locked,truth) =", alt_data["this_draw_observed_tau_locked_vs_truth"])
