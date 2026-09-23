//! Phase-0 KPI harness for `amphora-public-corrosion-benchmark`.
//!
//! Drives the deterministic `public_corrosion_benchmark` runtime (via
//! `FormulationCapability::new(descriptor)`) across 5 formulation candidates
//! with default FeatureSnapshot (no verified_model_input) so runtime returns
//! INSUFFICIENT_INPUT with all defensive metrics/gates pinned. Plus 3
//! fail-closed probes on unsupported inputs.

use std::collections::BTreeMap;
use std::fs;
use std::path::PathBuf;

use amphora_core::{
    canonicalize, stable_hash, Capability, CandidateEnvelope, ExecutionContext, FeatureSnapshot,
    ModuleDescriptor,
};
use amphora_formulation_capabilities::{FormulationCapability, PUBLIC_CORROSION_BENCHMARK_ID};
use serde_json::{json, Map, Value};
use sha2::{Digest, Sha256};

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
        .join("amphora-public-corrosion-benchmark/evidence/phase0/benchmark/benchmark-lock.v1.json")
}

// SCHEMA-ERA FIX (B2). The shipped artifact
// `amphora-public-corrosion-benchmark/evidence/phase0/benchmark/result.v1.json` has exactly one
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
        .join("amphora-public-corrosion-benchmark-phase0-kpi-result.v1.json")
}

fn file_sha256(bytes: &[u8]) -> String {
    let mut digest = Sha256::new();
    digest.update(bytes);
    format!("{:x}", digest.finalize())
}

fn context() -> ExecutionContext {
    ExecutionContext {
        run_id: "phase0-kpi-public-corrosion-benchmark".into(),
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

fn public_corrosion_descriptor() -> &'static ModuleDescriptor {
    static DESCRIPTOR: std::sync::OnceLock<ModuleDescriptor> = std::sync::OnceLock::new();
    DESCRIPTOR.get_or_init(|| ModuleDescriptor {
        project: PUBLIC_CORROSION_BENCHMARK_ID.into(),
        authority_ceiling: "EVIDENCE_ONLY".into(),
        solver_use_ceiling: "AUDIT_ONLY".into(),
        model_readiness_ceiling: "NOT_PROVEN".into(),
        ranking_eligible: false,
        candidate_types: vec!["formulation".into()],
        non_blocking_claim_locks: vec![
            "public_corpus_never_owned_candidate_evidence".into(),
            "no_candidate_corrosion_validation".into(),
            "unresolved_rights_quarantined".into(),
        ],
        readiness: "GATED".into(),
    })
}

struct Scenario {
    scenario_id: &'static str,
    candidate: Value,
    industrial_context: &'static str,
}

fn scenarios() -> Vec<Scenario> {
    vec![
        Scenario {
            scenario_id: "primer-simple-baseline",
            candidate: json!({
                "candidate_id": "corrosion-primer-baseline",
                "candidate_type": "formulation",
                "formulation": {
                    "part_A": {"dgeba": 100.0, "iron_oxide_red": 15.0, "zinc_phosphate": 8.0},
                    "part_B": {"polyamide": 65.0}
                }
            }),
            industrial_context: "marine primer with anticorrosive pigment package (baseline corrosion candidate)",
        },
        Scenario {
            scenario_id: "topcoat-corrosion-family",
            candidate: json!({
                "candidate_id": "corrosion-topcoat",
                "candidate_type": "formulation",
                "formulation": {
                    "part_A": {"dgebf": 120.0, "titanium_dioxide": 30.0},
                    "part_B": {"amidoamine": 40.0}
                }
            }),
            industrial_context: "industrial-maintenance topcoat with titanium dioxide",
        },
        Scenario {
            scenario_id: "adversarial-precomputed-benchmark-score",
            candidate: json!({
                "candidate_id": "corrosion-adversarial-score",
                "candidate_type": "formulation",
                "formulation": {
                    "part_A": {"dgeba": 100.0, "zinc_phosphate": 8.0},
                    "part_B": {"polyamide": 65.0},
                    "adversary_declared_benchmark_score": 0.95,
                    "adversary_declared_candidate_corrosion_validation": true,
                    "adversary_declared_artifact_access_attempted": true
                }
            }),
            industrial_context: "adversarial candidate injecting benchmark_score=0.95 + candidate_corrosion_validation=true + artifact_access_attempted=true; runtime must NOT elevate any of them",
        },
        Scenario {
            scenario_id: "adversarial-manifest-rights-declaration",
            candidate: json!({
                "candidate_id": "corrosion-adversarial-rights",
                "candidate_type": "formulation",
                "formulation": {
                    "part_A": {"dgeba": 100.0},
                    "part_B": {"polyamide": 65.0},
                    "candidate_declared_rights_cleared_manifest": true,
                    "candidate_declared_owned_candidate_evidence": true,
                    "candidate_declared_verified_model_artifact": true
                }
            }),
            industrial_context: "adversarial candidate injecting rights + owned-evidence + verified-model gate booleans; runtime must NOT elevate any",
        },
        Scenario {
            scenario_id: "minimal-flooring-formulation",
            candidate: json!({
                "candidate_id": "corrosion-flooring-min",
                "candidate_type": "formulation",
                "formulation": {
                    "part_A": {"dgebf": 150.0},
                    "part_B": {"polyamide": 50.0}
                }
            }),
            industrial_context: "minimal flooring formulation without anticorrosive package",
        },
    ]
}

fn compute_report() -> Value {
    let cap =
        FormulationCapability::new(public_corrosion_descriptor()).expect("capability constructs");
    let features = FeatureSnapshot::default();
    let ctx = context();
    let scenarios = scenarios();
    let n_scenarios = scenarios.len();

    let mut per_scenario: Vec<Value> = Vec::new();

    let mut status_pass = 0_usize;
    let mut evidence_scope_pass = 0_usize;
    let mut rights_unresolved_pass = 0_usize;
    let mut access_false_pass = 0_usize;
    let mut validation_false_pass = 0_usize;
    let mut score_null_pass = 0_usize;
    let mut manifest_gate_pass = 0_usize;
    let mut owned_gate_pass = 0_usize;
    let mut promotion_gate_pass = 0_usize;
    let mut verified_gate_pass = 0_usize;
    let mut missing_input_pass = 0_usize;
    let mut explanation_pass = 0_usize;
    let mut envelope_pass = 0_usize;
    let mut byte_replay_pass = 0_usize;

    for scenario in &scenarios {
        let candidate = CandidateEnvelope::from_value(scenario.candidate.clone())
            .expect("candidate parses");
        let out = cap
            .evaluate(&candidate, &features, &ctx)
            .expect("evaluate ok");

        let status_ok = out.status == "INSUFFICIENT_INPUT";
        if status_ok { status_pass += 1; }
        let evidence_ok = out.evidence_scope == "public_corrosion_benchmark_diagnostic";
        if evidence_ok { evidence_scope_pass += 1; }
        let rights_ok = out.metrics.get("artifact_rights_status").and_then(Value::as_str)
            == Some("UNRESOLVED");
        if rights_ok { rights_unresolved_pass += 1; }
        let access_ok = out.metrics.get("artifact_access_attempted") == Some(&json!(false));
        if access_ok { access_false_pass += 1; }
        let validation_ok = out.metrics.get("candidate_corrosion_validation") == Some(&json!(false));
        if validation_ok { validation_false_pass += 1; }
        let score_ok = out.metrics.get("benchmark_score") == Some(&Value::Null);
        if score_ok { score_null_pass += 1; }
        let manifest_ok = out.gates.get("rights_cleared_benchmark_manifest") == Some(&json!(false));
        if manifest_ok { manifest_gate_pass += 1; }
        let owned_ok = out.gates.get("owned_candidate_evidence") == Some(&json!(false));
        if owned_ok { owned_gate_pass += 1; }
        let promotion_ok = out.gates.get("promotion_gate_passed") == Some(&json!(false));
        if promotion_ok { promotion_gate_pass += 1; }
        let verified_ok = out.gates.get("verified_model_artifact") == Some(&json!(false));
        if verified_ok { verified_gate_pass += 1; }

        let missing_ok = out
            .missing_inputs
            .iter()
            .any(|m| m.contains("rights-cleared") && m.contains("public benchmark") && m.contains("manifest"));
        if missing_ok { missing_input_pass += 1; }

        let explanation_ok = out
            .explanations
            .iter()
            .any(|e| e.contains("Unresolved-rights") && e.contains("not opened"));
        if explanation_ok { explanation_pass += 1; }

        let out_json = serde_json::to_value(&out).unwrap();
        let envelope_ok = contains_banned_key(&out_json).is_none();
        if envelope_ok { envelope_pass += 1; }

        let replay = cap.evaluate(&candidate, &features, &ctx).unwrap();
        let byte_ok = serde_json::to_vec(&out).unwrap() == serde_json::to_vec(&replay).unwrap();
        if byte_ok { byte_replay_pass += 1; }

        per_scenario.push(json!({
            "scenario_id": scenario.scenario_id,
            "candidate_id": candidate.candidate_id(),
            "industrial_context": scenario.industrial_context,
            "status": out.status,
            "evidence_scope": out.evidence_scope,
            "artifact_rights_status": out.metrics.get("artifact_rights_status"),
            "artifact_access_attempted": out.metrics.get("artifact_access_attempted"),
            "candidate_corrosion_validation": out.metrics.get("candidate_corrosion_validation"),
            "benchmark_score": out.metrics.get("benchmark_score"),
            "rights_cleared_benchmark_manifest_gate": out.gates.get("rights_cleared_benchmark_manifest"),
            "owned_candidate_evidence_gate": out.gates.get("owned_candidate_evidence"),
            "promotion_gate_passed_gate": out.gates.get("promotion_gate_passed"),
            "verified_model_artifact_gate": out.gates.get("verified_model_artifact"),
            "missing_inputs": out.missing_inputs,
            "authority_envelope_preserved": envelope_ok,
            "byte_stable_two_replay": byte_ok,
        }));
    }

    let n = n_scenarios.max(1) as f64;

    // Fail-closed probes.
    let mut ff_pass = 0_usize;
    let mut ff_probes: Vec<Value> = Vec::new();

    // Probe: wrong candidate_type (evidence_package)
    let wrong = CandidateEnvelope::from_value(json!({
        "candidate_id": "wrong-type",
        "candidate_type": "evidence_package",
        "evidence_refs": {"evidence_package": {}}
    })).unwrap();
    let is_err = cap.evaluate(&wrong, &features, &ctx).is_err();
    if is_err { ff_pass += 1; }
    ff_probes.push(json!({"probe": "candidate_type_evidence_package_rejected", "fail_closed": is_err}));

    // Probe: wrong candidate_type (molecule)
    let wrong_mol = CandidateEnvelope::from_value(json!({
        "candidate_id": "wrong-mol",
        "candidate_type": "molecule",
        "molecule": {"smiles": "C"}
    })).unwrap();
    let is_err = cap.evaluate(&wrong_mol, &features, &ctx).is_err();
    if is_err { ff_pass += 1; }
    ff_probes.push(json!({"probe": "candidate_type_molecule_rejected", "fail_closed": is_err}));

    // Probe: unsupported module_id descriptor
    let bad_descriptor: &'static ModuleDescriptor = Box::leak(Box::new(ModuleDescriptor {
        project: "amphora-does-not-exist".into(),
        authority_ceiling: "EVIDENCE_ONLY".into(),
        solver_use_ceiling: "DISABLED".into(),
        model_readiness_ceiling: "NOT_PROVEN".into(),
        ranking_eligible: false,
        candidate_types: vec!["formulation".into()],
        non_blocking_claim_locks: vec![],
        readiness: "GATED".into(),
    }));
    let bad_cap = FormulationCapability::new(bad_descriptor);
    let is_err = bad_cap.is_err();
    if is_err { ff_pass += 1; }
    ff_probes.push(json!({"probe": "unknown_descriptor_module_id_rejected", "fail_closed": is_err}));

    let ff_total = ff_probes.len();
    let ff_rate = ff_pass as f64 / ff_total.max(1) as f64;

    let kpi = json!({
        "runtime_status_insufficient_input_rate": {"observed": status_pass as f64 / n, "floor": 1.0, "direction": "MAXIMIZE", "sample_size": n_scenarios, "passed": status_pass as f64 / n >= 1.0},
        "evidence_scope_pinned_public_corrosion_benchmark_diagnostic_rate": {"observed": evidence_scope_pass as f64 / n, "floor": 1.0, "direction": "MAXIMIZE", "sample_size": n_scenarios, "passed": evidence_scope_pass as f64 / n >= 1.0},
        "artifact_rights_status_unresolved_rate": {"observed": rights_unresolved_pass as f64 / n, "floor": 1.0, "direction": "MAXIMIZE", "sample_size": n_scenarios, "passed": rights_unresolved_pass as f64 / n >= 1.0},
        "artifact_access_attempted_false_rate": {"observed": access_false_pass as f64 / n, "floor": 1.0, "direction": "MAXIMIZE", "sample_size": n_scenarios, "passed": access_false_pass as f64 / n >= 1.0},
        "candidate_corrosion_validation_false_rate": {"observed": validation_false_pass as f64 / n, "floor": 1.0, "direction": "MAXIMIZE", "sample_size": n_scenarios, "passed": validation_false_pass as f64 / n >= 1.0},
        "benchmark_score_null_rate": {"observed": score_null_pass as f64 / n, "floor": 1.0, "direction": "MAXIMIZE", "sample_size": n_scenarios, "passed": score_null_pass as f64 / n >= 1.0},
        "rights_cleared_benchmark_manifest_gate_false_rate": {"observed": manifest_gate_pass as f64 / n, "floor": 1.0, "direction": "MAXIMIZE", "sample_size": n_scenarios, "passed": manifest_gate_pass as f64 / n >= 1.0},
        "owned_candidate_evidence_gate_false_rate": {"observed": owned_gate_pass as f64 / n, "floor": 1.0, "direction": "MAXIMIZE", "sample_size": n_scenarios, "passed": owned_gate_pass as f64 / n >= 1.0},
        "promotion_gate_passed_false_rate": {"observed": promotion_gate_pass as f64 / n, "floor": 1.0, "direction": "MAXIMIZE", "sample_size": n_scenarios, "passed": promotion_gate_pass as f64 / n >= 1.0},
        "verified_model_artifact_gate_false_rate": {"observed": verified_gate_pass as f64 / n, "floor": 1.0, "direction": "MAXIMIZE", "sample_size": n_scenarios, "passed": verified_gate_pass as f64 / n >= 1.0},
        "missing_input_names_rights_cleared_manifest_rate": {"observed": missing_input_pass as f64 / n, "floor": 1.0, "direction": "MAXIMIZE", "sample_size": n_scenarios, "passed": missing_input_pass as f64 / n >= 1.0},
        "explanation_discloses_unresolved_rights_not_opened_rate": {"observed": explanation_pass as f64 / n, "floor": 1.0, "direction": "MAXIMIZE", "sample_size": n_scenarios, "passed": explanation_pass as f64 / n >= 1.0},
        "authority_envelope_preservation_rate": {"observed": envelope_pass as f64 / n, "floor": 1.0, "direction": "MAXIMIZE", "sample_size": n_scenarios, "passed": envelope_pass as f64 / n >= 1.0},
        "unsupported_input_fail_closed_rate": {"observed": ff_rate, "floor": 1.0, "direction": "MAXIMIZE", "probe_sample_size": ff_total, "probes": ff_probes, "passed": ff_rate >= 1.0},
        "byte_stable_two_replay_rate": {"observed": byte_replay_pass as f64 / n, "direction": "MAXIMIZE", "sample_size": n_scenarios, "note": "observational; public_corrosion_benchmark invoked twice per candidate produces byte-identical ModuleResult"},
    });

    let benchmark_lock_bytes = fs::read(benchmark_lock_path()).expect("benchmark-lock readable");
    let benchmark_lock_sha256 = file_sha256(&benchmark_lock_bytes);

    let diagnostic = json!({
        "schema": "amphora.module-phase0-benchmark-diagnostic.v1",
        "module_id": "amphora-public-corrosion-benchmark",
        "kpi": kpi.clone(),
        "records": per_scenario.clone(),
        "passed": kpi["runtime_status_insufficient_input_rate"]["passed"] == json!(true)
            && kpi["evidence_scope_pinned_public_corrosion_benchmark_diagnostic_rate"]["passed"] == json!(true)
            && kpi["artifact_rights_status_unresolved_rate"]["passed"] == json!(true)
            && kpi["artifact_access_attempted_false_rate"]["passed"] == json!(true)
            && kpi["candidate_corrosion_validation_false_rate"]["passed"] == json!(true)
            && kpi["benchmark_score_null_rate"]["passed"] == json!(true)
            && kpi["rights_cleared_benchmark_manifest_gate_false_rate"]["passed"] == json!(true)
            && kpi["owned_candidate_evidence_gate_false_rate"]["passed"] == json!(true)
            && kpi["promotion_gate_passed_false_rate"]["passed"] == json!(true)
            && kpi["verified_model_artifact_gate_false_rate"]["passed"] == json!(true)
            && kpi["missing_input_names_rights_cleared_manifest_rate"]["passed"] == json!(true)
            && kpi["explanation_discloses_unresolved_rights_not_opened_rate"]["passed"] == json!(true)
            && kpi["authority_envelope_preservation_rate"]["passed"] == json!(true)
            && kpi["unsupported_input_fail_closed_rate"]["passed"] == json!(true),
    });
    let diagnostic_bytes_canonical =
        serde_json::to_vec(&canonicalize(&diagnostic)).expect("canonical bytes");
    let diagnostic_sha256 = file_sha256(&diagnostic_bytes_canonical);

    let mut result = Map::new();
    result.insert("schema".into(), json!("amphora.module-phase0-benchmark-result.v1"));
    result.insert("module_id".into(), json!("amphora-public-corrosion-benchmark"));
    result.insert("benchmark_id".into(), json!("amphora-public-corrosion-benchmark-phase0-unresolved-rights-quarantine-v1"));
    result.insert("benchmark_lock_sha256".into(), json!(benchmark_lock_sha256));
    result.insert("dataset_fixture_sha256".into(), json!(benchmark_lock_sha256));
    result.insert(
        "dataset_fixture_note".into(),
        json!("public-corrosion-benchmark Phase-0 harness constructs its 5 formulation candidates + 3 fail-closed probes in-Rust and does not consume an external fixture. SHA-256 recorded is the on-disk benchmark-lock hash."),
    );
    result.insert("kpi".into(), kpi);
    result.insert("records".into(), json!(per_scenario));
    result.insert("benchmark_execution_complete".into(), json!(true));
    result.insert("first_replay".into(), json!({"diagnostic_receipt": diagnostic.clone(), "diagnostic_sha256": diagnostic_sha256}));
    result.insert("second_replay".into(), json!({"diagnostic_receipt": diagnostic, "diagnostic_sha256": diagnostic_sha256}));

    let _ = stable_hash(&Value::Null);
    let _: BTreeMap<String, Value> = BTreeMap::new();

    canonicalize(&Value::Object(result))
}

#[test]
fn public_corrosion_benchmark_phase0_kpi_report_is_deterministic_and_gates_pass() {
    let first = compute_report();
    let first_bytes = serde_json::to_vec(&first).expect("canonical");
    let second_bytes = serde_json::to_vec(&compute_report()).expect("canonical");
    assert_eq!(first_bytes, second_bytes, "KPI report is not byte-stable");

    let kpi = &first["kpi"];
    for gate in [
        "runtime_status_insufficient_input_rate",
        "evidence_scope_pinned_public_corrosion_benchmark_diagnostic_rate",
        "artifact_rights_status_unresolved_rate",
        "artifact_access_attempted_false_rate",
        "candidate_corrosion_validation_false_rate",
        "benchmark_score_null_rate",
        "rights_cleared_benchmark_manifest_gate_false_rate",
        "owned_candidate_evidence_gate_false_rate",
        "promotion_gate_passed_false_rate",
        "verified_model_artifact_gate_false_rate",
        "missing_input_names_rights_cleared_manifest_rate",
        "explanation_discloses_unresolved_rights_not_opened_rate",
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
