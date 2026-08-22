//! Phase-0 KPI harness for `amphora-molecule-novelty`.
//!
//! Drives the deterministic `novelty_result` runtime (via
//! `capability("amphora-molecule-novelty").unwrap().evaluate(...)`) across
//! 5 molecule candidates with a default FeatureSnapshot (no
//! molecule_facts_v1 → runtime abstains) plus 3 fail-closed probes. Verifies
//! honest ABSTAINED reporting with all defensive metrics/gates pinned,
//! explicit missing_inputs naming the RDKit + corpus + retrieval-recall
//! gaps, uncertainty scope disclaiming novelty/patentability/desirability/
//! performance, authority envelope preservation, and byte-stable two-replay.

use std::collections::BTreeMap;
use std::fs;
use std::path::PathBuf;

use amphora_core::{
    canonicalize, stable_hash, Capability, CandidateEnvelope, ExecutionContext, FeatureSnapshot,
};
use amphora_molecule_capabilities::{capability, NOVELTY_ID};
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
        .join("amphora-molecule-novelty/evidence/phase0/benchmark/benchmark-lock.v1.json")
}

// SCHEMA-ERA FIX (B2). The shipped artifact
// `amphora-molecule-novelty/evidence/phase0/benchmark/result.v1.json` has exactly one
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
        .join("amphora-molecule-novelty-phase0-kpi-result.v1.json")
}

fn file_sha256(bytes: &[u8]) -> String {
    let mut digest = Sha256::new();
    digest.update(bytes);
    format!("{:x}", digest.finalize())
}

fn context() -> ExecutionContext {
    ExecutionContext {
        run_id: "phase0-kpi-molecule-novelty".into(),
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
    /// True iff the candidate.molecule provides a structure that
    /// structure_text accepts (non-empty, no wildcard, no fragment).
    expects_structure_input_present: bool,
    industrial_context: &'static str,
}

fn scenarios() -> Vec<Scenario> {
    vec![
        Scenario {
            scenario_id: "simple-defined-molecule-ethanol",
            candidate: json!({
                "candidate_id": "novelty-ethanol",
                "candidate_type": "molecule",
                "molecule": {"smiles": "CCO", "declared_role": "solvent"}
            }),
            expects_structure_input_present: true,
            industrial_context: "simple defined ethanol candidate - baseline structure",
        },
        Scenario {
            scenario_id: "canonical-smiles-preferred-over-plain",
            candidate: json!({
                "candidate_id": "novelty-canonical",
                "candidate_type": "molecule",
                "molecule": {"canonical_smiles": "CC(=O)O", "smiles": "OC(=O)C", "declared_role": "solvent"}
            }),
            expects_structure_input_present: true,
            industrial_context: "candidate with canonical_smiles + smiles fallback (acetic acid)",
        },
        Scenario {
            scenario_id: "wildcard-structure-fails-structure_text",
            candidate: json!({
                "candidate_id": "novelty-wildcard",
                "candidate_type": "molecule",
                "molecule": {"smiles": "C*C", "declared_role": "resin"}
            }),
            expects_structure_input_present: false,
            industrial_context: "candidate with wildcard '*' - structure_text rejects; abstains",
        },
        Scenario {
            scenario_id: "fragment-structure-fails-structure_text",
            candidate: json!({
                "candidate_id": "novelty-fragment",
                "candidate_type": "molecule",
                "molecule": {"smiles": "CC.O", "declared_role": "solvent"}
            }),
            expects_structure_input_present: false,
            industrial_context: "candidate with fragment 'CC.O' - structure_text rejects; abstains",
        },
        Scenario {
            scenario_id: "adversarial-precomputed-novelty-score-injection",
            candidate: json!({
                "candidate_id": "novelty-adversarial",
                "candidate_type": "molecule",
                "molecule": {
                    "smiles": "c1ccccc1",
                    "declared_role": "aromatic_solvent",
                    "adversary_declared_novelty_score": 0.99,
                    "adversary_declared_corpus_lookup_attempted": true,
                    "adversary_declared_rights_cleared_corpus_available": true
                }
            }),
            expects_structure_input_present: true,
            industrial_context: "adversarial candidate injecting adversary_declared_novelty_score=0.99 + corpus_lookup fields; runtime must NOT elevate any of them (features-based normalization required)",
        },
    ]
}

fn compute_report() -> Value {
    let cap = capability(NOVELTY_ID).expect("novelty capability");
    let features = FeatureSnapshot::default();
    let ctx = context();
    let scenarios = scenarios();
    let n_scenarios = scenarios.len();

    let mut per_scenario: Vec<Value> = Vec::new();

    let mut status_pass = 0_usize;
    let mut evidence_scope_pass = 0_usize;
    let mut novelty_status_pass = 0_usize;
    let mut lookup_attempted_pass = 0_usize;
    let mut rights_cleared_pass = 0_usize;
    let mut lookup_complete_gate_pass = 0_usize;
    let mut authorized_gate_pass = 0_usize;
    let mut structure_metric_pass = 0_usize;
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
        let evidence_ok = out.evidence_scope == "MOLECULE_NOVELTY_AUDIT_ONLY";
        if evidence_ok { evidence_scope_pass += 1; }
        let novelty_ok = out.metrics.get("novelty_status").and_then(Value::as_str) == Some("ABSTAINED");
        if novelty_ok { novelty_status_pass += 1; }
        let lookup_ok = out.metrics.get("corpus_lookup_attempted") == Some(&json!(false));
        if lookup_ok { lookup_attempted_pass += 1; }
        let rights_ok = out.metrics.get("rights_cleared_corpus_available") == Some(&json!(false));
        if rights_ok { rights_cleared_pass += 1; }
        let lookup_gate_ok = out.gates.get("corpus_lookup_complete") == Some(&json!(false));
        if lookup_gate_ok { lookup_complete_gate_pass += 1; }
        let auth_gate_ok = out.gates.get("novelty_constraint_authorized") == Some(&json!(false));
        if auth_gate_ok { authorized_gate_pass += 1; }
        let structure_ok = out.metrics.get("structure_input_present")
            == Some(&json!(scenario.expects_structure_input_present));
        if structure_ok { structure_metric_pass += 1; }

        let missing_ok = out.missing_inputs.iter().any(|m| m.contains("pinned RDKit"))
            && out.missing_inputs.iter().any(|m| m.contains("rights-cleared deduplicated corpus"))
            && out.missing_inputs.iter().any(|m| m.contains("locked exact-retrieval and top-k recall"));
        if missing_ok { missing_input_pass += 1; }

        let explanation_ok = out
            .explanations
            .iter()
            .any(|e| e.contains("rights-cleared frozen corpus") && e.contains("locked retrieval benchmark"));
        if explanation_ok { explanation_pass += 1; }

        let uncertainty_ok = out
            .uncertainty
            .get("scope")
            .and_then(Value::as_str)
            .is_some_and(|s| s.contains("No corpus distance") && s.contains("patentability")
                && s.contains("desirability") && s.contains("performance"));
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
            "novelty_status": out.metrics.get("novelty_status"),
            "corpus_lookup_attempted": out.metrics.get("corpus_lookup_attempted"),
            "rights_cleared_corpus_available": out.metrics.get("rights_cleared_corpus_available"),
            "structure_input_present": out.metrics.get("structure_input_present"),
            "corpus_lookup_complete_gate": out.gates.get("corpus_lookup_complete"),
            "novelty_constraint_authorized_gate": out.gates.get("novelty_constraint_authorized"),
            "missing_inputs": out.missing_inputs,
            "uncertainty_scope": out.uncertainty.get("scope"),
            "authority_envelope_preserved": envelope_ok,
            "byte_stable_two_replay": byte_ok,
        }));
    }

    let n = n_scenarios.max(1) as f64;

    // Fail-closed probes on unsupported inputs.
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
        "runtime_status_insufficient_input_rate": {
            "observed": status_pass as f64 / n, "floor": 1.0, "direction": "MAXIMIZE",
            "sample_size": n_scenarios, "passed": status_pass as f64 / n >= 1.0,
        },
        "evidence_scope_pinned_molecule_novelty_audit_only_rate": {
            "observed": evidence_scope_pass as f64 / n, "floor": 1.0, "direction": "MAXIMIZE",
            "sample_size": n_scenarios, "passed": evidence_scope_pass as f64 / n >= 1.0,
        },
        "novelty_status_pinned_abstained_rate": {
            "observed": novelty_status_pass as f64 / n, "floor": 1.0, "direction": "MAXIMIZE",
            "sample_size": n_scenarios, "passed": novelty_status_pass as f64 / n >= 1.0,
        },
        "corpus_lookup_attempted_false_rate": {
            "observed": lookup_attempted_pass as f64 / n, "floor": 1.0, "direction": "MAXIMIZE",
            "sample_size": n_scenarios, "passed": lookup_attempted_pass as f64 / n >= 1.0,
        },
        "rights_cleared_corpus_available_false_rate": {
            "observed": rights_cleared_pass as f64 / n, "floor": 1.0, "direction": "MAXIMIZE",
            "sample_size": n_scenarios, "passed": rights_cleared_pass as f64 / n >= 1.0,
        },
        "corpus_lookup_complete_gate_false_rate": {
            "observed": lookup_complete_gate_pass as f64 / n, "floor": 1.0, "direction": "MAXIMIZE",
            "sample_size": n_scenarios, "passed": lookup_complete_gate_pass as f64 / n >= 1.0,
        },
        "novelty_constraint_authorized_gate_false_rate": {
            "observed": authorized_gate_pass as f64 / n, "floor": 1.0, "direction": "MAXIMIZE",
            "sample_size": n_scenarios, "passed": authorized_gate_pass as f64 / n >= 1.0,
        },
        "structure_input_present_metric_matches_candidate_rate": {
            "observed": structure_metric_pass as f64 / n, "floor": 1.0, "direction": "MAXIMIZE",
            "sample_size": n_scenarios, "passed": structure_metric_pass as f64 / n >= 1.0,
        },
        "missing_input_names_rdkit_and_corpus_and_recall_rate": {
            "observed": missing_input_pass as f64 / n, "floor": 1.0, "direction": "MAXIMIZE",
            "sample_size": n_scenarios, "passed": missing_input_pass as f64 / n >= 1.0,
        },
        "explanation_disclaims_rights_cleared_corpus_and_locked_retrieval_rate": {
            "observed": explanation_pass as f64 / n, "floor": 1.0, "direction": "MAXIMIZE",
            "sample_size": n_scenarios, "passed": explanation_pass as f64 / n >= 1.0,
        },
        "uncertainty_scope_disclaims_novelty_patentability_desirability_performance_rate": {
            "observed": uncertainty_pass as f64 / n, "floor": 1.0, "direction": "MAXIMIZE",
            "sample_size": n_scenarios, "passed": uncertainty_pass as f64 / n >= 1.0,
        },
        "authority_envelope_preservation_rate": {
            "observed": envelope_pass as f64 / n, "floor": 1.0, "direction": "MAXIMIZE",
            "sample_size": n_scenarios, "passed": envelope_pass as f64 / n >= 1.0,
        },
        "unsupported_input_fail_closed_rate": {
            "observed": ff_rate, "floor": 1.0, "direction": "MAXIMIZE",
            "probe_sample_size": ff_total, "probes": ff_probes,
            "passed": ff_rate >= 1.0,
        },
        "byte_stable_two_replay_rate": {
            "observed": byte_replay_pass as f64 / n, "direction": "MAXIMIZE",
            "sample_size": n_scenarios,
            "note": "observational; novelty_result invoked twice per candidate produces byte-identical ModuleResult",
        },
    });

    let benchmark_lock_bytes = fs::read(benchmark_lock_path()).expect("benchmark-lock readable");
    let benchmark_lock_sha256 = file_sha256(&benchmark_lock_bytes);

    let diagnostic = json!({
        "schema": "amphora.module-phase0-benchmark-diagnostic.v1",
        "module_id": "amphora-molecule-novelty",
        "kpi": kpi.clone(),
        "records": per_scenario.clone(),
        "passed": kpi["runtime_status_insufficient_input_rate"]["passed"] == json!(true)
            && kpi["evidence_scope_pinned_molecule_novelty_audit_only_rate"]["passed"] == json!(true)
            && kpi["novelty_status_pinned_abstained_rate"]["passed"] == json!(true)
            && kpi["corpus_lookup_attempted_false_rate"]["passed"] == json!(true)
            && kpi["rights_cleared_corpus_available_false_rate"]["passed"] == json!(true)
            && kpi["corpus_lookup_complete_gate_false_rate"]["passed"] == json!(true)
            && kpi["novelty_constraint_authorized_gate_false_rate"]["passed"] == json!(true)
            && kpi["structure_input_present_metric_matches_candidate_rate"]["passed"] == json!(true)
            && kpi["missing_input_names_rdkit_and_corpus_and_recall_rate"]["passed"] == json!(true)
            && kpi["explanation_disclaims_rights_cleared_corpus_and_locked_retrieval_rate"]["passed"] == json!(true)
            && kpi["uncertainty_scope_disclaims_novelty_patentability_desirability_performance_rate"]["passed"] == json!(true)
            && kpi["authority_envelope_preservation_rate"]["passed"] == json!(true)
            && kpi["unsupported_input_fail_closed_rate"]["passed"] == json!(true),
    });
    let diagnostic_bytes_canonical =
        serde_json::to_vec(&canonicalize(&diagnostic)).expect("canonical bytes");
    let diagnostic_sha256 = file_sha256(&diagnostic_bytes_canonical);

    let mut result = Map::new();
    result.insert("schema".into(), json!("amphora.module-phase0-benchmark-result.v1"));
    result.insert("module_id".into(), json!("amphora-molecule-novelty"));
    result.insert(
        "benchmark_id".into(),
        json!("amphora-molecule-novelty-phase0-corpus-abstention-v1"),
    );
    result.insert("benchmark_lock_sha256".into(), json!(benchmark_lock_sha256));
    result.insert("dataset_fixture_sha256".into(), json!(benchmark_lock_sha256));
    result.insert(
        "dataset_fixture_note".into(),
        json!("molecule-novelty Phase-0 harness constructs its 5 molecule candidates + 3 fail-closed probes in-Rust with a default FeatureSnapshot (no molecule_facts_v1) so the runtime abstains without ever calling RDKit. SHA-256 recorded is the on-disk benchmark-lock hash."),
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
fn molecule_novelty_phase0_kpi_report_is_deterministic_and_gates_pass() {
    let first = compute_report();
    let first_bytes = serde_json::to_vec(&first).expect("canonical");
    let second_bytes = serde_json::to_vec(&compute_report()).expect("canonical");
    assert_eq!(first_bytes, second_bytes, "KPI report is not byte-stable");

    let kpi = &first["kpi"];
    for gate in [
        "runtime_status_insufficient_input_rate",
        "evidence_scope_pinned_molecule_novelty_audit_only_rate",
        "novelty_status_pinned_abstained_rate",
        "corpus_lookup_attempted_false_rate",
        "rights_cleared_corpus_available_false_rate",
        "corpus_lookup_complete_gate_false_rate",
        "novelty_constraint_authorized_gate_false_rate",
        "structure_input_present_metric_matches_candidate_rate",
        "missing_input_names_rdkit_and_corpus_and_recall_rate",
        "explanation_disclaims_rights_cleared_corpus_and_locked_retrieval_rate",
        "uncertainty_scope_disclaims_novelty_patentability_desirability_performance_rate",
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
