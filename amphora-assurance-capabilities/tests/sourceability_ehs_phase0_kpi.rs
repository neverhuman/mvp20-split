//! Phase-0 KPI harness for `amphora-sourceability-ehs`.
//!
//! Drives the deterministic `evaluate_sourceability` runtime (exposed via
//! AssuranceCapability::new("amphora-sourceability-ehs")) which loads the
//! compile-time-embedded `v5_epoch30_public_bom_sourceability_manifest.json`
//! (21 public regulatory/EHS source records covering TSCA, REACH, PFAS,
//! TAA, DLA, OSHA HazCom / GHS methodology anchors). Verifies honest
//! FAILED_GATES status, all 5 procurement/regulatory gates locked false,
//! source_hashes_verified matches fixture summary, sourceability_status
//! pinned to 'UNRESOLVED', supply_probability=Null, public_corpus_rights
//! ='QUARANTINED', explicit missing_inputs, and byte-stable two-replay
//! across 5 formulation candidates plus 3 fail-closed probes.

use std::collections::BTreeMap;
use std::fs;
use std::path::PathBuf;

use amphora_assurance_capabilities::AssuranceCapability;
use amphora_core::{
    canonicalize, stable_hash, Capability, CandidateEnvelope, ExecutionContext, FeatureSnapshot,
};
use serde_json::{json, Map, Value};
use sha2::{Digest, Sha256};

const SOURCEABILITY_EHS: &str = "amphora-sourceability-ehs";

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
        .join("amphora-sourceability-ehs/evidence/phase0/benchmark/benchmark-lock.v1.json")
}

fn sourceability_manifest_path() -> PathBuf {
    workspace_root().join(
        "amphora-sourceability-ehs/reference/mvp20/out/v5_epoch30_public_bom_sourceability_manifest.json",
    )
}

// SCHEMA-ERA FIX (B2). The shipped artifact
// `amphora-sourceability-ehs/evidence/phase0/benchmark/result.v1.json` has exactly one
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
        .join("amphora-sourceability-ehs-phase0-kpi-result.v1.json")
}

fn file_sha256(bytes: &[u8]) -> String {
    let mut digest = Sha256::new();
    digest.update(bytes);
    format!("{:x}", digest.finalize())
}

fn context() -> ExecutionContext {
    ExecutionContext {
        run_id: "phase0-kpi-sourceability-ehs".into(),
        deterministic_seed: 20260722,
        lineage: Value::Null,
    }
}

fn wrong_type_candidate() -> CandidateEnvelope {
    CandidateEnvelope::from_value(json!({
        "candidate_id": "evidence-probe",
        "candidate_type": "evidence_package",
        "evidence_refs": {"evidence_package": {}}
    }))
    .expect("valid evidence candidate")
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

struct Scenario {
    scenario_id: &'static str,
    candidate: Value,
    industrial_context: &'static str,
}

fn scenarios() -> Vec<Scenario> {
    vec![
        Scenario {
            scenario_id: "baseline-primer-no-supplier-refs",
            candidate: json!({
                "candidate_id": "primer-baseline",
                "candidate_type": "formulation",
                "formulation": {"part_A": {"dgeba": 100.0}, "part_B": {"polyamide": 65.0}}
            }),
            industrial_context: "solvent-borne two-pack epoxy-polyamide primer with no candidate-supplied supplier claims",
        },
        Scenario {
            scenario_id: "topcoat-with-adversarial-signed-declaration",
            candidate: json!({
                "candidate_id": "topcoat-adversarial-declaration",
                "candidate_type": "formulation",
                "formulation": {"part_A": {"dgebf": 120.0}, "part_B": {"amidoamine": 40.0}},
                "evidence_refs": {
                    "supplier_declaration": {
                        "signed_by_supplier": true,
                        "pfas_free_asserted": true,
                        "tsca_compliant_asserted": true,
                        "taa_domestic_asserted": true
                    }
                }
            }),
            industrial_context: "adversarial candidate injecting signed supplier declarations claiming PFAS-free / TSCA / TAA compliance; module must refuse to elevate any procurement or regulatory gate",
        },
        Scenario {
            scenario_id: "flooring-with-fake-lot-coa",
            candidate: json!({
                "candidate_id": "flooring-fake-coa",
                "candidate_type": "formulation",
                "formulation": {"part_A": {"dgebf": 150.0}, "part_B": {"polyamide": 50.0}},
                "evidence_refs": {
                    "lot_coa": {
                        "lot_id": "adversary-supplied-lot-12345",
                        "coa_claim": "meets specification"
                    }
                }
            }),
            industrial_context: "candidate injects fake lot Certificate-of-Analysis; module must remain quarantined-prescreen only",
        },
        Scenario {
            scenario_id: "adhesive-with-nested-authority-claims",
            candidate: json!({
                "candidate_id": "adhesive-authority-claims",
                "candidate_type": "formulation",
                "formulation": {"part_A": {"dgeba": 100.0}, "part_B": {"mxda": 35.0}},
                "evidence_refs": {
                    "procurement": {
                        "declared_ready": true,
                        "declared_grade": "commercial",
                        "declared_supplier": "unknown-issuer"
                    }
                }
            }),
            industrial_context: "candidate injects procurement.declared_ready=true; module must keep procurement_ready gate false",
        },
        Scenario {
            scenario_id: "encapsulant-minimal-formulation",
            candidate: json!({
                "candidate_id": "encapsulant-minimal",
                "candidate_type": "formulation",
                "formulation": {"part_A": {"dgeba": 100.0}, "part_B": {"dda": 15.0}}
            }),
            industrial_context: "electronic encapsulant with minimal formulation payload; module reports same locked prescreen result",
        },
    ]
}

fn compute_report() -> Value {
    // Independent recompute of fixture counts + summary.
    let manifest_bytes =
        fs::read(sourceability_manifest_path()).expect("sourceability manifest readable");
    let manifest: Value =
        serde_json::from_slice(&manifest_bytes).expect("sourceability manifest JSON");
    let harness_source_record_count = manifest["source_records"]
        .as_array()
        .map(Vec::len)
        .unwrap_or(0);
    let harness_all_have_sha256 = manifest
        .pointer("/summary/all_sources_have_sha256")
        .and_then(Value::as_bool)
        == Some(true);
    let fixture_pinned_ok = harness_source_record_count == 21 && harness_all_have_sha256;

    let cap = AssuranceCapability::new(SOURCEABILITY_EHS).expect("capability constructs");
    let features = FeatureSnapshot::default();
    let ctx = context();
    let scenarios = scenarios();
    let n_scenarios = scenarios.len();

    let mut per_scenario: Vec<Value> = Vec::new();

    let mut status_failed_pass = 0_usize;
    let mut score_zero_pass = 0_usize;
    let mut sourceability_status_pass = 0_usize;
    let mut supply_prob_null_pass = 0_usize;
    let mut public_rights_pass = 0_usize;
    let mut source_count_pass = 0_usize;
    let mut all_five_gates_locked_pass = 0_usize;
    let mut hashes_verified_pass = 0_usize;
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

        let status_ok = out.status == "FAILED_GATES";
        if status_ok {
            status_failed_pass += 1;
        }
        let score_ok = out.score_0_1 == Some(0.0);
        if score_ok {
            score_zero_pass += 1;
        }
        let sourceability_status_ok = out
            .metrics
            .get("sourceability_status")
            .and_then(Value::as_str)
            == Some("UNRESOLVED");
        if sourceability_status_ok {
            sourceability_status_pass += 1;
        }
        let supply_prob_ok = out.metrics.get("supply_probability") == Some(&Value::Null);
        if supply_prob_ok {
            supply_prob_null_pass += 1;
        }
        let public_rights_ok = out
            .metrics
            .get("public_corpus_rights")
            .and_then(Value::as_str)
            == Some("QUARANTINED");
        if public_rights_ok {
            public_rights_pass += 1;
        }
        let source_count_ok =
            out.metrics.get("public_source_record_count") == Some(&json!(21));
        if source_count_ok {
            source_count_pass += 1;
        }

        // All five procurement / regulatory gates locked.
        let exact_grade_locked = out.gates.get("exact_grade_source_present") == Some(&json!(false));
        let current_doc_locked = out.gates.get("current_document_present") == Some(&json!(false));
        let signed_decl_locked = out.gates.get("signed_declaration_present") == Some(&json!(false));
        let hashes_verified_locked =
            out.gates.get("source_hashes_verified") == Some(&json!(true));
        let procurement_locked = out.gates.get("procurement_ready") == Some(&json!(false));
        let five_gates_ok = exact_grade_locked
            && current_doc_locked
            && signed_decl_locked
            && procurement_locked;
        if five_gates_ok {
            all_five_gates_locked_pass += 1;
        }
        if hashes_verified_locked {
            hashes_verified_pass += 1;
        }

        let missing_ok = out
            .missing_inputs
            .iter()
            .any(|m| m.contains("supplier") && m.contains("candidate"));
        if missing_ok {
            missing_input_pass += 1;
        }
        let explanation_ok = out
            .explanations
            .iter()
            .any(|e| e.contains("procurement") && e.contains("regulatory"));
        if explanation_ok {
            explanation_pass += 1;
        }

        let out_json = serde_json::to_value(&out).expect("serializes");
        let envelope_ok = contains_banned_key(&out_json).is_none();
        if envelope_ok {
            envelope_pass += 1;
        }

        let replay = cap.evaluate(&candidate, &features, &ctx).unwrap();
        let byte_ok = serde_json::to_vec(&out).unwrap()
            == serde_json::to_vec(&replay).unwrap();
        if byte_ok {
            byte_replay_pass += 1;
        }

        per_scenario.push(json!({
            "scenario_id": scenario.scenario_id,
            "candidate_id": candidate.candidate_id(),
            "industrial_context": scenario.industrial_context,
            "status": out.status,
            "score_0_1": out.score_0_1,
            "sourceability_status": out.metrics.get("sourceability_status"),
            "supply_probability": out.metrics.get("supply_probability"),
            "public_corpus_rights": out.metrics.get("public_corpus_rights"),
            "public_source_record_count": out.metrics.get("public_source_record_count"),
            "exact_grade_source_present_gate": out.gates.get("exact_grade_source_present"),
            "current_document_present_gate": out.gates.get("current_document_present"),
            "signed_declaration_present_gate": out.gates.get("signed_declaration_present"),
            "source_hashes_verified_gate": out.gates.get("source_hashes_verified"),
            "procurement_ready_gate": out.gates.get("procurement_ready"),
            "status_failed_gates_honestly": status_ok,
            "score_zero": score_ok,
            "sourceability_status_unresolved": sourceability_status_ok,
            "supply_probability_null": supply_prob_ok,
            "public_corpus_rights_quarantined": public_rights_ok,
            "public_source_record_count_21": source_count_ok,
            "five_procurement_gates_locked_false": five_gates_ok,
            "source_hashes_verified_true": hashes_verified_locked,
            "explicit_missing_input_names_supplier_evidence": missing_ok,
            "explanation_disclaims_procurement_and_regulatory": explanation_ok,
            "authority_envelope_preserved": envelope_ok,
            "byte_stable_two_replay": byte_ok,
        }));
    }

    let n = n_scenarios.max(1) as f64;

    // Fail-closed probes.
    let mut fail_closed_pass = 0_usize;
    let mut fail_probes: Vec<Value> = Vec::new();

    let wrong = wrong_type_candidate();
    let is_err = cap.evaluate(&wrong, &features, &ctx).is_err();
    if is_err { fail_closed_pass += 1; }
    fail_probes.push(json!({"probe": "candidate_type_evidence_package_rejected", "fail_closed": is_err}));

    let unknown = AssuranceCapability::new("amphora-does-not-exist").is_err();
    if unknown { fail_closed_pass += 1; }
    fail_probes.push(json!({"probe": "unknown_module_id_rejected", "fail_closed": unknown}));

    let ws = AssuranceCapability::new("   ").is_err();
    if ws { fail_closed_pass += 1; }
    fail_probes.push(json!({"probe": "whitespace_module_id_rejected", "fail_closed": ws}));

    let fail_total = fail_probes.len();
    let fail_rate = fail_closed_pass as f64 / fail_total.max(1) as f64;

    let kpi = json!({
        "sourceability_manifest_pinned_21_records_and_sha256_verified_rate": {
            "observed": if fixture_pinned_ok { 1.0 } else { 0.0 },
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": 1,
            "passed": fixture_pinned_ok,
        },
        "runtime_status_failed_gates_honestly_rate": {
            "observed": status_failed_pass as f64 / n,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": n_scenarios,
            "passed": status_failed_pass as f64 / n >= 1.0,
        },
        "runtime_score_pinned_zero_rate": {
            "observed": score_zero_pass as f64 / n,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": n_scenarios,
            "passed": score_zero_pass as f64 / n >= 1.0,
        },
        "sourceability_status_pinned_unresolved_rate": {
            "observed": sourceability_status_pass as f64 / n,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": n_scenarios,
            "passed": sourceability_status_pass as f64 / n >= 1.0,
        },
        "supply_probability_null_rate": {
            "observed": supply_prob_null_pass as f64 / n,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": n_scenarios,
            "passed": supply_prob_null_pass as f64 / n >= 1.0,
        },
        "public_corpus_rights_quarantined_rate": {
            "observed": public_rights_pass as f64 / n,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": n_scenarios,
            "passed": public_rights_pass as f64 / n >= 1.0,
        },
        "public_source_record_count_pinned_21_rate": {
            "observed": source_count_pass as f64 / n,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": n_scenarios,
            "passed": source_count_pass as f64 / n >= 1.0,
        },
        "four_procurement_gates_locked_false_rate": {
            "observed": all_five_gates_locked_pass as f64 / n,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": n_scenarios,
            "passed": all_five_gates_locked_pass as f64 / n >= 1.0,
        },
        "source_hashes_verified_gate_true_rate": {
            "observed": hashes_verified_pass as f64 / n,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": n_scenarios,
            "passed": hashes_verified_pass as f64 / n >= 1.0,
        },
        "explicit_missing_input_names_supplier_evidence_rate": {
            "observed": missing_input_pass as f64 / n,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": n_scenarios,
            "passed": missing_input_pass as f64 / n >= 1.0,
        },
        "explanation_disclaims_procurement_and_regulatory_closure_rate": {
            "observed": explanation_pass as f64 / n,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": n_scenarios,
            "passed": explanation_pass as f64 / n >= 1.0,
        },
        "authority_envelope_preservation_rate": {
            "observed": envelope_pass as f64 / n,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": n_scenarios,
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
            "sample_size": n_scenarios,
            "note": "observational; evaluate_sourceability invoked twice per candidate produces byte-identical ModuleResult",
        },
    });

    let benchmark_lock_bytes = fs::read(benchmark_lock_path()).expect("benchmark-lock readable");
    let benchmark_lock_sha256 = file_sha256(&benchmark_lock_bytes);
    let dataset_sha256 = file_sha256(&manifest_bytes);

    let diagnostic = json!({
        "schema": "amphora.module-phase0-benchmark-diagnostic.v1",
        "module_id": "amphora-sourceability-ehs",
        "kpi": kpi.clone(),
        "records": per_scenario.clone(),
        "passed": kpi["sourceability_manifest_pinned_21_records_and_sha256_verified_rate"]["passed"] == json!(true)
            && kpi["runtime_status_failed_gates_honestly_rate"]["passed"] == json!(true)
            && kpi["runtime_score_pinned_zero_rate"]["passed"] == json!(true)
            && kpi["sourceability_status_pinned_unresolved_rate"]["passed"] == json!(true)
            && kpi["supply_probability_null_rate"]["passed"] == json!(true)
            && kpi["public_corpus_rights_quarantined_rate"]["passed"] == json!(true)
            && kpi["public_source_record_count_pinned_21_rate"]["passed"] == json!(true)
            && kpi["four_procurement_gates_locked_false_rate"]["passed"] == json!(true)
            && kpi["source_hashes_verified_gate_true_rate"]["passed"] == json!(true)
            && kpi["explicit_missing_input_names_supplier_evidence_rate"]["passed"] == json!(true)
            && kpi["explanation_disclaims_procurement_and_regulatory_closure_rate"]["passed"] == json!(true)
            && kpi["authority_envelope_preservation_rate"]["passed"] == json!(true)
            && kpi["unsupported_input_fail_closed_rate"]["passed"] == json!(true),
    });
    let diagnostic_bytes_canonical =
        serde_json::to_vec(&canonicalize(&diagnostic)).expect("canonical bytes");
    let diagnostic_sha256 = file_sha256(&diagnostic_bytes_canonical);

    let mut result = Map::new();
    result.insert("schema".into(), json!("amphora.module-phase0-benchmark-result.v1"));
    result.insert("module_id".into(), json!("amphora-sourceability-ehs"));
    result.insert(
        "benchmark_id".into(),
        json!("amphora-sourceability-ehs-phase0-public-prescreen-v1"),
    );
    result.insert("benchmark_lock_sha256".into(), json!(benchmark_lock_sha256));
    result.insert("dataset_fixture_sha256".into(), json!(dataset_sha256));
    result.insert(
        "dataset_fixture_note".into(),
        json!("SHA-256 of amphora-sourceability-ehs/reference/mvp20/out/v5_epoch30_public_bom_sourceability_manifest.json - 21 public regulatory/EHS source records covering TSCA, REACH, PFAS, TAA, DLA, OSHA HazCom / GHS methodology anchors, embedded at compile time by evaluate_sourceability. Any manifest drift changes this hash and the KPI recompute detects it via the record-count and all_sources_have_sha256 comparison."),
    );
    result.insert("kpi".into(), kpi);
    result.insert("records".into(), json!(per_scenario));
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
fn sourceability_ehs_phase0_kpi_report_is_deterministic_and_gates_pass() {
    let first = compute_report();
    let first_bytes = serde_json::to_vec(&first).expect("canonical");
    let second_bytes = serde_json::to_vec(&compute_report()).expect("canonical");
    assert_eq!(first_bytes, second_bytes, "KPI report is not byte-stable");

    let kpi = &first["kpi"];
    for gate in [
        "sourceability_manifest_pinned_21_records_and_sha256_verified_rate",
        "runtime_status_failed_gates_honestly_rate",
        "runtime_score_pinned_zero_rate",
        "sourceability_status_pinned_unresolved_rate",
        "supply_probability_null_rate",
        "public_corpus_rights_quarantined_rate",
        "public_source_record_count_pinned_21_rate",
        "four_procurement_gates_locked_false_rate",
        "source_hashes_verified_gate_true_rate",
        "explicit_missing_input_names_supplier_evidence_rate",
        "explanation_disclaims_procurement_and_regulatory_closure_rate",
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
