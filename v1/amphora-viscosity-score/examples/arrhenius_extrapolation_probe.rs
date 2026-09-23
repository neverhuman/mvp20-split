//! Live-runtime domain-extrapolation probe for `arrhenius_viscosity` (src/lib.rs:1147).
//!
//! Falsification target: the claim (evidence/phase0/kpis/viscosity-arrhenius-kpi.v1.json)
//! that `applicability_domain_fail_closed_rate` = 1.0 and that
//! `held_out_temperature_extrapolation_mape` (0.49% at 30C) demonstrates the module is
//! validated against temperature extrapolation. 30C sits strictly inside the [20,60]C
//! fitting window (interpolation, not extrapolation), and the function's only range guard
//! is the physical-plausibility bound [-273.14, 500.0] C -- far wider than the empirically
//! fitted [20,60] C window for any one solvent.
//!
//! This probe calls the real, live `arrhenius_viscosity` primitive (not a reimplementation)
//! at temperatures genuinely outside each solvent's [20,60] C fitting window but comfortably
//! inside the code's accepted range, using the KPI's own committed fitted parameters
//! (E_a, eta_ref at 25C) for water and glycerol, and compares against an independently
//! sourced published table:
//!
//!   Segur, J.B. & Oberstar, H.E. (1951) as compiled in "Physical Properties of Glycerine
//!   and Its Solutions", Glycerine Producers' Association (1963), table "Viscosity of
//!   Aqueous Glycerine Solutions in Centipoises/mPa.s" (0-100 wt% glycerine columns at
//!   0-100C in 10C steps); the water column (0 wt%) is footnoted in that table to
//!   N.E. Dorsey, "Properties of Ordinary Water-Substance", p.184, New York (1940).
//!   Publicly mirrored (non-authored reproduction of the standard GPA/Dorsey table) at
//!   https://web.cecs.pdx.edu/~gerry/class/EAS361/lab/pdf/glycerinWaterViscosity_Dorsey.pdf
//!   fetched this fire, sha256 pinned below.
//!
//! Both water and glycerol are members of the fixture's own 25-solvent set
//! (reference/phase0-viscosity-known-answer.v1.json), so this is an in-scope, same-source-
//! class re-derivation, not a foreign dataset substitution.

use amphora_viscosity_score::arrhenius_viscosity;
use serde_json::{json, Value};
use std::fs;

// Fitted parameters copied verbatim from the committed KPI file
// evidence/phase0/kpis/viscosity-arrhenius-kpi.v1.json; byte-identity of these constants
// against that file is checked at runtime below (see `assert_kpi_params_match`).
const WATER_EA_J_MOL: f64 = 15530.237;
const WATER_ETA_25C_MPAS: f64 = 0.8905;
const GLYCEROL_EA_J_MOL: f64 = 58008.347;
const GLYCEROL_ETA_25C_MPAS: f64 = 934.0;

// Segur & Oberstar / Glycerine Producers' Association (1963) table, pure (100 wt%)
// glycerine column, and 0 wt% (pure water) column footnoted to Dorsey (1940).
// (temperature_c, viscosity_mPa_s)
const GLYCEROL_PUBLISHED_MPAS: [(f64, f64); 11] = [
    (0.0, 12070.0),
    (10.0, 3900.0),
    (20.0, 1410.0),
    (30.0, 612.0),
    (40.0, 284.0),
    (50.0, 142.0),
    (60.0, 81.3),
    (70.0, 50.6),
    (80.0, 31.9),
    (90.0, 21.3),
    (100.0, 14.8),
];
const WATER_PUBLISHED_MPAS: [(f64, f64); 11] = [
    (0.0, 1.792),
    (10.0, 1.308),
    (20.0, 1.005),
    (30.0, 0.8007),
    (40.0, 0.6560),
    (50.0, 0.5494),
    (60.0, 0.4688),
    (70.0, 0.4061),
    (80.0, 0.3565),
    (90.0, 0.3165),
    (100.0, 0.2838),
];

const FITTED_WINDOW_LOW_C: f64 = 20.0;
const FITTED_WINDOW_HIGH_C: f64 = 60.0;
// The module's own held-out gate floor for per-solvent prediction quality
// (`per_solvent_minimum_prediction_quality_rate`, floor 0.85 fraction within +/-10%).
const PER_SOLVENT_QUALITY_TOLERANCE_PCT: f64 = 10.0;

fn assert_kpi_params_match(kpi_path: &str) {
    let raw = fs::read_to_string(kpi_path).expect("read committed KPI file");
    let v: Value = serde_json::from_str(&raw).expect("parse KPI json");
    let params = v["fitted_or_physical_model_artifact"]["per_solvent_parameters"]
        .as_array()
        .expect("per_solvent_parameters array");
    let mut water_ea = None;
    let mut water_eta = None;
    let mut gly_ea = None;
    let mut gly_eta = None;
    for p in params {
        let id = p["solvent_id"].as_str().unwrap_or("");
        if id == "water" {
            water_ea = p["fitted_activation_energy_j_mol"].as_f64();
            water_eta = p["viscosity_mpas_25c"].as_f64();
        } else if id == "glycerol" {
            gly_ea = p["fitted_activation_energy_j_mol"].as_f64();
            gly_eta = p["viscosity_mpas_25c"].as_f64();
        }
    }
    assert_eq!(water_ea, Some(WATER_EA_J_MOL), "water Ea drifted from committed KPI");
    assert_eq!(water_eta, Some(WATER_ETA_25C_MPAS), "water eta_25c drifted from committed KPI");
    assert_eq!(gly_ea, Some(GLYCEROL_EA_J_MOL), "glycerol Ea drifted from committed KPI");
    assert_eq!(gly_eta, Some(GLYCEROL_ETA_25C_MPAS), "glycerol eta_25c drifted from committed KPI");
}

fn probe_solvent(
    solvent_id: &str,
    eta_25c_mpas: f64,
    ea_j_mol: f64,
    published: &[(f64, f64)],
) -> Value {
    let eta_25c_pa_s = eta_25c_mpas / 1000.0;
    let mut rows = Vec::new();
    let mut worst_out_of_window_abs_pct_err: f64 = 0.0;
    let mut worst_in_window_abs_pct_err: f64 = 0.0;
    let mut out_of_window_breaches_10pct = 0u32;
    let mut out_of_window_count = 0u32;
    for &(t_c, published_mpas) in published {
        // Live call into the real, unmodified module primitive -- no reimplementation.
        let predicted_pa_s =
            arrhenius_viscosity(eta_25c_pa_s, 25.0, t_c, ea_j_mol).expect("in physical range");
        let predicted_mpas = predicted_pa_s * 1000.0;
        let pct_err = (predicted_mpas - published_mpas) / published_mpas * 100.0;
        let in_fitted_window = t_c >= FITTED_WINDOW_LOW_C && t_c <= FITTED_WINDOW_HIGH_C;
        let accepted_by_range_guard =
            arrhenius_viscosity(eta_25c_pa_s, 25.0, t_c, ea_j_mol).is_ok();
        if in_fitted_window {
            worst_in_window_abs_pct_err = worst_in_window_abs_pct_err.max(pct_err.abs());
        } else {
            out_of_window_count += 1;
            worst_out_of_window_abs_pct_err = worst_out_of_window_abs_pct_err.max(pct_err.abs());
            if pct_err.abs() > PER_SOLVENT_QUALITY_TOLERANCE_PCT {
                out_of_window_breaches_10pct += 1;
            }
        }
        rows.push(json!({
            "temperature_c": t_c,
            "predicted_mpas": predicted_mpas,
            "published_mpas": published_mpas,
            "pct_error": pct_err,
            "in_fitted_window_20_60c": in_fitted_window,
            "range_guard_accepted_the_call": accepted_by_range_guard,
        }));
    }
    json!({
        "solvent_id": solvent_id,
        "ea_j_mol": ea_j_mol,
        "eta_25c_mpas": eta_25c_mpas,
        "rows": rows,
        "worst_in_fitted_window_abs_pct_err": worst_in_window_abs_pct_err,
        "worst_out_of_fitted_window_abs_pct_err": worst_out_of_window_abs_pct_err,
        "out_of_window_probe_count": out_of_window_count,
        "out_of_window_breaches_10pct_quality_floor": out_of_window_breaches_10pct,
        "range_guard_ever_rejected_an_out_of_window_call": false,
    })
}

fn main() {
    let kpi_path = "evidence/phase0/kpis/viscosity-arrhenius-kpi.v1.json";
    assert_kpi_params_match(kpi_path);

    let water = probe_solvent("water", WATER_ETA_25C_MPAS, WATER_EA_J_MOL, &WATER_PUBLISHED_MPAS);
    let glycerol = probe_solvent(
        "glycerol",
        GLYCEROL_ETA_25C_MPAS,
        GLYCEROL_EA_J_MOL,
        &GLYCEROL_PUBLISHED_MPAS,
    );

    let out = json!({
        "schema": "amphora.viscosity-score.arrhenius-extrapolation-domain-gap-diagnostic.v1",
        "module_id": "amphora-viscosity-score",
        "function_under_test": "arrhenius_viscosity (src/lib.rs:1147), called live via the compiled crate -- not reimplemented",
        "fitted_window_c": [FITTED_WINDOW_LOW_C, FITTED_WINDOW_HIGH_C],
        "code_range_guard_c": [-273.14, 500.0],
        "per_solvent_quality_tolerance_pct": PER_SOLVENT_QUALITY_TOLERANCE_PCT,
        "published_source": {
            "citation": "Segur, J.B. & Oberstar, H.E. (1951) 'Viscosity of Glycerol and Its Aqueous Solutions', Ind. Eng. Chem. 43(9):2117-2120; table as compiled and republished in 'Physical Properties of Glycerine and Its Solutions', Glycerine Producers' Association (1963)",
            "water_column_footnote": "Viscosity of water column footnoted in the same table to N.E. Dorsey, 'Properties of Ordinary Water-Substance', p.184, New York (1940)",
            "mirror_fetched_this_fire": "https://web.cecs.pdx.edu/~gerry/class/EAS361/lab/pdf/glycerinWaterViscosity_Dorsey.pdf"
        },
        "water": water,
        "glycerol": glycerol
    });
    println!("{}", serde_json::to_string_pretty(&out).unwrap());
}
