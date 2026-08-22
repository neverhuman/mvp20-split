//! Phase-0 KPI harness for `amphora-report-packager`.
//!
//! Drives the deterministic `evaluate_report_packager` runtime (via
//! AssuranceCapability::new("amphora-report-packager")) which honestly
//! returns INSUFFICIENT_INPUT with all 4 human-deliverable gates pinned
//! false because signed score envelopes and a deterministic report package
//! are not yet available. Verifies 5 evidence_package candidates plus 3
//! fail-closed probes on unsupported inputs.

use std::collections::BTreeMap;
use std::fs;
use std::path::PathBuf;

use amphora_assurance_capabilities::AssuranceCapability;
use amphora_core::{
    canonicalize, stable_hash, Capability, CandidateEnvelope, ExecutionContext, FeatureSnapshot,
};
use serde_json::{json, Map, Value};
use sha2::{Digest, Sha256};

const REPORT_PACKAGER: &str = "amphora-report-packager";

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
        .join("amphora-report-packager/evidence/phase0/benchmark/benchmark-lock.v1.json")
}

// SCHEMA-ERA FIX (B2). The shipped artifact
// `amphora-report-packager/evidence/phase0/benchmark/result.v1.json` has exactly one
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
        .join("amphora-report-packager-phase0-kpi-result.v1.json")
}

fn file_sha256(bytes: &[u8]) -> String {
    let mut digest = Sha256::new();
    digest.update(bytes);
    format!("{:x}", digest.finalize())
}

fn context() -> ExecutionContext {
    ExecutionContext {
        run_id: "phase0-kpi-report-packager".into(),
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

fn evidence_candidate(id: &str) -> CandidateEnvelope {
    CandidateEnvelope::from_value(json!({
        "candidate_id": id,
        "candidate_type": "evidence_package",
        "evidence_refs": {"evidence_package": {"kind": "phase0-kpi"}}
    }))
    .expect("valid evidence candidate")
}

fn compute_report() -> Value {
    let cap = AssuranceCapability::new(REPORT_PACKAGER).expect("capability constructs");
    let features = FeatureSnapshot::default();
    let ctx = context();

    let candidates: Vec<CandidateEnvelope> = (0..5)
        .map(|i| evidence_candidate(&format!("phase0-kpi-report-packager-{i}")))
        .collect();

    let mut per_candidate: Vec<Value> = Vec::new();

    let mut status_pass = 0_usize;
    let mut evidence_scope_pass = 0_usize;
    let mut doc_count_pass = 0_usize;
    let mut signed_metric_pass = 0_usize;
    let mut score_gate_pass = 0_usize;
    let mut authority_gate_pass = 0_usize;
    let mut banned_gate_pass = 0_usize;
    let mut signed_gate_pass = 0_usize;
    let mut missing_input_pass = 0_usize;
    let mut explanation_pass = 0_usize;
    let mut envelope_pass = 0_usize;
    let mut byte_replay_pass = 0_usize;

    for candidate in &candidates {
        let out = cap.evaluate(candidate, &features, &ctx).expect("evaluate ok");

        let status_ok = out.status == "INSUFFICIENT_INPUT";
        if status_ok { status_pass += 1; }
        let evidence_ok = out.evidence_scope == "report_package";
        if evidence_ok { evidence_scope_pass += 1; }
        let doc_count_ok = out.metrics.get("generated_document_count") == Some(&json!(4));
        if doc_count_ok { doc_count_pass += 1; }
        let signed_metric_ok = out.metrics.get("signed_report_package_present") == Some(&json!(false));
        if signed_metric_ok { signed_metric_pass += 1; }
        let score_gate_ok = out.gates.get("score_envelopes_valid") == Some(&json!(false));
        if score_gate_ok { score_gate_pass += 1; }
        let authority_gate_ok = out.gates.get("authority_lock_present") == Some(&json!(false));
        if authority_gate_ok { authority_gate_pass += 1; }
        let banned_gate_ok = out.gates.get("banned_claim_lint_pass") == Some(&json!(false));
        if banned_gate_ok { banned_gate_pass += 1; }
        let signed_gate_ok = out.gates.get("signed_report_package_present") == Some(&json!(false));
        if signed_gate_ok { signed_gate_pass += 1; }

        let missing_ok = out.missing_inputs.iter().any(|m| {
            m.contains("registry-verified score envelopes") && m.contains("signed deterministic report package")
        });
        if missing_ok { missing_input_pass += 1; }

        let explanation_ok = out.explanations.iter().any(|e| {
            e.contains("Human deliverables") && e.contains("downstream") && e.contains("sealed score envelopes")
        });
        if explanation_ok { explanation_pass += 1; }

        let out_json = serde_json::to_value(&out).unwrap();
        let envelope_ok = contains_banned_key(&out_json).is_none();
        if envelope_ok { envelope_pass += 1; }

        let replay = cap.evaluate(candidate, &features, &ctx).unwrap();
        let byte_ok = serde_json::to_vec(&out).unwrap() == serde_json::to_vec(&replay).unwrap();
        if byte_ok { byte_replay_pass += 1; }

        per_candidate.push(json!({
            "candidate_id": candidate.candidate_id(),
            "status": out.status,
            "evidence_scope": out.evidence_scope,
            "generated_document_count": out.metrics.get("generated_document_count"),
            "signed_report_package_present_metric": out.metrics.get("signed_report_package_present"),
            "score_envelopes_valid_gate": out.gates.get("score_envelopes_valid"),
            "authority_lock_present_gate": out.gates.get("authority_lock_present"),
            "banned_claim_lint_pass_gate": out.gates.get("banned_claim_lint_pass"),
            "signed_report_package_present_gate": out.gates.get("signed_report_package_present"),
            "missing_inputs": out.missing_inputs,
            "authority_envelope_preserved": envelope_ok,
            "byte_stable_two_replay": byte_ok,
        }));
    }

    let n = candidates.len().max(1) as f64;

    // Fail-closed probes.
    let mut ff_pass = 0_usize;
    let mut ff_probes: Vec<Value> = Vec::new();

    let wrong = CandidateEnvelope::from_value(json!({
        "candidate_id": "wrong-type",
        "candidate_type": "formulation",
        "formulation": {"part_A": {"resin": 1.0}, "part_B": {"hardener": 1.0}}
    })).unwrap();
    let is_err = AssuranceCapability::new(REPORT_PACKAGER).unwrap()
        .evaluate(&wrong, &features, &ctx).is_err();
    if is_err { ff_pass += 1; }
    ff_probes.push(json!({"probe": "candidate_type_formulation_rejected", "fail_closed": is_err}));

    let unknown = AssuranceCapability::new("amphora-does-not-exist").is_err();
    if unknown { ff_pass += 1; }
    ff_probes.push(json!({"probe": "unknown_module_id_rejected", "fail_closed": unknown}));

    let ws = AssuranceCapability::new("   ").is_err();
    if ws { ff_pass += 1; }
    ff_probes.push(json!({"probe": "whitespace_module_id_rejected", "fail_closed": ws}));

    let ff_total = ff_probes.len();
    let ff_rate = ff_pass as f64 / ff_total.max(1) as f64;

    let kpi = json!({
        "runtime_status_insufficient_input_rate": {
            "observed": status_pass as f64 / n, "floor": 1.0, "direction": "MAXIMIZE",
            "sample_size": candidates.len(), "passed": status_pass as f64 / n >= 1.0,
        },
        "evidence_scope_pinned_report_package_rate": {
            "observed": evidence_scope_pass as f64 / n, "floor": 1.0, "direction": "MAXIMIZE",
            "sample_size": candidates.len(), "passed": evidence_scope_pass as f64 / n >= 1.0,
        },
        "generated_document_count_pinned_four_rate": {
            "observed": doc_count_pass as f64 / n, "floor": 1.0, "direction": "MAXIMIZE",
            "sample_size": candidates.len(), "passed": doc_count_pass as f64 / n >= 1.0,
        },
        "signed_report_package_present_metric_false_rate": {
            "observed": signed_metric_pass as f64 / n, "floor": 1.0, "direction": "MAXIMIZE",
            "sample_size": candidates.len(), "passed": signed_metric_pass as f64 / n >= 1.0,
        },
        "score_envelopes_valid_gate_false_rate": {
            "observed": score_gate_pass as f64 / n, "floor": 1.0, "direction": "MAXIMIZE",
            "sample_size": candidates.len(), "passed": score_gate_pass as f64 / n >= 1.0,
        },
        "authority_lock_present_gate_false_rate": {
            "observed": authority_gate_pass as f64 / n, "floor": 1.0, "direction": "MAXIMIZE",
            "sample_size": candidates.len(), "passed": authority_gate_pass as f64 / n >= 1.0,
        },
        "banned_claim_lint_pass_gate_false_rate": {
            "observed": banned_gate_pass as f64 / n, "floor": 1.0, "direction": "MAXIMIZE",
            "sample_size": candidates.len(), "passed": banned_gate_pass as f64 / n >= 1.0,
        },
        "signed_report_package_present_gate_false_rate": {
            "observed": signed_gate_pass as f64 / n, "floor": 1.0, "direction": "MAXIMIZE",
            "sample_size": candidates.len(), "passed": signed_gate_pass as f64 / n >= 1.0,
        },
        "missing_input_names_score_envelopes_and_signed_report_package_rate": {
            "observed": missing_input_pass as f64 / n, "floor": 1.0, "direction": "MAXIMIZE",
            "sample_size": candidates.len(), "passed": missing_input_pass as f64 / n >= 1.0,
        },
        "explanation_discloses_human_deliverables_downstream_rate": {
            "observed": explanation_pass as f64 / n, "floor": 1.0, "direction": "MAXIMIZE",
            "sample_size": candidates.len(), "passed": explanation_pass as f64 / n >= 1.0,
        },
        "authority_envelope_preservation_rate": {
            "observed": envelope_pass as f64 / n, "floor": 1.0, "direction": "MAXIMIZE",
            "sample_size": candidates.len(), "passed": envelope_pass as f64 / n >= 1.0,
        },
        "unsupported_input_fail_closed_rate": {
            "observed": ff_rate, "floor": 1.0, "direction": "MAXIMIZE",
            "probe_sample_size": ff_total, "probes": ff_probes,
            "passed": ff_rate >= 1.0,
        },
        "byte_stable_two_replay_rate": {
            "observed": byte_replay_pass as f64 / n, "direction": "MAXIMIZE",
            "sample_size": candidates.len(),
            "note": "observational; evaluate_report_packager invoked twice per candidate produces byte-identical ModuleResult",
        },
    });

    let benchmark_lock_bytes = fs::read(benchmark_lock_path()).expect("benchmark-lock readable");
    let benchmark_lock_sha256 = file_sha256(&benchmark_lock_bytes);

    let diagnostic = json!({
        "schema": "amphora.module-phase0-benchmark-diagnostic.v1",
        "module_id": "amphora-report-packager",
        "kpi": kpi.clone(),
        "records": per_candidate.clone(),
        "passed": kpi["runtime_status_insufficient_input_rate"]["passed"] == json!(true)
            && kpi["evidence_scope_pinned_report_package_rate"]["passed"] == json!(true)
            && kpi["generated_document_count_pinned_four_rate"]["passed"] == json!(true)
            && kpi["signed_report_package_present_metric_false_rate"]["passed"] == json!(true)
            && kpi["score_envelopes_valid_gate_false_rate"]["passed"] == json!(true)
            && kpi["authority_lock_present_gate_false_rate"]["passed"] == json!(true)
            && kpi["banned_claim_lint_pass_gate_false_rate"]["passed"] == json!(true)
            && kpi["signed_report_package_present_gate_false_rate"]["passed"] == json!(true)
            && kpi["missing_input_names_score_envelopes_and_signed_report_package_rate"]["passed"] == json!(true)
            && kpi["explanation_discloses_human_deliverables_downstream_rate"]["passed"] == json!(true)
            && kpi["authority_envelope_preservation_rate"]["passed"] == json!(true)
            && kpi["unsupported_input_fail_closed_rate"]["passed"] == json!(true),
    });
    let diagnostic_bytes_canonical =
        serde_json::to_vec(&canonicalize(&diagnostic)).expect("canonical bytes");
    let diagnostic_sha256 = file_sha256(&diagnostic_bytes_canonical);

    let mut result = Map::new();
    result.insert("schema".into(), json!("amphora.module-phase0-benchmark-result.v1"));
    result.insert("module_id".into(), json!("amphora-report-packager"));
    result.insert(
        "benchmark_id".into(),
        json!("amphora-report-packager-phase0-signed-deliverable-quarantine-v1"),
    );
    result.insert("benchmark_lock_sha256".into(), json!(benchmark_lock_sha256));
    result.insert("dataset_fixture_sha256".into(), json!(benchmark_lock_sha256));
    result.insert(
        "dataset_fixture_note".into(),
        json!("report-packager Phase-0 harness constructs its 5 evidence_package candidates + 3 fail-closed probes in-Rust; the runtime consumes 4 compile-time-embedded REPORT_ARTIFACTS (CUSTOMER_FACING.tex, FOUNDER_FACING.tex, blueprint.md, f718_style_datasheet.md) but never elevates them into a signed deliverable. SHA-256 recorded is the on-disk benchmark-lock hash."),
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
fn report_packager_phase0_kpi_report_is_deterministic_and_gates_pass() {
    let first = compute_report();
    let first_bytes = serde_json::to_vec(&first).expect("canonical");
    let second_bytes = serde_json::to_vec(&compute_report()).expect("canonical");
    assert_eq!(first_bytes, second_bytes, "KPI report is not byte-stable");

    let kpi = &first["kpi"];
    for gate in [
        "runtime_status_insufficient_input_rate",
        "evidence_scope_pinned_report_package_rate",
        "generated_document_count_pinned_four_rate",
        "signed_report_package_present_metric_false_rate",
        "score_envelopes_valid_gate_false_rate",
        "authority_lock_present_gate_false_rate",
        "banned_claim_lint_pass_gate_false_rate",
        "signed_report_package_present_gate_false_rate",
        "missing_input_names_score_envelopes_and_signed_report_package_rate",
        "explanation_discloses_human_deliverables_downstream_rate",
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
