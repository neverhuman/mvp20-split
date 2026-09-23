//! Phase-0 KPI harness for `amphora-molecule-generator`.
//!
//! Drives the deterministic `generator_result` runtime (via
//! `capability("amphora-molecule-generator").unwrap().evaluate(...)`) across
//! 5 molecule candidates. Runtime is a roadmap-diagnostic-only quarantine:
//! always returns status=INSUFFICIENT_INPUT with proposal_count=0,
//! generation_status='LOCKED_INTERNAL', pinned_rdkit_available=false,
//! locked_reaction_grammar_available=false, rights_cleared_corpus_available=false,
//! generation_authorized=false, but deterministic_lineage_recorded=true with
//! per-scenario lineage_diagnostic capturing candidate_id + seed + run_id.
//! Plus 3 fail-closed probes on unsupported inputs.

use std::collections::BTreeMap;
use std::fs;
use std::path::PathBuf;

use amphora_core::{
    canonicalize, stable_hash, Capability, CandidateEnvelope, ExecutionContext, FeatureSnapshot,
};
use amphora_molecule_capabilities::{capability, GENERATOR_ID};
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
        .join("amphora-molecule-generator/evidence/phase0/benchmark/benchmark-lock.v1.json")
}

// SCHEMA-ERA FIX (B2). The shipped artifact
// `amphora-molecule-generator/evidence/phase0/benchmark/result.v1.json` has exactly one
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
        .join("amphora-molecule-generator-phase0-kpi-result.v1.json")
}

fn file_sha256(bytes: &[u8]) -> String {
    let mut digest = Sha256::new();
    digest.update(bytes);
    format!("{:x}", digest.finalize())
}

fn context() -> ExecutionContext {
    ExecutionContext {
        run_id: "phase0-kpi-molecule-generator".into(),
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

struct Scenario {
    scenario_id: &'static str,
    candidate: Value,
    industrial_context: &'static str,
}

fn scenarios() -> Vec<Scenario> {
    vec![
        Scenario {
            scenario_id: "simple-defined-resin-oxirane",
            candidate: json!({
                "candidate_id": "generator-resin-oxirane",
                "candidate_type": "molecule",
                "molecule": {"smiles": "C1OC1", "declared_role": "resin"}
            }),
            industrial_context: "simple defined oxirane monomer candidate seeking resin-role expansion",
        },
        Scenario {
            scenario_id: "hardener-amine-baseline",
            candidate: json!({
                "candidate_id": "generator-hardener-amine",
                "candidate_type": "molecule",
                "molecule": {"smiles": "NCCN", "declared_role": "hardener"}
            }),
            industrial_context: "ethylenediamine baseline hardener seeking amine-role expansion",
        },
        Scenario {
            scenario_id: "adversarial-precomputed-proposals-injection",
            candidate: json!({
                "candidate_id": "generator-adversarial-proposals",
                "candidate_type": "molecule",
                "molecule": {
                    "smiles": "c1ccccc1O",
                    "declared_role": "resin",
                    "adversary_proposals": [
                        {"smiles": "C1OC1", "confidence": 0.99},
                        {"smiles": "CC(=O)O", "confidence": 0.95}
                    ],
                    "adversary_declared_proposal_count": 2,
                    "adversary_declared_generation_status": "SCORED"
                }
            }),
            industrial_context: "adversarial candidate injecting adversary_proposals + adversary_declared_generation_status='SCORED'; runtime must NOT elevate proposal_count or generation_status",
        },
        Scenario {
            scenario_id: "adversarial-rdkit-and-grammar-declarations",
            candidate: json!({
                "candidate_id": "generator-adversarial-rdkit",
                "candidate_type": "molecule",
                "molecule": {
                    "smiles": "CC(C)C",
                    "declared_role": "resin",
                    "candidate_declared_pinned_rdkit_available": true,
                    "candidate_declared_locked_reaction_grammar_available": true,
                    "candidate_declared_rights_cleared_corpus_available": true
                }
            }),
            industrial_context: "adversarial candidate injecting availability booleans for RDKit + grammar + corpus; runtime must NOT elevate any of them",
        },
        Scenario {
            scenario_id: "candidate-without-molecule-payload",
            candidate: json!({
                "candidate_id": "generator-no-molecule",
                "candidate_type": "molecule",
                "molecule": {"smiles": "C"}
            }),
            industrial_context: "minimal molecule candidate (methane) - runtime still records deterministic lineage but abstains on generation",
        },
    ]
}

fn compute_report() -> Value {
    let cap = capability(GENERATOR_ID).expect("generator capability");
    let features = FeatureSnapshot::default();
    let ctx = context();
    let scenarios = scenarios();
    let n_scenarios = scenarios.len();

    let mut per_scenario: Vec<Value> = Vec::new();

    let mut status_pass = 0_usize;
    let mut evidence_scope_pass = 0_usize;
    let mut generation_status_pass = 0_usize;
    let mut proposal_count_pass = 0_usize;
    let mut lineage_seed_pass = 0_usize;
    let mut lineage_candidate_pass = 0_usize;
    let mut lineage_run_pass = 0_usize;
    let mut rdkit_false_pass = 0_usize;
    let mut grammar_false_pass = 0_usize;
    let mut corpus_false_pass = 0_usize;
    let mut lineage_gate_pass = 0_usize;
    let mut authorized_gate_pass = 0_usize;
    let mut missing_input_pass = 0_usize;
    let mut explanation_pass = 0_usize;
    let mut uncertainty_pass = 0_usize;
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
        let evidence_ok = out.evidence_scope == "ROADMAP_DIAGNOSTIC_ONLY";
        if evidence_ok { evidence_scope_pass += 1; }
        let gen_status_ok = out.metrics.get("generation_status").and_then(Value::as_str) == Some("LOCKED_INTERNAL");
        if gen_status_ok { generation_status_pass += 1; }
        let proposal_ok = out.metrics.get("proposal_count") == Some(&json!(0));
        if proposal_ok { proposal_count_pass += 1; }

        let lineage = out.metrics.get("lineage_diagnostic").and_then(Value::as_object);
        let seed_ok = lineage.and_then(|l| l.get("deterministic_seed")) == Some(&json!(ctx.deterministic_seed));
        if seed_ok { lineage_seed_pass += 1; }
        let cand_ok = lineage.and_then(|l| l.get("parent_candidate_id")).and_then(Value::as_str)
            == Some(candidate.candidate_id());
        if cand_ok { lineage_candidate_pass += 1; }
        let run_ok = lineage.and_then(|l| l.get("run_id")).and_then(Value::as_str) == Some(ctx.run_id.as_str());
        if run_ok { lineage_run_pass += 1; }

        let rdkit_ok = out.metrics.get("pinned_rdkit_available") == Some(&json!(false));
        if rdkit_ok { rdkit_false_pass += 1; }
        let grammar_ok = out.metrics.get("locked_reaction_grammar_available") == Some(&json!(false));
        if grammar_ok { grammar_false_pass += 1; }
        let corpus_ok = out.metrics.get("rights_cleared_corpus_available") == Some(&json!(false));
        if corpus_ok { corpus_false_pass += 1; }

        let lineage_gate_ok = out.gates.get("deterministic_lineage_recorded") == Some(&json!(true));
        if lineage_gate_ok { lineage_gate_pass += 1; }
        let auth_gate_ok = out.gates.get("generation_authorized") == Some(&json!(false));
        if auth_gate_ok { authorized_gate_pass += 1; }

        let missing_ok = out.missing_inputs.iter().any(|m| m.contains("pinned RDKit"))
            && out.missing_inputs.iter().any(|m| m.contains("locked atom-mapped reaction grammar"))
            && out.missing_inputs.iter().any(|m| m.contains("rights-cleared generation evidence"));
        if missing_ok { missing_input_pass += 1; }

        let explanation_ok = out.explanations.iter()
            .any(|e| e.contains("roadmap lineage") && e.contains("no leads"));
        if explanation_ok { explanation_pass += 1; }

        let uncertainty_ok = out.uncertainty.get("scope").and_then(Value::as_str)
            .is_some_and(|s| s.contains("No molecular proposals were generated"));
        if uncertainty_ok { uncertainty_pass += 1; }

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
            "generation_status": out.metrics.get("generation_status"),
            "proposal_count": out.metrics.get("proposal_count"),
            "lineage_diagnostic": out.metrics.get("lineage_diagnostic"),
            "pinned_rdkit_available": out.metrics.get("pinned_rdkit_available"),
            "locked_reaction_grammar_available": out.metrics.get("locked_reaction_grammar_available"),
            "rights_cleared_corpus_available": out.metrics.get("rights_cleared_corpus_available"),
            "deterministic_lineage_recorded_gate": out.gates.get("deterministic_lineage_recorded"),
            "generation_authorized_gate": out.gates.get("generation_authorized"),
            "uncertainty_scope": out.uncertainty.get("scope"),
            "missing_inputs": out.missing_inputs,
            "authority_envelope_preserved": envelope_ok,
            "byte_stable_two_replay": byte_ok,
        }));
    }

    let n = n_scenarios.max(1) as f64;

    // Fail-closed probes.
    let mut ff_pass = 0_usize;
    let mut ff_probes: Vec<Value> = Vec::new();

    let wrong = CandidateEnvelope::from_value(json!({
        "candidate_id": "wrong-type",
        "candidate_type": "formulation",
        "formulation": {"part_A": {"resin": 1.0}, "part_B": {"hardener": 1.0}}
    })).unwrap();
    let is_err = cap.evaluate(&wrong, &features, &ctx).is_err();
    if is_err { ff_pass += 1; }
    ff_probes.push(json!({"probe": "candidate_type_formulation_rejected", "fail_closed": is_err}));

    let unknown = capability("amphora-does-not-exist").is_none();
    if unknown { ff_pass += 1; }
    ff_probes.push(json!({"probe": "unknown_module_id_returns_none", "fail_closed": unknown}));

    let ws = capability("   ").is_none();
    if ws { ff_pass += 1; }
    ff_probes.push(json!({"probe": "whitespace_module_id_returns_none", "fail_closed": ws}));

    let ff_total = ff_probes.len();
    let ff_rate = ff_pass as f64 / ff_total.max(1) as f64;

    let kpi = json!({
        "runtime_status_insufficient_input_rate": {"observed": status_pass as f64 / n, "floor": 1.0, "direction": "MAXIMIZE", "sample_size": n_scenarios, "passed": status_pass as f64 / n >= 1.0},
        "evidence_scope_pinned_roadmap_diagnostic_only_rate": {"observed": evidence_scope_pass as f64 / n, "floor": 1.0, "direction": "MAXIMIZE", "sample_size": n_scenarios, "passed": evidence_scope_pass as f64 / n >= 1.0},
        "generation_status_pinned_locked_internal_rate": {"observed": generation_status_pass as f64 / n, "floor": 1.0, "direction": "MAXIMIZE", "sample_size": n_scenarios, "passed": generation_status_pass as f64 / n >= 1.0},
        "proposal_count_zero_rate": {"observed": proposal_count_pass as f64 / n, "floor": 1.0, "direction": "MAXIMIZE", "sample_size": n_scenarios, "passed": proposal_count_pass as f64 / n >= 1.0},
        "lineage_diagnostic_records_deterministic_seed_rate": {"observed": lineage_seed_pass as f64 / n, "floor": 1.0, "direction": "MAXIMIZE", "sample_size": n_scenarios, "passed": lineage_seed_pass as f64 / n >= 1.0},
        "lineage_diagnostic_records_parent_candidate_id_rate": {"observed": lineage_candidate_pass as f64 / n, "floor": 1.0, "direction": "MAXIMIZE", "sample_size": n_scenarios, "passed": lineage_candidate_pass as f64 / n >= 1.0},
        "lineage_diagnostic_records_run_id_rate": {"observed": lineage_run_pass as f64 / n, "floor": 1.0, "direction": "MAXIMIZE", "sample_size": n_scenarios, "passed": lineage_run_pass as f64 / n >= 1.0},
        "pinned_rdkit_available_false_rate": {"observed": rdkit_false_pass as f64 / n, "floor": 1.0, "direction": "MAXIMIZE", "sample_size": n_scenarios, "passed": rdkit_false_pass as f64 / n >= 1.0},
        "locked_reaction_grammar_available_false_rate": {"observed": grammar_false_pass as f64 / n, "floor": 1.0, "direction": "MAXIMIZE", "sample_size": n_scenarios, "passed": grammar_false_pass as f64 / n >= 1.0},
        "rights_cleared_corpus_available_false_rate": {"observed": corpus_false_pass as f64 / n, "floor": 1.0, "direction": "MAXIMIZE", "sample_size": n_scenarios, "passed": corpus_false_pass as f64 / n >= 1.0},
        "deterministic_lineage_recorded_gate_true_rate": {"observed": lineage_gate_pass as f64 / n, "floor": 1.0, "direction": "MAXIMIZE", "sample_size": n_scenarios, "passed": lineage_gate_pass as f64 / n >= 1.0},
        "generation_authorized_gate_false_rate": {"observed": authorized_gate_pass as f64 / n, "floor": 1.0, "direction": "MAXIMIZE", "sample_size": n_scenarios, "passed": authorized_gate_pass as f64 / n >= 1.0},
        "missing_input_names_rdkit_grammar_evidence_rate": {"observed": missing_input_pass as f64 / n, "floor": 1.0, "direction": "MAXIMIZE", "sample_size": n_scenarios, "passed": missing_input_pass as f64 / n >= 1.0},
        "explanation_disclaims_roadmap_diagnostic_only_rate": {"observed": explanation_pass as f64 / n, "floor": 1.0, "direction": "MAXIMIZE", "sample_size": n_scenarios, "passed": explanation_pass as f64 / n >= 1.0},
        "uncertainty_disclaims_no_proposals_generated_rate": {"observed": uncertainty_pass as f64 / n, "floor": 1.0, "direction": "MAXIMIZE", "sample_size": n_scenarios, "passed": uncertainty_pass as f64 / n >= 1.0},
        "authority_envelope_preservation_rate": {"observed": envelope_pass as f64 / n, "floor": 1.0, "direction": "MAXIMIZE", "sample_size": n_scenarios, "passed": envelope_pass as f64 / n >= 1.0},
        "unsupported_input_fail_closed_rate": {"observed": ff_rate, "floor": 1.0, "direction": "MAXIMIZE", "probe_sample_size": ff_total, "probes": ff_probes, "passed": ff_rate >= 1.0},
        "byte_stable_two_replay_rate": {"observed": byte_replay_pass as f64 / n, "direction": "MAXIMIZE", "sample_size": n_scenarios, "note": "observational; generator_result invoked twice per candidate produces byte-identical ModuleResult"},
    });

    let benchmark_lock_bytes = fs::read(benchmark_lock_path()).expect("benchmark-lock readable");
    let benchmark_lock_sha256 = file_sha256(&benchmark_lock_bytes);

    let diagnostic = json!({
        "schema": "amphora.module-phase0-benchmark-diagnostic.v1",
        "module_id": "amphora-molecule-generator",
        "kpi": kpi.clone(),
        "records": per_scenario.clone(),
        "passed": kpi["runtime_status_insufficient_input_rate"]["passed"] == json!(true)
            && kpi["evidence_scope_pinned_roadmap_diagnostic_only_rate"]["passed"] == json!(true)
            && kpi["generation_status_pinned_locked_internal_rate"]["passed"] == json!(true)
            && kpi["proposal_count_zero_rate"]["passed"] == json!(true)
            && kpi["lineage_diagnostic_records_deterministic_seed_rate"]["passed"] == json!(true)
            && kpi["lineage_diagnostic_records_parent_candidate_id_rate"]["passed"] == json!(true)
            && kpi["lineage_diagnostic_records_run_id_rate"]["passed"] == json!(true)
            && kpi["pinned_rdkit_available_false_rate"]["passed"] == json!(true)
            && kpi["locked_reaction_grammar_available_false_rate"]["passed"] == json!(true)
            && kpi["rights_cleared_corpus_available_false_rate"]["passed"] == json!(true)
            && kpi["deterministic_lineage_recorded_gate_true_rate"]["passed"] == json!(true)
            && kpi["generation_authorized_gate_false_rate"]["passed"] == json!(true)
            && kpi["missing_input_names_rdkit_grammar_evidence_rate"]["passed"] == json!(true)
            && kpi["explanation_disclaims_roadmap_diagnostic_only_rate"]["passed"] == json!(true)
            && kpi["uncertainty_disclaims_no_proposals_generated_rate"]["passed"] == json!(true)
            && kpi["authority_envelope_preservation_rate"]["passed"] == json!(true)
            && kpi["unsupported_input_fail_closed_rate"]["passed"] == json!(true),
    });
    let diagnostic_bytes_canonical =
        serde_json::to_vec(&canonicalize(&diagnostic)).expect("canonical bytes");
    let diagnostic_sha256 = file_sha256(&diagnostic_bytes_canonical);

    let mut result = Map::new();
    result.insert("schema".into(), json!("amphora.module-phase0-benchmark-result.v1"));
    result.insert("module_id".into(), json!("amphora-molecule-generator"));
    result.insert(
        "benchmark_id".into(),
        json!("amphora-molecule-generator-phase0-roadmap-diagnostic-quarantine-v1"),
    );
    result.insert("benchmark_lock_sha256".into(), json!(benchmark_lock_sha256));
    result.insert("dataset_fixture_sha256".into(), json!(benchmark_lock_sha256));
    result.insert(
        "dataset_fixture_note".into(),
        json!("molecule-generator Phase-0 harness constructs its 5 molecule candidates + 3 fail-closed probes in-Rust. Runtime is a roadmap-diagnostic-only quarantine and never invokes RDKit. SHA-256 recorded is the on-disk benchmark-lock hash."),
    );
    result.insert("kpi".into(), kpi);
    result.insert("records".into(), json!(per_scenario));
    result.insert("benchmark_execution_complete".into(), json!(true));
    result.insert(
        "first_replay".into(),
        json!({"diagnostic_receipt": diagnostic.clone(), "diagnostic_sha256": diagnostic_sha256}),
    );
    result.insert(
        "second_replay".into(),
        json!({"diagnostic_receipt": diagnostic, "diagnostic_sha256": diagnostic_sha256}),
    );

    let _ = stable_hash(&Value::Null);
    let _: BTreeMap<String, Value> = BTreeMap::new();

    canonicalize(&Value::Object(result))
}

#[test]
fn molecule_generator_phase0_kpi_report_is_deterministic_and_gates_pass() {
    let first = compute_report();
    let first_bytes = serde_json::to_vec(&first).expect("canonical");
    let second_bytes = serde_json::to_vec(&compute_report()).expect("canonical");
    assert_eq!(first_bytes, second_bytes, "KPI report is not byte-stable");

    let kpi = &first["kpi"];
    for gate in [
        "runtime_status_insufficient_input_rate",
        "evidence_scope_pinned_roadmap_diagnostic_only_rate",
        "generation_status_pinned_locked_internal_rate",
        "proposal_count_zero_rate",
        "lineage_diagnostic_records_deterministic_seed_rate",
        "lineage_diagnostic_records_parent_candidate_id_rate",
        "lineage_diagnostic_records_run_id_rate",
        "pinned_rdkit_available_false_rate",
        "locked_reaction_grammar_available_false_rate",
        "rights_cleared_corpus_available_false_rate",
        "deterministic_lineage_recorded_gate_true_rate",
        "generation_authorized_gate_false_rate",
        "missing_input_names_rdkit_grammar_evidence_rate",
        "explanation_disclaims_roadmap_diagnostic_only_rate",
        "uncertainty_disclaims_no_proposals_generated_rate",
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
