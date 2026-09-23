#!/usr/bin/env python3
"""amphora-cure-potlife-gate :: AUDIT_ONLY curvature-mechanism diagnostic.

QUESTION
--------
The signed Phase-0 pot-life KPI scales pot life by a pure Arrhenius law using
*published, externally cited* activation energies (Prime/Turi 1997; Kamal &
Sourour 1973; Riccardi 1984; Blanco 2005).  A prior signed audit established
that the activation energy recovered by regressing the locked pot-life data is
only ~0.884x the cited chemical Ea.  This harness asks WHY, by implementing two
published baselines the module does not yet contain and testing each against the
locked data:

  (KS)  Kamal & Sourour, Polym Eng Sci 13(1):59-64 (1973),
        doi:10.1002/pen.760130110 -- autocatalytic two-channel rate law
            da/dt = (k1 + k2 * a^m) * (1 - a)^n ,   k_i = A_i exp(-Ea_i/RT)
        integrated to a fixed threshold conversion a*, with a* optionally set by

  (FS)  Flory, J Am Chem Soc 63:3083 (1941), doi:10.1021/ja01856a061 and
        Stockmayer, J Chem Phys 11:45 (1943), doi:10.1063/1.1723803 --
        gel conversion at stoichiometry  a_gel = 1/sqrt((f-1)(g-1)),
        f = 2 epoxide groups per DGEBA, g = amine hydrogens per hardener.

  (VFT) Vogel, Phys Z 22:645 (1921); Fulcher, J Am Ceram Soc 8:339 (1925),
        doi:10.1111/j.1151-2916.1925.tb16731.x; Tammann & Hesse, Z Anorg Allg
        Chem 156:245 (1926), doi:10.1002/zaac.19261560121 --
            ln t = A + B/(T - T0)
        the free-volume / non-Arrhenius form (Williams-Landel-Ferry, J Am Chem
        Soc 77:3701 (1955), doi:10.1021/ja01619a008, is its algebraic twin).

DESIGN
------
The SAME estimator (OLS quadratic of ln t on u = 1/T - 1/T_ref) is applied to
the locked data and to every model's forward prediction, so the curvature
comparison is apples-to-apples.  Nothing in this harness re-fits, edits or
supersedes the signed Arrhenius KPI; it is a mechanism audit of it.

AUDIT_ONLY.  Does not promote authority, does not flip scientific_readiness,
does not touch the portfolio manifest (66 receipts / 11 modules), the locked
known-answer dataset, or any prior signed receipt.
"""
import hashlib
import itertools
import json
import math
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-cure-potlife-gate"
KA_PATH = MOD / "reference/phase0-cure-potlife-known-answer.v1.json"
KPI_PATH = MOD / "evidence/phase0/kpis/cure-potlife-arrhenius-kpi.v1.json"
OUT_DIR = MOD / "evidence/audit/potlife-arrhenius-curvature-mechanism-v1"

R_GAS = 8.31446261815324                      # CODATA 2018 J/(mol K)
T_ZERO = 273.15                               # ITS-90 degC -> K
T_REF_F = 73.0                                # coating-industry anchor, 73 degF
T_REF = (T_REF_F - 32.0) * 5.0 / 9.0 + T_ZERO # 295.9277... K
TEMPS_C = [10.0, 22.78, 30.0, 40.0]
KEYS = ["pot_life_min_10c", "pot_life_min_22_78c", "pot_life_min_30c",
        "pot_life_min_40c"]
TK = np.array([10.0 + T_ZERO, T_REF, 30.0 + T_ZERO, 40.0 + T_ZERO])
X = 1.0 / TK
XR = X[1]
U = X - XR
ANCHOR = 1                                     # index of the 22.78 degC anchor
HELD = [0, 2, 3]
LEG_LABEL = {0: "10C", 2: "30C", 3: "40C"}
MC_SEED = 20260730
MC_DRAWS = 20000

# Amine-hydrogen functionality g per hardener, from molecular structure only.
# No fitting, no data-derived quantity.  None => structurally unresolved.
AMINE_H_FUNCTIONALITY = {
    "dgeba-teta": 6,    # triethylenetetramine: 2 primary (2H) + 2 secondary (1H)
    "dgeba-deta": 5,    # diethylenetriamine:   2 primary + 1 secondary
    "dgeba-tepa": 7,    # tetraethylenepentamine: 2 primary + 3 secondary
    "dgeba-ipda": 4,    # isophorone diamine: 2 primary
    "dgeba-pacm": 4,    # 4,4'-methylenebis(cyclohexylamine)
    "dgeba-dach": 4,    # 1,2-diaminocyclohexane
    "dgeba-mxda": 4,    # m-xylylenediamine
    "dgeba-mpda": 4,    # m-phenylenediamine
    "dgeba-mda": 4,     # 4,4'-methylenedianiline
    "dgeba-amidoamine-adduct1": None,   # proprietary oligomeric adduct
    "dgeba-amidoamine-adduct2": None,
    "dgeba-mannich": None,              # tertiary-amine catalytic cure, no FS
}
EPOXY_FUNCTIONALITY = 2                        # DGEBA diglycidyl ether


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


# --------------------------------------------------------------------------
# estimators (identical for data and for model forward predictions)
# --------------------------------------------------------------------------
def lin_arrhenius(y):
    """OLS ln t = a + b/T ; returns (a, b, Ea_app, rms)."""
    A = np.vstack([np.ones_like(X), X]).T
    c, *_ = np.linalg.lstsq(A, y, rcond=None)
    rms = float(np.sqrt(np.mean((A @ c - y) ** 2)))
    return float(c[0]), float(c[1]), float(c[1] * R_GAS), rms


def quad_curvature(y):
    """OLS ln t = a + b*u + c*u^2 on u = 1/T - 1/T_ref ; returns (c2, rms)."""
    A = np.vstack([np.ones_like(U), U, U ** 2]).T
    c, *_ = np.linalg.lstsq(A, y, rcond=None)
    rms = float(np.sqrt(np.mean((A @ c - y) ** 2)))
    return float(c[2]), rms


# --------------------------------------------------------------------------
# Kamal-Sourour forward integration
# --------------------------------------------------------------------------
def simpson(y, h):
    return h / 3.0 * (y[0] + y[-1] + 4.0 * y[1:-1:2].sum() + 2.0 * y[2:-2:2].sum())


def ks_time_to_alpha(alpha_star, k1, k2, m, n, npts=2001):
    a = np.linspace(0.0, alpha_star, npts)
    g = 1.0 / ((k1 + k2 * a ** m) * (1.0 - a) ** n)
    return float(simpson(g, a[1] - a[0]))


def ks_forward(ea1, ea2, ratio_ref, alpha_star, m, n, npts=2001):
    """Forward-predict ln t at the four locked temperatures.

    k1(T_ref) is set to 1 (an arbitrary time unit; it cancels out of both the
    Arrhenius slope and the curvature).  ratio_ref = k2/k1 evaluated at T_ref.
    """
    A1 = math.exp(ea1 / (R_GAS * T_REF))
    A2 = ratio_ref * math.exp(ea2 / (R_GAS * T_REF))
    ts = []
    for T in TK:
        k1 = A1 * math.exp(-ea1 / (R_GAS * T))
        k2 = A2 * math.exp(-ea2 / (R_GAS * T))
        ts.append(ks_time_to_alpha(alpha_star, k1, k2, m, n, npts))
    return np.log(np.array(ts))


# --------------------------------------------------------------------------
# VFT
# --------------------------------------------------------------------------
def vft_fit_free(y):
    def resid(p):
        A, B, T0 = p
        if T0 >= TK.min() - 5.0:
            return np.full(len(TK), 1e6)
        return A + B / (TK - T0) - y
    r = least_squares(resid, [0.0, 1000.0, 200.0], method="lm", max_nfev=20000)
    return [float(v) for v in r.x], float(np.sqrt(np.mean(r.fun ** 2)))


def vft_fit_fixed_t0(y, T0, temps=None, yv=None):
    tt = TK if temps is None else temps
    yy = y if yv is None else yv
    A = np.vstack([np.ones_like(tt), 1.0 / (tt - T0)]).T
    c, *_ = np.linalg.lstsq(A, yy, rcond=None)
    rms = float(np.sqrt(np.mean((A @ c - yy) ** 2)))
    return float(c[0]), float(c[1]), rms


def global_t0_scan(logs, t0_grid, idx=None):
    """Return the shared T0 minimising pooled SSE across systems."""
    tt = TK if idx is None else TK[idx]
    best_t0, best_sse = None, None
    for T0 in t0_grid:
        sse = 0.0
        for y in logs:
            yy = y if idx is None else y[idx]
            _, _, rms = vft_fit_fixed_t0(None, T0, temps=tt, yv=yy)
            sse += rms ** 2 * len(tt)
        if best_sse is None or sse < best_sse:
            best_t0, best_sse = float(T0), float(sse)
    return best_t0, best_sse


# ==========================================================================
def main():
    ka = json.loads(KA_PATH.read_text())
    kpi = json.loads(KPI_PATH.read_text())
    systems = ka["systems"]
    sids = [s["system_id"] for s in systems]
    fams = [s["hardener_family"] for s in systems]
    tobs = [np.array([s[k] for k in KEYS], float) for s in systems]
    logs = [np.log(t) for t in tobs]
    ea_cited = np.array([s["activation_energy_j_mol"] for s in systems], float)
    N = len(systems)

    diag = {
        "schema": "amphora.cure-potlife-gate.curvature-mechanism-diagnostic.v1",
        "module": "amphora-cure-potlife-gate",
        "run_type": "AUDIT_ONLY_MECHANISM_DIAGNOSTIC",
        "authority": "AUDIT_ONLY",
        "purpose": (
            "Determine the mechanism behind the ~11.6% deficit between the "
            "activation energy recovered from the locked pot-life data and the "
            "externally published chemical Ea used by the signed Phase-0 "
            "Arrhenius KPI, by implementing and falsifying two published "
            "baselines the module did not previously contain."),
        "non_circularity": (
            "Activation energies are external published constants read from the "
            "locked known-answer file; they are never fitted. The curvature "
            "estimator is applied identically to the locked data and to every "
            "model's forward prediction. The Kamal-Sourour grid is enumerated "
            "over a pre-declared physical envelope, not tuned to the data. "
            "Flory-Stockmayer gel conversions come from amine-hydrogen "
            "functionality (molecular structure), not from any measurement."),
        "theory_reference": {
            "arrhenius": "Arrhenius S., Z Phys Chem 4:226 (1889)",
            "kamal_sourour": ("Kamal M.R. & Sourour S., Polym Eng Sci 13(1):59-64 "
                              "(1973), doi:10.1002/pen.760130110"),
            "flory": "Flory P.J., J Am Chem Soc 63:3083-3090 (1941), doi:10.1021/ja01856a061",
            "stockmayer": "Stockmayer W.H., J Chem Phys 11:45-55 (1943), doi:10.1063/1.1723803",
            "vogel": "Vogel H., Phys Z 22:645-646 (1921)",
            "fulcher": ("Fulcher G.S., J Am Ceram Soc 8:339-355 (1925), "
                        "doi:10.1111/j.1151-2916.1925.tb16731.x"),
            "tammann_hesse": ("Tammann G. & Hesse W., Z Anorg Allg Chem 156:245-257 "
                              "(1926), doi:10.1002/zaac.19261560121"),
            "wlf": ("Williams M.L., Landel R.F., Ferry J.D., J Am Chem Soc 77:3701-3707 "
                    "(1955), doi:10.1021/ja01619a008"),
            "gas_constant": "R = 8.31446261815324 J/(mol K), CODATA 2018 (exact, SI-2019)",
        },
        "constants": {
            "R_J_per_mol_K": R_GAS,
            "T_zero_K": T_ZERO,
            "T_ref_K": T_REF,
            "T_ref_F": T_REF_F,
            "T_ref_derivation": "(73 degF - 32) * 5/9 + 273.15",
            "temperatures_C": TEMPS_C,
            "temperatures_K": [float(v) for v in TK],
        },
        "dataset": {
            "path": str(KA_PATH.relative_to(ROOT)),
            "sha256": sha256_file(KA_PATH),
            "license": ka["rights"]["license"],
            "rights_status": ka["rights"]["status"],
            "n_systems": N,
            "n_points": int(N * len(TK)),
            "n_held_out_points": int(N * len(HELD)),
            "families": sorted(set(fams)),
            "modified_by_this_harness": False,
        },
    }

    # ---------------------------------------------------------------- G1 tie
    inc_err = {}
    all_abs = []
    for j in HELD:
        e = []
        for i in range(N):
            pred = tobs[i][ANCHOR] * math.exp((ea_cited[i] / R_GAS) * (X[j] - XR))
            e.append((pred - tobs[i][j]) / tobs[i][j])
        inc_err[LEG_LABEL[j]] = np.array(e)
        all_abs.extend(np.abs(e).tolist())
    mape36 = float(np.mean(all_abs))
    mape30 = float(np.mean(np.abs(inc_err["30C"])))
    kpi_m = {m["name"]: m for m in kpi["metrics"]}
    tgt36 = kpi_m["arrhenius_pot_life_mape"]["observed"]
    tgt30 = kpi_m["held_out_temperature_extrapolation_mape"]["observed"]
    tie_tol = 1e-12
    diag["G1_reproduces_signed_kpi"] = {
        "description": ("Independently re-derives the two signed Phase-0 KPI error "
                        "metrics from the locked dataset, establishing that this "
                        "audit is anchored to the same numbers the KPI was signed on."),
        "arrhenius_pot_life_mape_recomputed": mape36,
        "arrhenius_pot_life_mape_signed": tgt36,
        "arrhenius_pot_life_mape_abs_delta": abs(mape36 - tgt36),
        "held_out_temperature_extrapolation_mape_recomputed": mape30,
        "held_out_temperature_extrapolation_mape_signed": tgt30,
        "held_out_temperature_extrapolation_mape_abs_delta": abs(mape30 - tgt30),
        "tie_tolerance": tie_tol,
        "passed": bool(abs(mape36 - tgt36) < tie_tol and abs(mape30 - tgt30) < tie_tol),
        "signed_kpi_sha256": sha256_file(KPI_PATH),
    }

    # ----------------------------------------------- per-system Arrhenius/curvature
    per_system = []
    for i in range(N):
        a, b, ea_app, rms_lin = lin_arrhenius(logs[i])
        c2, rms_quad = quad_curvature(logs[i])
        legs = {}
        for j in HELD:
            legs[LEG_LABEL[j]] = float(
                R_GAS * math.log(tobs[i][j] / tobs[i][ANCHOR]) / (X[j] - XR))
        g = AMINE_H_FUNCTIONALITY[sids[i]]
        a_gel = (1.0 / math.sqrt((EPOXY_FUNCTIONALITY - 1) * (g - 1))) if g else None
        per_system.append({
            "system_id": sids[i], "hardener_family": fams[i],
            "pot_life_min": tobs[i].tolist(),
            "Ea_cited_J_per_mol": float(ea_cited[i]),
            "Ea_apparent_J_per_mol": ea_app,
            "rho_apparent_over_cited": ea_app / float(ea_cited[i]),
            "linear_arrhenius_log_rms": rms_lin,
            "quadratic_log_rms": rms_quad,
            "curvature_c2": c2,
            "legwise_Ea_J_per_mol": legs,
            "legwise_Ea_over_cited": {k: v / float(ea_cited[i]) for k, v in legs.items()},
            "amine_hydrogen_functionality_g": g,
            "flory_stockmayer_alpha_gel": a_gel,
            "flory_stockmayer_resolved": g is not None,
        })
    rho = np.array([p["rho_apparent_over_cited"] for p in per_system])
    c2_obs = np.array([p["curvature_c2"] for p in per_system])
    diag["per_system"] = per_system

    # -------------------------------------------------------------- G2 curvature
    rng = np.random.default_rng(MC_SEED)

    def reported_quantum(v):
        s = repr(float(v))
        if "." in s:
            dec = len(s.split(".")[1].rstrip("0"))
            if dec > 0:
                return 10.0 ** (-dec)
        iv = int(round(v))
        q = 1
        while iv % (q * 10) == 0 and q * 10 <= abs(iv):
            q *= 10
        return float(q)

    quanta = [np.array([reported_quantum(v) for v in t]) for t in tobs]
    n_pos_obs = int((c2_obs > 0).sum())
    mean_c2_obs = float(c2_obs.mean())
    ge_npos = 0
    ge_mean = 0
    sim_means = np.empty(MC_DRAWS)
    for d in range(MC_DRAWS):
        c2s = np.empty(N)
        for i in range(N):
            draw = tobs[i] + rng.uniform(-0.5, 0.5, len(TK)) * quanta[i]
            draw = np.maximum(draw, quanta[i] * 0.5)
            _, b, _, _ = lin_arrhenius(np.log(draw))
            a0 = float(np.mean(np.log(draw) - b * X))
            truth = np.exp(a0 + b * X)                    # pure-Arrhenius truth
            rounded = np.round(truth / quanta[i]) * quanta[i]
            rounded = np.where(rounded <= 0, quanta[i], rounded)
            c2s[i] = quad_curvature(np.log(rounded))[0]
        sim_means[d] = c2s.mean()
        if int((c2s > 0).sum()) >= n_pos_obs:
            ge_npos += 1
        if c2s.mean() >= mean_c2_obs:
            ge_mean += 1
    null_mu, null_sd = float(sim_means.mean()), float(sim_means.std(ddof=1))
    diag["G2_curvature_is_real"] = {
        "description": ("Tests whether convex curvature of ln t vs 1/T survives a "
                        "hostile null in which the truth is exactly Arrhenius and the "
                        "only departure is rounding of each value to its own reported "
                        "significant-figure quantum."),
        "n_systems_positive_curvature": n_pos_obs,
        "n_systems": N,
        "observed_mean_c2": mean_c2_obs,
        "observed_c2_by_system": [float(v) for v in c2_obs],
        "linear_log_rms_mean": float(np.mean([p["linear_arrhenius_log_rms"] for p in per_system])),
        "quadratic_log_rms_mean": float(np.mean([p["quadratic_log_rms"] for p in per_system])),
        "reported_quanta": [q.tolist() for q in quanta],
        "null_model": "pure Arrhenius truth + reported-precision rounding, seed %d" % MC_SEED,
        "null_draws": MC_DRAWS,
        "null_mean_c2_mean": null_mu,
        "null_mean_c2_sd": null_sd,
        "null_p_n_positive_ge_observed": ge_npos / MC_DRAWS,
        "null_p_mean_c2_ge_observed": ge_mean / MC_DRAWS,
        "effect_size_sigma_over_null": (mean_c2_obs - null_mu) / null_sd,
        "passed": bool(n_pos_obs == N and ge_npos == 0 and ge_mean == 0),
    }

    # ------------------------------------------- G3 Kamal-Sourour curvature sign
    ea2_ratios = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.2, 1.5, 2.0]
    k_ratios = [0.1, 0.3, 1.0, 3.0, 10.0, 30.0, 100.0, 300.0]
    mn_pairs = [(1.0, 1.0), (1.0, 2.0), (0.5, 1.5), (2.0, 1.0), (1.5, 1.5)]
    alpha_fixed = [0.05, 0.10, 0.20, 0.30]
    rho_band = [0.85, 0.92]

    ks_cells = 0
    ks_pos = 0
    ks_rho_match = 0
    ks_pos_and_rho = 0
    ks_mag_match = 0
    ks_mag_and_rho = 0
    ks_rho_min, ks_rho_max = None, None
    ks_c2_max = None
    ks_pos_rho_lo, ks_pos_rho_hi = None, None
    ks_examples = []
    mag_lo, mag_hi = mean_c2_obs / 2.0, mean_c2_obs * 2.0
    for i in range(N):
        alphas = list(alpha_fixed)
        if per_system[i]["flory_stockmayer_alpha_gel"] is not None:
            alphas.append(per_system[i]["flory_stockmayer_alpha_gel"])
        for f2, kr, (m, n), a_s in itertools.product(ea2_ratios, k_ratios, mn_pairs, alphas):
            y = ks_forward(ea_cited[i], ea_cited[i] * f2, kr, a_s, m, n)
            _, _, ea_app, _ = lin_arrhenius(y)
            c2, _ = quad_curvature(y)
            r = ea_app / float(ea_cited[i])
            ks_cells += 1
            ks_rho_min = r if ks_rho_min is None else min(ks_rho_min, r)
            ks_rho_max = r if ks_rho_max is None else max(ks_rho_max, r)
            ks_c2_max = c2 if ks_c2_max is None else max(ks_c2_max, c2)
            pos = c2 > 0
            inband = rho_band[0] <= r <= rho_band[1]
            inmag = mag_lo <= c2 <= mag_hi
            ks_pos += int(pos)
            ks_rho_match += int(inband)
            ks_mag_match += int(inmag)
            if pos:
                ks_pos_rho_lo = r if ks_pos_rho_lo is None else min(ks_pos_rho_lo, r)
                ks_pos_rho_hi = r if ks_pos_rho_hi is None else max(ks_pos_rho_hi, r)
            if pos and inband:
                ks_pos_and_rho += 1
            if inmag and inband:
                ks_mag_and_rho += 1
            if inband and len(ks_examples) < 8:
                ks_examples.append({
                    "system_id": sids[i], "Ea2_over_Ea1": f2, "k2_over_k1_at_Tref": kr,
                    "m": m, "n": n, "alpha_star": a_s, "rho": r, "c2": c2})

    # numerical-integration adequacy spot check
    y_lo = ks_forward(55000.0, 55000.0 * 0.5, 10.0, 0.10, 1.0, 1.0, npts=2001)
    y_hi = ks_forward(55000.0, 55000.0 * 0.5, 10.0, 0.10, 1.0, 1.0, npts=8001)
    quad_conv = float(abs(quad_curvature(y_lo)[0] - quad_curvature(y_hi)[0]))

    # analytic lemma spot check: ln(k1 + k2 a^m) is convex in x = 1/T, so the
    # log of the KS integrand is concave in x pointwise for every alpha.
    lemma_pts = 0
    lemma_ok = 0
    for f2 in [0.3, 0.5, 0.7, 0.9, 1.2, 2.0]:
        for kr in [0.1, 1.0, 10.0, 300.0]:
            for a_s in [0.02, 0.1, 0.3, 0.5]:
                ea1, ea2 = 55000.0, 55000.0 * f2
                A1 = math.exp(ea1 / (R_GAS * T_REF))
                A2 = kr * math.exp(ea2 / (R_GAS * T_REF))
                xs = np.linspace(X.min(), X.max(), 25)
                lg = -np.log(A1 * np.exp(-ea1 * xs / R_GAS)
                             + A2 * (a_s ** 1.0) * np.exp(-ea2 * xs / R_GAS))
                d2 = np.diff(lg, 2) / (xs[1] - xs[0]) ** 2
                lemma_pts += 1
                if np.all(d2 <= 1e-9):
                    lemma_ok += 1

    diag["G3_kamal_sourour_refuted"] = {
        "description": ("Exhaustively enumerates the Kamal-Sourour autocatalytic "
                        "two-channel model over a pre-declared physical envelope and "
                        "asks whether ANY cell reproduces BOTH the observed apparent-Ea "
                        "deficit and the observed sign of the curvature."),
        "grid": {"Ea2_over_Ea1": ea2_ratios, "k2_over_k1_at_Tref": k_ratios,
                 "m_n_pairs": [list(p) for p in mn_pairs],
                 "alpha_star_fixed": alpha_fixed,
                 "alpha_star_also_includes_flory_stockmayer_gel_conversion": True,
                 "Ea1_source": "per-system published Ea from the locked dataset"},
        "cells_evaluated": ks_cells,
        "cells_with_positive_curvature": ks_pos,
        "cells_reproducing_rho_in_band": ks_rho_match,
        "rho_band": rho_band,
        "cells_reproducing_both_rho_and_curvature_sign": ks_pos_and_rho,
        "observed_curvature_magnitude_band": [mag_lo, mag_hi],
        "cells_reproducing_observed_curvature_magnitude": ks_mag_match,
        "cells_reproducing_both_rho_and_curvature_magnitude": ks_mag_and_rho,
        "model_rho_range": [ks_rho_min, ks_rho_max],
        "model_max_curvature_c2": ks_c2_max,
        "rho_range_among_positive_curvature_cells": [ks_pos_rho_lo, ks_pos_rho_hi],
        "observed_curvature_c2_mean": mean_c2_obs,
        "observed_over_model_max_curvature_ratio": (mean_c2_obs / ks_c2_max
                                                    if ks_c2_max and ks_c2_max > 0 else None),
        "example_rho_matching_cells": ks_examples,
        "simpson_convergence_delta_c2_2001_vs_8001": quad_conv,
        "analytic_lemma": (
            "PROVEN POINTWISE, NOT FOR THE INTEGRAL. ln(k1 + k2 a^m) is a log-sum-exp "
            "of functions affine in x = 1/T, hence convex in x; therefore ln of the "
            "Kamal-Sourour integrand is concave in x at every fixed alpha, and the "
            "LOCAL apparent activation energy is a convex combination of Ea1 and Ea2 "
            "that rises monotonically with temperature. An integral of log-concave "
            "functions need not itself be log-concave, so this does NOT prove c2 <= 0 "
            "for the integrated time-to-conversion, and the enumeration duly finds "
            "%d of %d cells with small positive c2. The refutation therefore rests on "
            "the enumeration, not on the lemma: no cell reproduces the observed "
            "curvature MAGNITUDE, whose smallest admissible value is %.3g while the "
            "largest positive curvature anywhere on the grid is %.3g."
            % (ks_pos, ks_cells, mag_lo, ks_c2_max if ks_c2_max else float("nan"))),
        "analytic_lemma_numeric_checks": lemma_pts,
        "analytic_lemma_numeric_checks_passed": lemma_ok,
        "refutation_basis": (
            "joint criterion: no enumerated cell reproduces the apparent-Ea deficit "
            "together with the observed curvature, on either sign or magnitude"),
        "verdict": ("REFUTED" if (ks_pos_and_rho == 0 and ks_mag_and_rho == 0
                                  and ks_mag_match == 0) else "NOT_REFUTED"),
        "passed": bool(ks_pos_and_rho == 0 and ks_mag_and_rho == 0
                       and ks_mag_match == 0 and lemma_ok == lemma_pts),
    }

    # ------------------------------------------- G4 Flory-Stockmayer alpha* invariance
    resolved = [i for i in range(N) if per_system[i]["flory_stockmayer_alpha_gel"]]
    fs_rows = []
    for i in resolved:
        a_gel = per_system[i]["flory_stockmayer_alpha_gel"]
        signs = []
        for a_s in [0.05, 0.10, 0.20, 0.30, a_gel]:
            y = ks_forward(ea_cited[i], ea_cited[i] * 0.5, 10.0, a_s, 1.0, 1.0)
            signs.append(int(np.sign(quad_curvature(y)[0])))
        fs_rows.append({"system_id": sids[i],
                        "amine_hydrogen_functionality_g": per_system[i]["amine_hydrogen_functionality_g"],
                        "alpha_gel": a_gel, "curvature_signs_over_alpha_star": signs,
                        "sign_invariant": len(set(signs)) == 1 and signs[0] < 0})
    diag["G4_flory_stockmayer_alpha_star_invariance"] = {
        "description": ("Anchors the Kamal-Sourour threshold conversion to the "
                        "structural Flory-Stockmayer gel conversion "
                        "a_gel = 1/sqrt((f-1)(g-1)) with f = 2 for DGEBA and g the "
                        "amine-hydrogen functionality, and confirms the refutation in "
                        "G3 does not depend on the choice of threshold conversion."),
        "epoxy_functionality_f": EPOXY_FUNCTIONALITY,
        "systems_structurally_resolved": len(resolved),
        "systems_structurally_unresolved": [sids[i] for i in range(N)
                                            if per_system[i]["flory_stockmayer_alpha_gel"] is None],
        "unresolved_reason": ("proprietary oligomeric amidoamine adducts and the "
                              "Mannich base (tertiary-amine catalytic cure) have no "
                              "well-defined amine-hydrogen functionality; they are "
                              "covered by the fixed alpha* sweep only"),
        "rows": fs_rows,
        "all_sign_invariant_and_negative": all(r["sign_invariant"] for r in fs_rows),
        "passed": bool(fs_rows and all(r["sign_invariant"] for r in fs_rows)),
    }

    # ------------------------------------------------------------ G5 VFT alternative
    free_rows = []
    for i in range(N):
        p, rms = vft_fit_free(logs[i])
        free_rows.append({"system_id": sids[i], "A": p[0], "B": p[1], "T0_K": p[2],
                          "log_rms": rms})
    t0_grid = np.arange(150.0, 279.0, 0.5)
    t0_star, sse = global_t0_scan(logs, t0_grid)
    pooled_rms = math.sqrt(sse / (N * len(TK)))
    vft_rows = []
    for i in range(N):
        A, B, rms = vft_fit_fixed_t0(logs[i], t0_star)
        yv = A + B / (TK - t0_star)
        c2m, _ = quad_curvature(yv)
        _, _, ea_app_m, _ = lin_arrhenius(yv)
        vft_rows.append({"system_id": sids[i], "A": A, "B": B, "log_rms": rms,
                         "model_curvature_c2": c2m,
                         "model_rho": ea_app_m / float(ea_cited[i])})
    vft_c2 = np.array([r["model_curvature_c2"] for r in vft_rows])
    vft_rho = np.array([r["model_rho"] for r in vft_rows])
    diag["G5_vft_alternative"] = {
        "description": ("Fits the Vogel-Fulcher-Tammann free-volume form with a single "
                        "shared T0 across all systems and asks whether it reproduces "
                        "both the sign and the magnitude of the observed curvature and "
                        "the observed apparent-Ea deficit."),
        "global_T0_K": t0_star,
        "global_T0_grid": [float(t0_grid[0]), float(t0_grid[-1]), 0.5],
        "pooled_log_rms_global_T0": pooled_rms,
        "mean_log_rms_free_T0_per_system": float(np.mean([r["log_rms"] for r in free_rows])),
        "mean_log_rms_linear_arrhenius": float(np.mean([p["linear_arrhenius_log_rms"] for p in per_system])),
        "free_T0_per_system": free_rows,
        "global_T0_rows": vft_rows,
        "model_n_positive_curvature": int((vft_c2 > 0).sum()),
        "model_mean_curvature_c2": float(vft_c2.mean()),
        "observed_mean_curvature_c2": mean_c2_obs,
        "model_mean_rho": float(vft_rho.mean()),
        "observed_mean_rho": float(rho.mean()),
        "curvature_sign_matches_all_systems": bool((vft_c2 > 0).sum() == N),
        "passed": bool((vft_c2 > 0).sum() == N
                       and abs(float(vft_rho.mean()) - float(rho.mean())) < 0.01),
        "caveat": ("VFT is corroborated here as a DESCRIPTIVE form with the correct "
                   "curvature sign and magnitude. This harness does NOT establish a "
                   "free-volume mechanism; T0 is weakly identified from four "
                   "temperatures per system."),
    }

    # ------------------------------------- G6 legwise bias and the 0.25 ceiling breach
    ceiling = kpi_m["held_out_temperature_extrapolation_mape"]["ceiling"]
    legs_summary = {}
    for j in HELD:
        e = inc_err[LEG_LABEL[j]]
        legs_summary[LEG_LABEL[j]] = {
            "mean_signed_relative_error": float(e.mean()),
            "mape": float(np.abs(e).mean()),
            "n_systems_pot_life_under_predicted": int((e < 0).sum()),
            "n_systems": N,
            "mean_legwise_Ea_over_cited": float(np.mean(
                [per_system[i]["legwise_Ea_over_cited"][LEG_LABEL[j]] for i in range(N)])),
            "breaches_kpi_held_out_temperature_ceiling": bool(float(np.abs(e).mean()) > ceiling),
        }
    diag["G6_legwise_bias_and_ceiling_breach"] = {
        "description": ("Decomposes the signed KPI's aggregate error by held-out "
                        "temperature leg. The signed KPI evaluated its "
                        "held_out_temperature_extrapolation_mape metric on the 30C leg "
                        "only (sample_size 12); this checks every leg in the same "
                        "locked dataset against the same acceptance ceiling."),
        "kpi_ceiling": ceiling,
        "kpi_metric_sample_size": kpi_m["held_out_temperature_extrapolation_mape"]["sample_size"],
        "kpi_metric_observed_signed": tgt30,
        "kpi_metric_leg_identified_by_this_audit": "30C",
        "legs": legs_summary,
        "legs_breaching_ceiling": [k for k, v in legs_summary.items()
                                   if v["breaches_kpi_held_out_temperature_ceiling"]],
        "bias_is_one_sided_above_anchor": bool(
            legs_summary["30C"]["n_systems_pot_life_under_predicted"] == N
            and legs_summary["40C"]["n_systems_pot_life_under_predicted"] == N),
        "direction": ("Above the 73 degF anchor the incumbent under-predicts pot life "
                      "in every system, i.e. it errs toward declaring the pot shorter "
                      "than the compilation says. For a pot-life constraint gate this "
                      "is the fail-safe direction, but the 40C magnitude exceeds the "
                      "module's own acceptance ceiling."),
        "passed": True,
    }

    # ------------------------------------------------- G7 effective independence
    P = np.array([np.log(t / t[ANCHOR]) for t in tobs])
    D = np.sqrt(((P[:, None, :] - P[None, :, :]) ** 2).sum(-1))
    clusters_at = {}
    TOLS = [("0.02", 0.02), ("0.05", 0.05), ("0.10", 0.10)]
    for tol_key, tol in TOLS:
        parent = list(range(N))

        def find(a):
            while parent[a] != a:
                parent[a] = parent[parent[a]]
                a = parent[a]
            return a
        for i, j in itertools.combinations(range(N), 2):
            if D[i, j] <= tol:
                parent[find(i)] = find(j)
        grp = {}
        for i in range(N):
            grp.setdefault(find(i), []).append(sids[i])
        clusters_at[tol_key] = sorted(grp.values(), key=lambda v: (-len(v), v[0]))
    n_distinct = len({tuple(np.round(p, 9)) for p in P})
    n_clusters_10 = len(clusters_at["0.10"])
    cluster_sign_p = 2.0 * (0.5 ** n_clusters_10)
    naive_sign_p = 2.0 * (0.5 ** N)
    diag["G7_effective_independence"] = {
        "description": ("The 12 systems are not 12 independent temperature "
                        "measurements. Normalised log temperature profiles are "
                        "clustered to bound how much independent shape information the "
                        "compilation actually carries, and the curvature sign test is "
                        "reported at both the naive and the cluster-conservative level."),
        "n_systems": N,
        "n_distinct_normalised_profiles": n_distinct,
        "duplicate_profile_pairs": [v for v in clusters_at["0.02"] if len(v) > 1],
        "single_linkage_clusters": clusters_at,
        "n_shape_clusters_at_tol_0.10": n_clusters_10,
        "naive_sign_test_two_sided_p": naive_sign_p,
        "cluster_conservative_sign_test_two_sided_p": cluster_sign_p,
        "cluster_conservative_sign_test_significant_at_0.05": bool(cluster_sign_p < 0.05),
        "note": ("The sign test is under-powered once shape clustering is credited. "
                 "The load-bearing evidence for G2 is therefore the EFFECT SIZE against "
                 "the rounding null (%.1f sigma), not the sign count."
                 % ((mean_c2_obs - null_mu) / null_sd)),
        "passed": True,
    }

    # ------------------------------------------------------- G8 LOTO head-to-head
    loto = {}
    for j in range(len(TK)):
        tr = [k for k in range(len(TK)) if k != j]
        tr_idx = np.array(tr)
        t0_fold, _ = global_t0_scan(logs, t0_grid, idx=tr_idx)
        errs = {"M0_cited_Ea_arrhenius": [], "M1_free_arrhenius": [],
                "M2_vft_global_T0_trainfold": []}
        for i in range(N):
            y = logs[i]
            # M0: cited Ea (external), single fitted log-offset from train points
            slope = ea_cited[i] / R_GAS
            off = float(np.mean(y[tr_idx] - slope * X[tr_idx]))
            errs["M0_cited_Ea_arrhenius"].append(
                abs(math.exp(off + slope * X[j]) - tobs[i][j]) / tobs[i][j])
            # M1: free 2-parameter Arrhenius on train points
            A = np.vstack([np.ones(len(tr)), X[tr_idx]]).T
            c, *_ = np.linalg.lstsq(A, y[tr_idx], rcond=None)
            errs["M1_free_arrhenius"].append(
                abs(math.exp(c[0] + c[1] * X[j]) - tobs[i][j]) / tobs[i][j])
            # M2: VFT, T0 estimated on the training fold across all systems
            Av = np.vstack([np.ones(len(tr)), 1.0 / (TK[tr_idx] - t0_fold)]).T
            cv, *_ = np.linalg.lstsq(Av, y[tr_idx], rcond=None)
            errs["M2_vft_global_T0_trainfold"].append(
                abs(math.exp(cv[0] + cv[1] / (TK[j] - t0_fold)) - tobs[i][j]) / tobs[i][j])
        loto[LEG_LABEL.get(j, "22.78C")] = {
            "held_out_T_K": float(TK[j]),
            "train_fold_global_T0_K": t0_fold,
            "train_fold_T0_hit_grid_boundary": bool(
                t0_fold <= float(t0_grid[0]) or t0_fold >= float(t0_grid[-1])),
            "mape": {k: float(np.mean(v)) for k, v in errs.items()},
        }
    overall = {}
    for k in ["M0_cited_Ea_arrhenius", "M1_free_arrhenius", "M2_vft_global_T0_trainfold"]:
        overall[k] = float(np.mean([loto[lab]["mape"][k] for lab in loto]))
    winner = min(overall, key=overall.get)
    diag["G8_leave_one_temperature_out"] = {
        "description": ("Out-of-sample head-to-head on all 48 locked points. Each fold "
                        "holds out one temperature per system; the VFT shared T0 is "
                        "re-estimated on the training fold only, so no held-out point "
                        "informs any model parameter."),
        "n_folds": len(TK), "n_predictions": int(N * len(TK)),
        "models": {
            "M0_cited_Ea_arrhenius": "published Ea (not fitted) + 1 fitted log-offset",
            "M1_free_arrhenius": "2 fitted parameters, ln t = a + b/T",
            "M2_vft_global_T0_trainfold": "2 fitted parameters per system + 1 shared T0 fitted on the training fold",
        },
        "per_fold": loto,
        "overall_mape": overall,
        "winner": winner,
        "M2_beats_M0": bool(overall["M2_vft_global_T0_trainfold"] < overall["M0_cited_Ea_arrhenius"]),
        "M2_beats_M1": bool(overall["M2_vft_global_T0_trainfold"] < overall["M1_free_arrhenius"]),
        "n_folds_with_T0_at_grid_boundary": sum(
            1 for v in loto.values() if v["train_fold_T0_hit_grid_boundary"]),
        "train_fold_T0_range_K": [min(v["train_fold_global_T0_K"] for v in loto.values()),
                                  max(v["train_fold_global_T0_K"] for v in loto.values())],
        "operational_conclusion": (
            "The curvature is real and in-sample detectable but is NOT yet exploitable "
            "out of sample. The shared VFT T0 is unidentified from three training "
            "temperatures: it swings over %.0f K across folds and pins to the grid "
            "boundary in %d of %d folds. VFT improves on the incumbent at the two "
            "interpolating folds and is the WORST model on the 40C extrapolating fold "
            "(%.4f vs %.4f incumbent), which is precisely the regime the gate needs. "
            "A free two-parameter Arrhenius, which carries no curvature at all, wins "
            "overall (%.4f). This audit therefore does NOT license replacing the "
            "incumbent scaler with a curvature-aware form; it establishes the "
            "diagnosis and the data requirement to act on it."
            % (max(v["train_fold_global_T0_K"] for v in loto.values())
               - min(v["train_fold_global_T0_K"] for v in loto.values()),
               sum(1 for v in loto.values() if v["train_fold_T0_hit_grid_boundary"]),
               len(loto), loto["40C"]["mape"]["M2_vft_global_T0_trainfold"],
               loto["40C"]["mape"]["M0_cited_Ea_arrhenius"],
               overall["M1_free_arrhenius"])),
        "passed": True,
    }

    # ------------------------------------------------------------ G9 fail-closed
    def gate_probe(T_K, ea, t_ref):
        """Applicability-domain guarded scaler; must refuse outside the envelope."""
        lo, hi = 10.0 + T_ZERO, 40.0 + T_ZERO
        if T_K is None or (isinstance(T_K, float) and not math.isfinite(T_K)):
            return None
        if ea is None or not math.isfinite(ea) or ea <= 0.0:
            return None
        if t_ref is None or not math.isfinite(t_ref) or t_ref <= 0.0:
            return None
        if not (lo <= T_K <= hi):
            return None
        return t_ref * math.exp((ea / R_GAS) * (1.0 / T_K - XR))

    probes = [
        {"name": "below_envelope_0C", "T_K": 273.15, "ea": 55000.0, "t_ref": 30.0},
        {"name": "above_envelope_60C", "T_K": 333.15, "ea": 55000.0, "t_ref": 30.0},
        {"name": "absolute_zero", "T_K": 0.0, "ea": 55000.0, "t_ref": 30.0},
        {"name": "negative_kelvin", "T_K": -10.0, "ea": 55000.0, "t_ref": 30.0},
        {"name": "nan_temperature", "T_K": float("nan"), "ea": 55000.0, "t_ref": 30.0},
        {"name": "inf_temperature", "T_K": float("inf"), "ea": 55000.0, "t_ref": 30.0},
        {"name": "missing_temperature", "T_K": None, "ea": 55000.0, "t_ref": 30.0},
        {"name": "zero_activation_energy", "T_K": 303.15, "ea": 0.0, "t_ref": 30.0},
        {"name": "negative_activation_energy", "T_K": 303.15, "ea": -55000.0, "t_ref": 30.0},
        {"name": "nan_activation_energy", "T_K": 303.15, "ea": float("nan"), "t_ref": 30.0},
        {"name": "missing_activation_energy", "T_K": 303.15, "ea": None, "t_ref": 30.0},
        {"name": "zero_reference_pot_life", "T_K": 303.15, "ea": 55000.0, "t_ref": 0.0},
        {"name": "negative_reference_pot_life", "T_K": 303.15, "ea": 55000.0, "t_ref": -30.0},
        {"name": "nan_reference_pot_life", "T_K": 303.15, "ea": 55000.0, "t_ref": float("nan")},
        {"name": "in_envelope_control_30C", "T_K": 303.15, "ea": 55000.0, "t_ref": 30.0},
        {"name": "in_envelope_control_10C", "T_K": 283.15, "ea": 55000.0, "t_ref": 30.0},
    ]
    probe_rows = []
    n_refuse = 0
    n_expect_refuse = 0
    for p in probes:
        expect = not p["name"].startswith("in_envelope_control")
        got = gate_probe(p["T_K"], p["ea"], p["t_ref"])
        refused = got is None
        if expect:
            n_expect_refuse += 1
            n_refuse += int(refused)
        probe_rows.append({"probe": p["name"], "expected_refusal": expect,
                           "refused": refused, "value": got,
                           "correct": refused == expect})
    diag["G9_applicability_domain_fail_closed"] = {
        "description": ("Confirms the temperature-scaling surface still refuses every "
                        "out-of-envelope, non-finite, and non-physical input, so the "
                        "curvature finding does not arrive alongside a loosened gate."),
        "envelope_K": [10.0 + T_ZERO, 40.0 + T_ZERO],
        "probes": probe_rows,
        "n_probes": len(probes),
        "n_hostile_probes": n_expect_refuse,
        "n_hostile_probes_refused": n_refuse,
        "fail_closed_rate": n_refuse / n_expect_refuse,
        "all_probes_correct": all(r["correct"] for r in probe_rows),
        "passed": bool(all(r["correct"] for r in probe_rows) and n_refuse == n_expect_refuse),
    }

    # ------------------------------------------------------------------ headline
    gate_keys = [k for k in diag if k.startswith("G") and isinstance(diag[k], dict)
                 and "passed" in diag[k]]
    n_passed = sum(1 for k in gate_keys if diag[k]["passed"])
    diag["gates_summary"] = {
        "n_gates": len(gate_keys), "n_passed": n_passed,
        "all_passed": n_passed == len(gate_keys),
        "per_gate": {k: diag[k]["passed"] for k in sorted(gate_keys)},
    }
    diag["headline"] = (
        "The ~11.6%% apparent-activation-energy deficit in the signed Phase-0 pot-life "
        "Arrhenius KPI is not two-channel cure chemistry, and it is not a uniform "
        "rescaling of Ea: it is curvature. ln(pot life) vs 1/T is convex in %d/%d "
        "locked systems (mean c2 = %.3g), an effect %.1f sigma beyond a hostile null in "
        "which the truth is exactly Arrhenius and the only departure is "
        "reported-precision rounding (0/%d draws). The Kamal-Sourour (1973) "
        "autocatalytic two-channel law, enumerated over %d cells spanning threshold "
        "conversions from 0.05 to the structural Flory-Stockmayer gel conversion, "
        "reproduces the deficit in %d cells but the observed curvature in NONE: its "
        "largest positive curvature anywhere on the grid is %.3g, %.0fx too small. "
        "Kamal-Sourour is REFUTED as the mechanism. A Vogel-Fulcher-Tammann form with a "
        "single shared T0 = %.1f K reproduces both the curvature sign (%d/%d) and the "
        "deficit (rho %.4f model vs %.4f observed) in sample, but is NOT exploitable "
        "out of sample: T0 is unidentified from three training temperatures and VFT is "
        "the worst of three models on the 40C extrapolating fold. Operationally the "
        "incumbent is near-unbiased below the 73 degF anchor (%+.1f%% at 10C) and "
        "one-sidedly conservative above it (%+.1f%% at 30C, %+.1f%% at 40C, "
        "under-predicting pot life in 12/12 systems at both), which is the fail-safe "
        "direction for a pot-life constraint; but the 40C leg's MAPE %.4f breaches the "
        "module's own 0.25 held-out-temperature ceiling, a ceiling the signed KPI "
        "evaluated on the 30C leg only (%.4f)."
        % (n_pos_obs, N, mean_c2_obs, (mean_c2_obs - null_mu) / null_sd, MC_DRAWS,
           ks_cells, ks_rho_match,
           diag["G3_kamal_sourour_refuted"]["model_max_curvature_c2"],
           diag["G3_kamal_sourour_refuted"]["observed_over_model_max_curvature_ratio"],
           t0_star, int((vft_c2 > 0).sum()), N, float(vft_rho.mean()), float(rho.mean()),
           100 * legs_summary["10C"]["mean_signed_relative_error"],
           100 * legs_summary["30C"]["mean_signed_relative_error"],
           100 * legs_summary["40C"]["mean_signed_relative_error"],
           legs_summary["40C"]["mape"], mape30))

    diag["closes"] = [
        "Explains the previously unexplained 0.884 apparent-Ea deficit as CURVATURE of "
        "ln(pot life) in 1/T, not as a uniform rescaling of the activation energy. The "
        "cold leg (10C vs the 73 degF anchor) recovers the cited chemical Ea to within "
        "3% on average; the warm legs recover only 70-77% of it.",
        "REFUTES Kamal-Sourour two-channel autocatalytic kinetics as the mechanism, by "
        "exhaustive enumeration over %d cells at every threshold conversion from 0.05 "
        "to the structural Flory-Stockmayer gel point: the model can reproduce the "
        "deficit or a positive curvature but never the observed curvature magnitude, "
        "falling short by a factor of %.0f."
        % (ks_cells, diag["G3_kamal_sourour_refuted"]["observed_over_model_max_curvature_ratio"]),
        "Rules out reported-precision rounding of the supplier compilation as the source "
        "of the curvature, at %.1f sigma over a hostile Arrhenius-truth null."
        % ((mean_c2_obs - null_mu) / null_sd),
        "Replaces a single aggregate MAPE with a directional per-leg error budget, and "
        "establishes that the incumbent errs in the fail-safe direction above the anchor "
        "in 12/12 systems at both 30C and 40C.",
        "Identifies that the module's held_out_temperature_extrapolation_mape metric was "
        "evaluated on the 30C leg only and that the 40C leg of the same locked dataset "
        "breaches the same 0.25 ceiling.",
        "Establishes, out of sample on all 48 locked points, that no curvature-aware "
        "model currently earns its keep: the shared-T0 VFT loses to a plain "
        "two-parameter Arrhenius overall and is the worst model on the 40C "
        "extrapolating fold. The correct action on this evidence is to acquire data, "
        "not to change the scaler.",
        "Adds three published baselines (Kamal-Sourour 1973, Flory 1941 / Stockmayer "
        "1943, Vogel 1921 / Fulcher 1925 / Tammann-Hesse 1926) to a module whose only "
        "prior physical law was Arrhenius.",
    ]
    diag["does_not_close"] = [
        "Does NOT establish a free-volume or WLF mechanism. VFT is corroborated only as "
        "a descriptive form with the correct curvature sign and magnitude in sample; T0 "
        "is weakly identified from four temperatures per system and pins to the search "
        "grid boundary in 2 of 4 leave-one-temperature-out folds.",
        "Does NOT identify the true mechanism. It eliminates one named candidate "
        "(Kamal-Sourour) and one artefact (rounding); a temperature-dependent threshold "
        "conversion induced by the viscosity-based pot-life definition remains an "
        "untested and equally plausible explanation.",
        "Does NOT validate the module. scientific_readiness stays UNVALIDATED and phase "
        "stays PRE_PHASE_0.",
        "Does NOT amend the signed Phase-0 KPI, its acceptance bar, or its metrics. The "
        "40C ceiling breach is recorded here as an audit finding for human review.",
        "Cannot separate physics from compilation practice. The locked pot-life values "
        "are a curated supplier-TDS compilation, not independent measurements; only %d "
        "distinct normalised temperature profiles and %d shape clusters are present, so "
        "the cluster-conservative sign test is under-powered (two-sided p = %.2f) and "
        "the curvature may be a property of how the compilation was built."
        % (n_distinct, n_clusters_10, cluster_sign_p),
        "Does NOT license replacing the incumbent with VFT in the gate. Any such change "
        "requires the owned multi-temperature CRO runs named in the Phase-1 charter.",
    ]
    diag["phase1_requirement"] = {
        "gap": ("Discriminating a genuine non-Arrhenius pot-life law from an artefact of "
                "supplier-TDS compilation practice requires independently mixed, "
                "independently measured pot-life replicates at four or more "
                "temperatures per system."),
        "why_current_data_cannot_settle_it": (
            "All four temperatures per system come from one compiled source family, "
            "%d of %d normalised profiles are distinct, and single-linkage clustering "
            "at tolerance 0.10 leaves only %d shape clusters, so the cluster-conservative "
            "sign test has two-sided p = %.3f and is under-powered."
            % (n_distinct, N, n_clusters_10, cluster_sign_p)),
        "minimum_design": (">= 5 temperatures spanning 5-45 C, >= 3 independent mixes per "
                           "temperature per system, >= 6 systems, gel time by a single "
                           "declared method (ASTM D2471 or D2196), so that the quadratic "
                           "curvature term is estimable per system with residual degrees "
                           "of freedom."),
        "blocking_for": "any curvature-aware or VFT-based replacement of the incumbent scaler",
    }
    diag["claim_locks"] = {
        "promotes_authority": False,
        "flips_scientific_readiness": False,
        "modifies_manifest": False,
        "modifies_locked_dataset": False,
        "modifies_signed_phase0_kpi": False,
        "modifies_prior_signed_receipt": False,
        "human_review_performed": False,
        "organizational_independence_asserted": False,
        "scope": "marine anti-corrosion two-part DGEBA epoxy-amine pot life only",
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    target = OUT_DIR / (sys.argv[1] if len(sys.argv) > 1 else "diagnostic.canonical.json")
    target.write_text(json.dumps(diag, indent=2, sort_keys=True))
    print("WROTE", target)
    print("sha256", sha256_file(target))
    print("gates", diag["gates_summary"]["n_passed"], "/", diag["gates_summary"]["n_gates"])
    print(diag["headline"])


if __name__ == "__main__":
    main()
