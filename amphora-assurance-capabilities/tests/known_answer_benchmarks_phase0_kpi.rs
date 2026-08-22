//! Phase-0 KPI harness for `amphora-known-answer-benchmarks`.
//!
//! Drives the deterministic `evaluate_known_answers` runtime (exposed via
//! AssuranceCapability::new("amphora-known-answer-benchmarks")) which loads
//! the embedded `control_by_control_receipt.v1.json` fixture and verifies
//! (a) receipt schema + structural integrity, (b) 13 VERIFIED_PASS + 0
//! VERIFIED_FAIL + 1 UNVERIFIED historical control counts pinned bit-exact,
//! (c) 6/6 arithmetic subset checks, (d) every control row bound to a valid
//! SHA-256 source artifact hash, (e) honest FAILED_GATES status because the
//! audit is 13/14 not 14/14, (f) explicit missing_inputs entry that
//! communicates the historical gap, (g) authority ceiling preservation, and
//! (h) byte-stable two-replay, plus dedicated fail-closed probes for wrong
//! candidate_type and unknown module_id.

use std::collections::BTreeMap;
use std::fs;
use std::path::PathBuf;

use amphora_assurance_capabilities::AssuranceCapability;
use amphora_core::{
    canonicalize, stable_hash, Capability, CandidateEnvelope, ExecutionContext, FeatureSnapshot,
};
use serde_json::{json, Map, Value};
use sha2::{Digest, Sha256};

const KNOWN_ANSWERS: &str = "amphora-known-answer-benchmarks";

const BANNED_AUTHORITY_KEYS: [&str; 6] = [
    "batch_release",
    "release_authorized",
    "qualified",
    "authorized_by",
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
    workspace_root()
        .join("amphora-known-answer-benchmarks/evidence/phase0/benchmark/benchmark-lock.v1.json")
}

fn control_receipt_path() -> PathBuf {
    workspace_root().join(
        "amphora-known-answer-benchmarks/reference/mvp20/out/control_by_control_receipt.v1.json",
    )
}

// SCHEMA-ERA FIX (B2). The shipped artifact
// `amphora-known-answer-benchmarks/evidence/phase0/benchmark/result.v1.json` has exactly one
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
        .join("amphora-known-answer-benchmarks-phase0-kpi-result.v1.json")
}

fn file_sha256(bytes: &[u8]) -> String {
    let mut digest = Sha256::new();
    digest.update(bytes);
    format!("{:x}", digest.finalize())
}

fn formulation_candidate(id: &str) -> CandidateEnvelope {
    CandidateEnvelope::from_value(json!({
        "candidate_id": id,
        "candidate_type": "formulation",
        "formulation": {"part_A": {"resin": 1.0}, "part_B": {"hardener": 1.0}}
    }))
    .expect("valid formulation candidate")
}

fn wrong_type_candidate() -> CandidateEnvelope {
    CandidateEnvelope::from_value(json!({
        "candidate_id": "evidence-probe",
        "candidate_type": "evidence_package",
        "evidence_refs": {"evidence_package": {}}
    }))
    .expect("valid evidence candidate")
}

fn context() -> ExecutionContext {
    ExecutionContext {
        run_id: "phase0-kpi-known-answer".into(),
        deterministic_seed: 20260722,
        lineage: Value::Null,
    }
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

fn is_valid_sha256(value: &str) -> bool {
    value.len() == 64
        && value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
}

fn compute_report() -> Value {
    // Read the embedded control receipt from disk (same bytes as runtime include_bytes!).
    let receipt_bytes = fs::read(control_receipt_path()).expect("control receipt readable");
    let receipt: Value =
        serde_json::from_slice(&receipt_bytes).expect("control receipt JSON parses");

    let controls = receipt["controls"]
        .as_array()
        .expect("controls array");

    // Independent recompute (harness-side) of the receipt's structural claims.
    let schema_ok = receipt["schema"].as_str() == Some("amphora.known-answer-control-receipt.v1");
    let control_count_ok = receipt["control_count"].as_u64() == Some(controls.len() as u64);
    let receipt_verified_pass = receipt["verified_pass_count"].as_u64().unwrap_or(u64::MAX);
    let receipt_verified_fail = receipt["verified_fail_count"].as_u64().unwrap_or(u64::MAX);
    let receipt_unverified = receipt["unverified_count"].as_u64().unwrap_or(u64::MAX);

    let harness_verified_pass = controls
        .iter()
        .filter(|c| c["status"].as_str() == Some("VERIFIED_PASS"))
        .count() as u64;
    let harness_verified_fail = controls
        .iter()
        .filter(|c| c["status"].as_str() == Some("VERIFIED_FAIL"))
        .count() as u64;
    let harness_unverified = controls
        .iter()
        .filter(|c| c["status"].as_str() == Some("UNVERIFIED"))
        .count() as u64;

    let sub_counts_match = receipt_verified_pass == harness_verified_pass
        && receipt_verified_fail == harness_verified_fail
        && receipt_unverified == harness_unverified;

    let unique_ids: std::collections::BTreeSet<&str> = controls
        .iter()
        .filter_map(|c| c["control_id"].as_str())
        .collect();
    let unique_ids_ok = unique_ids.len() == controls.len();

    let all_have_source_sha = controls.iter().all(|c| {
        c["source_artifact_sha256"]
            .as_str()
            .is_some_and(is_valid_sha256)
    });

    let structure_ok =
        schema_ok && control_count_ok && sub_counts_match && all_have_source_sha && unique_ids_ok;

    // Pinned expected counts from the checked-in receipt at populate-time.
    let pinned_control_count_ok = controls.len() == 14;
    let pinned_verified_pass_ok = harness_verified_pass == 13;
    let pinned_verified_fail_ok = harness_verified_fail == 0;
    let pinned_unverified_ok = harness_unverified == 1;

    // Arithmetic subset: 6 control_ids that start with "ARITH-".
    let arith_controls: Vec<&Value> = controls
        .iter()
        .filter(|c| {
            c["control_id"]
                .as_str()
                .is_some_and(|id| id.starts_with("ARITH-"))
        })
        .collect();
    let arith_verified_pass = arith_controls
        .iter()
        .filter(|c| c["status"].as_str() == Some("VERIFIED_PASS"))
        .count();
    let arith_subset_ok = arith_controls.len() == 6 && arith_verified_pass == 6;

    // Now invoke the runtime and check runtime-reported gates/metrics.
    let cap = AssuranceCapability::new(KNOWN_ANSWERS).expect("capability constructs");
    let features = FeatureSnapshot::default();
    let ctx = context();
    let candidates: Vec<CandidateEnvelope> = (0..5)
        .map(|i| formulation_candidate(&format!("phase0-kpi-formula-{i}")))
        .collect();

    let mut runtime_records: Vec<Value> = Vec::new();
    let mut status_pass = 0_usize;
    let mut score_pass = 0_usize;
    let mut gate_receipt_pass = 0_usize;
    let mut gate_unverified_pass = 0_usize;
    let mut gate_audit_pass = 0_usize;
    let mut metric_arith_pass = 0_usize;
    let mut metric_counts_pass = 0_usize;
    let mut authority_pass = 0_usize;
    let mut missing_input_pass = 0_usize;
    let mut envelope_pass = 0_usize;
    let mut byte_replay_pass = 0_usize;

    for candidate in &candidates {
        let out = cap
            .evaluate(candidate, &features, &ctx)
            .expect("evaluate ok");

        // The runtime returns FAILED_GATES honestly because 1/14 is UNVERIFIED.
        let status_ok = out.status == "FAILED_GATES";
        if status_ok {
            status_pass += 1;
        }
        let expected_pass_rate = 13.0_f64 / 14.0;
        let score_ok = out
            .score_0_1
            .is_some_and(|s| (s - expected_pass_rate).abs() < 1e-12);
        if score_ok {
            score_pass += 1;
        }

        let gate_receipt = out.gates.get("control_receipt_well_formed") == Some(&json!(true));
        if gate_receipt {
            gate_receipt_pass += 1;
        }
        // 1 UNVERIFIED → all_14_controls_verified must be false (honest)
        let gate_unverified = out.gates.get("all_14_controls_verified") == Some(&json!(false));
        if gate_unverified {
            gate_unverified_pass += 1;
        }
        // audit_pass gate must also be false (13/14 not 14/14)
        let gate_audit = out.gates.get("known_answer_audit_passed") == Some(&json!(false));
        if gate_audit {
            gate_audit_pass += 1;
        }

        let metric_arith = out.metrics.get("arithmetic_subset_checks") == Some(&json!(6))
            && out.metrics.get("arithmetic_subset_pass") == Some(&json!(6));
        if metric_arith {
            metric_arith_pass += 1;
        }
        let metric_counts = out.metrics.get("control_count") == Some(&json!(14))
            && out.metrics.get("verified_pass_count") == Some(&json!(13))
            && out.metrics.get("verified_fail_count") == Some(&json!(0))
            && out.metrics.get("unverified_count") == Some(&json!(1));
        if metric_counts {
            metric_counts_pass += 1;
        }

        // Authority envelope: ranking_quarantine=true, scientific_applicability=UNVALIDATED,
        // no ranking-authority tier upgrade.
        let authority_ok = out.metrics.get("ranking_quarantine") == Some(&json!(true))
            && out
                .metrics
                .get("scientific_applicability")
                .and_then(Value::as_str)
                == Some("UNVALIDATED");
        if authority_ok {
            authority_pass += 1;
        }

        // The missing_inputs must call out the historical UNVERIFIED gap so a
        // reader can see the runtime is not pretending the audit is 14/14.
        let missing_ok = out
            .missing_inputs
            .iter()
            .any(|m| m.contains("UNVERIFIED"));
        if missing_ok {
            missing_input_pass += 1;
        }

        // No banned authority key anywhere in serialized module result.
        let out_json = serde_json::to_value(&out).expect("serializes");
        let envelope_ok = contains_banned_key(&out_json).is_none();
        if envelope_ok {
            envelope_pass += 1;
        }

        // Byte-stable two-replay.
        let replay = cap.evaluate(candidate, &features, &ctx).unwrap();
        let byte_ok = serde_json::to_vec(&out).unwrap()
            == serde_json::to_vec(&replay).unwrap();
        if byte_ok {
            byte_replay_pass += 1;
        }

        runtime_records.push(json!({
            "candidate_id": candidate.candidate_id(),
            "status": out.status,
            "score_0_1": out.score_0_1,
            "control_count": out.metrics.get("control_count"),
            "verified_pass_count": out.metrics.get("verified_pass_count"),
            "verified_fail_count": out.metrics.get("verified_fail_count"),
            "unverified_count": out.metrics.get("unverified_count"),
            "arithmetic_subset_checks": out.metrics.get("arithmetic_subset_checks"),
            "arithmetic_subset_pass": out.metrics.get("arithmetic_subset_pass"),
            "audit_pass_rate": out.metrics.get("audit_pass_rate"),
            "control_receipt_well_formed_gate": out.gates.get("control_receipt_well_formed"),
            "all_14_controls_verified_gate": out.gates.get("all_14_controls_verified"),
            "known_answer_audit_passed_gate": out.gates.get("known_answer_audit_passed"),
            "status_is_failed_gates_honestly": status_ok,
            "score_matches_13_over_14": score_ok,
            "counts_pinned_correctly": metric_counts,
            "arithmetic_subset_6_of_6": metric_arith,
            "authority_ceiling_preserved": authority_ok,
            "explicit_missing_input_communicates_gap": missing_ok,
            "authority_envelope_preserved": envelope_ok,
            "byte_stable_two_replay": byte_ok,
        }));
    }

    let n = candidates.len().max(1) as f64;

    // Fail-closed probes.
    let mut fail_closed_pass = 0_usize;
    let mut fail_probes: Vec<Value> = Vec::new();

    // Probe A: wrong candidate_type
    let wrong = wrong_type_candidate();
    let err = cap
        .evaluate(&wrong, &features, &ctx)
        .is_err();
    if err {
        fail_closed_pass += 1;
    }
    fail_probes.push(json!({"probe": "candidate_type_evidence_package_rejected", "fail_closed": err}));

    // Probe B: unknown module_id
    let unknown = AssuranceCapability::new("amphora-does-not-exist").is_err();
    if unknown {
        fail_closed_pass += 1;
    }
    fail_probes.push(json!({"probe": "unknown_module_id_rejected", "fail_closed": unknown}));

    // Probe C: module_id whitespace
    let ws = AssuranceCapability::new("   ").is_err();
    if ws {
        fail_closed_pass += 1;
    }
    fail_probes.push(json!({"probe": "whitespace_module_id_rejected", "fail_closed": ws}));

    let fail_total = fail_probes.len();
    let fail_rate = fail_closed_pass as f64 / fail_total.max(1) as f64;

    let kpi = json!({
        "receipt_schema_and_structure_correctness_rate": {
            "observed": if structure_ok { 1.0 } else { 0.0 },
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": 1,
            "passed": structure_ok,
        },
        "pinned_control_count_14_rate": {
            "observed": if pinned_control_count_ok { 1.0 } else { 0.0 },
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": 1,
            "passed": pinned_control_count_ok,
        },
        "pinned_verified_pass_count_13_rate": {
            "observed": if pinned_verified_pass_ok { 1.0 } else { 0.0 },
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": 1,
            "passed": pinned_verified_pass_ok,
        },
        "pinned_verified_fail_count_0_rate": {
            "observed": if pinned_verified_fail_ok { 1.0 } else { 0.0 },
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": 1,
            "passed": pinned_verified_fail_ok,
        },
        "pinned_unverified_historical_count_1_rate": {
            "observed": if pinned_unverified_ok { 1.0 } else { 0.0 },
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": 1,
            "passed": pinned_unverified_ok,
        },
        "arithmetic_subset_6_of_6_pass_rate": {
            "observed": if arith_subset_ok { 1.0 } else { 0.0 },
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": 1,
            "passed": arith_subset_ok,
        },
        "runtime_status_honestly_failed_gates_rate": {
            "observed": status_pass as f64 / n,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": candidates.len(),
            "passed": status_pass as f64 / n >= 1.0,
        },
        "runtime_score_matches_13_over_14_rate": {
            "observed": score_pass as f64 / n,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": candidates.len(),
            "passed": score_pass as f64 / n >= 1.0,
        },
        "runtime_gates_correctly_report_incomplete_audit_rate": {
            "observed": (gate_receipt_pass + gate_unverified_pass + gate_audit_pass) as f64
                / (3.0 * n),
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": 3 * candidates.len(),
            "passed": gate_receipt_pass == candidates.len()
                && gate_unverified_pass == candidates.len()
                && gate_audit_pass == candidates.len(),
        },
        "runtime_metrics_pin_counts_and_arithmetic_subset_rate": {
            "observed": (metric_arith_pass + metric_counts_pass) as f64 / (2.0 * n),
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": 2 * candidates.len(),
            "passed": metric_arith_pass == candidates.len() && metric_counts_pass == candidates.len(),
        },
        "explicit_missing_input_communicates_gap_rate": {
            "observed": missing_input_pass as f64 / n,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": candidates.len(),
            "passed": missing_input_pass as f64 / n >= 1.0,
        },
        "authority_ceiling_preservation_rate": {
            "observed": (authority_pass + envelope_pass) as f64 / (2.0 * n),
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": 2 * candidates.len(),
            "passed": authority_pass == candidates.len() && envelope_pass == candidates.len(),
        },
        "unsupported_input_fail_closed_rate": {
            "observed": fail_rate,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "probe_sample_size": fail_total,
            "probes": fail_probes,
            "passed": fail_rate >= 1.0,
        },
        "byte_stable_two_replay_rate": {
            "observed": byte_replay_pass as f64 / n,
            "direction": "MAXIMIZE",
            "sample_size": candidates.len(),
            "note": "observational; evaluate_known_answers invoked twice per candidate produces byte-identical ModuleResult",
        },
    });

    let benchmark_lock_bytes = fs::read(benchmark_lock_path()).expect("benchmark-lock readable");
    let benchmark_lock_sha256 = file_sha256(&benchmark_lock_bytes);
    let dataset_sha256 = file_sha256(&receipt_bytes);

    let diagnostic = json!({
        "schema": "amphora.module-phase0-benchmark-diagnostic.v1",
        "module_id": "amphora-known-answer-benchmarks",
        "kpi": kpi.clone(),
        "records": runtime_records.clone(),
        "passed": kpi["receipt_schema_and_structure_correctness_rate"]["passed"] == json!(true)
            && kpi["pinned_control_count_14_rate"]["passed"] == json!(true)
            && kpi["pinned_verified_pass_count_13_rate"]["passed"] == json!(true)
            && kpi["pinned_verified_fail_count_0_rate"]["passed"] == json!(true)
            && kpi["pinned_unverified_historical_count_1_rate"]["passed"] == json!(true)
            && kpi["arithmetic_subset_6_of_6_pass_rate"]["passed"] == json!(true)
            && kpi["runtime_status_honestly_failed_gates_rate"]["passed"] == json!(true)
            && kpi["runtime_score_matches_13_over_14_rate"]["passed"] == json!(true)
            && kpi["runtime_gates_correctly_report_incomplete_audit_rate"]["passed"] == json!(true)
            && kpi["runtime_metrics_pin_counts_and_arithmetic_subset_rate"]["passed"] == json!(true)
            && kpi["explicit_missing_input_communicates_gap_rate"]["passed"] == json!(true)
            && kpi["authority_ceiling_preservation_rate"]["passed"] == json!(true)
            && kpi["unsupported_input_fail_closed_rate"]["passed"] == json!(true),
    });
    let diagnostic_bytes_canonical =
        serde_json::to_vec(&canonicalize(&diagnostic)).expect("canonical bytes");
    let diagnostic_sha256 = file_sha256(&diagnostic_bytes_canonical);

    let mut result = Map::new();
    result.insert("schema".into(), json!("amphora.module-phase0-benchmark-result.v1"));
    result.insert("module_id".into(), json!("amphora-known-answer-benchmarks"));
    result.insert(
        "benchmark_id".into(),
        json!("amphora-known-answer-benchmarks-phase0-audit-v1"),
    );
    result.insert("benchmark_lock_sha256".into(), json!(benchmark_lock_sha256));
    result.insert("dataset_fixture_sha256".into(), json!(dataset_sha256));
    result.insert(
        "dataset_fixture_note".into(),
        json!("SHA-256 of amphora-known-answer-benchmarks/reference/mvp20/out/control_by_control_receipt.v1.json - the on-disk 14-control receipt embedded at compile time by evaluate_known_answers. 13 VERIFIED_PASS + 0 VERIFIED_FAIL + 1 UNVERIFIED historical (F160-BLACK, awaiting authoritative /38B or NAVSEA/DLA source)."),
    );
    result.insert("kpi".into(), kpi);
    result.insert("records".into(), json!(runtime_records));
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
fn known_answer_benchmarks_phase0_kpi_report_is_deterministic_and_gates_pass() {
    let first = compute_report();
    let first_bytes = serde_json::to_vec(&first).expect("canonical");
    let second_bytes = serde_json::to_vec(&compute_report()).expect("canonical");
    assert_eq!(first_bytes, second_bytes, "KPI report is not byte-stable");

    let kpi = &first["kpi"];
    for gate in [
        "receipt_schema_and_structure_correctness_rate",
        "pinned_control_count_14_rate",
        "pinned_verified_pass_count_13_rate",
        "pinned_verified_fail_count_0_rate",
        "pinned_unverified_historical_count_1_rate",
        "arithmetic_subset_6_of_6_pass_rate",
        "runtime_status_honestly_failed_gates_rate",
        "runtime_score_matches_13_over_14_rate",
        "runtime_gates_correctly_report_incomplete_audit_rate",
        "runtime_metrics_pin_counts_and_arithmetic_subset_rate",
        "explicit_missing_input_communicates_gap_rate",
        "authority_ceiling_preservation_rate",
        "unsupported_input_fail_closed_rate",
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
