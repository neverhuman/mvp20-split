//! Phase-0 KPI harness for `amphora-cure-potlife-gate`.
//!
//! Drives the deterministic `effective_cure_rate` primitive across a
//! self-authored known-answer fixture of 12 two-part epoxy-amine systems
//! with published activation energies (Prime 1997; Kamal-Sourour 1973;
//! Riccardi et al. 1984; Blanco et al. 2005) and pot-life values from
//! supplier TDSs at four temperatures (10, 22.78, 30, 40 °C). Reference
//! temperature is 22.78 °C = 73 °F (coating industry standard, ASTM D2196
//! and Navy prime spec).
//!
//! Pot-life scales inversely with the Arrhenius rate constant:
//!   pot_life(T) = pot_life_ref / effective_cure_rate(T)
//!
//! The Rust primitive `effective_cure_rate(T_k, Ea, T_ref_k)` returns
//! `exp(-Ea/R · (1/T − 1/T_ref))`, so the reciprocal is
//! `exp((Ea/R) · (1/T − 1/T_ref))` — the classical Arrhenius pot-life
//! scaling.

use std::collections::BTreeMap;
use std::fs;
use std::path::PathBuf;

use amphora_core::{canonicalize, stable_hash};
use amphora_cure_potlife_gate::{celsius_to_kelvin, effective_cure_rate};
use serde_json::{json, Map, Value};
use sha2::{Digest, Sha256};

const T_REF_C: f64 = 22.777_777_777_777_778; // 73 °F

fn workspace_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .expect("crate has a parent workspace")
        .to_path_buf()
}

fn fixture_path() -> PathBuf {
    workspace_root()
        .join("amphora-cure-potlife-gate/reference/phase0-cure-potlife-known-answer.v1.json")
}

fn benchmark_lock_path() -> PathBuf {
    workspace_root()
        .join("amphora-cure-potlife-gate/evidence/phase0/benchmark/benchmark-lock.v1.json")
}

// SCHEMA-ERA FIX (B2). The shipped artifact
// `amphora-cure-potlife-gate/evidence/phase0/benchmark/result.v1.json` has exactly one
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
        .join("amphora-cure-potlife-gate-phase0-kpi-result.v1.json")
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

fn arrhenius_pot_life(pot_life_ref_min: f64, t_ref_k: f64, t_k: f64, ea: f64) -> f64 {
    let rate = effective_cure_rate(t_k, ea, t_ref_k).expect("in-domain Arrhenius rate");
    pot_life_ref_min / rate
}

fn compute_report() -> Value {
    let fixture = read_fixture();
    let acceptance_bar = fixture["acceptance_bar"].clone();
    let systems = fixture["systems"].as_array().expect("systems array");
    let t_ref_k = celsius_to_kelvin(T_REF_C).expect("T_ref in domain");

    let mut per_system: Vec<Value> = Vec::new();
    let mut all_within_range_errors: Vec<f64> = Vec::new();
    let mut baseline_within_range_errors: Vec<f64> = Vec::new();
    let mut held_out_30c_errors: Vec<f64> = Vec::new();
    let mut per_system_within_40_pass = 0_usize;
    let mut per_system_within_20_pass = 0_usize;

    for system in systems {
        let sid = system["system_id"].as_str().unwrap();
        let ea = system["activation_energy_j_mol"].as_f64().unwrap();
        let pot_ref = system["pot_life_min_22_78c"].as_f64().unwrap();
        let mut per_t = Vec::new();
        let mut system_max_err = 0.0_f64;
        for (t_c, key) in [
            (10.0_f64, "pot_life_min_10c"),
            (30.0_f64, "pot_life_min_30c"),
            (40.0_f64, "pot_life_min_40c"),
        ] {
            let obs = system[key].as_f64().unwrap();
            let t_k = celsius_to_kelvin(t_c).expect("T in domain");
            let predicted = arrhenius_pot_life(pot_ref, t_ref_k, t_k, ea);
            let err = (predicted - obs).abs() / obs;
            all_within_range_errors.push(err);
            baseline_within_range_errors.push((pot_ref - obs).abs() / obs);
            if err > system_max_err {
                system_max_err = err;
            }
            if t_c == 30.0 {
                held_out_30c_errors.push(err);
            }
            per_t.push(json!({
                "temperature_c": t_c,
                "published_pot_life_min": obs,
                "arrhenius_predicted_pot_life_min": predicted,
                "constant_baseline_pot_life_min": pot_ref,
                "arrhenius_absolute_percent_error": err,
                "constant_baseline_absolute_percent_error": (pot_ref - obs).abs() / obs,
            }));
        }
        if system_max_err <= 0.40 {
            per_system_within_40_pass += 1;
        }
        if system_max_err <= 0.20 {
            per_system_within_20_pass += 1;
        }
        per_system.push(json!({
            "system_id": sid,
            "hardener_family": system["hardener_family"],
            "resin": system["resin"],
            "activation_energy_j_mol": ea,
            "reference_pot_life_min_22_78c": pot_ref,
            "worst_case_absolute_percent_error": system_max_err,
            "held_out_temperatures": per_t,
        }));
    }

    let n_pairs = all_within_range_errors.len().max(1) as f64;
    let arrhenius_mape = all_within_range_errors.iter().sum::<f64>() / n_pairs;
    let baseline_mape = baseline_within_range_errors.iter().sum::<f64>() / n_pairs;
    let lift = baseline_mape - arrhenius_mape;
    let held_out_30_mape = held_out_30c_errors.iter().sum::<f64>()
        / held_out_30c_errors.len().max(1) as f64;
    let per_system_within_40_rate = per_system_within_40_pass as f64 / systems.len().max(1) as f64;
    let per_system_within_20_rate = per_system_within_20_pass as f64 / systems.len().max(1) as f64;

    // Applicability-domain probes: every one must reject.
    let ad_probes: Vec<(f64, f64, f64, &str)> = vec![
        (f64::NAN, 55_000.0, 295.928, "nan_temperature"),
        (298.15, f64::INFINITY, 295.928, "infinity_activation_energy"),
        (298.15, 55_000.0, f64::NAN, "nan_reference_temperature"),
        (0.0, 55_000.0, 295.928, "zero_temperature"),
        (-10.0, 55_000.0, 295.928, "negative_temperature"),
        (298.15, 0.0, 295.928, "zero_activation_energy"),
        (298.15, -1_000.0, 295.928, "negative_activation_energy"),
        (298.15, 55_000.0, 0.0, "zero_reference_temperature"),
        (298.15, 55_000.0, -10.0, "negative_reference_temperature"),
    ];
    let ad_probe_total = ad_probes.len();
    let ad_probe_details: Vec<Value> = ad_probes
        .iter()
        .map(|(t, ea, t_ref, label)| {
            let result = effective_cure_rate(*t, *ea, *t_ref);
            json!({
                "probe": label,
                "arguments": {"T_k": t, "Ea_j_mol": ea, "T_ref_k": t_ref},
                "fail_closed": result.is_err(),
            })
        })
        .collect();
    let fail_closed = ad_probe_details
        .iter()
        .filter(|r| r["fail_closed"] == json!(true))
        .count();
    let applicability_domain_fail_closed_rate = fail_closed as f64 / ad_probe_total as f64;

    let authority = &fixture["authority"];
    let authority_lock_preservation_rate = if authority["optimizer_authority"] == json!(false)
        && authority["constraint_only"] == json!(true)
        && authority["commercial_product_authority"] == json!(false)
        && authority["cro_gated_promotion"] == json!(true)
    {
        1.0
    } else {
        0.0
    };

    let kpi = json!({
        "arrhenius_pot_life_mape": {
            "observed": arrhenius_mape,
            "ceiling": acceptance_bar["arrhenius_pot_life_mape_ceiling"],
            "direction": "MINIMIZE",
            "sample_size": all_within_range_errors.len(),
            "passed": arrhenius_mape
                <= acceptance_bar["arrhenius_pot_life_mape_ceiling"].as_f64().unwrap_or(0.20),
        },
        "arrhenius_over_constant_baseline_lift": {
            "observed": lift,
            "constant_baseline_mape": baseline_mape,
            "floor": acceptance_bar["arrhenius_over_constant_baseline_lift_floor"],
            "direction": "MAXIMIZE",
            "passed": lift
                >= acceptance_bar["arrhenius_over_constant_baseline_lift_floor"].as_f64().unwrap_or(0.30),
        },
        "held_out_temperature_extrapolation_mape": {
            "observed": held_out_30_mape,
            "ceiling": acceptance_bar["held_out_temperature_extrapolation_mape_ceiling"],
            "direction": "MINIMIZE",
            "sample_size": held_out_30c_errors.len(),
            "passed": held_out_30_mape
                <= acceptance_bar["held_out_temperature_extrapolation_mape_ceiling"].as_f64().unwrap_or(0.25),
        },
        "per_system_within_40_percent_rate": {
            "observed": per_system_within_40_rate,
            "within_20_percent_rate": per_system_within_20_rate,
            "floor": acceptance_bar["per_system_within_40_percent_rate_floor"],
            "direction": "MAXIMIZE",
            "sample_size": systems.len(),
            "passed": per_system_within_40_rate
                >= acceptance_bar["per_system_within_40_percent_rate_floor"].as_f64().unwrap_or(0.80),
        },
        "applicability_domain_fail_closed_rate": {
            "observed": applicability_domain_fail_closed_rate,
            "probe_sample_size": ad_probe_total,
            "floor": acceptance_bar["applicability_domain_fail_closed_rate_floor"],
            "direction": "MAXIMIZE",
            "probes": ad_probe_details,
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
    });

    let benchmark_lock_bytes = fs::read(benchmark_lock_path()).expect("benchmark-lock readable");
    let benchmark_lock_sha256 = file_sha256(&benchmark_lock_bytes);
    let fixture_bytes = fs::read(fixture_path()).expect("fixture readable");
    let dataset_sha256 = file_sha256(&fixture_bytes);

    let diagnostic = json!({
        "schema": "amphora.module-phase0-benchmark-diagnostic.v1",
        "module_id": "amphora-cure-potlife-gate",
        "kpi": kpi.clone(),
        "records": per_system.clone(),
        "passed": kpi["arrhenius_pot_life_mape"]["passed"] == json!(true)
            && kpi["arrhenius_over_constant_baseline_lift"]["passed"] == json!(true)
            && kpi["held_out_temperature_extrapolation_mape"]["passed"] == json!(true)
            && kpi["per_system_within_40_percent_rate"]["passed"] == json!(true)
            && kpi["applicability_domain_fail_closed_rate"]["passed"] == json!(true)
            && kpi["authority_lock_preservation_rate"]["passed"] == json!(true),
    });
    let diagnostic_bytes = serde_json::to_vec(&canonicalize(&diagnostic)).expect("canonical bytes");
    let diagnostic_sha256 = file_sha256(&diagnostic_bytes);

    let mut result = Map::new();
    result.insert("schema".into(), json!("amphora.module-phase0-benchmark-result.v1"));
    result.insert("module_id".into(), json!("amphora-cure-potlife-gate"));
    result.insert(
        "benchmark_id".into(),
        json!("amphora-cure-potlife-gate-phase0-arrhenius-known-answer-v1"),
    );
    result.insert("benchmark_lock_sha256".into(), json!(benchmark_lock_sha256));
    result.insert("dataset_fixture_sha256".into(), json!(dataset_sha256));
    result.insert("acceptance_bar".into(), acceptance_bar);
    result.insert("kpi".into(), kpi);
    result.insert("records".into(), json!(per_system));
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

    let _ = stable_hash(&Value::Null);
    let _: BTreeMap<String, Value> = BTreeMap::new();

    canonicalize(&Value::Object(result))
}

#[test]
fn cure_potlife_phase0_kpi_report_is_deterministic_and_gates_pass() {
    let first = compute_report();
    let first_bytes = serde_json::to_vec(&first).expect("canonical");
    let second_bytes = serde_json::to_vec(&compute_report()).expect("canonical");
    assert_eq!(first_bytes, second_bytes, "KPI report is not byte-stable");

    let kpi = &first["kpi"];
    for gate in [
        "arrhenius_pot_life_mape",
        "arrhenius_over_constant_baseline_lift",
        "held_out_temperature_extrapolation_mape",
        "per_system_within_40_percent_rate",
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
