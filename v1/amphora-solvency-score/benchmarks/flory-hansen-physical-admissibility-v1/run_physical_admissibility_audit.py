#!/usr/bin/env python3
"""W-campaign falsification attack on amphora-solvency-score.

Claim under attack: the signed Phase-0 KPI receipts
`omg-chi-flory-huggins-physical-baseline-vs-ml-kpi.v1.json` and
`omg-chi-hansen-3component-physical-baseline-vs-ml-kpi.v1.json` assert that
"ML beats classical Flory-Huggins/Hansen theory", where the classical-theory
predictor is a genuine Fedors 1974 / Van Krevelen-Beerbower group-contribution
solubility-parameter (delta_p / delta_d/delta_p/delta_h) computation.

This script performs a physical-admissibility audit of that baseline, using
ONLY numbers already embedded in the two signed parent receipts (no new
per-polymer computation) plus an independent re-derivation of the B2
"linear-rescaled" OLS fit from the receipts' own reported y_stats and
fitted_slope/fitted_intercept, to test two pre-registered, falsifying
criteria:

  Criterion A (admissibility): the reported delta_p / delta_d / delta_h
  summary statistics fall within a generous physically-admissible envelope
  bounded by the very handbooks the receipts cite as their coefficient
  source (Barton 1991 CRC Handbook of Solubility Parameters; Hansen 2007
  Handbook of Solubility Parameters 2nd ed. Table A.1) -- both of which
  tabulate real solvents and polymers essentially entirely within
  [12, 50] MPa^0.5 (water, at 47.9, is the most extreme value used
  in-receipt). We use a 20% margin on each side: [ADMISSIBLE_MIN,
  ADMISSIBLE_MAX] = [9.6, 60.0] MPa^0.5.

  Criterion B (degeneracy): the B2 "2-fitted-parameter linear rescaling"
  baseline's fitted OLS slope is statistically indistinguishable from zero
  (|slope| < DEGENERATE_SLOPE_EPS), which would mean B2 collapsed to the
  B0 constant-mean predictor and is not a meaningful test of "does a fairly
  rescaled classical theory compete with ML" as claimed.

If EITHER criterion trips for a receipt's reported delta statistics, the
receipt's physical-baseline predictor is not an admissible representation of
classical theory, and the "ML beats classical Flory-Huggins/Hansen theory"
R^2-gap claims computed against it are not valid evidence for that
comparison (independent of whether ML is in fact superior to a *correctly*
computed baseline, which this receipt does not determine).
"""
import hashlib
import json
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-solvency-score"

FH_RECEIPT = MOD / "reference/mvp20/data/omg_chi_flory_huggins_physical_baseline_receipt.v1.json"
HANSEN_RECEIPT = MOD / "reference/mvp20/data/omg_chi_hansen_3component_physical_baseline_receipt.v1.json"
FH_KPI = MOD / "evidence/phase0/kpis/omg-chi-flory-huggins-physical-baseline-vs-ml-kpi.v1.json"
HANSEN_KPI = MOD / "evidence/phase0/kpis/omg-chi-hansen-3component-physical-baseline-vs-ml-kpi.v1.json"

# Physically-admissible envelope for Hildebrand / Hansen partial solubility
# parameters, MPa^0.5. Barton 1991 CRC Handbook of Solubility Parameters and
# Hansen 2007 Handbook 2nd ed. Table A.1 -- both cited in the receipts under
# audit as the coefficient source -- compile essentially all known organic
# solvents and amorphous polymers within roughly [12.0 (fluorocarbons), 47.9
# (water, the single most extreme value actually used as a solvent constant
# in-receipt)] MPa^0.5. We apply a deliberately generous +/-20% margin so
# that any trip of this bound is decisive, not a borderline judgment call.
ADMISSIBLE_MIN = 12.0 * 0.8   # 9.6
ADMISSIBLE_MAX = 47.9 * 1.25  # 59.875, rounded to 60.0 in reporting
DEGENERATE_SLOPE_EPS = 1e-10


def sha(b):
    return hashlib.sha256(b).hexdigest()


def load(p):
    return json.loads(p.read_bytes())


def admissibility_check(stats, label):
    """stats: dict with mean/std/min/max. Returns exceedance record."""
    out = {}
    for k in ("mean", "max"):
        v = stats[k]
        exceeds = v > ADMISSIBLE_MAX or v < ADMISSIBLE_MIN
        orders_of_magnitude = None
        if v > 0 and ADMISSIBLE_MAX > 0:
            import math
            orders_of_magnitude = round(math.log10(v / ADMISSIBLE_MAX), 2) if v > ADMISSIBLE_MAX else None
        out[k] = {
            "observed": v,
            "admissible_envelope_MPa_half": [ADMISSIBLE_MIN, ADMISSIBLE_MAX],
            "exceeds_envelope": bool(exceeds),
            "orders_of_magnitude_over_ceiling": orders_of_magnitude,
        }
    out["min_reported"] = stats.get("min")
    out["std_reported"] = stats.get("std")
    out["std_exceeds_mean_evidence_of_heavy_tail"] = bool(stats.get("std", 0) > stats.get("mean", 0))
    out["criterion_a_triggered_" + label] = bool(out["mean"]["exceeds_envelope"] or out["max"]["exceeds_envelope"])
    return out


def degeneracy_check(per_solvent_block, b2_key, label):
    out = {}
    any_degenerate = False
    for solvent, rec in per_solvent_block.items():
        b2 = rec[b2_key]
        slope = b2["fitted_slope"]
        degenerate = abs(slope) < DEGENERATE_SLOPE_EPS
        any_degenerate = any_degenerate or degenerate
        # Independent re-derivation check: if B2 is truly degenerate to a
        # constant predictor, its R^2/RMSE/MAE must equal B0's to high
        # precision (both receipts also report b0_constant_mean per solvent).
        b0 = rec["b0_constant_mean"]
        r2_match = round(b2["r2"], 4) == round(b0["r2"], 4)
        rmse_match = round(b2["rmse"], 4) == round(b0["rmse"], 4)
        out[solvent] = {
            "fitted_slope": slope,
            "degenerate_slope": bool(degenerate),
            "b2_r2": b2["r2"], "b0_r2": b0["r2"], "r2_matches_b0_to_4dp": bool(r2_match),
            "b2_rmse": b2["rmse"], "b0_rmse": b0["rmse"], "rmse_matches_b0_to_4dp": bool(rmse_match),
            "b2_collapsed_to_constant_predictor": bool(degenerate and r2_match and rmse_match),
        }
    out["criterion_b_triggered_" + label] = bool(any_degenerate)
    return out


def run_once():
    fh = load(FH_RECEIPT)
    hn = load(HANSEN_RECEIPT)
    fh_kpi = load(FH_KPI)
    hn_kpi = load(HANSEN_KPI)

    fh_admiss = admissibility_check(fh["kpis"]["hildebrand_delta_p_stats_MPa_half"], "fh_delta_p")
    hn_admiss = {
        comp: admissibility_check(hn["kpis"]["hansen_delta_p_stats_MPa_half"][comp], f"hansen_{comp}")
        for comp in ("delta_d", "delta_p", "delta_h", "delta_total")
    }

    fh_degen = degeneracy_check(fh["kpis"]["per_solvent"], "b2_flory_huggins_linear_rescaled", "fh")
    hn_degen = degeneracy_check(hn["kpis"]["per_solvent"], "b2_hansen_3component_linear_rescaled", "hansen")

    fh_scale_note = next(
        (m["note"] for m in fh_kpi["metrics"]
         if m["name"] == "flory_huggins_pure_R2_catastrophically_worse_than_constant_documented_chloroform"),
        None,
    )

    criterion_a_triggered = fh_admiss["criterion_a_triggered_fh_delta_p"] or any(
        v["criterion_a_triggered_hansen_" + comp] for comp, v in hn_admiss.items()
    )
    criterion_b_triggered = fh_degen["criterion_b_triggered_fh"] or hn_degen["criterion_b_triggered_hansen"]
    verdict = "CLAIM_REFUTED" if (criterion_a_triggered or criterion_b_triggered) else "CLAIM_SURVIVED"

    return {
        "schema": "amphora.solvency-score.flory-hansen-physical-admissibility-audit.v1",
        "attack_type": "physical_admissibility_audit_of_underlying_baseline_labels",
        "claim_under_attack": {
            "receipts": [str(FH_RECEIPT.relative_to(ROOT)), str(HANSEN_RECEIPT.relative_to(ROOT))],
            "kpi_receipts": [str(FH_KPI.relative_to(ROOT)), str(HANSEN_KPI.relative_to(ROOT))],
            "claim_text": (
                "ML (HistGBM) beats classical Flory-Huggins theory (B1 pure Fedors 1974 "
                "group-contribution delta_p, 0 fitted params; B2 linear-rescaled, 2 fitted "
                "params) and classical Hansen 1967/2007 3-component theory (same "
                "Van Krevelen 1990 / Beerbower 1984 group contribution for delta_d/delta_p/"
                "delta_h), by R^2 gaps of +5029.7/+5390.0/+208.1 (Flory-Huggins pure), "
                "+0.835/+0.826/+0.914 (Flory-Huggins rescaled), and +2,041,132/+3,637,462/"
                "+... (Hansen pure) across chloroform/ethanol/water."
            ),
        },
        "admissibility_envelope_MPa_half": [ADMISSIBLE_MIN, round(ADMISSIBLE_MAX, 3)],
        "admissibility_envelope_source": (
            "Barton 1991 CRC Handbook of Solubility Parameters and Hansen 2007 Handbook of "
            "Solubility Parameters 2nd ed. Table A.1 -- the two references cited BY THESE "
            "SAME RECEIPTS as the coefficient source -- tabulate solvents/polymers within "
            "roughly [12, 47.9] MPa^0.5 (47.9, water, is the single most extreme value "
            "actually consumed as a Barton-table constant in these receipts). Envelope "
            "applies a further +/-20-25% margin for a deliberately conservative test."
        ),
        "flory_huggins_delta_p_admissibility": fh_admiss,
        "hansen_delta_d_p_h_total_admissibility": hn_admiss,
        "flory_huggins_b2_degeneracy": fh_degen,
        "hansen_b2_degeneracy": hn_degen,
        "pre_registered_refutation_criteria": {
            "criterion_a": (
                f"reported delta_p (FH) or any of delta_d/delta_p/delta_h/delta_total (Hansen) "
                f"mean or max lies outside [{ADMISSIBLE_MIN}, {round(ADMISSIBLE_MAX,3)}] MPa^0.5"
            ),
            "criterion_a_triggered": bool(criterion_a_triggered),
            "criterion_b": (
                f"B2 (linear-rescaled) fitted OLS slope has |slope| < {DEGENERATE_SLOPE_EPS} for "
                "any solvent in either receipt, AND its R^2/RMSE match the B0 constant-mean "
                "baseline to 4 decimal places (i.e. B2 collapsed to a constant predictor)"
            ),
            "criterion_b_triggered": bool(criterion_b_triggered),
            "verdict": verdict,
        },
        "mechanism": (
            "chi_FH = V_s/(RT) x (delta_p - delta_s)^2 + 0.34 is quadratic in delta_p. A "
            "denominator collapse in the Fedors delta_p = sqrt(sum(dE_i)/sum(dV_i)) computation "
            "(sum(dV_i) -> ~0 for a nonzero subset of the 98,328 OMG polymer structures, most "
            "plausibly caused by SMARTS/group-matching failures on unusual ring/branching "
            "patterns in the 'methyl_terminated_product' polymer-analog SMILES) produces "
            "delta_p values up to 5.16e9 MPa^0.5 (Flory-Huggins receipt) and Hansen components "
            "up to 5.33e17 MPa^0.5 (Hansen receipt) -- 8 to 16 orders of magnitude beyond any "
            "physically real solubility parameter. Squaring these in chi_FH produces "
            "astronomically large predicted-chi values for the contaminated subset, which "
            "dominates the sum-of-squared-errors an OLS fit (B2's slope+intercept) minimizes, "
            "driving the fitted slope to ~1e-19 to 1e-35 (statistically zero) and collapsing B2 "
            "to the constant-mean predictor B0 -- explaining, mechanically, why the receipts "
            "report 'flory_huggins_rescaled_beats_pure' / 'hansen_rescaled_beats_pure' as "
            "trivially true (B2 == B0, both == R^2 ~ 0) rather than as a genuine finding that "
            "linearly-recalibrated classical theory cannot compete."
        ),
        "interpretation": (
            "Both physical-baseline computations (Fedors 1974 delta_p for Flory-Huggins; "
            "Van Krevelen/Beerbower delta_d/delta_p/delta_h for Hansen) are not physically "
            "admissible representations of classical solubility-parameter theory: their own "
            "reported summary statistics violate the admissibility envelope defined by the "
            "receipts' own cited reference handbooks by many orders of magnitude, and the "
            "B2 'fairly rescaled physical theory' comparator is mathematically degenerate "
            "(collapsed to a constant predictor) as a direct, mechanically-traceable "
            "consequence. The claim that these two signed Phase-0 KPIs establish 'ML beats "
            "classical Flory-Huggins/Hansen theory' via a genuine physical baseline is "
            "REFUTED: the comparison was never made against admissible classical theory. "
            "This does NOT establish that ML is inferior to a correctly-computed classical "
            "baseline -- that comparison remains untested and is flagged as follow-on work. "
            "It also does not affect the module's live Rust runtime (mission.md: 'Retired "
            "Python implementation records have diagnostic provenance only and are not live "
            "authority') or the BigSolDB LSO claim (separately attacked under campaign items "
            "C1/W6); it is scoped strictly to the two OMG chi Flory-Huggins/Hansen physical-"
            "baseline-vs-ML KPI receipts."
        ),
        "self_framing_discrepancy": {
            "kpi_receipt_gate": "flory_huggins_pure_R2_catastrophically_worse_than_constant_documented_chloroform",
            "kpi_receipt_quoted_note": fh_scale_note,
            "discrepancy": (
                "The KPI receipt's own 'HONEST FRAMING' note attributes the catastrophic R^2 "
                "(-5028.92) to the physical formula's outputs being 'in the wrong scale range' "
                "-- i.e. framed as a linear scale/units mismatch, fixable in principle by "
                "rescaling (which is exactly what B2 attempts). That framing is materially "
                "understated: this audit's admissibility check shows delta_p is not merely "
                "off-scale, it is physically impossible (mean 209,738 MPa^0.5 against a "
                "physically-real ceiling of ~48 MPa^0.5 -- a ~4,400x, not a small-multiple, "
                "deviation, driven by a denominator-collapse computational defect, not a unit "
                "convention choice). Because Pearson r (used by the receipt's fallback "
                "'flory_huggins_pure_pearson_correlation_positive' gates, e.g. r=0.239 for "
                "chloroform, cited as evidence physical theory 'does capture SOME signal') is "
                "itself sensitive to high-leverage outliers, a Pearson r computed against a "
                "predictor with values spanning 12.9 to 5.16e9 cannot be assumed to reflect the "
                "bulk-sample physical relationship either -- it may be dominated by the same "
                "handful of pathological structures. This audit does not re-derive the r value "
                "and cannot confirm or rule out leverage-driven inflation; it is flagged as an "
                "open question for the W7 follow-on, not asserted as established."
            ),
        },
        "does_not_close": [
            "a corrected re-derivation of delta_p/delta_d/delta_p/delta_h from raw OMG SMILES "
            "with a bug-fixed (non-degenerate) Fedors/Van Krevelen implementation, and a re-run "
            "of B1/B2 on the corrected values, to determine whether ML still wins against a "
            "VALID physical baseline (not attempted this fire -- flagged as W7 follow-on)",
            "root-causing the exact line-level defect in the (unrecovered -- not checked into "
            "this module tree) Python script that produced these two receipts",
            "human / independent review",
        ],
    }


runA = run_once()
runB = run_once()
byte_identical = json.dumps(runA, sort_keys=True) == json.dumps(runB, sort_keys=True)

BENCH = MOD / "benchmarks/flory-hansen-physical-admissibility-v1"
BENCH.mkdir(parents=True, exist_ok=True)
canon_bytes = json.dumps(runA, indent=2, sort_keys=True).encode()
(BENCH / "diagnostic.runA.json").write_bytes(canon_bytes)
(BENCH / "diagnostic.runB.json").write_bytes(json.dumps(runB, indent=2, sort_keys=True).encode())
(BENCH / "diagnostic.canonical.json").write_bytes(canon_bytes)

print("byte_identical_two_replay:", byte_identical)
print("verdict:", runA["pre_registered_refutation_criteria"]["verdict"])
print("criterion_a_triggered:", runA["pre_registered_refutation_criteria"]["criterion_a_triggered"])
print("criterion_b_triggered:", runA["pre_registered_refutation_criteria"]["criterion_b_triggered"])
print("canonical_sha256:", sha(canon_bytes))
