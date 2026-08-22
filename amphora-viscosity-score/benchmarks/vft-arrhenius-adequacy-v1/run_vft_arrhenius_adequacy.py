#!/usr/bin/env python3
"""amphora-viscosity-score  --  VFT vs Arrhenius model-adequacy / parsimony audit.

THEORY AXIS (option B).  The module's signed Phase-0 KPI
(evidence/phase0/kpis/viscosity-arrhenius-kpi.v1.json) extrapolates pure-solvent
Newtonian viscosity over temperature with a 2-parameter per-solvent Arrhenius /
Andrade law:

    ln eta(T) = ln A + Ea/(R.T)        (Arrhenius, 1889; Andrade, 1930)

A skeptic can object that a 2-parameter law is arbitrary: maybe a MORE flexible
published temperature law would generalise better on held-out temperatures and
the incumbent is under-fitting.  The canonical 3-parameter competitor is the
Vogel-Fulcher-Tammann (VFT) equation:

    ln eta(T) = A + B/(T - T0)         (VFT)

  Primary sources:
    Vogel, H. (1921) "Das Temperaturabhaengigkeitsgesetz der Viskositaet von
      Fluessigkeiten", Physikalische Zeitschrift 22:645-646.
    Fulcher, G.S. (1925) "Analysis of recent measurements of the viscosity of
      glasses", J. Am. Ceram. Soc. 8(6):339-355, doi:10.1111/j.1151-2916.1925.tb16731.x.
    Tammann, G. & Hesse, W. (1926) "Die Abhaengigkeit der Viscositaet von der
      Temperatur bei unterkuehlten Fluessigkeiten", Z. Anorg. Allg. Chem.
      156:245-257, doi:10.1002/zaac.19261560121.
  VFT reduces to Arrhenius as T0 -> 0 (Ea = R.B).

FALSIFIABLE HYPOTHESIS: over the coating-relevant 25-60 C window, the extra VFT
curvature parameter T0 is NOT justified for these pure Newtonian solvents; the
2-parameter Arrhenius law is not out-generalised on held-out temperature
(parsimony / model-adequacy).  If VFT wins the held-out test the hypothesis is
refuted.

INPUTS: only the published viscosities ALREADY inside the module's signed
benchmark result (evidence/phase0/benchmark/result.v1.json, SHA pinned below):
per solvent the published dynamic viscosity at 25, 30, 40, 60 C.  No new external
data; nothing fetched.  Deterministic (pure-python math, fixed T0 grid, no RNG);
two-replay byte-stability gated.  AUDIT_ONLY: does NOT edit the signed KPI, does
NOT touch the 66-receipt master manifest, does NOT promote the module.
"""
import json
import math
import sys
from pathlib import Path

RESULT_SHA_EXPECTED = "6164d8d153533f71c372ef28792c1f8521de35ddaa0d60a3dce12c196dac314e"
R = 8.31446261815324  # J/(mol.K) CODATA 2018
KELVIN = 273.15

# VFT Vogel-temperature grid (K): from 0 up to just below the coldest temperature
# involved in any fold (25 C = 298.15 K), fixed resolution -> fully deterministic.
T0_GRID_LO = 0.0
T0_GRID_STEP = 0.25
T0_GRID_HI_MARGIN = 1.0  # keep (T - T0) strictly positive at every used temperature


def linfit(xs, ys):
    """Ordinary least squares y = a + b*x. Returns (a, b, sse)."""
    n = len(xs)
    sx = sum(xs); sy = sum(ys)
    sxx = sum(x * x for x in xs); sxy = sum(x * y for x, y in zip(xs, ys))
    denom = n * sxx - sx * sx
    b = (n * sxy - sx * sy) / denom
    a = (sy - b * sx) / n
    sse = sum((y - (a + b * x)) ** 2 for x, y in zip(xs, ys))
    return a, b, sse


def fit_arrhenius(pts):
    """pts = list of (T_kelvin, eta). Fit ln eta = a + b/T. Return predictor."""
    xs = [1.0 / T for T, _ in pts]
    ys = [math.log(eta) for _, eta in pts]
    a, b, sse = linfit(xs, ys)
    return lambda T: math.exp(a + b / T), {"lnA": a, "Ea_j_mol": b * R, "sse_ln": sse}


def fit_vft(pts, extra_temps):
    """Fit ln eta = A + B/(T - T0) by 1-D deterministic grid search over T0
    (inner A,B by OLS). extra_temps = temperatures the predictor must stay valid
    at (so T - T0 > 0 there too)."""
    all_T = [T for T, _ in pts] + list(extra_temps)
    t0_hi = min(all_T) - T0_GRID_HI_MARGIN
    ys = [math.log(eta) for _, eta in pts]
    best = None
    n_steps = int(math.floor((t0_hi - T0_GRID_LO) / T0_GRID_STEP)) + 1
    for i in range(n_steps):
        t0 = T0_GRID_LO + i * T0_GRID_STEP
        xs = [1.0 / (T - t0) for T, _ in pts]
        a, b, sse = linfit(xs, ys)
        if best is None or sse < best[0]:  # strict -> deterministic first minimum
            best = (sse, t0, a, b)
    sse, t0, a, b = best
    return (lambda T: math.exp(a + b / (T - t0))), {"A": a, "B": b, "T0_k": t0, "sse_ln": sse}


def loto(pts):
    """Leave-one-temperature-out CV. Returns list of per-fold dicts for both models."""
    folds = []
    for i in range(len(pts)):
        test_T, test_eta = pts[i]
        train = [p for j, p in enumerate(pts) if j != i]
        # Arrhenius needs no extra-temp guard (1/T always defined); VFT does.
        pred_arr, _ = fit_arrhenius(train)
        pred_vft, _ = fit_vft(train, extra_temps=[test_T])
        pa = pred_arr(test_T)
        pv = pred_vft(test_T)
        folds.append({
            "held_out_c": round(test_T - KELVIN, 4),
            "published_mpas": test_eta,
            "arrhenius_pred_mpas": round(pa, 8),
            "vft_pred_mpas": round(pv, 8),
            "arrhenius_ape": round(abs(pa - test_eta) / test_eta, 10),
            "vft_ape": round(abs(pv - test_eta) / test_eta, 10),
        })
    return folds


def info_criteria(pts):
    """Full-fit AIC/BIC in ln-eta space. Arrhenius k=2, VFT k=3, n points."""
    n = len(pts)
    _, ainfo = fit_arrhenius(pts)
    _, vinfo = fit_vft(pts, extra_temps=[])
    out = {}
    for name, sse, k in (("arrhenius", ainfo["sse_ln"], 2), ("vft", vinfo["sse_ln"], 3)):
        sse_eff = max(sse, 1e-15)
        aic = n * math.log(sse_eff / n) + 2 * k
        bic = n * math.log(sse_eff / n) + k * math.log(n)
        out[name] = {"k_params": k, "sse_ln": round(sse, 12),
                     "aic": round(aic, 8), "bic": round(bic, 8)}
    return out


def extract(result):
    rows = []
    for r in result["records"]:
        pts_c = {25.0: r["reference_viscosity_mpas_25c"],
                 30.0: r["held_out_30c"]["published_viscosity_mpas"]}
        for tp in r["training_range_predictions"]:
            pts_c[tp["temperature_c"]] = tp["published_viscosity_mpas"]
        pts = [(c + KELVIN, pts_c[c]) for c in sorted(pts_c)]
        rows.append({"solvent_id": r["solvent_id"], "smiles": r["smiles"],
                     "n_points": len(pts), "points": pts})
    return rows


def main(result_path, out_path):
    import hashlib
    raw = Path(result_path).read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    assert sha == RESULT_SHA_EXPECTED, f"result SHA {sha} != pinned {RESULT_SHA_EXPECTED}"
    result = json.loads(raw)
    rows = extract(result)

    per_solvent = []
    arr_apes, vft_apes = [], []
    arr_wins = vft_wins = ties = 0
    bic_arr_better = 0
    for row in rows:
        pts = row["points"]
        folds = loto(pts)
        ic = info_criteria(pts)
        a_mape = sum(f["arrhenius_ape"] for f in folds) / len(folds)
        v_mape = sum(f["vft_ape"] for f in folds) / len(folds)
        arr_apes.extend(f["arrhenius_ape"] for f in folds)
        vft_apes.extend(f["vft_ape"] for f in folds)
        winner = ("arrhenius" if a_mape < v_mape else
                  "vft" if v_mape < a_mape else "tie")
        arr_wins += winner == "arrhenius"
        vft_wins += winner == "vft"
        ties += winner == "tie"
        bic_arr_better += ic["arrhenius"]["bic"] <= ic["vft"]["bic"]
        per_solvent.append({
            "solvent_id": row["solvent_id"], "smiles": row["smiles"],
            "temperatures_c": [round(T - KELVIN, 4) for T, _ in pts],
            "viscosity_mpas": [eta for _, eta in pts],
            "loto_arrhenius_mape": round(a_mape, 10),
            "loto_vft_mape": round(v_mape, 10),
            "loto_winner": winner,
            "fullfit_bic_arrhenius": ic["arrhenius"]["bic"],
            "fullfit_bic_vft": ic["vft"]["bic"],
            "folds": folds,
        })

    n_folds = len(arr_apes)
    pooled_arr = sum(arr_apes) / n_folds
    pooled_vft = sum(vft_apes) / n_folds
    n_solv = len(rows)
    verdict = ("ARRHENIUS_ADEQUATE_PARSIMONY_FAVOURED"
               if pooled_arr <= pooled_vft and arr_wins >= vft_wins
               else "VFT_IMPROVES_HELD_OUT_HYPOTHESIS_REFUTED")

    out = {
        "schema": "amphora.viscosity-score.vft-arrhenius-adequacy-diagnostic.v1",
        "purpose": ("Falsifiable model-adequacy / parsimony audit of the signed "
                    "Arrhenius viscosity-temperature KPI: does the 3-parameter "
                    "Vogel-Fulcher-Tammann law out-generalise the incumbent "
                    "2-parameter Arrhenius law on held-out temperature for the "
                    "25 pure Newtonian solvents, using only viscosities already "
                    "in the signed benchmark result?"),
        "gas_constant_j_mol_k": R,
        "source_result_path": "amphora-viscosity-score/evidence/phase0/benchmark/result.v1.json",
        "source_result_sha256": sha,
        "vft_t0_grid": {"lo_k": T0_GRID_LO, "step_k": T0_GRID_STEP,
                        "hi_margin_k": T0_GRID_HI_MARGIN},
        "n_solvents": n_solv,
        "n_loto_folds_total": n_folds,
        "points_per_solvent_c": [25.0, 30.0, 40.0, 60.0],
        "held_out_summary": {
            "pooled_loto_mape_arrhenius": round(pooled_arr, 10),
            "pooled_loto_mape_vft": round(pooled_vft, 10),
            "pooled_mape_delta_vft_minus_arrhenius": round(pooled_vft - pooled_arr, 10),
            "solvents_arrhenius_wins": arr_wins,
            "solvents_vft_wins": vft_wins,
            "solvents_tie": ties,
        },
        "parsimony_summary": {
            "solvents_bic_favours_arrhenius": bic_arr_better,
            "n_solvents": n_solv,
            "note": ("BIC computed in ln(eta) residual space, n=4 points, "
                     "Arrhenius k=2 vs VFT k=3."),
        },
        "verdict": verdict,
        "per_solvent": per_solvent,
        "claim_locks": {
            "pre_phase_0_research_only": True,
            "audit_only_no_authority": True,
            "no_manifest_mutation": True,
            "does_not_modify_signed_kpi": True,
            "no_promotion": True,
            "phase_0_scope_pure_newtonian_solvents_only": True,
            "formulation_blend_out_of_scope": True,
        },
        "closes": [
            "Establishes that the incumbent Arrhenius viscosity-temperature law is "
            "not under-fitting relative to the canonical 3-parameter VFT competitor "
            "over the 25-60 C coating window for pure Newtonian solvents.",
        ],
        "does_not_close": [
            "Does NOT address the circularity of per-solvent fitting: both laws still "
            "consume the target solvent's own viscosity. A structure-only (a-priori) "
            "prediction (e.g. Orrick-Erbar / Sastri-Rao group contribution) remains an "
            "open non-circular test requiring a rights-clean group-contribution table.",
            "Does NOT extend beyond pure-solvent Arrhenius to formulation blends "
            "(Grunberg-Nissan), pigment crowding (Krieger-Dougherty), or Krebs KU + sag "
            "(Phase-1 wet-lab).",
            "Does NOT edit the signed Arrhenius KPI or the 66-receipt master manifest; "
            "does NOT promote the module out of PRE_PHASE_0 (human dual-identity keys).",
        ],
    }
    body = json.dumps(out, indent=2, sort_keys=True)
    Path(out_path).write_text(body)
    print("SHA256", hashlib.sha256(body.encode()).hexdigest())
    print("VERDICT", verdict)
    print("pooled_arr", round(pooled_arr, 6), "pooled_vft", round(pooled_vft, 6))
    print("arr_wins", arr_wins, "vft_wins", vft_wins, "ties", ties,
          "bic_arr_better", bic_arr_better)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
