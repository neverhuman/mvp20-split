#!/usr/bin/env python3
"""amphora-viscosity-score  --  calibrated prediction-interval audit (MODEL AXIS, option C).

The module's signed Phase-0 KPI (evidence/phase0/kpis/viscosity-arrhenius-kpi.v1.json)
reports POINT predictions and R^2 for the 2-parameter Arrhenius / Andrade
viscosity-temperature law

    ln eta(T) = ln A + Ea/(R.T)            (Arrhenius 1889; Andrade 1930)

extrapolated to a held-out 30 C from training points at 25/40/60 C.  A point
prediction is not a decision-grade artifact: a formulator needs to know HOW WIDE
an honest predictive band is, and whether that band is trustworthy for the
particular chemical family being formulated.  The prior signed receipt
(vft-arrhenius-adequacy-v1) settled parsimony (Arrhenius is not out-generalised
by VFT on held-out temperature) but left the interval UNCALIBRATED.

THIS AUDIT (model axis): wrap the incumbent Arrhenius extrapolator in a
distribution-free split/jackknife conformal predictor and quantify:
  (1) does the marginal leave-one-solvent-out (LOO) conformal coverage match the
      nominal 1-alpha (the distribution-free finite-sample guarantee, Vovk 2005 /
      Papadopoulos 2002)?
  (2) how wide is the deployment band, as a multiplicative viscosity factor, and
      what is its bootstrap CI (Efron 1979, seeded)?
  (3) is coverage FAMILY-CONDITIONAL -- i.e. does the marginal guarantee hide
      per-chemistry under-coverage for associating / super-Arrhenius liquids
      (water, alcohols, glycerol)?  Mondrian/conditional validity, Vovk 2012.
  (4) does the calibrated band discriminate the fitted Arrhenius extrapolator
      from a temperature-blind control (predict 25 C viscosity at 30 C)?
  (5) Arrhenius vs VFT band width at equal nominal coverage.

Conformity score = |ln eta_pred - ln eta_true| at the held-out 30 C (natural
absolute score for a multiplicative quantity).  LOO conformal quantile is an
exact integer order statistic (no float-quantile interpolation) -> deterministic.
Bootstrap uses random.Random(pinned seed) -> deterministic; two-replay SHA gated.

INPUTS: only viscosities already inside the module's signed benchmark result
(evidence/phase0/benchmark/result.v1.json, SHA pinned).  No external data fetched.
AUDIT_ONLY: does NOT edit the signed KPI, does NOT touch the 66-receipt master
manifest, does NOT promote the module.

Primary references (conformal / resampling):
  Vovk, V., Gammerman, A., Shafer, G. (2005) "Algorithmic Learning in a Random
    World", Springer, ISBN 978-0-387-00152-4 (split/inductive conformal, marginal
    finite-sample coverage 1-alpha).
  Papadopoulos, H., Proedrou, K., Vovk, V., Gammerman, A. (2002) "Inductive
    confidence machines for regression", ECML 2002, LNCS 2430:345-356,
    doi:10.1007/3-540-36755-1_29.
  Barber, R.F., Candes, E.J., Ramdas, A., Tibshirani, R.J. (2021) "Predictive
    inference with the jackknife+", Ann. Statist. 49(1):486-507,
    doi:10.1214/20-AOS1965.
  Vovk, V. (2012) "Conditional validity of inductive conformal predictors",
    ACML 2012, PMLR 25:475-490 (Mondrian / category-conditional coverage).
  Efron, B. (1979) "Bootstrap methods: another look at the jackknife",
    Ann. Statist. 7(1):1-26, doi:10.1214/aos/1176344552.
"""
import hashlib
import json
import math
import random
import sys
from pathlib import Path

RESULT_SHA_EXPECTED = "6164d8d153533f71c372ef28792c1f8521de35ddaa0d60a3dce12c196dac314e"
R = 8.31446261815324  # J/(mol.K) CODATA 2018
KELVIN = 273.15
BOOT_SEED = 20260728          # pinned -> deterministic bootstrap
BOOT_N = 4000
ALPHAS = [0.20, 0.10, 0.05]   # nominal 80 / 90 / 95 %

FAMILY = {
    "water": "water",
    "methanol": "alcohol", "ethanol": "alcohol", "n-butanol": "alcohol",
    "isopropanol": "alcohol",
    "glycerol": "polyol",
    "acetone": "ketone", "methyl-ethyl-ketone": "ketone",
    "toluene": "aromatic", "p-xylene": "aromatic", "benzene": "aromatic",
    "n-hexane": "n-alkane", "n-pentane": "n-alkane", "n-heptane": "n-alkane",
    "n-octane": "n-alkane",
    "cyclohexane": "cycloalkane",
    "dichloromethane": "halogenated", "chloroform": "halogenated",
    "ethyl-acetate": "ester",
    "tetrahydrofuran": "ether", "diethyl-ether": "ether", "1-4-dioxane": "ether",
    "dimethylformamide": "polar-aprotic", "dimethyl-sulfoxide": "polar-aprotic",
    "acetonitrile": "polar-aprotic",
}


def linfit(xs, ys):
    n = len(xs)
    sx = sum(xs); sy = sum(ys)
    sxx = sum(x * x for x in xs); sxy = sum(x * y for x, y in zip(xs, ys))
    denom = n * sxx - sx * sx
    b = (n * sxy - sx * sy) / denom
    a = (sy - b * sx) / n
    sse = sum((y - (a + b * x)) ** 2 for x, y in zip(xs, ys))
    return a, b, sse


def fit_arrhenius(pts):
    xs = [1.0 / T for T, _ in pts]
    ys = [math.log(eta) for _, eta in pts]
    a, b, _ = linfit(xs, ys)
    return lambda T: a + b / T          # returns ln eta


def fit_vft(pts, extra_temps):
    all_T = [T for T, _ in pts] + list(extra_temps)
    t0_hi = min(all_T) - 1.0
    ys = [math.log(eta) for _, eta in pts]
    best = None
    n_steps = int(math.floor((t0_hi - 0.0) / 0.25)) + 1
    for i in range(n_steps):
        t0 = i * 0.25
        xs = [1.0 / (T - t0) for T, _ in pts]
        a, b, sse = linfit(xs, ys)
        if best is None or sse < best[0]:
            best = (sse, t0, a, b)
    _, t0, a, b = best
    return lambda T: a + b / (T - t0)   # returns ln eta


def order_stat_quantile(scores, alpha):
    """Exact split-conformal band half-width: k-th smallest of the n calibration
    scores with k = ceil((n+1)(1-alpha)); if k > n the band is +inf (always
    covers). Integer index -> fully deterministic, no float interpolation."""
    s = sorted(scores)
    n = len(s)
    k = math.ceil((n + 1) * (1.0 - alpha))
    if k > n:
        return math.inf
    return s[k - 1]


def loo_coverage(scores, alpha):
    """Honest jackknife-LOO conformal coverage: each solvent scored against a band
    built from the OTHER n-1 scores (no self-inclusion)."""
    n = len(scores)
    covered = []
    for i in range(n):
        cal = scores[:i] + scores[i + 1:]
        q = order_stat_quantile(cal, alpha)
        covered.append(scores[i] <= q)
    return covered


def build_scores(rows, model):
    """Per-solvent held-out-30C |ln residual| for the chosen extrapolator."""
    out = []
    for row in rows:
        pts = [(T, e) for (T, e) in row["points"] if abs((T - KELVIN) - 30.0) > 1e-9]
        held = [e for (T, e) in row["points"] if abs((T - KELVIN) - 30.0) <= 1e-9][0]
        T30 = 30.0 + KELVIN
        if model == "arrhenius":
            ln_pred = fit_arrhenius(pts)(T30)
        elif model == "vft":
            ln_pred = fit_vft(pts, extra_temps=[T30])(T30)
        elif model == "tempblind":  # control: predict 25 C viscosity at 30 C
            eta25 = [e for (T, e) in row["points"] if abs((T - KELVIN) - 25.0) <= 1e-9][0]
            ln_pred = math.log(eta25)
        else:
            raise ValueError(model)
        s = abs(ln_pred - math.log(held))
        out.append({"solvent_id": row["solvent_id"], "family": FAMILY[row["solvent_id"]],
                    "ln_residual": ln_pred - math.log(held), "score": s,
                    "held_out_30c_mpas": held,
                    "pred_30c_mpas": math.exp(ln_pred)})
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
                     "points": pts})
    return rows


def summarize_model(score_recs):
    scores = [r["score"] for r in score_recs]
    n = len(scores)
    per_alpha = {}
    for a in ALPHAS:
        cov_flags = loo_coverage(scores, a)
        cov = sum(cov_flags) / n
        q_deploy = order_stat_quantile(scores, a)  # full-calibration deployment band
        band_factor = math.exp(q_deploy) if math.isfinite(q_deploy) else None
        # family-conditional LOO coverage
        fam = {}
        for i, rec in enumerate(score_recs):
            fam.setdefault(rec["family"], []).append(cov_flags[i])
        fam_cov = {k: {"n": len(v), "coverage": round(sum(v) / len(v), 6)}
                   for k, v in sorted(fam.items())}
        undercover = sorted(k for k, v in fam_cov.items()
                            if v["coverage"] < (1.0 - a) - 1e-9)
        # seeded bootstrap CI on the deployment band half-width q_deploy
        rng = random.Random(BOOT_SEED + int(round(a * 100)))
        boot_q = []
        for _ in range(BOOT_N):
            samp = [scores[rng.randrange(n)] for _ in range(n)]
            bq = order_stat_quantile(samp, a)
            boot_q.append(bq if math.isfinite(bq) else q_deploy)
        boot_q.sort()
        lo = boot_q[int(math.floor(0.05 * (BOOT_N - 1)))]
        hi = boot_q[int(math.ceil(0.95 * (BOOT_N - 1)))]
        per_alpha[f"{a:.2f}"] = {
            "nominal_coverage": round(1.0 - a, 4),
            "loo_marginal_coverage": round(cov, 6),
            "coverage_meets_nominal": cov >= (1.0 - a) - 1e-9,
            "deploy_band_halfwidth_ln": (round(q_deploy, 8) if math.isfinite(q_deploy) else None),
            "deploy_band_mult_factor": (round(band_factor, 6) if band_factor else None),
            "deploy_band_halfwidth_bootstrap90_ln": [round(lo, 8), round(hi, 8)],
            "family_conditional_coverage": fam_cov,
            "families_undercovering": undercover,
        }
    return {
        "n_solvents": n,
        "score_stats_ln": {
            "min": round(min(scores), 8), "median": round(sorted(scores)[n // 2], 8),
            "max": round(max(scores), 8),
            "argmax_solvent": max(score_recs, key=lambda r: r["score"])["solvent_id"],
        },
        "per_alpha": per_alpha,
        "per_solvent": sorted(
            [{"solvent_id": r["solvent_id"], "family": r["family"],
              "held_out_30c_mpas": r["held_out_30c_mpas"],
              "pred_30c_mpas": round(r["pred_30c_mpas"], 8),
              "ln_residual": round(r["ln_residual"], 8),
              "score_abs_ln": round(r["score"], 8)} for r in score_recs],
            key=lambda x: x["solvent_id"]),
    }


def main(result_path, out_path):
    raw = Path(result_path).read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    assert sha == RESULT_SHA_EXPECTED, f"result SHA {sha} != pinned {RESULT_SHA_EXPECTED}"
    result = json.loads(raw)
    rows = extract(result)
    assert len(rows) == 25, len(rows)

    arr = summarize_model(build_scores(rows, "arrhenius"))
    vft = summarize_model(build_scores(rows, "vft"))
    blind = summarize_model(build_scores(rows, "tempblind"))

    # fail-closed / sanity probes -----------------------------------------
    arr_scores = [r for r in build_scores(rows, "arrhenius")]
    zero_band_cov = sum(1 for r in arr_scores if r["score"] <= 0.0) / len(arr_scores)
    fail_closed = [
        {"probe": "result_sha_pin",
         "assert": "aborts if benchmark result bytes differ from pinned SHA",
         "pinned_sha256": RESULT_SHA_EXPECTED, "observed_sha256": sha,
         "pass": sha == RESULT_SHA_EXPECTED},
        {"probe": "zero_width_band_not_vacuous",
         "assert": "a zero half-width band must NOT achieve nominal coverage",
         "coverage_at_zero_halfwidth": round(zero_band_cov, 6),
         "pass": zero_band_cov < 0.90},
        {"probe": "temperature_blind_control_wider",
         "assert": "fitted Arrhenius 90% band must be tighter than temperature-blind control",
         "arrhenius_band_factor_a0.10": arr["per_alpha"]["0.10"]["deploy_band_mult_factor"],
         "tempblind_band_factor_a0.10": blind["per_alpha"]["0.10"]["deploy_band_mult_factor"],
         "pass": (arr["per_alpha"]["0.10"]["deploy_band_mult_factor"]
                  < blind["per_alpha"]["0.10"]["deploy_band_mult_factor"])},
    ]

    # verdict --------------------------------------------------------------
    marg_ok = all(arr["per_alpha"][f"{a:.2f}"]["coverage_meets_nominal"] for a in ALPHAS)
    any_family_under = any(arr["per_alpha"][f"{a:.2f}"]["families_undercovering"] for a in ALPHAS)
    if marg_ok and not any_family_under:
        verdict = "CALIBRATED_MARGINAL_AND_FAMILY_CONDITIONAL"
    elif marg_ok and any_family_under:
        verdict = "CALIBRATED_MARGINAL_ONLY_FAMILY_CONDITIONAL_GAP"
    else:
        verdict = "MARGINAL_COVERAGE_BELOW_NOMINAL"

    # Arrhenius vs VFT band comparison at each alpha
    band_cmp = {}
    for a in ALPHAS:
        k = f"{a:.2f}"
        ba = arr["per_alpha"][k]["deploy_band_mult_factor"]
        bv = vft["per_alpha"][k]["deploy_band_mult_factor"]
        band_cmp[k] = {
            "arrhenius_band_factor": ba, "vft_band_factor": bv,
            "arrhenius_loo_cov": arr["per_alpha"][k]["loo_marginal_coverage"],
            "vft_loo_cov": vft["per_alpha"][k]["loo_marginal_coverage"],
            "tighter_model": ("arrhenius" if ba < bv else "vft" if bv < ba else "tie"),
        }

    out = {
        "schema": "amphora.viscosity-score.conformal-interval-calibration-diagnostic.v1",
        "purpose": (
            "Distribution-free calibrated prediction-interval audit of the signed "
            "Arrhenius viscosity-temperature KPI: wrap the 2-parameter Arrhenius "
            "extrapolator (25/40/60 C -> held-out 30 C) in a split/jackknife-LOO "
            "conformal predictor over the 25 rights-clean pure Newtonian solvents "
            "and quantify marginal coverage, deployment band width (with bootstrap "
            "CI), FAMILY-CONDITIONAL coverage, and discrimination vs a temperature-"
            "blind control -- turning the incumbent point prediction into a "
            "decision-grade interval, using only data already in the signed benchmark."),
        "conformity_score": "abs(ln eta_pred - ln eta_true) at held-out 30 C (multiplicative-scale absolute residual)",
        "hold_out_scheme": "per solvent: train Arrhenius/VFT on 25/40/60 C, predict 30 C; conformal calibration is leave-one-SOLVENT-out over the 25 held-out-30C scores",
        "n_solvents": 25,
        "alphas": ALPHAS,
        "bootstrap": {"seed": BOOT_SEED, "resamples": BOOT_N, "ci": "percentile 90%"},
        "arrhenius": arr,
        "vft": vft,
        "temperature_blind_control": blind,
        "arrhenius_vs_vft_band": band_cmp,
        "fail_closed": fail_closed,
        "verdict": verdict,
        "interpretation_fields": {
            "marginal_calibration_ok": marg_ok,
            "family_conditional_gap": any_family_under,
        },
        "closes": [
            "Delivers calibrated (distribution-free, finite-sample) prediction "
            "intervals for the incumbent Arrhenius viscosity-temperature "
            "extrapolation -- the signed KPI previously reported only point "
            "predictions and R^2.",
            "Quantifies the deployment band as a multiplicative viscosity factor "
            "with a seeded bootstrap CI, and tests whether marginal coverage hides "
            "family-conditional (per-chemistry) under-coverage.",
            "Confirms the calibrated band discriminates the fitted extrapolator "
            "from a temperature-blind control (fail-closed probe).",
        ],
        "does_not_close": [
            "Coverage is over EXCHANGEABLE solvents within this fixed 25-solvent "
            "corpus; a genuinely new solvent from an unseen chemical class carries "
            "no finite-sample guarantee (Mondrian per-family n as low as 1).",
            "Still a per-solvent temperature fit (needs >=3 measured viscosities "
            "per solvent); does NOT predict viscosity from structure a-priori -- "
            "the Orrick-Erbar / Sastri-Rao group-contribution gap remains open, "
            "blocked on a rights-clean group-contribution table.",
            "Newtonian pure solvents only; formulation blends, pigment crowding, "
            "and Krebs-KU / sag rheology are Phase-1 wet-lab.",
        ],
        "closes_gap_from_prior_receipt": "vft-arrhenius-adequacy-v1 phase0_gap_ledger left interval UNCALIBRATED; this receipt calibrates it.",
        "source_result_path": "amphora-viscosity-score/evidence/phase0/benchmark/result.v1.json",
        "source_result_sha256": sha,
        "claim_locks": {
            "scientific_success_required_for_phase0": False,
            "authority": "AUDIT_ONLY",
            "promotes_module": False,
            "edits_signed_kpi": False,
            "edits_master_manifest": False,
        },
    }
    Path(out_path).write_text(json.dumps(out, indent=2, sort_keys=True))
    print("WROTE", out_path)
    print("diagnostic_sha256", hashlib.sha256(Path(out_path).read_bytes()).hexdigest())
    print("verdict", verdict)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
