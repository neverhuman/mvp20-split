#!/usr/bin/env python3
"""amphora-cure-potlife-gate :: AUDIT_ONLY gel<->TFS cross-endpoint diagnostic.

QUESTION
--------
The module's locked known-answer set (cure_verification_set.json, n=25 Evonik
polyamide/amidoamine hardeners x DGEBA-class epoxy at 25 C) carries TWO cure
endpoints per hardener:

  gel_min : bulk gel time, 150 g mass, 25 C (Evonik basis)
  tfs_h   : thin-film set time, Beck-Koller recorder (ASTM D5895 method), 25 C

The dataset's honesty disclosure asserts -- but has never quantified -- that
bulk gel time maps to application-relevant endpoints only DIRECTIONALLY.  This
harness turns that caveat into a tested claim by asking whether the thin-film
endpoint is REDUCIBLE to the bulk endpoint.

H0 (iso-conversional reduction): for a cure governed by a single rate constant
k(T) and a system-independent conversion function, the time to any fixed
conversion a* is t(a*) = g(a*)/k, so the ratio of times to two fixed
conversion events (gelation at a_gel, film set at a_set) is a SYSTEM-
INDEPENDENT constant:  tfs_h = c * gel_h  for all 25 systems, i.e. slope 1 and
constant offset in log-log space.

  Theory:  Flory, J Am Chem Soc 63:3083 (1941), doi:10.1021/ja01856a061 and
  Stockmayer, J Chem Phys 11:45 (1943), doi:10.1063/1.1723803 (gelation is a
  fixed-conversion event); Enns & Gillham, J Appl Polym Sci 28:2567 (1983),
  doi:10.1002/app.1983.070280810 (TTT diagram: gelation AND solidification are
  iso-conversional contours, so at fixed T their times are proportional across
  systems sharing a kinetic law); Horie et al., J Polym Sci A-1 8:1357 (1970),
  doi:10.1002/pol.1970.150080605 and Kamal & Sourour, Polym Eng Sci 13:59
  (1973), doi:10.1002/pen.760130110 (epoxy-amine conversion kinetics with a
  shared k(T) prefactor).

H1 (mass/exotherm confound, directional): the 150 g bulk gel measurement is
self-heated (Semenov thermal-ignition scaling: Semenov, Z Phys 48:571 (1928),
doi:10.1007/BF01340021; Frank-Kamenetskii, Acta Physicochim URSS 10:365
(1939)), while a Beck-Koller film is quasi-isothermal.  Self-heating shortens
bulk gel time MORE for intrinsically fast systems, stretching the fast end of
the gel axis.  Prediction: the log-log slope b of tfs on gel is < 1, and a
single fold-ratio c cannot cover the panel.

DESIGN
------
G1  dataset integrity (sha256 pinned to the value recorded in the module's
    signed Evonik correlation receipt; n=25; both endpoints present per row).
G2  directional concordance: Spearman rho and Kendall tau between gel_min and
    tfs_h with a seeded 20000-draw permutation null.  This is the module's
    load-bearing "gel maps pot-life-like endpoints directionally" assumption,
    tested on an endpoint pair no prior receipt has examined.
G3  H0 fixed-ratio fit: c = geometric mean of tfs_h/gel_h; log10 residual
    spread, per-system fold errors, fraction of systems inside the module's
    x/1.5 band around the fixed-ratio prediction.
G4  power-law alternative log10(tfs) = a + b*log10(gel): OLS point estimate,
    seeded pairs-bootstrap (20000) CI for b, H0 b=1 test, b=0 test.
G5  leave-one-out model comparison in log10 space: M0 predict-mean null,
    M1 fixed-ratio, M2 power-law.
G6  Semenov direction gate: is the deviation from H0 in the direction the
    exotherm confound predicts (b < 1)?
G7  fail-closed scope: rows lacking either endpoint must be excluded, and the
    verdict must not depend on any imputed value.

AUDIT_ONLY.  Does not promote authority, does not flip scientific_readiness,
does not touch the portfolio manifest (66 receipts / 11 modules), the locked
known-answer dataset, the signed Arrhenius Phase-0 KPI, or any prior signed
receipt.
"""
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np
from scipy import stats

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-cure-potlife-gate"
DATA = MOD / "reference/mvp20/data/cure_verification_set.json"
CORR_RECEIPT = MOD / "reference/mvp20/data/evonik_cure_kinetics_correlation_receipt.v1.json"
OUT_DIR = MOD / "evidence/audit/potlife-gel-tfs-crossendpoint-v1"

PINNED_DATASET_SHA256 = "884356a094bd6f4def926e7ef218070b83d917742009c8922f953c097f9305d2"
SEED = 20260731
N_PERM = 20000
N_BOOT = 20000
BAND_FOLD = 1.5          # module's existing x//1.5 validation band
MIN_H = 1e-9


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def r6(x):
    """Round for byte-stable JSON while keeping full scientific resolution."""
    if isinstance(x, float):
        return float(f"{x:.10g}")
    return x


def main():
    raw = DATA.read_bytes()
    ds_sha = sha(raw)
    ds = json.loads(raw)
    rows = ds["rows"]

    usable, excluded = [], []
    for r in rows:
        if r.get("gel_min") is not None and r.get("tfs_h") is not None:
            usable.append(r)
        else:
            excluded.append(r["hardener"])
    g1 = {
        "dataset_sha256": ds_sha,
        "dataset_sha256_matches_signed_correlation_receipt": ds_sha == PINNED_DATASET_SHA256,
        "n_rows_total": len(rows),
        "n_rows_usable_both_endpoints": len(usable),
        "rows_excluded_fail_closed": excluded,
        "passed": ds_sha == PINNED_DATASET_SHA256 and len(usable) == 25 and not excluded,
    }

    names = [r["hardener"] for r in usable]
    gel_h = np.array([r["gel_min"] / 60.0 for r in usable], dtype=float)
    tfs_h = np.array([float(r["tfs_h"]) for r in usable], dtype=float)
    lx = np.log10(np.maximum(gel_h, MIN_H))
    ly = np.log10(np.maximum(tfs_h, MIN_H))
    n = len(usable)

    # G2 -- directional concordance with permutation null
    rho, _ = stats.spearmanr(gel_h, tfs_h)
    tau, tau_p = stats.kendalltau(gel_h, tfs_h)
    rng = np.random.default_rng(SEED)
    perm_ge = 0
    for _ in range(N_PERM):
        pr, _ = stats.spearmanr(gel_h, rng.permutation(tfs_h))
        if pr >= rho:
            perm_ge += 1
    perm_p = (perm_ge + 1) / (N_PERM + 1)
    g2 = {
        "spearman_rho": r6(rho),
        "spearman_permutation_p_one_sided": r6(perm_p),
        "kendall_tau": r6(tau),
        "kendall_tau_p_two_sided": r6(tau_p),
        "n": n,
        "directional_concordance_established": bool(perm_p < 0.05 and rho > 0),
        "passed": True,  # measurement gate: value is reported either way
    }

    # G3 -- H0 fixed ratio tfs = c * gel
    lr = ly - lx                       # log10 fold ratios
    c_hat = 10.0 ** float(np.mean(lr))
    resid = lr - np.mean(lr)
    fold_err = 10.0 ** np.abs(resid)   # per-system fold deviation from c_hat
    inside_band = fold_err <= BAND_FOLD
    loo_folds = []
    for i in range(n):
        mask = np.ones(n, bool); mask[i] = False
        c_i = float(np.mean(lr[mask]))
        loo_folds.append(10.0 ** abs(lr[i] - c_i))
    g3 = {
        "c_hat_fold_tfs_over_gel": r6(c_hat),
        "log10_ratio_sd": r6(float(np.std(lr, ddof=1))),
        "fold_ratio_min": r6(float(np.min(10.0 ** lr))),
        "fold_ratio_max": r6(float(np.max(10.0 ** lr))),
        "fold_ratio_span": r6(float(10.0 ** (np.max(lr) - np.min(lr)))),
        "max_fold_error_vs_c_hat": r6(float(np.max(fold_err))),
        "n_inside_1p5x_band": int(np.sum(inside_band)),
        "n_outside_1p5x_band": int(n - np.sum(inside_band)),
        "loo_geometric_mean_fold_error": r6(float(np.exp(np.mean(np.log(loo_folds))))),
        "loo_max_fold_error": r6(float(np.max(loo_folds))),
    }

    # G4 -- power-law alternative
    b, a, r_val, p_b0, se_b = stats.linregress(lx, ly)
    boot_b = np.empty(N_BOOT)
    rng2 = np.random.default_rng(SEED + 1)
    for k in range(N_BOOT):
        idx = rng2.integers(0, n, n)
        while len(set(idx.tolist())) < 3:
            idx = rng2.integers(0, n, n)
        bb, _, _, _, _ = stats.linregress(lx[idx], ly[idx])
        boot_b[k] = bb
    ci_lo, ci_hi = np.percentile(boot_b, [2.5, 97.5])
    boot_p_b_ge_1 = float((np.sum(boot_b >= 1.0) + 1) / (N_BOOT + 1))
    g4 = {
        "slope_b": r6(float(b)),
        "intercept_a_log10": r6(float(a)),
        "r_squared": r6(float(r_val ** 2)),
        "residual_sd_log10": r6(float(np.std(ly - (a + b * lx), ddof=2))),
        "p_slope_zero_two_sided": r6(float(p_b0)),
        "slope_se_ols": r6(float(se_b)),
        "bootstrap_b_ci95": [r6(float(ci_lo)), r6(float(ci_hi))],
        "bootstrap_p_b_ge_1_one_sided": r6(boot_p_b_ge_1),
        "fixed_ratio_slope_inside_ci": bool(ci_lo <= 1.0 <= ci_hi),
    }

    # G5 -- LOO model comparison in log10 space
    e0, e1, e2 = [], [], []
    for i in range(n):
        mask = np.ones(n, bool); mask[i] = False
        e0.append(ly[i] - float(np.mean(ly[mask])))
        e1.append(ly[i] - (lx[i] + float(np.mean(lr[mask]))))
        bb, aa, _, _, _ = stats.linregress(lx[mask], ly[mask])
        e2.append(ly[i] - (aa + bb * lx[i]))
    rmse = lambda e: float(np.sqrt(np.mean(np.square(e))))
    loo = {"M0_null_predict_mean": r6(rmse(e0)),
           "M1_fixed_ratio": r6(rmse(e1)),
           "M2_power_law": r6(rmse(e2))}
    winner = min(loo, key=loo.get)
    g5 = {"loo_rmse_log10": loo, "winner": winner,
          "M1_beats_M0": loo["M1_fixed_ratio"] < loo["M0_null_predict_mean"],
          "M2_beats_M1": loo["M2_power_law"] < loo["M1_fixed_ratio"]}

    # G6 -- Semenov direction gate
    slope_below_1 = bool(g4["bootstrap_b_ci95"][1] < 1.0)
    g6 = {
        "semenov_prediction": "log-log slope b < 1 (bulk exotherm stretches the fast end of the gel axis)",
        "observed_slope_b": g4["slope_b"],
        "ci95_excludes_1": slope_below_1,
        "direction_matches_semenov_if_h0_refuted": bool(g4["slope_b"] < 1.0),
    }

    # Verdict on H0
    h0_refuted = bool((not g4["fixed_ratio_slope_inside_ci"] and g4["slope_b"] < 1.0)
                      or g3["n_outside_1p5x_band"] > n // 2)
    reduction_verdict = "REFUTED" if h0_refuted else "NOT_REFUTED"

    g7 = {
        "rows_excluded": excluded,
        "imputation_used": False,
        "verdict_depends_only_on_rows_with_both_endpoints": True,
        "passed": True,
    }

    per_system = [
        {"hardener": names[i], "gel_min": r6(float(gel_h[i] * 60.0)),
         "gel_h": r6(float(gel_h[i])), "tfs_h": r6(float(tfs_h[i])),
         "fold_ratio_tfs_over_gel": r6(float(10.0 ** lr[i])),
         "fold_error_vs_c_hat": r6(float(fold_err[i])),
         "inside_1p5x_band": bool(inside_band[i])}
        for i in range(n)
    ]

    headline = (
        f"Cross-endpoint iso-conversional reduction H0 (thin-film set time = c x bulk gel time) "
        f"{reduction_verdict} on the locked n={n} Evonik panel: fold ratio spans "
        f"{g3['fold_ratio_min']}x-{g3['fold_ratio_max']}x ({g3['n_outside_1p5x_band']}/{n} systems "
        f"outside the module's 1.5x band around the best single ratio), log-log slope "
        f"b={g4['slope_b']} (95% bootstrap CI {g4['bootstrap_b_ci95']}), while directional "
        f"concordance (Spearman rho={g2['spearman_rho']}, permutation p={g2['spearman_permutation_p_one_sided']}) "
        f"{'HOLDS' if g2['directional_concordance_established'] else 'FAILS'} -- quantifying the dataset's "
        f"standing honesty disclosure that bulk gel maps application endpoints directionally, not absolutely."
    )

    diag = {
        "schema": "amphora.cure-potlife-gate.gel-tfs-crossendpoint-diagnostic.v1",
        "module": "amphora-cure-potlife-gate",
        "run_type": "AUDIT_ONLY_THEORY_AXIS",
        "authority": "AUDIT_ONLY",
        "purpose": (
            "Test whether the thin-film set endpoint (Beck-Koller, 25 C) is reducible to the "
            "bulk 150 g gel endpoint via a single system-independent iso-conversional time "
            "ratio, as single-rate-constant cure kinetics predicts for two fixed-conversion "
            "events at fixed temperature; and whether any deviation is in the direction the "
            "Semenov self-heating confound predicts."),
        "headline": headline,
        "reduction_h0_verdict": reduction_verdict,
        "directional_concordance": bool(g2["directional_concordance_established"]),
        "theory_reference": {
            "flory_1941": "doi:10.1021/ja01856a061",
            "stockmayer_1943": "doi:10.1063/1.1723803",
            "enns_gillham_1983_ttt": "doi:10.1002/app.1983.070280810",
            "horie_1970": "doi:10.1002/pol.1970.150080605",
            "kamal_sourour_1973": "doi:10.1002/pen.760130110",
            "semenov_1928": "doi:10.1007/BF01340021",
            "frank_kamenetskii_1939": "Acta Physicochim URSS 10:365 (1939)",
            "beck_koller_method": "ASTM D5895 (mechanical drying-time recorder)",
        },
        "dataset": {
            "path": "amphora-cure-potlife-gate/reference/mvp20/data/cure_verification_set.json",
            "sha256": ds_sha,
            "basis": ("Evonik product-guide known-answer set: DGEBA-class epoxy (EEW~190) x "
                      "polyamide/amidoamine at supplier phr; gel 150 g @25C; thin-film set "
                      "(Beck-Koller) @25C; verification-only, never used for candidate generation."),
            "n_rows": len(rows),
            "n_used": n,
        },
        "constants": {"seed": SEED, "n_permutations": N_PERM, "n_bootstrap": N_BOOT,
                      "band_fold": BAND_FOLD,
                      "numpy_version": np.__version__,
                      "scipy_version": __import__("scipy").__version__,
                      "python_version": sys.version.split()[0]},
        "non_circularity": (
            "No quantity in this harness is fitted to, or derived from, the module's signed "
            "Arrhenius KPI, the temperature-scaling known-answer set, or any prior receipt's "
            "estimates. Both endpoints come from the same locked supplier dataset; the tested "
            "H0 is a parameter-free structural prediction (slope exactly 1 in log-log space) "
            "of single-rate-constant kinetics, with only the offset c estimated from data."),
        "G1_dataset_integrity": g1,
        "G2_directional_concordance": g2,
        "G3_fixed_ratio_h0": g3,
        "G4_power_law_alternative": g4,
        "G5_loo_model_comparison": g5,
        "G6_semenov_direction": g6,
        "G7_fail_closed_scope": g7,
        "gates_summary": {
            "G1": g1["passed"], "G2": g2["passed"],
            "G3_h0_fixed_ratio": reduction_verdict,
            "G4_slope_ci_excludes_1": not g4["fixed_ratio_slope_inside_ci"],
            "G5_loo_winner": winner,
            "G6_direction_matches_semenov": g6["direction_matches_semenov_if_h0_refuted"],
            "G7": g7["passed"],
        },
        "per_system": per_system,
        "closes": [
            "Quantifies the previously untested gel<->TFS cross-endpoint relation on the locked panel",
            "Converts the dataset's narrative honesty disclosure (directional-only mapping) into a signed, replayable statistical result",
            "Establishes whether a single fold-ratio ever licenses absolute film-set predictions from bulk gel data (it does not, if H0 refuted)",
        ],
        "does_not_close": [
            "No pot-life (viscosity-doubling) endpoint is present in this panel; the mapping tested is gel->thin-film-set",
            "Single temperature (25 C) and single supplier basis; no cross-supplier generalization claimed",
            "Semenov direction gate is consistency-only: mass-varied gel data would be needed to identify the exotherm magnitude",
            "No authority promotion; scientific_readiness stays UNVALIDATED; PRE_PHASE_0 unchanged",
        ],
        "phase1_requirement": (
            "Absolute film-set or pot-life prediction from bulk gel data would require "
            "mass-varied gel measurements (>=3 masses per system) or isothermal DSC "
            "conversion curves to separate the kinetic ratio g(a_set)/g(a_gel) from the "
            "Semenov self-heating term."),
        "claim_locks": {
            "modifies_manifest": False,
            "modifies_locked_dataset": False,
            "modifies_signed_phase0_kpi": False,
            "modifies_prior_signed_receipt": False,
            "promotes_authority": False,
            "flips_scientific_readiness": False,
        },
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(diag, indent=2, sort_keys=True).encode()
    out = OUT_DIR / ("diagnostic.runB.json" if "--replay" in sys.argv
                     else "diagnostic.canonical.json")
    out.write_bytes(payload)
    print("WROTE", out)
    print("sha256", sha(payload))
    print("verdict", reduction_verdict,
          "| rho", g2["spearman_rho"], "perm_p", g2["spearman_permutation_p_one_sided"],
          "| c_hat", g3["c_hat_fold_tfs_over_gel"],
          "| b", g4["slope_b"], g4["bootstrap_b_ci95"],
          "| outside band", g3["n_outside_1p5x_band"], "/", n,
          "| loo winner", winner)


if __name__ == "__main__":
    main()
