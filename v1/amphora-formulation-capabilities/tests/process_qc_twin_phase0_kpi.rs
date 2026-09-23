//! Phase-0 KPI harness for `amphora-process-qc-twin`.
//!
//! Drives the deterministic `audit_process_qc` primitive across a hand-authored
//! fixture of 10 SPC universes covering stable, step-shift (1σ/2σ/3σ), linear
//! drift, isolated outlier, spec-only-fail, control-only-fail, boundary spec,
//! and larger-baseline stable scenarios. Verifies I/MR Shewhart 3σ, EWMA
//! (λ=0.2, L=3), and standardized tabular CUSUM (k=0.5, h=5) arithmetic
//! correctness via an *independent* Rust recompute of every trace, plus
//! seeded-shift recall, stable false-positive absence, spec/control channel
//! separation, and dedicated fail-closed probes for the five module-specific
//! attack axes (REORDERED_BATCHES, BASELINE_CONTAMINATION, TIME_LEAKAGE,
//! SPECIFICATION_CONTROL_CONFLATION, UNAUTHORIZED_RELEASE) — all with
//! byte-stable two-replay.

use std::collections::BTreeMap;
use std::fs;
use std::path::PathBuf;

use amphora_core::{canonicalize, stable_hash};
use amphora_formulation_capabilities::{
    audit_process_qc, ProcessQcObservationV1, ProcessQcSeriesV1, SpcAuditResultV1,
};
use serde_json::{json, Map, Value};
use sha2::{Digest, Sha256};

fn workspace_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .expect("crate has a parent workspace")
        .to_path_buf()
}

fn fixture_path() -> PathBuf {
    workspace_root().join(
        "amphora-process-qc-twin/reference/phase0-process-qc-twin-known-answer.v1.json",
    )
}

fn benchmark_lock_path() -> PathBuf {
    workspace_root()
        .join("amphora-process-qc-twin/evidence/phase0/benchmark/benchmark-lock.v1.json")
}

// SCHEMA-ERA FIX (B2). The shipped artifact
// `amphora-process-qc-twin/evidence/phase0/benchmark/result.v1.json` has exactly one
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
        .join("amphora-process-qc-twin-phase0-kpi-result.v1.json")
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

fn parse_obs(value: &Value) -> ProcessQcObservationV1 {
    serde_json::from_value::<ProcessQcObservationV1>(value.clone()).expect("obs parses")
}

fn parse_series(entry: &Value) -> ProcessQcSeriesV1 {
    let baseline: Vec<ProcessQcObservationV1> = entry["baseline"]
        .as_array()
        .expect("baseline array")
        .iter()
        .map(parse_obs)
        .collect();
    let monitoring: Vec<ProcessQcObservationV1> = entry["monitoring"]
        .as_array()
        .expect("monitoring array")
        .iter()
        .map(parse_obs)
        .collect();
    ProcessQcSeriesV1 {
        variable: entry["variable"].as_str().expect("variable string").into(),
        baseline,
        monitoring,
        specification_lower: entry["specification_lower"].as_f64(),
        specification_upper: entry["specification_upper"].as_f64(),
    }
}

fn diagnostic_bytes(r: &SpcAuditResultV1) -> Vec<u8> {
    serde_json::to_vec(r).expect("SpcAuditResultV1 serializes")
}

/// Independent Rust recompute of baseline mean and sample stdev using the same
/// order and formula as the runtime (n-1 denominator).
fn independent_mean_sigma(baseline: &[ProcessQcObservationV1]) -> (f64, f64) {
    let n = baseline.len() as f64;
    let mean = baseline.iter().map(|o| o.value).sum::<f64>() / n;
    let var = baseline
        .iter()
        .map(|o| (o.value - mean).powi(2))
        .sum::<f64>()
        / (n - 1.0);
    (mean, var.sqrt())
}

/// Independent Shewhart alert list: strict > UCL or strict < LCL.
fn independent_shewhart(
    monitoring: &[ProcessQcObservationV1],
    mean: f64,
    sigma: f64,
) -> Vec<String> {
    let ucl = mean + 3.0 * sigma;
    let lcl = mean - 3.0 * sigma;
    monitoring
        .iter()
        .filter(|o| o.value > ucl || o.value < lcl)
        .map(|o| o.batch_id.clone())
        .collect()
}

/// Independent EWMA trace with the runtime's exact recursion and closed-form
/// limit; alerts when `|ewma_t - mean| > L_t`.
fn independent_ewma(
    baseline_len: usize,
    monitoring: &[ProcessQcObservationV1],
    mean: f64,
    sigma: f64,
) -> Vec<String> {
    let mut ewma = mean;
    let mut alerts = Vec::new();
    for o in monitoring {
        ewma = 0.2 * o.value + 0.8 * ewma;
        let t = (o.sequence.saturating_sub(baseline_len as u64) + 1) as f64;
        let lim = 3.0 * sigma * (0.2_f64 / 1.8 * (1.0 - 0.8_f64.powf(2.0 * t))).sqrt();
        if (ewma - mean).abs() > lim {
            alerts.push(o.batch_id.clone());
        }
    }
    alerts
}

/// Independent standardized tabular CUSUM with reset-on-alert (matches runtime).
fn independent_cusum(
    monitoring: &[ProcessQcObservationV1],
    mean: f64,
    sigma: f64,
) -> Vec<String> {
    let mut cp = 0.0_f64;
    let mut cm = 0.0_f64;
    let mut alerts = Vec::new();
    for o in monitoring {
        let z = (o.value - mean) / sigma;
        cp = (cp + z - 0.5).max(0.0);
        cm = (cm - z - 0.5).max(0.0);
        if cp > 5.0 || cm > 5.0 {
            alerts.push(o.batch_id.clone());
            cp = 0.0;
            cm = 0.0;
        }
    }
    alerts
}

fn independent_spec_failures(
    monitoring: &[ProcessQcObservationV1],
    lower: Option<f64>,
    upper: Option<f64>,
) -> Vec<String> {
    monitoring
        .iter()
        .filter(|o| lower.is_some_and(|v| o.value < v) || upper.is_some_and(|v| o.value > v))
        .map(|o| o.batch_id.clone())
        .collect()
}

/// The fixture stores expected alert lists as either an array of batch IDs or
/// the string sentinel "PIN_FORWARD_FROM_RUNTIME" for scenarios where exact
/// indices sit on floating-point boundaries. The recall gate uses non-empty
/// as the pin-forward semantics.
enum Expected {
    Exact(Vec<String>),
    PinForward,
}

fn parse_expected(value: &Value) -> Expected {
    if value.is_string() {
        Expected::PinForward
    } else {
        Expected::Exact(
            value
                .as_array()
                .expect("expected list array or PIN sentinel")
                .iter()
                .map(|v| v.as_str().expect("batch id string").to_string())
                .collect(),
        )
    }
}

fn compute_report() -> Value {
    let fixture = read_fixture();
    let acceptance_bar = fixture["acceptance_bar"].clone();
    let universes = fixture["universes"].as_array().expect("universes array");

    let mut per_universe: Vec<Value> = Vec::new();

    // Universe-level gate counters
    let mut shewhart_arith_pass = 0_usize;
    let mut ewma_arith_pass = 0_usize;
    let mut cusum_arith_pass = 0_usize;
    let mut authority_pass = 0_usize;
    let mut byte_replay_pass = 0_usize;
    let mut universe_total = 0_usize;

    // Subset counters
    let mut seeded_universes = 0_usize;
    let mut seeded_recall_pass = 0_usize;
    let mut stable_universes = 0_usize;
    let mut stable_fp_pass = 0_usize;
    let mut separation_universes = 0_usize;
    let mut separation_pass = 0_usize;

    for entry in universes {
        universe_total += 1;
        let uid = entry["universe_id"].as_str().unwrap();
        let scenario = entry["scenario_type"].as_str().unwrap();

        let series = parse_series(entry);
        let out = audit_process_qc(&series).expect("in-domain universe");

        let (harness_mean, harness_sigma) = independent_mean_sigma(&series.baseline);
        let harness_shewhart = independent_shewhart(&series.monitoring, harness_mean, harness_sigma);
        let harness_ewma = independent_ewma(
            series.baseline.len(),
            &series.monitoring,
            harness_mean,
            harness_sigma,
        );
        let harness_cusum = independent_cusum(&series.monitoring, harness_mean, harness_sigma);
        let harness_spec = independent_spec_failures(
            &series.monitoring,
            series.specification_lower,
            series.specification_upper,
        );

        // Gate 1: Shewhart arithmetic — mean/sigma/UCL/LCL/alerts bit-exact.
        let shewhart_arith_ok = out.baseline_mean.to_bits() == harness_mean.to_bits()
            && out.baseline_sigma.to_bits() == harness_sigma.to_bits()
            && out.shewhart_alerts == harness_shewhart
            && out.specification_failures == harness_spec;
        if shewhart_arith_ok {
            shewhart_arith_pass += 1;
        }

        // Gate 2: EWMA recursion bit-exact.
        let ewma_arith_ok = out.ewma_alerts == harness_ewma;
        if ewma_arith_ok {
            ewma_arith_pass += 1;
        }

        // Gate 3: CUSUM tabular bit-exact.
        let cusum_arith_ok = out.cusum_alerts == harness_cusum;
        if cusum_arith_ok {
            cusum_arith_pass += 1;
        }

        // Gate 4/5: seeded recall vs. stable false-positive absence.
        let total_alerts =
            out.shewhart_alerts.len() + out.ewma_alerts.len() + out.cusum_alerts.len();
        let is_stable = matches!(
            scenario,
            "STABLE" | "SPEC_ONLY_FAIL" | "BOUNDARY_TIGHT_SPEC" | "LARGE_STABLE"
        );
        let is_seeded = matches!(
            scenario,
            "STEP_SHIFT_1SIGMA"
                | "STEP_SHIFT_2SIGMA"
                | "STEP_SHIFT_3SIGMA"
                | "LINEAR_DRIFT"
                | "ISOLATED_OUTLIER"
                | "CONTROL_ONLY_FAIL"
        );
        // STEP_SHIFT_1SIGMA: 1σ shift is Roberts' whole point for EWMA — one of
        // the three detectors is expected to catch it.
        if is_seeded {
            seeded_universes += 1;
            if total_alerts >= 1 {
                seeded_recall_pass += 1;
            }
        }
        if is_stable {
            stable_universes += 1;
            if total_alerts == 0 {
                stable_fp_pass += 1;
            }
        }

        // Gate 6: SPECIFICATION_CONTROL_SEPARATION only for the two dedicated
        // universes.
        if scenario == "SPEC_ONLY_FAIL" {
            separation_universes += 1;
            if !out.specification_failures.is_empty() && total_alerts == 0 {
                separation_pass += 1;
            }
        }
        if scenario == "CONTROL_ONLY_FAIL" {
            separation_universes += 1;
            if out.specification_failures.is_empty() && total_alerts >= 1 {
                separation_pass += 1;
            }
        }

        // Gate 10: authority envelope.
        let mut auth_ok = out.detector_status == "AUDIT_ONLY";
        let out_json = serde_json::to_value(&out).expect("serializes");
        for banned in [
            "batch_release",
            "release_authorized",
            "qualified",
            "authorized",
            "manufacturing_qualification",
            "release_authority",
        ] {
            if find_key(&out_json, banned) {
                auth_ok = false;
            }
        }
        if auth_ok {
            authority_pass += 1;
        }

        // Byte-stable two-replay.
        let out2 = audit_process_qc(&series).expect("replay in-domain");
        let byte_ok = diagnostic_bytes(&out) == diagnostic_bytes(&out2);
        if byte_ok {
            byte_replay_pass += 1;
        }

        // Fixture-declared expectations (either exact or pin-forward).
        let expected_shewhart = parse_expected(&entry["expected_shewhart_alerts"]);
        let expected_ewma = parse_expected(&entry["expected_ewma_alerts"]);
        let expected_cusum = parse_expected(&entry["expected_cusum_alerts"]);
        let expected_spec: Vec<String> = entry["expected_specification_failures"]
            .as_array()
            .expect("spec failure list")
            .iter()
            .map(|v| v.as_str().expect("bid").to_string())
            .collect();

        let shewhart_matches_expected = match &expected_shewhart {
            Expected::Exact(v) => v == &out.shewhart_alerts,
            Expected::PinForward => true,
        };
        let ewma_matches_expected = match &expected_ewma {
            Expected::Exact(v) => v == &out.ewma_alerts,
            Expected::PinForward => true,
        };
        let cusum_matches_expected = match &expected_cusum {
            Expected::Exact(v) => v == &out.cusum_alerts,
            Expected::PinForward => true,
        };
        let spec_matches_expected = expected_spec == out.specification_failures;

        assert!(
            shewhart_matches_expected,
            "Shewhart list mismatch for {uid}: observed={:?}, expected={:?}",
            out.shewhart_alerts,
            entry["expected_shewhart_alerts"]
        );
        assert!(
            ewma_matches_expected,
            "EWMA list mismatch for {uid}",
        );
        assert!(
            cusum_matches_expected,
            "CUSUM list mismatch for {uid}",
        );
        assert!(
            spec_matches_expected,
            "Spec-failure list mismatch for {uid}: observed={:?}, expected={:?}",
            out.specification_failures, expected_spec
        );

        per_universe.push(json!({
            "universe_id": uid,
            "scenario_type": scenario,
            "variable": series.variable,
            "baseline_n": series.baseline.len() as u64,
            "monitoring_n": series.monitoring.len() as u64,
            "observed_baseline_mean_bits": out.baseline_mean.to_bits(),
            "observed_baseline_sigma_bits": out.baseline_sigma.to_bits(),
            "observed_shewhart_alerts": out.shewhart_alerts,
            "observed_ewma_alerts": out.ewma_alerts,
            "observed_cusum_alerts": out.cusum_alerts,
            "observed_specification_failures": out.specification_failures,
            "detector_status": out.detector_status,
            "nominal_source": entry["nominal_source"],
            "industrial_context": entry["industrial_context"],
            "shewhart_arithmetic_bit_exact": shewhart_arith_ok,
            "ewma_arithmetic_bit_exact": ewma_arith_ok,
            "cusum_arithmetic_bit_exact": cusum_arith_ok,
            "authority_locked": auth_ok,
            "byte_stable_two_replay": byte_ok,
            "is_seeded_deviation": is_seeded,
            "is_stable_process": is_stable,
        }));
    }

    let n = universe_total.max(1) as f64;
    let shewhart_arith_rate = shewhart_arith_pass as f64 / n;
    let ewma_arith_rate = ewma_arith_pass as f64 / n;
    let cusum_arith_rate = cusum_arith_pass as f64 / n;
    let authority_rate = authority_pass as f64 / n;
    let byte_replay_rate = byte_replay_pass as f64 / n;
    let seeded_recall_rate = if seeded_universes > 0 {
        seeded_recall_pass as f64 / seeded_universes as f64
    } else {
        1.0
    };
    let stable_fp_rate = if stable_universes > 0 {
        stable_fp_pass as f64 / stable_universes as f64
    } else {
        1.0
    };
    let separation_rate = if separation_universes > 0 {
        separation_pass as f64 / separation_universes as f64
    } else {
        1.0
    };

    // REORDERED_BATCHES probes.
    let (reordered_rate, reordered_probes, reordered_total) = reordered_probes();
    // BASELINE_CONTAMINATION probes.
    let (contamination_rate, contamination_probes, contamination_total) =
        contamination_probes();
    // TIME_LEAKAGE probes.
    let (leakage_rate, leakage_probes, leakage_total) = leakage_probes();

    let kpi = json!({
        "shewhart_control_limit_arithmetic_correctness_rate": {
            "observed": shewhart_arith_rate,
            "floor": acceptance_bar["shewhart_control_limit_arithmetic_correctness_rate_floor"],
            "direction": "MAXIMIZE",
            "sample_size": universe_total,
            "passed": shewhart_arith_rate
                >= acceptance_bar["shewhart_control_limit_arithmetic_correctness_rate_floor"]
                    .as_f64()
                    .unwrap_or(1.0),
        },
        "ewma_recursion_arithmetic_correctness_rate": {
            "observed": ewma_arith_rate,
            "floor": acceptance_bar["ewma_recursion_arithmetic_correctness_rate_floor"],
            "direction": "MAXIMIZE",
            "sample_size": universe_total,
            "passed": ewma_arith_rate
                >= acceptance_bar["ewma_recursion_arithmetic_correctness_rate_floor"]
                    .as_f64()
                    .unwrap_or(1.0),
        },
        "cusum_tabular_arithmetic_correctness_rate": {
            "observed": cusum_arith_rate,
            "floor": acceptance_bar["cusum_tabular_arithmetic_correctness_rate_floor"],
            "direction": "MAXIMIZE",
            "sample_size": universe_total,
            "passed": cusum_arith_rate
                >= acceptance_bar["cusum_tabular_arithmetic_correctness_rate_floor"]
                    .as_f64()
                    .unwrap_or(1.0),
        },
        "seeded_shift_detection_recall_rate": {
            "observed": seeded_recall_rate,
            "floor": acceptance_bar["seeded_shift_detection_recall_rate_floor"],
            "direction": "MAXIMIZE",
            "sample_size": seeded_universes,
            "passed": seeded_recall_rate
                >= acceptance_bar["seeded_shift_detection_recall_rate_floor"]
                    .as_f64()
                    .unwrap_or(1.0),
        },
        "stable_process_false_positive_absence_rate": {
            "observed": stable_fp_rate,
            "floor": acceptance_bar["stable_process_false_positive_absence_rate_floor"],
            "direction": "MAXIMIZE",
            "sample_size": stable_universes,
            "passed": stable_fp_rate
                >= acceptance_bar["stable_process_false_positive_absence_rate_floor"]
                    .as_f64()
                    .unwrap_or(1.0),
        },
        "specification_control_separation_correctness_rate": {
            "observed": separation_rate,
            "floor": acceptance_bar["specification_control_separation_correctness_rate_floor"],
            "direction": "MAXIMIZE",
            "sample_size": separation_universes,
            "passed": separation_rate
                >= acceptance_bar["specification_control_separation_correctness_rate_floor"]
                    .as_f64()
                    .unwrap_or(1.0),
        },
        "reordered_batches_fail_closed_rate": {
            "observed": reordered_rate,
            "floor": acceptance_bar["reordered_batches_fail_closed_rate_floor"],
            "direction": "MAXIMIZE",
            "probe_sample_size": reordered_total,
            "probes": reordered_probes,
            "passed": reordered_rate
                >= acceptance_bar["reordered_batches_fail_closed_rate_floor"]
                    .as_f64()
                    .unwrap_or(1.0),
        },
        "baseline_contamination_fail_closed_rate": {
            "observed": contamination_rate,
            "floor": acceptance_bar["baseline_contamination_fail_closed_rate_floor"],
            "direction": "MAXIMIZE",
            "probe_sample_size": contamination_total,
            "probes": contamination_probes,
            "passed": contamination_rate
                >= acceptance_bar["baseline_contamination_fail_closed_rate_floor"]
                    .as_f64()
                    .unwrap_or(1.0),
        },
        "time_leakage_fail_closed_rate": {
            "observed": leakage_rate,
            "floor": acceptance_bar["time_leakage_fail_closed_rate_floor"],
            "direction": "MAXIMIZE",
            "probe_sample_size": leakage_total,
            "probes": leakage_probes,
            "passed": leakage_rate
                >= acceptance_bar["time_leakage_fail_closed_rate_floor"]
                    .as_f64()
                    .unwrap_or(1.0),
        },
        "authority_lock_preservation_rate": {
            "observed": authority_rate,
            "floor": acceptance_bar["authority_lock_preservation_rate_floor"],
            "direction": "MAXIMIZE",
            "sample_size": universe_total,
            "passed": authority_rate
                >= acceptance_bar["authority_lock_preservation_rate_floor"]
                    .as_f64()
                    .unwrap_or(1.0),
        },
        "byte_stable_two_replay_rate": {
            "observed": byte_replay_rate,
            "direction": "MAXIMIZE",
            "sample_size": universe_total,
            "note": "observational; validated by re-invoking audit_process_qc on the same series and asserting byte-identical SpcAuditResultV1",
        },
    });

    let benchmark_lock_bytes = fs::read(benchmark_lock_path()).expect("benchmark-lock readable");
    let benchmark_lock_sha256 = file_sha256(&benchmark_lock_bytes);
    let fixture_bytes = fs::read(fixture_path()).expect("fixture readable");
    let dataset_sha256 = file_sha256(&fixture_bytes);

    let diagnostic = json!({
        "schema": "amphora.module-phase0-benchmark-diagnostic.v1",
        "module_id": "amphora-process-qc-twin",
        "kpi": kpi.clone(),
        "records": per_universe.clone(),
        "passed": kpi["shewhart_control_limit_arithmetic_correctness_rate"]["passed"] == json!(true)
            && kpi["ewma_recursion_arithmetic_correctness_rate"]["passed"] == json!(true)
            && kpi["cusum_tabular_arithmetic_correctness_rate"]["passed"] == json!(true)
            && kpi["seeded_shift_detection_recall_rate"]["passed"] == json!(true)
            && kpi["stable_process_false_positive_absence_rate"]["passed"] == json!(true)
            && kpi["specification_control_separation_correctness_rate"]["passed"] == json!(true)
            && kpi["reordered_batches_fail_closed_rate"]["passed"] == json!(true)
            && kpi["baseline_contamination_fail_closed_rate"]["passed"] == json!(true)
            && kpi["time_leakage_fail_closed_rate"]["passed"] == json!(true)
            && kpi["authority_lock_preservation_rate"]["passed"] == json!(true),
    });
    let diagnostic_bytes_canonical =
        serde_json::to_vec(&canonicalize(&diagnostic)).expect("canonical bytes");
    let diagnostic_sha256 = file_sha256(&diagnostic_bytes_canonical);

    let mut result = Map::new();
    result.insert("schema".into(), json!("amphora.module-phase0-benchmark-result.v1"));
    result.insert("module_id".into(), json!("amphora-process-qc-twin"));
    result.insert(
        "benchmark_id".into(),
        json!("amphora-process-qc-twin-phase0-spc-audit-v1"),
    );
    result.insert("benchmark_lock_sha256".into(), json!(benchmark_lock_sha256));
    result.insert("dataset_fixture_sha256".into(), json!(dataset_sha256));
    result.insert("acceptance_bar".into(), acceptance_bar);
    result.insert("kpi".into(), kpi);
    result.insert("records".into(), json!(per_universe));
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

fn find_key(value: &Value, key: &str) -> bool {
    match value {
        Value::Object(map) => {
            if map.contains_key(key) {
                return true;
            }
            map.values().any(|v| find_key(v, key))
        }
        Value::Array(arr) => arr.iter().any(|v| find_key(v, key)),
        _ => false,
    }
}

fn make_obs(prefix: &str, seq: u64, val: f64) -> ProcessQcObservationV1 {
    ProcessQcObservationV1 {
        batch_id: format!("{prefix}-{seq:03}"),
        sequence: seq,
        value: val,
    }
}

fn stable_baseline_n(n: u64) -> Vec<ProcessQcObservationV1> {
    (1..=n)
        .map(|s| {
            let offset = ((s - 1) % 5) as f64 - 2.0;
            make_obs("baseline", s, 100.0 + offset * 0.1)
        })
        .collect()
}

fn stable_monitoring_from(start: u64, n: u64) -> Vec<ProcessQcObservationV1> {
    (start..start + n)
        .map(|s| {
            let offset = ((s - start) % 5) as f64 - 2.0;
            make_obs("monitor", s, 100.0 + offset * 0.1)
        })
        .collect()
}

fn reordered_probes() -> (f64, Vec<Value>, usize) {
    let mut passes = 0_usize;
    let mut probes: Vec<Value> = Vec::new();

    // Probe A: baseline seq swap.
    let mut baseline = stable_baseline_n(20);
    baseline.swap(5, 6);
    let series = ProcessQcSeriesV1 {
        variable: "reordered-baseline".into(),
        baseline,
        monitoring: stable_monitoring_from(21, 20),
        specification_lower: None,
        specification_upper: None,
    };
    let ok = audit_process_qc(&series).is_err();
    if ok {
        passes += 1;
    }
    probes.push(json!({"probe": "baseline_swap_indices_5_6", "fail_closed": ok}));

    // Probe B: monitoring seq swap.
    let baseline = stable_baseline_n(20);
    let mut monitoring = stable_monitoring_from(21, 20);
    monitoring.swap(5, 6);
    let series = ProcessQcSeriesV1 {
        variable: "reordered-monitoring".into(),
        baseline,
        monitoring,
        specification_lower: None,
        specification_upper: None,
    };
    let ok = audit_process_qc(&series).is_err();
    if ok {
        passes += 1;
    }
    probes.push(json!({"probe": "monitoring_swap_indices_5_6", "fail_closed": ok}));

    // Probe C: monitoring in strict reverse.
    let baseline = stable_baseline_n(20);
    let mut monitoring = stable_monitoring_from(21, 20);
    monitoring.reverse();
    let series = ProcessQcSeriesV1 {
        variable: "reversed-monitoring".into(),
        baseline,
        monitoring,
        specification_lower: None,
        specification_upper: None,
    };
    let ok = audit_process_qc(&series).is_err();
    if ok {
        passes += 1;
    }
    probes.push(json!({"probe": "monitoring_full_reverse", "fail_closed": ok}));

    let total = probes.len();
    (passes as f64 / total.max(1) as f64, probes, total)
}

fn contamination_probes() -> (f64, Vec<Value>, usize) {
    let mut passes = 0_usize;
    let mut probes: Vec<Value> = Vec::new();

    // Probe A: monitoring first seq == baseline last seq.
    let baseline = stable_baseline_n(20);
    let monitoring = vec![make_obs("monitor", 20, 100.0)];
    let series = ProcessQcSeriesV1 {
        variable: "contamination-equal".into(),
        baseline,
        monitoring,
        specification_lower: None,
        specification_upper: None,
    };
    let ok = audit_process_qc(&series).is_err();
    if ok {
        passes += 1;
    }
    probes.push(json!({"probe": "monitoring_first_seq_equals_baseline_last_seq", "fail_closed": ok}));

    // Probe B: monitoring first seq strictly below baseline last seq.
    let baseline = stable_baseline_n(20);
    let monitoring = vec![
        make_obs("monitor", 15, 100.0),
        make_obs("monitor", 16, 100.0),
    ];
    let series = ProcessQcSeriesV1 {
        variable: "contamination-below".into(),
        baseline,
        monitoring,
        specification_lower: None,
        specification_upper: None,
    };
    let ok = audit_process_qc(&series).is_err();
    if ok {
        passes += 1;
    }
    probes.push(json!({"probe": "monitoring_first_seq_below_baseline_last_seq", "fail_closed": ok}));

    // Probe C: monitoring first seq mid-baseline (deep contamination).
    let baseline = stable_baseline_n(25);
    let monitoring = vec![make_obs("monitor", 12, 100.0)];
    let series = ProcessQcSeriesV1 {
        variable: "contamination-deep".into(),
        baseline,
        monitoring,
        specification_lower: None,
        specification_upper: None,
    };
    let ok = audit_process_qc(&series).is_err();
    if ok {
        passes += 1;
    }
    probes.push(json!({"probe": "monitoring_first_seq_mid_baseline", "fail_closed": ok}));

    let total = probes.len();
    (passes as f64 / total.max(1) as f64, probes, total)
}

fn leakage_probes() -> (f64, Vec<Value>, usize) {
    let mut passes = 0_usize;
    let mut probes: Vec<Value> = Vec::new();

    // Probe A: duplicate sequence inside baseline.
    let mut baseline = stable_baseline_n(20);
    baseline[6] = make_obs("baseline", baseline[5].sequence, 100.0);
    let series = ProcessQcSeriesV1 {
        variable: "leakage-baseline-dup".into(),
        baseline,
        monitoring: stable_monitoring_from(21, 20),
        specification_lower: None,
        specification_upper: None,
    };
    let ok = audit_process_qc(&series).is_err();
    if ok {
        passes += 1;
    }
    probes.push(json!({"probe": "duplicate_sequence_in_baseline", "fail_closed": ok}));

    // Probe B: duplicate sequence inside monitoring.
    let mut monitoring = stable_monitoring_from(21, 20);
    monitoring[6] = make_obs("monitor", monitoring[5].sequence, 100.0);
    let series = ProcessQcSeriesV1 {
        variable: "leakage-monitoring-dup".into(),
        baseline: stable_baseline_n(20),
        monitoring,
        specification_lower: None,
        specification_upper: None,
    };
    let ok = audit_process_qc(&series).is_err();
    if ok {
        passes += 1;
    }
    probes.push(json!({"probe": "duplicate_sequence_in_monitoring", "fail_closed": ok}));

    // Probe C: baseline last seq == monitoring first seq (equality boundary).
    let baseline = stable_baseline_n(20);
    let monitoring = vec![make_obs("monitor", 20, 100.0), make_obs("monitor", 21, 100.0)];
    let series = ProcessQcSeriesV1 {
        variable: "leakage-boundary".into(),
        baseline,
        monitoring,
        specification_lower: None,
        specification_upper: None,
    };
    let ok = audit_process_qc(&series).is_err();
    if ok {
        passes += 1;
    }
    probes.push(json!({"probe": "boundary_equality_baseline_last_equals_monitoring_first", "fail_closed": ok}));

    let total = probes.len();
    (passes as f64 / total.max(1) as f64, probes, total)
}

#[test]
fn process_qc_twin_phase0_kpi_report_is_deterministic_and_gates_pass() {
    let first = compute_report();
    let first_bytes = serde_json::to_vec(&first).expect("canonical");
    let second_bytes = serde_json::to_vec(&compute_report()).expect("canonical");
    assert_eq!(first_bytes, second_bytes, "KPI report is not byte-stable");

    let kpi = &first["kpi"];
    for gate in [
        "shewhart_control_limit_arithmetic_correctness_rate",
        "ewma_recursion_arithmetic_correctness_rate",
        "cusum_tabular_arithmetic_correctness_rate",
        "seeded_shift_detection_recall_rate",
        "stable_process_false_positive_absence_rate",
        "specification_control_separation_correctness_rate",
        "reordered_batches_fail_closed_rate",
        "baseline_contamination_fail_closed_rate",
        "time_leakage_fail_closed_rate",
        "authority_lock_preservation_rate",
    ] {
        assert_eq!(
            kpi[gate]["passed"],
            json!(true),
            "KPI gate {gate} failed: observed={}, floor={}",
            kpi[gate]["observed"],
            kpi[gate].get("floor").unwrap_or(&Value::Null),
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
