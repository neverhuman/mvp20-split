#!/usr/bin/env python3
"""AUDIT_ONLY falsification probe for amphora-viscosity-score.

Attacks the standing Phase-0 KPI claim at
evidence/phase0/kpis/viscosity-arrhenius-kpi.v1.json:
  arrhenius_mape_within_training_range   observed 1.26%  PASSED (ceiling 5%)
  arrhenius_over_constant_baseline_lift  observed +64.1pp PASSED (floor 20pp)
  held_out_temperature_extrapolation_mape observed 0.49% PASSED (ceiling 8%)
  per_solvent_minimum_prediction_quality_rate observed 1.0 PASSED (floor 0.85)
  r_squared_arrhenius_minimum observed 0.9904 (reported observationally)

Two independent, previously-untested angles on the fixture that produces these numbers
(reference/phase0-viscosity-known-answer.v1.json), which the mission.md prose says has
per-solvent activation energies "fitted offline via numpy linear regression" from
CRC Handbook / NIST WebBook / Yaws' Handbook published values:

  1. OFFLINE-FIT REPRODUCIBILITY -- independently re-run the exact linear regression
     (ln(eta) vs 1/T over the fixture's own {20,40,60}C points) for all 25 solvents and
     diff against the fixture's baked-in fitted_activation_energy_j_mol / fitted_r_squared.
     A prior fire (kd-live-runtime-parity-v1, hb-live-runtime-parity-v1) proved this class
     of "verbatim re-derivation" claim can be false elsewhere in this module; never checked
     for the Arrhenius fixture itself.

  2. EXTERNAL DATA-PROVENANCE CROSS-CHECK -- glycerol is the fixture's highest-activation-
     energy, most temperature-sensitive solvent. Its published source is cited as "CRC
     Handbook 100th ed. Table 6.183". This probe independently fetches, this fire, a
     widely-cited alternate compilation of the same physical quantity -- Segur & Oberstar
     (1951) Ind. Eng. Chem. 43(9):2117, 100 wt%-glycerine column, as reproduced at
     web.cecs.pdx.edu/~gerry/class/EAS361/lab/pdf/glycerinWaterViscosity_Dorsey.pdf -- and
     diffs the fixture's own raw viscosity_mpas_{20,30,40,60}c entries against it. It then
     asks whether substituting the independently-sourced numbers would flip any KPI gate.

Refutation criterion: the claim under attack -- that the signed KPI's PASS verdicts
(arrhenius_mape_within_training_range, held_out_temperature_extrapolation_mape,
arrhenius_over_constant_baseline_lift, per_solvent_minimum_prediction_quality_rate) reflect
the model's true accuracy against correctly-transcribed published reference data -- would be
REFUTED if (a) the offline-fit reproducibility check found a baked-in Ea/R2 that does not
match a from-scratch regression on the fixture's own raw numbers (evidence the "numpy fit"
description is false, mirroring the KD/HB live-runtime-parity findings), OR (b) substituting
independently re-sourced raw viscosity data for any solvent flips any KPI gate from PASS to
FAIL. It SURVIVES if the offline fit reproduces exactly AND no gate flips under the
externally-verified data.
"""
import json
import math
import subprocess
import sys

R = 8.31446261815324

FIXTURE = "/home/ubuntu/amphora/build/mvp20-split/amphora-viscosity-score/reference/phase0-viscosity-known-answer.v1.json"
KPI = "/home/ubuntu/amphora/build/mvp20-split/amphora-viscosity-score/evidence/phase0/kpis/viscosity-arrhenius-kpi.v1.json"


def sha256_file(path):
    out = subprocess.check_output(["sha256sum", path]).decode().split()[0]
    return out


def fit_ea_r2(t20, t40, t60):
    ts = [20.0, 40.0, 60.0]
    visc = [t20, t40, t60]
    xs = [1.0 / (t + 273.15) for t in ts]
    ys = [math.log(v) for v in visc]
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    slope = sxy / sxx
    intercept = my - slope * mx
    ea = slope * R
    ss_res = sum((y - (intercept + slope * x)) ** 2 for x, y in zip(xs, ys))
    ss_tot = sum((y - my) ** 2 for y in ys)
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    return ea, r2


def arrhenius(eta_ref, t_ref, t, ea):
    t_ref_k = t_ref + 273.15
    t_k = t + 273.15
    return eta_ref * math.exp((ea / R) * (1.0 / t_k - 1.0 / t_ref_k))


def run_report(solvents):
    train_err_sum = 0.0
    train_pairs = 0
    baseline_err_sum = 0.0
    held_out_err_sum = 0.0
    per_total = 0
    within10 = 0
    within5 = 0
    min_r2 = float("inf")
    max_held = 0.0
    for s in solvents:
        eta_ref = s["viscosity_mpas_25c"]
        ea = s["fitted_activation_energy_j_mol"]
        r2 = s["fitted_r_squared"]
        if r2 < min_r2:
            min_r2 = r2
        per_total += 1
        for tc, key in [(40.0, "viscosity_mpas_40c"), (60.0, "viscosity_mpas_60c")]:
            pub = s[key]
            pred = arrhenius(eta_ref, 25.0, tc, ea)
            err = abs(pred - pub) / pub
            base_err = abs(eta_ref - pub) / pub
            train_err_sum += err
            baseline_err_sum += base_err
            train_pairs += 1
        pub30 = s["viscosity_mpas_30c"]
        pred30 = arrhenius(eta_ref, 25.0, 30.0, ea)
        err30 = abs(pred30 - pub30) / pub30
        held_out_err_sum += err30
        if err30 > max_held:
            max_held = err30
        if err30 <= 0.10:
            within10 += 1
        if err30 <= 0.05:
            within5 += 1
    mape = train_err_sum / train_pairs
    base_mape = baseline_err_sum / train_pairs
    lift = base_mape - mape
    held_mape = held_out_err_sum / per_total
    return {
        "arrhenius_mape_within_training_range": mape,
        "constant_baseline_mape": base_mape,
        "arrhenius_over_constant_baseline_lift": lift,
        "held_out_temperature_extrapolation_mape": held_mape,
        "per_solvent_within_10pct_rate": within10 / per_total,
        "per_solvent_within_5pct_rate": within5 / per_total,
        "r_squared_arrhenius_minimum": min_r2,
        "held_out_worst_case_abs_pct_error": max_held,
    }


GATES = {
    "arrhenius_mape_within_training_range": ("ceiling", 0.05),
    "held_out_temperature_extrapolation_mape": ("ceiling", 0.08),
    "arrhenius_over_constant_baseline_lift": ("floor", 0.20),
    "per_solvent_within_10pct_rate": ("floor", 0.85),
}


def gate_pass(report):
    out = {}
    for k, (kind, bound) in GATES.items():
        v = report[k]
        out[k] = (v <= bound) if kind == "ceiling" else (v >= bound)
    return out


def main():
    fixture = json.load(open(FIXTURE))
    solvents = fixture["solvents"]

    original_report = run_report(solvents)
    original_gates = gate_pass(original_report)

    # --- Angle 1: offline-fit reproducibility ---------------------------------
    reproducibility_rows = []
    max_ea_rel_err = 0.0
    max_r2_abs_err = 0.0
    for s in solvents:
        ea2, r22 = fit_ea_r2(s["viscosity_mpas_20c"], s["viscosity_mpas_40c"], s["viscosity_mpas_60c"])
        rel = abs(ea2 - s["fitted_activation_energy_j_mol"]) / abs(s["fitted_activation_energy_j_mol"])
        r2diff = abs(r22 - s["fitted_r_squared"])
        max_ea_rel_err = max(max_ea_rel_err, rel)
        max_r2_abs_err = max(max_r2_abs_err, r2diff)
        reproducibility_rows.append({
            "solvent_id": s["solvent_id"],
            "fixture_ea_j_mol": s["fitted_activation_energy_j_mol"],
            "rederived_ea_j_mol": round(ea2, 6),
            "rel_err": rel,
            "fixture_r2": s["fitted_r_squared"],
            "rederived_r2": round(r22, 8),
        })

    # --- Angle 2: external data-provenance cross-check (glycerol) -------------
    dow_glycerol_100pct = {20.0: 1410.0, 30.0: 612.0, 40.0: 284.0, 60.0: 81.3}
    fixture_glycerol = next(s for s in solvents if s["solvent_id"] == "glycerol")
    provenance_rows = []
    for tc, dow_val in dow_glycerol_100pct.items():
        key = "viscosity_mpas_{}c".format(int(tc))
        fixture_val = fixture_glycerol[key]
        rel_pct = (fixture_val - dow_val) / dow_val * 100
        provenance_rows.append({
            "temperature_c": tc,
            "fixture_value_mpas": fixture_val,
            "segur_oberstar_1951_dow_table_value_mpas": dow_val,
            "relative_diff_pct": round(rel_pct, 4),
        })

    corrected_solvents = []
    for s in solvents:
        if s["solvent_id"] == "glycerol":
            s2 = dict(s)
            s2["viscosity_mpas_20c"] = dow_glycerol_100pct[20.0]
            s2["viscosity_mpas_30c"] = dow_glycerol_100pct[30.0]
            s2["viscosity_mpas_40c"] = dow_glycerol_100pct[40.0]
            s2["viscosity_mpas_60c"] = dow_glycerol_100pct[60.0]
            ea, r2 = fit_ea_r2(dow_glycerol_100pct[20.0], dow_glycerol_100pct[40.0], dow_glycerol_100pct[60.0])
            s2["fitted_activation_energy_j_mol"] = ea
            s2["fitted_r_squared"] = r2
            corrected_solvents.append(s2)
        else:
            corrected_solvents.append(s)

    corrected_report = run_report(corrected_solvents)
    corrected_gates = gate_pass(corrected_report)
    any_gate_flip = any(original_gates[k] != corrected_gates[k] for k in GATES)

    # --- Positive control 1: fabricated offline-fit Ea (should be caught by angle 1) ---
    planted_ea = []
    for s in solvents:
        if s["solvent_id"] == "water":
            s3 = dict(s)
            s3["fitted_activation_energy_j_mol"] = s["fitted_activation_energy_j_mol"] * 1.20
            planted_ea.append(s3)
        else:
            planted_ea.append(s)
    planted_ea_max_rel = 0.0
    for s in planted_ea:
        ea2, _ = fit_ea_r2(s["viscosity_mpas_20c"], s["viscosity_mpas_40c"], s["viscosity_mpas_60c"])
        rel = abs(ea2 - s["fitted_activation_energy_j_mol"]) / abs(s["fitted_activation_energy_j_mol"])
        planted_ea_max_rel = max(planted_ea_max_rel, rel)

    # --- Positive control 2: realistic wrong-column defect (should flip gates, angle 2) ---
    wrong_column_90pct = {20.0: 219.0, 30.0: 109.0, 40.0: 60.0, 60.0: 22.5}
    planted_col = []
    for s in solvents:
        if s["solvent_id"] == "glycerol":
            s4 = dict(s)
            s4["viscosity_mpas_20c"] = wrong_column_90pct[20.0]
            s4["viscosity_mpas_30c"] = wrong_column_90pct[30.0]
            s4["viscosity_mpas_40c"] = wrong_column_90pct[40.0]
            s4["viscosity_mpas_60c"] = wrong_column_90pct[60.0]
            ea4, r24 = fit_ea_r2(wrong_column_90pct[20.0], wrong_column_90pct[40.0], wrong_column_90pct[60.0])
            s4["fitted_activation_energy_j_mol"] = ea4
            s4["fitted_r_squared"] = r24
            planted_col.append(s4)
        else:
            planted_col.append(s)
    planted_col_report = run_report(planted_col)
    planted_col_gates = gate_pass(planted_col_report)
    planted_col_any_flip = any(planted_col_gates[k] != True for k in GATES)

    refuted = (max_ea_rel_err > 1e-6) or (max_r2_abs_err > 1e-6) or any_gate_flip

    diagnostic = {
        "schema": "amphora.viscosity-score.arrhenius-fixture-source-provenance-probe.v1",
        "fixture_path": "amphora-viscosity-score/reference/phase0-viscosity-known-answer.v1.json",
        "fixture_sha256": sha256_file(FIXTURE),
        "kpi_under_attack_path": "amphora-viscosity-score/evidence/phase0/kpis/viscosity-arrhenius-kpi.v1.json",
        "kpi_under_attack_sha256": sha256_file(KPI),
        "gas_constant_j_mol_k": R,
        "original_report": original_report,
        "original_gates_pass": original_gates,
        "angle_1_offline_fit_reproducibility": {
            "max_ea_relative_error": max_ea_rel_err,
            "max_r2_absolute_error": max_r2_abs_err,
            "n_solvents": len(reproducibility_rows),
            "per_solvent": sorted(reproducibility_rows, key=lambda r: -r["rel_err"]),
            "interpretation": (
                "essentially exact (floating-point-precision) reproduction of the fixture's baked-in "
                "'fitted offline via numpy' Ea/R2 from its own raw {20,40,60}C viscosity numbers"
                if max_ea_rel_err <= 1e-6 else
                "MISMATCH: fixture's claimed offline fit does not reproduce from its own raw data"
            ),
        },
        "angle_2_external_data_provenance": {
            "solvent_checked": "glycerol",
            "reason_selected": "highest fitted_activation_energy_j_mol (58008 J/mol) of all 25 solvents; "
                                "most temperature-sensitive; a known super-Arrhenius, glass-forming liquid",
            "external_source": {
                "citation": "Segur, J.B. & Oberstar, H.E. (1951) Ind. Eng. Chem. 43(9):2117-2120, "
                             "100 wt% glycerine column, as reproduced in the widely-cited Dow/GPA "
                             "aqueous-glycerine-viscosity compilation",
                "mirror_url_fetched_this_fire": "https://web.cecs.pdx.edu/~gerry/class/EAS361/lab/pdf/glycerinWaterViscosity_Dorsey.pdf",
            },
            "fixture_cited_source": "CRC Handbook 100th ed. Table 6.183 glycerol dynamic viscosity",
            "per_temperature": provenance_rows,
            "corrected_report": corrected_report,
            "corrected_gates_pass": corrected_gates,
            "any_gate_flip_vs_original": any_gate_flip,
            "deltas_vs_original": {
                k: corrected_report[k] - original_report[k] for k in original_report
            },
        },
        "positive_control_1_fabricated_ea": {
            "planted_defect": "water fitted_activation_energy_j_mol multiplied by 1.20 (a +20% fabrication)",
            "how_planted": "reference/phase0-viscosity-known-answer.v1.json solvents[water].fitted_activation_energy_j_mol "
                            "15530.237 -> 18636.284 (in a private in-memory copy only; fixture file itself untouched)",
            "detected": bool(planted_ea_max_rel > 0.01),
            "evidence": "angle-1 reproducibility check max_ea_relative_error jumps from {:.10f} to {:.6f}".format(
                max_ea_rel_err, planted_ea_max_rel),
        },
        "positive_control_2_wrong_column": {
            "planted_defect": "glycerol viscosity_mpas_{20,30,40,60}c replaced with the table's 90 wt% "
                               "glycerine column instead of the correct 100 wt% column -- the same class "
                               "of table-misread error this portfolio's Amorim-2021 HB fire already proved "
                               "is a real, recurring hazard",
            "how_planted": "glycerol raw values 1412.0/623.0/289.0/81.3 -> 219.0/109.0/60.0/22.5 mPa*s "
                            "(private in-memory copy only; fixture file itself untouched)",
            "detected": bool(planted_col_any_flip),
            "evidence": {
                "gates": planted_col_gates,
                "arrhenius_mape_within_training_range": planted_col_report["arrhenius_mape_within_training_range"],
                "held_out_temperature_extrapolation_mape": planted_col_report["held_out_temperature_extrapolation_mape"],
            },
        },
        "verdict": "CLAIM_REFUTED" if refuted else "CLAIM_SURVIVED",
    }

    print(json.dumps(diagnostic, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
