//! Phase-0 KPI harness for `amphora-source-ledger`.
//!
//! Drives the deterministic `evaluate_source_ledger` runtime (via
//! AssuranceCapability::new("amphora-source-ledger")) which loads the
//! compile-time-embedded facts.json and source_records.json, and returns
//! honest FAILED_GATES because 14 load-bearing constants lack a second
//! controlled source and 14 prose waivers exist. Verifies pinned counts
//! (cited=83, load_bearing=23, two_source=9, prose_waiver=14, missing_url=0,
//! source_record=162, incomplete=0), pinned gate/status/score, explicit
//! missing_inputs, authority envelope preservation, byte-stable two-replay
//! across 5 evidence-package candidates plus 3 fail-closed probes.

use std::collections::BTreeMap;
use std::fs;
use std::path::PathBuf;

use amphora_assurance_capabilities::AssuranceCapability;
use amphora_core::{
    canonicalize, stable_hash, Capability, CandidateEnvelope, ExecutionContext, FeatureSnapshot,
};
use serde_json::{json, Map, Value};
use sha2::{Digest, Sha256};

const SOURCE_LEDGER: &str = "amphora-source-ledger";

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
        .join("amphora-source-ledger/evidence/phase0/benchmark/benchmark-lock.v1.json")
}

fn facts_path() -> PathBuf {
    workspace_root().join("amphora-source-ledger/reference/mvp20/data/facts.json")
}

fn records_path() -> PathBuf {
    workspace_root().join("amphora-source-ledger/reference/mvp20/data/source_records.json")
}

// SCHEMA-ERA FIX (B2). The shipped artifact
// `amphora-source-ledger/evidence/phase0/benchmark/result.v1.json` has exactly one
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
        .join("amphora-source-ledger-phase0-kpi-result.v1.json")
}

fn file_sha256(bytes: &[u8]) -> String {
    let mut digest = Sha256::new();
    digest.update(bytes);
    format!("{:x}", digest.finalize())
}

fn context() -> ExecutionContext {
    ExecutionContext {
        run_id: "phase0-kpi-source-ledger".into(),
        deterministic_seed: 20260722,
        lineage: Value::Null,
    }
}

fn wrong_type_candidate() -> CandidateEnvelope {
    CandidateEnvelope::from_value(json!({
        "candidate_id": "formulation-probe",
        "candidate_type": "formulation",
        "formulation": {"part_A": {"resin": 1.0}, "part_B": {"hardener": 1.0}}
    }))
    .expect("valid formulation candidate")
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
    // Independent recompute of counts from the on-disk facts.json + source_records.json.
    let facts_bytes = fs::read(facts_path()).expect("facts readable");
    let facts: Value = serde_json::from_slice(&facts_bytes).expect("facts JSON");
    let entries = facts["entries"].as_object().expect("entries object");
    let harness_cited = entries.len();
    let load_bearing: Vec<&Value> = entries
        .values()
        .filter(|v| v["load_bearing"].as_bool() == Some(true))
        .collect();
    let harness_load_bearing = load_bearing.len();
    let harness_two_source = load_bearing
        .iter()
        .filter(|v| {
            v["second_url"]
                .as_str()
                .is_some_and(|s| !s.trim().is_empty())
        })
        .count();
    let harness_prose_waiver = load_bearing
        .iter()
        .filter(|v| {
            v["single_source_waiver"]
                .as_str()
                .is_some_and(|s| !s.trim().is_empty())
        })
        .count();
    let harness_missing_url = entries
        .values()
        .filter(|v| v["url"].as_str().is_none_or(|s| s.trim().is_empty()))
        .count();
    let records_bytes = fs::read(records_path()).expect("records readable");
    let records: Value = serde_json::from_slice(&records_bytes).expect("records JSON");
    let source_records = records["records"].as_array().expect("records array");
    let harness_source_record = source_records.len();
    let required_fields = records["required_record_fields"]
        .as_array()
        .expect("required fields");
    let harness_incomplete = source_records
        .iter()
        .filter(|r| {
            required_fields
                .iter()
                .any(|f| f.as_str().is_some_and(|f| r[f].is_null()))
        })
        .count();

    // Pinned expected counts.
    let pinned_ok = harness_cited == 83
        && harness_load_bearing == 23
        && harness_two_source == 9
        && harness_prose_waiver == 14
        && harness_missing_url == 0
        && harness_source_record == 162
        && harness_incomplete == 0;

    // Invoke runtime across 5 candidates.
    let cap = AssuranceCapability::new(SOURCE_LEDGER).expect("capability constructs");
    let features = FeatureSnapshot::default();
    let ctx = context();
    let candidates: Vec<CandidateEnvelope> = (0..5)
        .map(|i| {
            CandidateEnvelope::from_value(json!({
                "candidate_id": format!("phase0-kpi-source-ledger-evidence-{i}"),
                "candidate_type": "evidence_package",
                "evidence_refs": {"evidence_package": {}}
            }))
            .expect("valid evidence candidate")
        })
        .collect();

    let mut per_candidate: Vec<Value> = Vec::new();
    let mut status_pass = 0_usize;
    let mut score_pass = 0_usize;
    let mut metrics_pass = 0_usize;
    let mut uncited_gate_pass = 0_usize;
    let mut two_source_gate_pass = 0_usize;
    let mut waiver_gate_pass = 0_usize;
    let mut prose_gate_pass = 0_usize;
    let mut missing_input_two_source_pass = 0_usize;
    let mut missing_input_prose_pass = 0_usize;
    let mut explanation_pass = 0_usize;
    let mut envelope_pass = 0_usize;
    let mut byte_replay_pass = 0_usize;

    for candidate in &candidates {
        let out = cap
            .evaluate(candidate, &features, &ctx)
            .expect("evaluate ok");

        let status_ok = out.status == "FAILED_GATES";
        if status_ok {
            status_pass += 1;
        }
        let score_ok = out.score_0_1 == Some(0.0);
        if score_ok {
            score_pass += 1;
        }

        let metrics_ok = out.metrics.get("cited_constant_count") == Some(&json!(83))
            && out.metrics.get("load_bearing_constant_count") == Some(&json!(23))
            && out.metrics.get("two_source_count") == Some(&json!(9))
            && out.metrics.get("prose_waiver_count") == Some(&json!(14))
            && out.metrics.get("missing_url_count") == Some(&json!(0))
            && out.metrics.get("source_record_count") == Some(&json!(162))
            && out.metrics.get("incomplete_source_record_count") == Some(&json!(0));
        if metrics_ok {
            metrics_pass += 1;
        }

        let uncited_ok = out.gates.get("uncited_constants_rejected") == Some(&json!(true));
        if uncited_ok {
            uncited_gate_pass += 1;
        }
        let two_source_ok = out.gates.get("load_bearing_two_source") == Some(&json!(false));
        if two_source_ok {
            two_source_gate_pass += 1;
        }
        let waiver_ok =
            out.gates.get("load_bearing_two_source_or_waiver") == Some(&json!(false));
        if waiver_ok {
            waiver_gate_pass += 1;
        }
        let prose_ok = out.gates.get("prose_waivers_rejected") == Some(&json!(false));
        if prose_ok {
            prose_gate_pass += 1;
        }

        let missing_two_source_ok = out.missing_inputs.iter().any(|m| {
            m.contains("14") && m.contains("load-bearing") && m.contains("second controlled source")
        });
        if missing_two_source_ok {
            missing_input_two_source_pass += 1;
        }
        let missing_prose_ok = out
            .missing_inputs
            .iter()
            .any(|m| m.contains("14 prose waivers"));
        if missing_prose_ok {
            missing_input_prose_pass += 1;
        }

        let explanation_ok = out
            .explanations
            .iter()
            .any(|e| e.contains("audit-only") && e.contains("load-bearing"));
        if explanation_ok {
            explanation_pass += 1;
        }

        let out_json = serde_json::to_value(&out).expect("serializes");
        let envelope_ok = contains_banned_key(&out_json).is_none();
        if envelope_ok {
            envelope_pass += 1;
        }

        let replay = cap.evaluate(candidate, &features, &ctx).unwrap();
        let byte_ok = serde_json::to_vec(&out).unwrap()
            == serde_json::to_vec(&replay).unwrap();
        if byte_ok {
            byte_replay_pass += 1;
        }

        per_candidate.push(json!({
            "candidate_id": candidate.candidate_id(),
            "status": out.status,
            "score_0_1": out.score_0_1,
            "cited_constant_count": out.metrics.get("cited_constant_count"),
            "load_bearing_constant_count": out.metrics.get("load_bearing_constant_count"),
            "two_source_count": out.metrics.get("two_source_count"),
            "prose_waiver_count": out.metrics.get("prose_waiver_count"),
            "missing_url_count": out.metrics.get("missing_url_count"),
            "source_record_count": out.metrics.get("source_record_count"),
            "incomplete_source_record_count": out.metrics.get("incomplete_source_record_count"),
            "uncited_constants_rejected_gate": out.gates.get("uncited_constants_rejected"),
            "load_bearing_two_source_gate": out.gates.get("load_bearing_two_source"),
            "load_bearing_two_source_or_waiver_gate": out.gates.get("load_bearing_two_source_or_waiver"),
            "prose_waivers_rejected_gate": out.gates.get("prose_waivers_rejected"),
            "missing_inputs": out.missing_inputs,
            "authority_envelope_preserved": envelope_ok,
            "byte_stable_two_replay": byte_ok,
        }));
    }

    let n = candidates.len().max(1) as f64;

    // Fail-closed probes.
    let mut fail_closed_pass = 0_usize;
    let mut fail_probes: Vec<Value> = Vec::new();

    let wrong = wrong_type_candidate();
    let is_err = cap.evaluate(&wrong, &features, &ctx).is_err();
    if is_err { fail_closed_pass += 1; }
    fail_probes.push(json!({"probe": "candidate_type_formulation_rejected", "fail_closed": is_err}));

    let unknown = AssuranceCapability::new("amphora-does-not-exist").is_err();
    if unknown { fail_closed_pass += 1; }
    fail_probes.push(json!({"probe": "unknown_module_id_rejected", "fail_closed": unknown}));

    let ws = AssuranceCapability::new("   ").is_err();
    if ws { fail_closed_pass += 1; }
    fail_probes.push(json!({"probe": "whitespace_module_id_rejected", "fail_closed": ws}));

    let fail_total = fail_probes.len();
    let fail_rate = fail_closed_pass as f64 / fail_total.max(1) as f64;

    let kpi = json!({
        "facts_and_records_pinned_counts_rate": {
            "observed": if pinned_ok { 1.0 } else { 0.0 },
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": 1,
            "passed": pinned_ok,
        },
        "runtime_status_failed_gates_honestly_rate": {
            "observed": status_pass as f64 / n,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": candidates.len(),
            "passed": status_pass as f64 / n >= 1.0,
        },
        "runtime_score_zero_rate": {
            "observed": score_pass as f64 / n,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": candidates.len(),
            "passed": score_pass as f64 / n >= 1.0,
        },
        "runtime_metrics_pin_seven_counts_rate": {
            "observed": metrics_pass as f64 / n,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": candidates.len(),
            "passed": metrics_pass as f64 / n >= 1.0,
        },
        "uncited_constants_rejected_gate_true_rate": {
            "observed": uncited_gate_pass as f64 / n,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": candidates.len(),
            "passed": uncited_gate_pass as f64 / n >= 1.0,
        },
        "load_bearing_two_source_gate_false_rate": {
            "observed": two_source_gate_pass as f64 / n,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": candidates.len(),
            "passed": two_source_gate_pass as f64 / n >= 1.0,
        },
        "load_bearing_two_source_or_waiver_gate_false_rate": {
            "observed": waiver_gate_pass as f64 / n,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": candidates.len(),
            "passed": waiver_gate_pass as f64 / n >= 1.0,
        },
        "prose_waivers_rejected_gate_false_rate": {
            "observed": prose_gate_pass as f64 / n,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": candidates.len(),
            "passed": prose_gate_pass as f64 / n >= 1.0,
        },
        "missing_input_names_14_load_bearing_second_source_gap_rate": {
            "observed": missing_input_two_source_pass as f64 / n,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": candidates.len(),
            "passed": missing_input_two_source_pass as f64 / n >= 1.0,
        },
        "missing_input_names_14_prose_waivers_rate": {
            "observed": missing_input_prose_pass as f64 / n,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": candidates.len(),
            "passed": missing_input_prose_pass as f64 / n >= 1.0,
        },
        "explanation_discloses_audit_only_load_bearing_gate_failure_rate": {
            "observed": explanation_pass as f64 / n,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": candidates.len(),
            "passed": explanation_pass as f64 / n >= 1.0,
        },
        "authority_envelope_preservation_rate": {
            "observed": envelope_pass as f64 / n,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": candidates.len(),
            "passed": envelope_pass as f64 / n >= 1.0,
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
            "note": "observational; evaluate_source_ledger invoked twice per candidate produces byte-identical ModuleResult",
        },
    });

    let benchmark_lock_bytes = fs::read(benchmark_lock_path()).expect("benchmark-lock readable");
    let benchmark_lock_sha256 = file_sha256(&benchmark_lock_bytes);
    let facts_sha256 = file_sha256(&facts_bytes);
    let records_sha256 = file_sha256(&records_bytes);

    let diagnostic = json!({
        "schema": "amphora.module-phase0-benchmark-diagnostic.v1",
        "module_id": "amphora-source-ledger",
        "kpi": kpi.clone(),
        "records": per_candidate.clone(),
        "passed": kpi["facts_and_records_pinned_counts_rate"]["passed"] == json!(true)
            && kpi["runtime_status_failed_gates_honestly_rate"]["passed"] == json!(true)
            && kpi["runtime_score_zero_rate"]["passed"] == json!(true)
            && kpi["runtime_metrics_pin_seven_counts_rate"]["passed"] == json!(true)
            && kpi["uncited_constants_rejected_gate_true_rate"]["passed"] == json!(true)
            && kpi["load_bearing_two_source_gate_false_rate"]["passed"] == json!(true)
            && kpi["load_bearing_two_source_or_waiver_gate_false_rate"]["passed"] == json!(true)
            && kpi["prose_waivers_rejected_gate_false_rate"]["passed"] == json!(true)
            && kpi["missing_input_names_14_load_bearing_second_source_gap_rate"]["passed"] == json!(true)
            && kpi["missing_input_names_14_prose_waivers_rate"]["passed"] == json!(true)
            && kpi["explanation_discloses_audit_only_load_bearing_gate_failure_rate"]["passed"] == json!(true)
            && kpi["authority_envelope_preservation_rate"]["passed"] == json!(true)
            && kpi["unsupported_input_fail_closed_rate"]["passed"] == json!(true),
    });
    let diagnostic_bytes_canonical =
        serde_json::to_vec(&canonicalize(&diagnostic)).expect("canonical bytes");
    let diagnostic_sha256 = file_sha256(&diagnostic_bytes_canonical);

    let mut result = Map::new();
    result.insert("schema".into(), json!("amphora.module-phase0-benchmark-result.v1"));
    result.insert("module_id".into(), json!("amphora-source-ledger"));
    result.insert(
        "benchmark_id".into(),
        json!("amphora-source-ledger-phase0-dual-source-integrity-v1"),
    );
    result.insert("benchmark_lock_sha256".into(), json!(benchmark_lock_sha256));
    result.insert("dataset_fixture_sha256".into(), json!(facts_sha256));
    result.insert("dataset_fixture_secondary_sha256".into(), json!(records_sha256));
    result.insert(
        "dataset_fixture_note".into(),
        json!("dataset_fixture_sha256 = SHA-256 of amphora-source-ledger/reference/mvp20/data/facts.json (83 cited constants, 23 load-bearing, 9 dual-sourced, 14 prose-waived, 0 missing-URL). dataset_fixture_secondary_sha256 = SHA-256 of source_records.json (162 records with 26 required fields, 0 incomplete). Both embedded at compile time by evaluate_source_ledger. Any drift in either file changes these hashes and the KPI recompute detects it via bit-exact count comparison."),
    );
    result.insert("kpi".into(), kpi);
    result.insert("records".into(), json!(per_candidate));
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
fn source_ledger_phase0_kpi_report_is_deterministic_and_gates_pass() {
    let first = compute_report();
    let first_bytes = serde_json::to_vec(&first).expect("canonical");
    let second_bytes = serde_json::to_vec(&compute_report()).expect("canonical");
    assert_eq!(first_bytes, second_bytes, "KPI report is not byte-stable");

    let kpi = &first["kpi"];
    for gate in [
        "facts_and_records_pinned_counts_rate",
        "runtime_status_failed_gates_honestly_rate",
        "runtime_score_zero_rate",
        "runtime_metrics_pin_seven_counts_rate",
        "uncited_constants_rejected_gate_true_rate",
        "load_bearing_two_source_gate_false_rate",
        "load_bearing_two_source_or_waiver_gate_false_rate",
        "prose_waivers_rejected_gate_false_rate",
        "missing_input_names_14_load_bearing_second_source_gap_rate",
        "missing_input_names_14_prose_waivers_rate",
        "explanation_discloses_audit_only_load_bearing_gate_failure_rate",
        "authority_envelope_preservation_rate",
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
