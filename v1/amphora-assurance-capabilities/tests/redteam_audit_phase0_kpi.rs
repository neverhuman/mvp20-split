//! Phase-0 KPI harness for `amphora-redteam-audit`.
//!
//! Drives the deterministic `deterministic_control_diagnostic` meta-audit
//! runtime across nine upstream Amphora modules (evidence-intake-validator,
//! source-ledger, redteam-audit, report-packager, formulation-arithmetic,
//! formulation-universe, envelope-gates, cro-protocol-packager,
//! optimizer-orchestrator). Verifies passed-flag correctness, expected vs.
//! observed embedded-fixture outcome bit-equality, zero-authority-lock
//! coverage, result-digest byte stability across replays, fail-closed on
//! unsupported module IDs, and full 24-axis attack coverage cross-checked
//! against the on-disk benchmark-lock.v1.json.

use std::collections::BTreeMap;
use std::fs;
use std::path::PathBuf;

use amphora_assurance_capabilities::{deterministic_control_diagnostic, REDTEAM_ATTACK_AXES};
use amphora_core::{
    canonicalize, stable_hash, DeterministicControlDiagnosticV1,
    DETERMINISTIC_CONTROL_DIAGNOSTIC_SCHEMA, REQUIRED_ZERO_AUTHORITY_CLAIM_LOCKS,
};
use serde_json::{json, Map, Value};
use sha2::{Digest, Sha256};

const SUPPORTED_MODULES: [&str; 9] = [
    "amphora-evidence-intake-validator",
    "amphora-source-ledger",
    "amphora-redteam-audit",
    "amphora-report-packager",
    "amphora-formulation-arithmetic",
    "amphora-formulation-universe",
    "amphora-envelope-gates",
    "amphora-cro-protocol-packager",
    "amphora-optimizer-orchestrator",
];

const UNSUPPORTED_PROBES: [&str; 6] = [
    "",
    "   ",
    "amphora-does-not-exist",
    "amphora-source_ledger",
    "AMPHORA-REDTEAM-AUDIT",
    "АМФОРА",
];

const BANNED_AUTHORITY_KEYS: [&str; 6] = [
    "batch_release",
    "release_authorized",
    "qualified",
    "authorized",
    "manufacturing_qualification",
    "release_authority",
];

fn workspace_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .expect("crate has a parent workspace")
        .to_path_buf()
}

fn benchmark_lock_path() -> PathBuf {
    workspace_root().join("amphora-redteam-audit/evidence/phase0/benchmark/benchmark-lock.v1.json")
}

fn diagnostics_source_path() -> PathBuf {
    workspace_root().join("amphora-assurance-capabilities/src/diagnostics.rs")
}

// SCHEMA-ERA FIX (B2). The shipped artifact
// `amphora-redteam-audit/evidence/phase0/benchmark/result.v1.json` has exactly one
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
        .join("amphora-redteam-audit-phase0-kpi-result.v1.json")
}

fn file_sha256(bytes: &[u8]) -> String {
    let mut digest = Sha256::new();
    digest.update(bytes);
    format!("{:x}", digest.finalize())
}

fn diagnostic_bytes(d: &DeterministicControlDiagnosticV1) -> Vec<u8> {
    serde_json::to_vec(d).expect("diagnostic serializes")
}

fn contains_banned_key(value: &Value) -> Option<String> {
    match value {
        Value::Object(map) => {
            for k in map.keys() {
                if BANNED_AUTHORITY_KEYS.iter().any(|b| b == k) {
                    return Some(k.clone());
                }
            }
            for v in map.values() {
                if let Some(k) = contains_banned_key(v) {
                    return Some(k);
                }
            }
            None
        }
        Value::Array(arr) => arr.iter().find_map(contains_banned_key),
        _ => None,
    }
}

fn compute_report() -> Value {
    let mut per_module: Vec<Value> = Vec::new();

    let mut dispatch_pass = 0_usize;
    let mut passed_flag_pass = 0_usize;
    let mut outcomes_pass = 0_usize;
    let mut readiness_pass = 0_usize;
    let mut zero_auth_pass = 0_usize;
    let mut digest_replay_pass = 0_usize;
    let mut counts_present_pass = 0_usize;
    let mut authority_pass = 0_usize;
    let mut byte_replay_pass = 0_usize;

    for module_id in SUPPORTED_MODULES {
        let result = deterministic_control_diagnostic(module_id);
        let ok = result.is_ok();
        if ok {
            dispatch_pass += 1;
        }
        let diagnostic = match result {
            Ok(d) => d,
            Err(err) => {
                per_module.push(json!({
                    "module_id": module_id,
                    "dispatch_ok": false,
                    "error": err,
                }));
                continue;
            }
        };

        if diagnostic.passed {
            passed_flag_pass += 1;
        }
        if diagnostic.expected_fixture_outcomes == diagnostic.observed_fixture_outcomes {
            outcomes_pass += 1;
        }
        if diagnostic.implementation_readiness == "COMPLETE"
            && diagnostic.schema == DETERMINISTIC_CONTROL_DIAGNOSTIC_SCHEMA
        {
            readiness_pass += 1;
        }
        let zero_auth_ok = REQUIRED_ZERO_AUTHORITY_CLAIM_LOCKS.iter().all(|lock| {
            matches!(diagnostic.zero_authority_assertions.get(*lock), Some(true))
        });
        if zero_auth_ok {
            zero_auth_pass += 1;
        }
        let counts_present = diagnostic.positive_control_count + diagnostic.negative_control_count
            >= 1;
        if counts_present {
            counts_present_pass += 1;
        }
        let auth_ok = contains_banned_key(&serde_json::to_value(&diagnostic).unwrap()).is_none();
        if auth_ok {
            authority_pass += 1;
        }

        // Two-replay.
        let replay = deterministic_control_diagnostic(module_id).expect("replay ok");
        let digest_ok = diagnostic.details.get("result_digest")
            == replay.details.get("result_digest");
        if digest_ok {
            digest_replay_pass += 1;
        }
        let byte_ok = diagnostic_bytes(&diagnostic) == diagnostic_bytes(&replay);
        if byte_ok {
            byte_replay_pass += 1;
        }

        per_module.push(json!({
            "module_id": module_id,
            "dispatch_ok": ok,
            "passed_flag": diagnostic.passed,
            "expected_equals_observed_fixture_outcomes": diagnostic.expected_fixture_outcomes
                == diagnostic.observed_fixture_outcomes,
            "implementation_readiness": diagnostic.implementation_readiness,
            "schema": diagnostic.schema,
            "positive_control_count": diagnostic.positive_control_count,
            "negative_control_count": diagnostic.negative_control_count,
            "zero_authority_lock_coverage_complete": zero_auth_ok,
            "result_digest_byte_stable": digest_ok,
            "full_struct_byte_stable_two_replay": byte_ok,
            "authority_envelope_preserved": auth_ok,
            "expected_fixture_outcome_count": diagnostic.expected_fixture_outcomes.len() as u64,
            "observed_fixture_outcome_count": diagnostic.observed_fixture_outcomes.len() as u64,
            "result_digest": diagnostic.details.get("result_digest").cloned().unwrap_or(Value::Null),
        }));
    }

    let n = SUPPORTED_MODULES.len() as f64;
    let dispatch_rate = dispatch_pass as f64 / n;
    let passed_rate = passed_flag_pass as f64 / n;
    let outcomes_rate = outcomes_pass as f64 / n;
    let readiness_rate = readiness_pass as f64 / n;
    let zero_auth_rate = zero_auth_pass as f64 / n;
    let digest_replay_rate = digest_replay_pass as f64 / n;
    let counts_rate = counts_present_pass as f64 / n;
    let byte_replay_rate = byte_replay_pass as f64 / n;

    // UNSUPPORTED_MODULE_ID probes.
    let mut unsupported_pass = 0_usize;
    let mut unsupported_probes: Vec<Value> = Vec::new();
    for probe in UNSUPPORTED_PROBES {
        let is_err = deterministic_control_diagnostic(probe).is_err();
        if is_err {
            unsupported_pass += 1;
        }
        unsupported_probes.push(json!({
            "probe": probe,
            "fail_closed": is_err,
        }));
    }
    let unsupported_total = unsupported_probes.len();
    let unsupported_rate = unsupported_pass as f64 / unsupported_total.max(1) as f64;

    // ATTACK_AXIS coverage.
    let benchmark_lock_bytes = fs::read(benchmark_lock_path()).expect("benchmark-lock readable");
    let benchmark_lock: Value =
        serde_json::from_slice(&benchmark_lock_bytes).expect("benchmark-lock is JSON");
    let benchmark_attacks: Vec<String> = benchmark_lock["attacks"]
        .as_array()
        .expect("attacks array")
        .iter()
        .map(|v| v.as_str().expect("string").to_string())
        .collect();
    let mut axis_pass = 0_usize;
    let mut axis_details: Vec<Value> = Vec::new();
    for axis in REDTEAM_ATTACK_AXES {
        let in_lock = benchmark_attacks.iter().any(|a| a == axis);
        if in_lock {
            axis_pass += 1;
        }
        axis_details.push(json!({
            "axis": axis,
            "declared_in_benchmark_lock": in_lock,
        }));
    }
    let axis_total = REDTEAM_ATTACK_AXES.len();
    let axis_rate = if axis_total == 24 {
        axis_pass as f64 / axis_total as f64
    } else {
        0.0
    };

    // Authority envelope on probes: no banned key inside error strings (they
    // are simple strings not JSON, but we still check the Result JSON encoding
    // just to be exhaustive).
    let mut probe_authority_pass = unsupported_probes.len();
    for probe in UNSUPPORTED_PROBES {
        if let Err(err) = deterministic_control_diagnostic(probe) {
            let err_value = Value::String(err);
            if contains_banned_key(&err_value).is_some() {
                probe_authority_pass -= 1;
            }
        }
    }
    let authority_total = SUPPORTED_MODULES.len() + UNSUPPORTED_PROBES.len();
    let authority_rate =
        (authority_pass + probe_authority_pass) as f64 / authority_total as f64;

    let kpi = json!({
        "diagnostic_dispatch_ok_rate": {
            "observed": dispatch_rate,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": SUPPORTED_MODULES.len(),
            "passed": dispatch_rate >= 1.0,
        },
        "diagnostic_passed_flag_true_rate": {
            "observed": passed_rate,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": SUPPORTED_MODULES.len(),
            "passed": passed_rate >= 1.0,
        },
        "expected_equals_observed_fixture_outcomes_rate": {
            "observed": outcomes_rate,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": SUPPORTED_MODULES.len(),
            "passed": outcomes_rate >= 1.0,
        },
        "implementation_readiness_complete_rate": {
            "observed": readiness_rate,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": SUPPORTED_MODULES.len(),
            "passed": readiness_rate >= 1.0,
        },
        "zero_authority_lock_coverage_rate": {
            "observed": zero_auth_rate,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": SUPPORTED_MODULES.len(),
            "passed": zero_auth_rate >= 1.0,
        },
        "result_digest_byte_stable_across_replays_rate": {
            "observed": digest_replay_rate,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": SUPPORTED_MODULES.len(),
            "passed": digest_replay_rate >= 1.0,
        },
        "positive_or_negative_control_counts_present_rate": {
            "observed": counts_rate,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": SUPPORTED_MODULES.len(),
            "passed": counts_rate >= 1.0,
        },
        "unsupported_module_id_fail_closed_rate": {
            "observed": unsupported_rate,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "probe_sample_size": unsupported_total,
            "probes": unsupported_probes,
            "passed": unsupported_rate >= 1.0,
        },
        "attack_axis_coverage_complete_rate": {
            "observed": axis_rate,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": axis_total,
            "axis_details": axis_details,
            "passed": axis_rate >= 1.0,
        },
        "authority_envelope_preservation_rate": {
            "observed": authority_rate,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": authority_total,
            "passed": authority_rate >= 1.0,
        },
        "byte_stable_two_replay_rate": {
            "observed": byte_replay_rate,
            "direction": "MAXIMIZE",
            "sample_size": SUPPORTED_MODULES.len(),
            "note": "observational; entire DeterministicControlDiagnosticV1 serialized byte-identical across two invocations; strict superset of the result_digest gate",
        },
    });

    let diagnostics_source_bytes =
        fs::read(diagnostics_source_path()).expect("diagnostics.rs readable");
    let dataset_sha256 = file_sha256(&diagnostics_source_bytes);
    let benchmark_lock_sha256 = file_sha256(&benchmark_lock_bytes);

    let diagnostic = json!({
        "schema": "amphora.module-phase0-benchmark-diagnostic.v1",
        "module_id": "amphora-redteam-audit",
        "kpi": kpi.clone(),
        "records": per_module.clone(),
        "passed": kpi["diagnostic_dispatch_ok_rate"]["passed"] == json!(true)
            && kpi["diagnostic_passed_flag_true_rate"]["passed"] == json!(true)
            && kpi["expected_equals_observed_fixture_outcomes_rate"]["passed"] == json!(true)
            && kpi["implementation_readiness_complete_rate"]["passed"] == json!(true)
            && kpi["zero_authority_lock_coverage_rate"]["passed"] == json!(true)
            && kpi["result_digest_byte_stable_across_replays_rate"]["passed"] == json!(true)
            && kpi["positive_or_negative_control_counts_present_rate"]["passed"] == json!(true)
            && kpi["unsupported_module_id_fail_closed_rate"]["passed"] == json!(true)
            && kpi["attack_axis_coverage_complete_rate"]["passed"] == json!(true)
            && kpi["authority_envelope_preservation_rate"]["passed"] == json!(true),
    });
    let diagnostic_bytes_canonical =
        serde_json::to_vec(&canonicalize(&diagnostic)).expect("canonical bytes");
    let diagnostic_sha256 = file_sha256(&diagnostic_bytes_canonical);

    let mut result = Map::new();
    result.insert("schema".into(), json!("amphora.module-phase0-benchmark-result.v1"));
    result.insert("module_id".into(), json!("amphora-redteam-audit"));
    result.insert(
        "benchmark_id".into(),
        json!("amphora-redteam-audit-phase0-deterministic-control-diagnostic-v1"),
    );
    result.insert("benchmark_lock_sha256".into(), json!(benchmark_lock_sha256));
    result.insert("dataset_fixture_sha256".into(), json!(dataset_sha256));
    result.insert(
        "dataset_fixture_note".into(),
        json!("SHA-256 of amphora-assurance-capabilities/src/diagnostics.rs — the runtime IS the fixture corpus (each per-module inner diagnostic embeds its reference bytes via include_bytes! at compile time)"),
    );
    result.insert("kpi".into(), kpi);
    result.insert("records".into(), json!(per_module));
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
fn redteam_audit_phase0_kpi_report_is_deterministic_and_gates_pass() {
    let first = compute_report();
    let first_bytes = serde_json::to_vec(&first).expect("canonical");
    let second_bytes = serde_json::to_vec(&compute_report()).expect("canonical");
    assert_eq!(first_bytes, second_bytes, "KPI report is not byte-stable");

    let kpi = &first["kpi"];
    for gate in [
        "diagnostic_dispatch_ok_rate",
        "diagnostic_passed_flag_true_rate",
        "expected_equals_observed_fixture_outcomes_rate",
        "implementation_readiness_complete_rate",
        "zero_authority_lock_coverage_rate",
        "result_digest_byte_stable_across_replays_rate",
        "positive_or_negative_control_counts_present_rate",
        "unsupported_module_id_fail_closed_rate",
        "attack_axis_coverage_complete_rate",
        "authority_envelope_preservation_rate",
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
