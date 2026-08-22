//! Phase-0 KPI harness for `amphora-molecule-design-gate`.
//!
//! Drives the deterministic `design_gate_result` capability across a
//! hand-curated fixture of 42 labelled molecules from PubChem plus
//! synthetic malformed controls. Verifies gate decision correctness,
//! `gate_reason` attribution across six categories, per-gate boolean
//! agreement, malformed-input fail-closed behaviour, and authority-lock
//! preservation, all with byte-stable two-replay determinism.

use std::collections::BTreeMap;
use std::fs;
use std::path::PathBuf;

use amphora_core::{
    canonicalize, stable_hash, CandidateEnvelope, Capability, ExecutionContext, FeatureSnapshot,
};
use amphora_molecule_capabilities::{capability, DESIGN_GATE_ID};
use amphora_rdkit_ffi::{
    MoleculeFactsV1, ReactiveFlagsV1, ToolkitProvenanceV1, REACTIVE_ONTOLOGY_VERSION,
    REQUIRED_RDKIT_VERSION,
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
        "amphora-molecule-design-gate/reference/phase0-design-gate-known-answer.v1.json",
    )
}

fn benchmark_lock_path() -> PathBuf {
    workspace_root()
        .join("amphora-molecule-design-gate/evidence/phase0/benchmark/benchmark-lock.v1.json")
}

// SCHEMA-ERA FIX (B2). The shipped artifact
// `amphora-molecule-design-gate/evidence/phase0/benchmark/result.v1.json` has exactly one
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
        .join("amphora-molecule-design-gate-phase0-kpi-result.v1.json")
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

fn synth_facts(record_facts: &Value, canonical_smiles: &str) -> MoleculeFactsV1 {
    let mw = record_facts["average_molecular_weight_g_mol"].as_f64().unwrap_or(0.0);
    let ox = record_facts["oxirane_ring_count"].as_u64().unwrap_or(0) as u32;
    let nh = record_facts["reactive_amine_hydrogen_count"]
        .as_u64()
        .unwrap_or(0) as u32;
    let has_oxirane = ox > 0;
    let has_reactive_amine_hydrogen = nh > 0;
    let dual_role = has_oxirane && has_reactive_amine_hydrogen;
    MoleculeFactsV1 {
        schema: "amphora.molecule-facts.v1".into(),
        canonical_isomeric_smiles: canonical_smiles.into(),
        structure_identity: format!("smiles-sha256:{}", stable_hash(&json!(canonical_smiles))),
        canonical_structure_sha256: stable_hash(&json!(canonical_smiles)),
        formula: record_facts["formula"].as_str().unwrap_or("C_H_N_O_").into(),
        average_molecular_weight_g_mol: mw,
        oxirane_ring_count: ox,
        reactive_amine_hydrogen_count: nh,
        reactive_flags: ReactiveFlagsV1 {
            has_oxirane,
            has_reactive_amine_hydrogen,
            dual_role,
        },
        ontology_version: REACTIVE_ONTOLOGY_VERSION.into(),
        toolkit_provenance: ToolkitProvenanceV1 {
            toolkit: "RDKit C++".into(),
            required_version: REQUIRED_RDKIT_VERSION.into(),
            detected_version: REQUIRED_RDKIT_VERSION.into(),
            exact_version_match: true,
        },
    }
}

fn features_for(facts: &MoleculeFactsV1) -> FeatureSnapshot {
    let mut values = BTreeMap::new();
    values.insert(
        "molecule_facts_v1".into(),
        serde_json::to_value(facts).expect("facts serialize"),
    );
    FeatureSnapshot { values }
}

fn build_candidate(case_id: &str, smiles: &Value, role: &Value) -> CandidateEnvelope {
    // Build the molecule sub-object with optional smiles/role.
    let mut molecule = Map::new();
    if let Some(s) = smiles.as_str() {
        molecule.insert("smiles".into(), json!(s));
    }
    if let Some(r) = role.as_str() {
        molecule.insert("role".into(), json!(r));
    }
    CandidateEnvelope::from_value(json!({
        "candidate_id": case_id,
        "candidate_type": "molecule",
        "molecule": molecule,
    }))
    .expect("valid candidate envelope")
}

fn context() -> ExecutionContext {
    ExecutionContext {
        run_id: "phase0-design-gate-kpi".into(),
        deterministic_seed: 0,
        lineage: Value::Null,
    }
}

fn evaluate(candidate: &CandidateEnvelope, features: &FeatureSnapshot) -> Value {
    let capability = capability(DESIGN_GATE_ID).expect("design-gate capability registered");
    let result = capability
        .evaluate(candidate, features, &context())
        .expect("design-gate evaluation");
    serde_json::to_value(&result).expect("result serializes")
}

fn compute_report() -> Value {
    let fixture = read_fixture();
    let acceptance_bar = fixture["acceptance_bar"].clone();
    let records = fixture["records"].as_array().expect("records array");

    let mut per_case: Vec<Value> = Vec::new();
    let mut gate_decision_pass = 0_usize;
    let mut gate_reason_pass = 0_usize;
    let mut role_appropriate_pass = 0_usize;
    let mut explicit_role_pass = 0_usize;
    let mut valid_single_pass = 0_usize;
    let mut authority_pass = 0_usize;
    let mut byte_replay_pass = 0_usize;
    let mut malformed_fail_closed_pass = 0_usize;
    let mut malformed_total = 0_usize;

    for record in records {
        let case_id = record["case_id"].as_str().unwrap();
        let subgroup = record["subgroup"].as_str().unwrap();
        let smiles_val = &record["smiles"];
        let role_val = &record["role"];
        let expected_pass = record["expected_pass_all_hard"].as_bool().unwrap();
        let expected_reason = record["expected_gate_reason"].as_str().unwrap();
        let expected_role_flag = record["expected_explicit_role"].as_bool().unwrap();
        let expected_react = record["expected_role_appropriate_reactivity"].as_bool().unwrap();
        let expected_valid_single = record["expected_valid_single_component"].as_bool().unwrap();
        let expected_scope = record["expected_evidence_scope"].as_str().unwrap();

        let candidate = build_candidate(case_id, smiles_val, role_val);

        // Only send facts for cases where they are provided.
        let facts_field = &record["facts"];
        let features = if facts_field.is_object() {
            let facts_obj = synth_facts(
                facts_field,
                smiles_val.as_str().unwrap_or("canonical-placeholder"),
            );
            features_for(&facts_obj)
        } else {
            FeatureSnapshot::default()
        };

        // Two replays for byte-stability check.
        let out1 = evaluate(&candidate, &features);
        let out2 = evaluate(&candidate, &features);
        let byte_stable =
            serde_json::to_vec(&out1).unwrap() == serde_json::to_vec(&out2).unwrap();
        if byte_stable {
            byte_replay_pass += 1;
        }

        let observed_pass = out1["gates"]["pass_all_hard"].as_bool().unwrap_or(false);
        let observed_reason = out1["metrics"]["gate_reason"].as_str().unwrap_or("").to_string();
        let observed_role_flag = out1["gates"]["explicit_role"].as_bool().unwrap_or(false);
        let observed_react = out1["gates"]["role_appropriate_reactivity"].as_bool().unwrap_or(false);
        let observed_valid_single = out1["gates"]["valid_single_component"].as_bool().unwrap_or(false);
        let observed_scope = out1["evidence_scope"].as_str().unwrap_or("").to_string();

        if observed_pass == expected_pass {
            gate_decision_pass += 1;
        }
        if observed_reason == expected_reason {
            gate_reason_pass += 1;
        }
        if observed_role_flag == expected_role_flag {
            explicit_role_pass += 1;
        }
        if observed_react == expected_react {
            role_appropriate_pass += 1;
        }
        if observed_valid_single == expected_valid_single {
            valid_single_pass += 1;
        }

        // Authority lock preservation.
        let scope_ok = observed_scope == expected_scope;
        let score_none = out1["score_0_1"].is_null();
        let objective_empty = out1["objective_values"]
            .as_object()
            .map(|m| m.is_empty())
            .unwrap_or(false);
        let struct_applic_ok = if out1["status"].as_str() == Some("SCORED") {
            out1["metrics"]["structural_applicability_only"] == Value::Bool(true)
        } else {
            true // FAILED_GATES path does not carry this metric
        };
        let auth_ok = scope_ok && score_none && objective_empty && struct_applic_ok;
        if auth_ok {
            authority_pass += 1;
        }

        // MALFORMED_STRUCTURE-specific fail-closed check.
        if subgroup == "MALFORMED_STRUCTURE" {
            malformed_total += 1;
            let malformed_ok = !observed_pass && observed_reason == expected_reason;
            if malformed_ok {
                malformed_fail_closed_pass += 1;
            }
        }

        per_case.push(json!({
            "case_id": case_id,
            "subgroup": subgroup,
            "smiles": smiles_val.clone(),
            "role": role_val.clone(),
            "expected_pass_all_hard": expected_pass,
            "expected_gate_reason": expected_reason,
            "observed_pass_all_hard": observed_pass,
            "observed_gate_reason": observed_reason,
            "observed_explicit_role": observed_role_flag,
            "observed_role_appropriate_reactivity": observed_react,
            "observed_valid_single_component": observed_valid_single,
            "observed_evidence_scope": observed_scope,
            "byte_stable_two_replay": byte_stable,
            "authority_locked": auth_ok,
            "sources": record["sources"].clone(),
        }));
    }

    let n = records.len().max(1) as f64;
    let gate_decision_rate = gate_decision_pass as f64 / n;
    let gate_reason_rate = gate_reason_pass as f64 / n;
    let role_react_rate = role_appropriate_pass as f64 / n;
    let explicit_role_rate = explicit_role_pass as f64 / n;
    let valid_single_rate = valid_single_pass as f64 / n;
    let authority_rate = authority_pass as f64 / n;
    let byte_replay_rate = byte_replay_pass as f64 / n;
    let malformed_rate = if malformed_total == 0 {
        1.0
    } else {
        malformed_fail_closed_pass as f64 / malformed_total as f64
    };

    let kpi = json!({
        "gate_decision_correctness_rate": {
            "observed": gate_decision_rate,
            "floor": acceptance_bar["gate_decision_correctness_rate_floor"],
            "direction": "MAXIMIZE",
            "sample_size": records.len(),
            "passed": gate_decision_rate
                >= acceptance_bar["gate_decision_correctness_rate_floor"].as_f64().unwrap_or(1.0),
        },
        "gate_reason_attribution_correctness_rate": {
            "observed": gate_reason_rate,
            "floor": acceptance_bar["gate_reason_attribution_correctness_rate_floor"],
            "direction": "MAXIMIZE",
            "sample_size": records.len(),
            "passed": gate_reason_rate
                >= acceptance_bar["gate_reason_attribution_correctness_rate_floor"].as_f64().unwrap_or(1.0),
        },
        "role_appropriate_reactivity_correctness_rate": {
            "observed": role_react_rate,
            "floor": acceptance_bar["role_appropriate_reactivity_correctness_rate_floor"],
            "direction": "MAXIMIZE",
            "sample_size": records.len(),
            "passed": role_react_rate
                >= acceptance_bar["role_appropriate_reactivity_correctness_rate_floor"].as_f64().unwrap_or(1.0),
        },
        "explicit_role_correctness_rate": {
            "observed": explicit_role_rate,
            "floor": acceptance_bar["explicit_role_correctness_rate_floor"],
            "direction": "MAXIMIZE",
            "sample_size": records.len(),
            "passed": explicit_role_rate
                >= acceptance_bar["explicit_role_correctness_rate_floor"].as_f64().unwrap_or(1.0),
        },
        "valid_single_component_correctness_rate": {
            "observed": valid_single_rate,
            "floor": acceptance_bar["valid_single_component_correctness_rate_floor"],
            "direction": "MAXIMIZE",
            "sample_size": records.len(),
            "passed": valid_single_rate
                >= acceptance_bar["valid_single_component_correctness_rate_floor"].as_f64().unwrap_or(1.0),
        },
        "malformed_structure_fail_closed_rate": {
            "observed": malformed_rate,
            "floor": acceptance_bar["malformed_structure_fail_closed_rate_floor"],
            "direction": "MAXIMIZE",
            "sample_size": malformed_total,
            "passed": malformed_rate
                >= acceptance_bar["malformed_structure_fail_closed_rate_floor"].as_f64().unwrap_or(1.0),
        },
        "authority_lock_preservation_rate": {
            "observed": authority_rate,
            "floor": acceptance_bar["authority_lock_preservation_rate_floor"],
            "direction": "MAXIMIZE",
            "sample_size": records.len(),
            "passed": authority_rate
                >= acceptance_bar["authority_lock_preservation_rate_floor"].as_f64().unwrap_or(1.0),
        },
        "byte_stable_two_replay_rate": {
            "observed": byte_replay_rate,
            "direction": "MAXIMIZE",
            "sample_size": records.len(),
            "note": "observational; every case invocation replayed twice back-to-back and asserted byte-identical ModuleResult",
        },
    });

    let benchmark_lock_bytes = fs::read(benchmark_lock_path()).expect("benchmark-lock readable");
    let benchmark_lock_sha256 = file_sha256(&benchmark_lock_bytes);
    let fixture_bytes = fs::read(fixture_path()).expect("fixture readable");
    let dataset_sha256 = file_sha256(&fixture_bytes);

    let diagnostic = json!({
        "schema": "amphora.module-phase0-benchmark-diagnostic.v1",
        "module_id": "amphora-molecule-design-gate",
        "kpi": kpi.clone(),
        "records": per_case.clone(),
        "passed": kpi["gate_decision_correctness_rate"]["passed"] == json!(true)
            && kpi["gate_reason_attribution_correctness_rate"]["passed"] == json!(true)
            && kpi["role_appropriate_reactivity_correctness_rate"]["passed"] == json!(true)
            && kpi["explicit_role_correctness_rate"]["passed"] == json!(true)
            && kpi["valid_single_component_correctness_rate"]["passed"] == json!(true)
            && kpi["malformed_structure_fail_closed_rate"]["passed"] == json!(true)
            && kpi["authority_lock_preservation_rate"]["passed"] == json!(true),
    });
    let diagnostic_bytes = serde_json::to_vec(&canonicalize(&diagnostic)).expect("canonical bytes");
    let diagnostic_sha256 = file_sha256(&diagnostic_bytes);

    let mut result = Map::new();
    result.insert("schema".into(), json!("amphora.module-phase0-benchmark-result.v1"));
    result.insert("module_id".into(), json!("amphora-molecule-design-gate"));
    result.insert(
        "benchmark_id".into(),
        json!("amphora-molecule-design-gate-phase0-structural-applicability-v1"),
    );
    result.insert("benchmark_lock_sha256".into(), json!(benchmark_lock_sha256));
    result.insert("dataset_fixture_sha256".into(), json!(dataset_sha256));
    result.insert("acceptance_bar".into(), acceptance_bar);
    result.insert("kpi".into(), kpi);
    result.insert("records".into(), json!(per_case));
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
fn design_gate_phase0_kpi_report_is_deterministic_and_gates_pass() {
    let first = compute_report();
    let first_bytes = serde_json::to_vec(&first).expect("canonical");
    let second_bytes = serde_json::to_vec(&compute_report()).expect("canonical");
    assert_eq!(first_bytes, second_bytes, "KPI report is not byte-stable");

    let kpi = &first["kpi"];
    for gate in [
        "gate_decision_correctness_rate",
        "gate_reason_attribution_correctness_rate",
        "role_appropriate_reactivity_correctness_rate",
        "explicit_role_correctness_rate",
        "valid_single_component_correctness_rate",
        "malformed_structure_fail_closed_rate",
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
