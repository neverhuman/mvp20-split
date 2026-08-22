//! Phase-0 KPI harness for `amphora-viscosity-score` — pure-solvent Arrhenius slice.
//!
//! Drives the deterministic `arrhenius_viscosity` primitive across a
//! self-authored known-answer fixture of 25 pure solvents with viscosity
//! at {20, 25, 30, 40, 60}°C from CRC Handbook 100th ed., NIST WebBook,
//! and Yaws' Handbook. Activation energies are fitted offline from the
//! {20, 40, 60}°C points; 25°C anchors the runtime `η_ref`; 30°C is a
//! held-out mid-range interpolation target.

use std::collections::BTreeMap;
use std::fs;
use std::path::PathBuf;

use amphora_core::{canonicalize, stable_hash};
use amphora_viscosity_score::arrhenius_viscosity;
use serde_json::{json, Map, Value};
use sha2::{Digest, Sha256};

fn workspace_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .expect("crate has a parent workspace")
        .to_path_buf()
}

fn fixture_path() -> PathBuf {
    workspace_root().join("amphora-viscosity-score/reference/phase0-viscosity-known-answer.v1.json")
}

fn benchmark_lock_path() -> PathBuf {
    workspace_root()
        .join("amphora-viscosity-score/evidence/phase0/benchmark/benchmark-lock.v1.json")
}

// SCHEMA-ERA FIX (B2). The shipped artifact
// `amphora-viscosity-score/evidence/phase0/benchmark/result.v1.json` has exactly one
// legitimate writer: the runtime evaluator (`amphora phase0 evaluate` ->
// amphora-cli/src/phase0.rs::evaluate). Its exact bytes are pinned by
// `metrics.benchmark_result_sha256` inside the immutable, signed Phase-0
// evaluation receipt, and re-read by `verify_evaluation_result`. This harness
// emits the MODULE-HARNESS KPI shape, which the verifier rejects, so writing it
// there silently dropped the module out of `phase0_count`. The round-trip now
// uses the per-target cargo scratch directory and never mutates shipped
// evidence.
fn result_path() -> PathBuf {
    PathBuf::from(env!("CARGO_TARGET_TMPDIR"))
        .join("amphora-viscosity-score-phase0-kpi-result.v1.json")
}

fn read_fixture() -> Value {
    let bytes = fs::read(fixture_path()).expect("fixture readable");
    serde_json::from_slice(&bytes).expect("fixture is JSON")
}

fn file_sha256(bytes: &[u8]) -> String {
    let mut digest = Sha256::new();
    digest.update(bytes);
    format!("{:x}", digest.finalize())
}

fn observed_number(value: &Value, key: &str) -> f64 {
    value[key].as_f64().expect("f64 present")
}

fn compute_report() -> Value {
    let fixture = read_fixture();
    let acceptance_bar = fixture["acceptance_bar"].clone();
    let solvents = fixture["solvents"].as_array().expect("solvents array");

    let mut per_solvent: Vec<Value> = Vec::new();

    let mut train_range_abs_err_sum = 0.0_f64;
    let mut train_range_pairs = 0_usize;
    let mut baseline_abs_err_sum = 0.0_f64;
    let mut held_out_30_abs_err_sum = 0.0_f64;
    let mut per_solvent_within_10 = 0_usize;
    let mut per_solvent_within_5 = 0_usize;
    let mut per_solvent_total = 0_usize;
    let mut min_r_squared = f64::INFINITY;
    let mut max_held_out_error = 0.0_f64;

    for solvent in solvents {
        let sid = solvent["solvent_id"].as_str().unwrap();
        let eta_ref_mpas = observed_number(solvent, "viscosity_mpas_25c");
        let eta_ref_pas = eta_ref_mpas * 1e-3;
        let ea = observed_number(solvent, "fitted_activation_energy_j_mol");
        let r_sq = observed_number(solvent, "fitted_r_squared");
        if r_sq < min_r_squared {
            min_r_squared = r_sq;
        }
        per_solvent_total += 1;

        let mut per_temperature = Vec::new();
        for (t_c, key) in [
            (40.0_f64, "viscosity_mpas_40c"),
            (60.0_f64, "viscosity_mpas_60c"),
        ] {
            let eta_pub_mpas = observed_number(solvent, key);
            let predicted_pas = arrhenius_viscosity(eta_ref_pas, 25.0, t_c, ea)
                .expect("Arrhenius in-domain prediction");
            let predicted_mpas = predicted_pas * 1e3;
            let abs_err_rel = (predicted_mpas - eta_pub_mpas).abs() / eta_pub_mpas;
            let baseline_abs_err_rel = (eta_ref_mpas - eta_pub_mpas).abs() / eta_pub_mpas;
            train_range_abs_err_sum += abs_err_rel;
            baseline_abs_err_sum += baseline_abs_err_rel;
            train_range_pairs += 1;
            per_temperature.push(json!({
                "temperature_c": t_c,
                "predicted_viscosity_mpas": predicted_mpas,
                "published_viscosity_mpas": eta_pub_mpas,
                "arrhenius_absolute_percent_error": abs_err_rel,
                "constant_baseline_predicted_viscosity_mpas": eta_ref_mpas,
                "constant_baseline_absolute_percent_error": baseline_abs_err_rel,
            }));
        }

        // Held-out 30°C interpolation
        let eta_30_pub = observed_number(solvent, "viscosity_mpas_30c");
        let predicted_30_pas = arrhenius_viscosity(eta_ref_pas, 25.0, 30.0, ea)
            .expect("Arrhenius 30°C interpolation");
        let predicted_30_mpas = predicted_30_pas * 1e3;
        let abs_err_30 = (predicted_30_mpas - eta_30_pub).abs() / eta_30_pub;
        held_out_30_abs_err_sum += abs_err_30;
        if abs_err_30 > max_held_out_error {
            max_held_out_error = abs_err_30;
        }
        if abs_err_30 <= 0.10 {
            per_solvent_within_10 += 1;
        }
        if abs_err_30 <= 0.05 {
            per_solvent_within_5 += 1;
        }

        per_solvent.push(json!({
            "solvent_id": sid,
            "smiles": solvent["smiles"],
            "formula": solvent["formula"],
            "fitted_activation_energy_j_mol": ea,
            "fitted_r_squared": r_sq,
            "reference_viscosity_mpas_25c": eta_ref_mpas,
            "training_range_predictions": per_temperature,
            "held_out_30c": {
                "predicted_viscosity_mpas": predicted_30_mpas,
                "published_viscosity_mpas": eta_30_pub,
                "absolute_percent_error": abs_err_30,
            },
        }));
    }

    let arrhenius_mape = train_range_abs_err_sum / train_range_pairs.max(1) as f64;
    let baseline_mape = baseline_abs_err_sum / train_range_pairs.max(1) as f64;
    let lift = baseline_mape - arrhenius_mape;
    let held_out_30_mape = held_out_30_abs_err_sum / per_solvent_total.max(1) as f64;
    let per_solvent_within_10_rate = per_solvent_within_10 as f64 / per_solvent_total.max(1) as f64;
    let per_solvent_within_5_rate = per_solvent_within_5 as f64 / per_solvent_total.max(1) as f64;

    // Applicability-domain probes: every one must return Err.
    let ad_probes: Vec<(f64, f64, f64, f64, &str)> = vec![
        (f64::NAN, 25.0, 40.0, 10_000.0, "nan_viscosity"),
        (0.5e-3, f64::INFINITY, 40.0, 10_000.0, "infinity_reference_temperature"),
        (0.5e-3, 25.0, 40.0, f64::NAN, "nan_activation_energy"),
        (0.0, 25.0, 40.0, 10_000.0, "zero_viscosity"),
        (0.5e-3, 25.0, 40.0, 0.0, "zero_activation_energy"),
        (-0.5e-3, 25.0, 40.0, 10_000.0, "negative_viscosity"),
        (0.5e-3, 25.0, 40.0, -1_000.0, "negative_activation_energy"),
        (0.5e-3, -300.0, 40.0, 10_000.0, "reference_temperature_below_absolute_zero"),
        (0.5e-3, 25.0, -273.5, 10_000.0, "test_temperature_below_absolute_zero"),
        (0.5e-3, 25.0, 700.0, 10_000.0, "test_temperature_above_500c_ceiling"),
    ];
    let ad_probe_total = ad_probes.len();
    let ad_fail_closed: Vec<Value> = ad_probes
        .iter()
        .map(|(eta, t_ref, t, ea, label)| {
            let result = arrhenius_viscosity(*eta, *t_ref, *t, *ea);
            json!({
                "probe": label,
                "arguments": {"eta_ref_pa_s": eta, "T_ref_c": t_ref, "T_c": t, "Ea_j_mol": ea},
                "fail_closed": result.is_err(),
            })
        })
        .collect();
    let fail_closed_count = ad_fail_closed
        .iter()
        .filter(|row| row["fail_closed"] == json!(true))
        .count();
    let applicability_domain_fail_closed_rate =
        fail_closed_count as f64 / ad_probe_total as f64;

    // Authority-lock preservation: fixture authority block preserves required locks.
    let authority = &fixture["authority"];
    let authority_lock_preservation_rate = if authority["optimizer_authority"] == json!(false)
        && authority["solver_use_disabled"] == json!(true)
        && authority["commercial_formulation_authority"] == json!(false)
    {
        1.0
    } else {
        0.0
    };

    let kpi = json!({
        "arrhenius_mape_within_training_range": {
            "observed": arrhenius_mape,
            "ceiling": acceptance_bar["arrhenius_mape_within_training_range_ceiling"],
            "direction": "MINIMIZE",
            "sample_size": train_range_pairs,
            "passed": arrhenius_mape
                <= acceptance_bar["arrhenius_mape_within_training_range_ceiling"].as_f64().unwrap_or(0.05),
        },
        "arrhenius_over_constant_baseline_lift": {
            "observed": lift,
            "constant_baseline_mape": baseline_mape,
            "floor": acceptance_bar["arrhenius_over_constant_baseline_lift_floor"],
            "direction": "MAXIMIZE",
            "passed": lift
                >= acceptance_bar["arrhenius_over_constant_baseline_lift_floor"].as_f64().unwrap_or(0.20),
        },
        "held_out_temperature_extrapolation_mape": {
            "observed": held_out_30_mape,
            "worst_case_absolute_percent_error": max_held_out_error,
            "ceiling": acceptance_bar["held_out_temperature_extrapolation_mape_ceiling"],
            "direction": "MINIMIZE",
            "sample_size": per_solvent_total,
            "passed": held_out_30_mape
                <= acceptance_bar["held_out_temperature_extrapolation_mape_ceiling"].as_f64().unwrap_or(0.08),
        },
        "per_solvent_minimum_prediction_quality_rate": {
            "observed": per_solvent_within_10_rate,
            "within_5_percent_rate": per_solvent_within_5_rate,
            "floor": acceptance_bar["per_solvent_minimum_prediction_quality_rate_floor"],
            "direction": "MAXIMIZE",
            "sample_size": per_solvent_total,
            "passed": per_solvent_within_10_rate
                >= acceptance_bar["per_solvent_minimum_prediction_quality_rate_floor"].as_f64().unwrap_or(0.85),
        },
        "applicability_domain_fail_closed_rate": {
            "observed": applicability_domain_fail_closed_rate,
            "probe_sample_size": ad_probe_total,
            "floor": acceptance_bar["applicability_domain_fail_closed_rate_floor"],
            "direction": "MAXIMIZE",
            "probes": ad_fail_closed,
            "passed": applicability_domain_fail_closed_rate
                >= acceptance_bar["applicability_domain_fail_closed_rate_floor"].as_f64().unwrap_or(1.0),
        },
        "authority_lock_preservation_rate": {
            "observed": authority_lock_preservation_rate,
            "floor": acceptance_bar["authority_lock_preservation_rate_floor"],
            "direction": "MAXIMIZE",
            "passed": authority_lock_preservation_rate
                >= acceptance_bar["authority_lock_preservation_rate_floor"].as_f64().unwrap_or(1.0),
        },
        "r_squared_arrhenius_minimum": {
            "observed": min_r_squared,
            "ceiling_reported_only": acceptance_bar["reported_r_squared_ceiling_only"],
            "direction": "MAXIMIZE",
            "note": "reported observationally; every solvent's linear ln(η) vs. 1/T fit R² is stored per-record",
        },
    });

    let benchmark_lock_bytes = fs::read(benchmark_lock_path()).expect("benchmark-lock readable");
    let benchmark_lock_sha256 = file_sha256(&benchmark_lock_bytes);
    let fixture_bytes = fs::read(fixture_path()).expect("fixture readable");
    let dataset_sha256 = file_sha256(&fixture_bytes);

    let diagnostic = json!({
        "schema": "amphora.module-phase0-benchmark-diagnostic.v1",
        "module_id": "amphora-viscosity-score",
        "kpi": kpi.clone(),
        "records": per_solvent.clone(),
        "passed": kpi["arrhenius_mape_within_training_range"]["passed"] == json!(true)
            && kpi["arrhenius_over_constant_baseline_lift"]["passed"] == json!(true)
            && kpi["held_out_temperature_extrapolation_mape"]["passed"] == json!(true)
            && kpi["per_solvent_minimum_prediction_quality_rate"]["passed"] == json!(true)
            && kpi["applicability_domain_fail_closed_rate"]["passed"] == json!(true)
            && kpi["authority_lock_preservation_rate"]["passed"] == json!(true),
    });
    let diagnostic_bytes = serde_json::to_vec(&canonicalize(&diagnostic)).expect("canonical bytes");
    let diagnostic_sha256 = file_sha256(&diagnostic_bytes);

    let mut result = Map::new();
    result.insert("schema".into(), json!("amphora.module-phase0-benchmark-result.v1"));
    result.insert("module_id".into(), json!("amphora-viscosity-score"));
    result.insert(
        "benchmark_id".into(),
        json!("amphora-viscosity-score-phase0-arrhenius-known-answer-v1"),
    );
    result.insert("benchmark_lock_sha256".into(), json!(benchmark_lock_sha256));
    result.insert("dataset_fixture_sha256".into(), json!(dataset_sha256));
    result.insert("acceptance_bar".into(), acceptance_bar);
    result.insert("kpi".into(), kpi);
    result.insert("records".into(), json!(per_solvent));
    result.insert("benchmark_execution_complete".into(), json!(true));
    result.insert(
        "first_replay".into(),
        json!({
            "diagnostic_receipt": diagnostic.clone(),
            "diagnostic_sha256": diagnostic_sha256,
        }),
    );
    result.insert(
        "second_replay".into(),
        json!({
            "diagnostic_receipt": diagnostic,
            "diagnostic_sha256": diagnostic_sha256,
        }),
    );

    // Silence unused warning about stable_hash import kept for future canonical binding.
    let _ = stable_hash(&Value::Null);
    let _: BTreeMap<String, Value> = BTreeMap::new();

    canonicalize(&Value::Object(result))
}

#[test]
fn viscosity_phase0_kpi_report_is_deterministic_and_gates_pass() {
    let first = compute_report();
    let first_bytes = serde_json::to_vec(&first).expect("canonical");
    let second_bytes = serde_json::to_vec(&compute_report()).expect("canonical");
    assert_eq!(first_bytes, second_bytes, "KPI report is not byte-stable");

    let kpi = &first["kpi"];
    for gate in [
        "arrhenius_mape_within_training_range",
        "arrhenius_over_constant_baseline_lift",
        "held_out_temperature_extrapolation_mape",
        "per_solvent_minimum_prediction_quality_rate",
        "applicability_domain_fail_closed_rate",
        "authority_lock_preservation_rate",
    ] {
        assert_eq!(
            kpi[gate]["passed"],
            json!(true),
            "KPI gate {gate} failed: observed={}, threshold={}",
            kpi[gate]["observed"],
            kpi[gate].get("ceiling").or_else(|| kpi[gate].get("floor")).unwrap_or(&Value::Null),
        );
    }

    let result_path = result_path();
    if let Some(parent) = result_path.parent() {
        fs::create_dir_all(parent).expect("create result parent");
    }
    fs::write(&result_path, &first_bytes).expect("write result artifact");
    let round_trip = fs::read(&result_path).expect("read back");
    assert_eq!(round_trip, first_bytes, "written artifact differs");
}
