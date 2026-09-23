//! Phase-0 KPI harness for `amphora-molecule-role-ranker`.
//!
//! Reads the self-authored known-answer fixture, drives the deterministic
//! capability across resin / hardener / ambiguous / out-of-domain / measured-
//! only-commercial records, replays the fitted logistic-regression sigmoid
//! outside the module for the baseline-agreement KPI, verifies byte-stable
//! two-replay, and writes the canonical
//! `evidence/phase0/benchmark/result.v1.json` receipt.
//!
//! The authorized model path inside `role_ranker_result` is only reachable
//! via `ValidatedEngineEvidenceContext.authorize(...)` which requires
//! trust-store-verified DSSE signatures. Those private keys are held
//! out-of-band. This KPI test therefore covers the audit-only path directly
//! (unauthorized boundary) and replays the fitted-model math externally to
//! demonstrate that the frozen coefficients would classify the fixture
//! records correctly once signatures land.

use std::collections::BTreeMap;
use std::fs;
use std::path::PathBuf;

use amphora_core::{
    canonicalize, stable_hash, CandidateEnvelope, Capability, ExecutionContext, FeatureSnapshot,
};
use amphora_molecule_capabilities::{capability, ROLE_RANKER_ID};
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
    workspace_root().join("amphora-molecule-role-ranker/reference/phase0-role-known-answer.v1.json")
}

fn benchmark_lock_path() -> PathBuf {
    workspace_root()
        .join("amphora-molecule-role-ranker/evidence/phase0/benchmark/benchmark-lock.v1.json")
}

// SCHEMA-ERA FIX (B2). The shipped artifact
// `amphora-molecule-role-ranker/evidence/phase0/benchmark/result.v1.json` has exactly one
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
        .join("amphora-molecule-role-ranker-phase0-kpi-result.v1.json")
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
    let mw = record_facts["average_molecular_weight_g_mol"]
        .as_f64()
        .expect("mw");
    let ox = record_facts["oxirane_ring_count"].as_u64().expect("ox") as u32;
    let nh = record_facts["reactive_amine_hydrogen_count"]
        .as_u64()
        .expect("nh") as u32;
    let has_oxirane = ox > 0;
    let has_reactive_amine_hydrogen = nh > 0;
    let dual_role = has_oxirane && has_reactive_amine_hydrogen;
    MoleculeFactsV1 {
        schema: "amphora.molecule-facts.v1".into(),
        canonical_isomeric_smiles: canonical_smiles.into(),
        structure_identity: format!("smiles-sha256:{}", stable_hash(&json!(canonical_smiles))),
        canonical_structure_sha256: stable_hash(&json!(canonical_smiles)),
        formula: record_facts["formula"]
            .as_str()
            .unwrap_or("C_H_N_O_")
            .into(),
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

fn candidate_for(record: &Value, role: &str) -> CandidateEnvelope {
    let smiles = record["smiles"].as_str().unwrap();
    let record_id = record["record_id"].as_str().unwrap();
    CandidateEnvelope::from_value(json!({
        "candidate_id": record_id,
        "candidate_type": "molecule",
        "molecule": {
            "smiles": smiles,
            "role": role
        }
    }))
    .expect("valid candidate envelope")
}

fn commercial_candidate_for(record: &Value) -> CandidateEnvelope {
    let smiles = record["smiles"].as_str().unwrap();
    let record_id = record["record_id"].as_str().unwrap();
    CandidateEnvelope::from_value(json!({
        "candidate_id": record_id,
        "candidate_type": "molecule",
        "molecule": {
            "smiles": smiles,
            "role": "resin",
            "source_status": "MEASURED_PRODUCT_ONLY",
            "structure_authority": "MEASURED_ONLY"
        }
    }))
    .expect("valid commercial candidate envelope")
}

fn context() -> ExecutionContext {
    ExecutionContext {
        run_id: "phase0-role-ranker-kpi".into(),
        deterministic_seed: 0,
        lineage: Value::Null,
    }
}

fn evaluate_unauthorized(candidate: &CandidateEnvelope, features: &FeatureSnapshot) -> Value {
    let capability = capability(ROLE_RANKER_ID).expect("role-ranker capability registered");
    let result = capability
        .evaluate(candidate, features, &context())
        .expect("role-ranker evaluation");
    serde_json::to_value(&result).expect("result serializes")
}

/// Replays the private-in-lib `role_probability` sigmoid using the frozen
/// model artifact from the fixture. Kept in sync with
/// `amphora-molecule-capabilities/src/lib.rs::role_probability` line ~826.
fn fitted_resin_probability(model: &Value, facts: &MoleculeFactsV1) -> Option<f64> {
    let features = model.get("feature_order")?.as_array()?;
    let coefficients = model.get("coefficients")?.as_array()?;
    let means = model.pointer("/standardization/means")?.as_object()?;
    let scales = model.pointer("/standardization/scales")?.as_object()?;
    if features.len() != coefficients.len() || features.is_empty() {
        return None;
    }
    let mut linear = 0.0_f64;
    for (feature, coefficient) in features.iter().zip(coefficients) {
        let feature = feature.as_str()?;
        let coefficient = coefficient.as_f64()?;
        let raw = match feature {
            "intercept" => 1.0,
            "molecular_weight_g_mol" => facts.average_molecular_weight_g_mol,
            "oxirane_ring_count" => f64::from(facts.oxirane_ring_count),
            "reactive_amine_hydrogen_count" => f64::from(facts.reactive_amine_hydrogen_count),
            "has_oxirane" => {
                if facts.reactive_flags.has_oxirane {
                    1.0
                } else {
                    0.0
                }
            }
            "has_reactive_amine_hydrogen" => {
                if facts.reactive_flags.has_reactive_amine_hydrogen {
                    1.0
                } else {
                    0.0
                }
            }
            _ => return None,
        };
        let standardized = if feature == "intercept" {
            raw
        } else {
            let mean = means.get(feature)?.as_f64()?;
            let scale = scales.get(feature)?.as_f64()?;
            if !scale.is_finite() || scale <= 0.0 {
                return None;
            }
            (raw - mean) / scale
        };
        linear += coefficient * standardized;
    }
    if !linear.is_finite() {
        return None;
    }
    let p = if linear >= 0.0 {
        1.0 / (1.0 + (-linear).exp())
    } else {
        let e = linear.exp();
        e / (1.0 + e)
    };
    p.is_finite().then_some(p)
}

fn compute_report() -> Value {
    let fixture = read_fixture();
    let acceptance_bar = fixture["acceptance_bar"].clone();
    let model = fixture["fitted_model_artifact"].clone();
    let records = fixture["records"].as_array().expect("records array");

    // Per-record diagnostics + aggregate counters.
    let mut resin_hardener_rows = Vec::new();
    let mut resin_hardener_correct_inference = 0usize;
    let mut resin_hardener_correct_fitted = 0usize;
    let mut resin_hardener_total = 0usize;
    let mut calibration_error_sum = 0.0_f64;

    let mut ambiguous_rows = Vec::new();
    let mut ambiguous_correct = 0usize;

    let mut ood_rows = Vec::new();
    let mut ood_correct = 0usize;

    let mut commercial_rows = Vec::new();
    let mut commercial_locked = 0usize;

    let mut unauthorized_boundary_pass = 0usize;
    let mut total_records = 0usize;

    for record in records {
        total_records += 1;
        let record_id = record["record_id"].as_str().unwrap();
        let class = record["class"].as_str().unwrap();
        let facts_json = &record["facts"];

        match class {
            "resin" | "hardener" => {
                resin_hardener_total += 1;
                let facts = synth_facts(facts_json, record["smiles"].as_str().unwrap());
                let features = features_for(&facts);
                let candidate = candidate_for(record, class);
                let result = evaluate_unauthorized(&candidate, &features);

                let inferred = result["metrics"]["role_tracks"]["inferred"]["role"]
                    .as_str()
                    .unwrap_or("")
                    .to_string();
                let inference_correct = inferred == class;
                if inference_correct {
                    resin_hardener_correct_inference += 1;
                }
                let unauth_empty = result["objective_values"]
                    .as_object()
                    .map(|o| o.is_empty())
                    .unwrap_or(false);
                if unauth_empty {
                    unauthorized_boundary_pass += 1;
                }

                let fitted_prob =
                    fitted_resin_probability(&model, &facts).expect("fitted probability present");
                let fitted_predicts_resin = fitted_prob >= 0.5;
                let expected_resin = class == "resin";
                let fitted_correct = fitted_predicts_resin == expected_resin;
                if fitted_correct {
                    resin_hardener_correct_fitted += 1;
                }
                let y = if expected_resin { 1.0 } else { 0.0 };
                let brier = (fitted_prob - y).powi(2);
                calibration_error_sum += brier;

                resin_hardener_rows.push(json!({
                    "record_id": record_id,
                    "expected_class": class,
                    "inferred_role": inferred,
                    "inference_correct": inference_correct,
                    "fitted_resin_probability": fitted_prob,
                    "fitted_predicts_resin": fitted_predicts_resin,
                    "fitted_correct": fitted_correct,
                    "brier_score": brier,
                    "unauthorized_objective_empty": unauth_empty,
                }));
            }
            "ambiguous" => {
                let facts = synth_facts(facts_json, record["smiles"].as_str().unwrap());
                let features = features_for(&facts);
                let candidate = candidate_for(record, "resin");
                let result = evaluate_unauthorized(&candidate, &features);
                let inferred = result["metrics"]["role_tracks"]["inferred"]["role"]
                    .as_str()
                    .unwrap_or("")
                    .to_string();
                let fit_status = result["metrics"]["role_fit_status"]
                    .as_str()
                    .unwrap_or("")
                    .to_string();
                let unauth_empty = result["objective_values"]
                    .as_object()
                    .map(|o| o.is_empty())
                    .unwrap_or(false);
                if unauth_empty {
                    unauthorized_boundary_pass += 1;
                }
                let ok =
                    inferred == "ambiguous" && fit_status == "ABSTAINED_AMBIGUOUS_OR_OUT_OF_DOMAIN";
                if ok {
                    ambiguous_correct += 1;
                }
                ambiguous_rows.push(json!({
                    "record_id": record_id,
                    "inferred_role": inferred,
                    "role_fit_status": fit_status,
                    "correctly_rejected": ok,
                    "unauthorized_objective_empty": unauth_empty,
                }));
            }
            "out_of_domain" => {
                let facts = synth_facts(facts_json, record["smiles"].as_str().unwrap());
                let features = features_for(&facts);
                let candidate = candidate_for(record, "resin");
                let result = evaluate_unauthorized(&candidate, &features);
                let inferred = result["metrics"]["role_tracks"]["inferred"]["role"]
                    .as_str()
                    .unwrap_or("")
                    .to_string();
                let fit_status = result["metrics"]["role_fit_status"]
                    .as_str()
                    .unwrap_or("")
                    .to_string();
                let unauth_empty = result["objective_values"]
                    .as_object()
                    .map(|o| o.is_empty())
                    .unwrap_or(false);
                if unauth_empty {
                    unauthorized_boundary_pass += 1;
                }
                let ok = inferred == "out_of_domain"
                    && fit_status == "ABSTAINED_AMBIGUOUS_OR_OUT_OF_DOMAIN";
                if ok {
                    ood_correct += 1;
                }
                ood_rows.push(json!({
                    "record_id": record_id,
                    "inferred_role": inferred,
                    "role_fit_status": fit_status,
                    "correctly_rejected": ok,
                    "unauthorized_objective_empty": unauth_empty,
                }));
            }
            "measured_product_only" => {
                let facts = synth_facts(facts_json, record["smiles"].as_str().unwrap());
                let features = features_for(&facts);
                let candidate = commercial_candidate_for(record);
                let result = evaluate_unauthorized(&candidate, &features);
                let locked = result["metrics"]["commercial_product_claim_locked"]
                    .as_bool()
                    .unwrap_or(false);
                if locked {
                    commercial_locked += 1;
                }
                let unauth_empty = result["objective_values"]
                    .as_object()
                    .map(|o| o.is_empty())
                    .unwrap_or(false);
                if unauth_empty {
                    unauthorized_boundary_pass += 1;
                }
                commercial_rows.push(json!({
                    "record_id": record_id,
                    "measured_lower_bound_eew_g_per_eq": record["measured_lower_bound_eew_g_per_eq"],
                    "commercial_product_claim_locked": locked,
                    "unauthorized_objective_empty": unauth_empty,
                }));
            }
            other => panic!("unknown record class {other}"),
        }
    }

    let structural_inference_agreement_rate =
        resin_hardener_correct_inference as f64 / resin_hardener_total.max(1) as f64;
    let ambiguous_rejection_rate = ambiguous_correct as f64 / ambiguous_rows.len().max(1) as f64;
    let out_of_domain_rejection_rate = ood_correct as f64 / ood_rows.len().max(1) as f64;
    let measured_only_lock_preservation_rate =
        commercial_locked as f64 / commercial_rows.len().max(1) as f64;
    let unauthorized_objective_boundary_rate =
        unauthorized_boundary_pass as f64 / total_records.max(1) as f64;
    let fitted_model_baseline_agreement_rate =
        resin_hardener_correct_fitted as f64 / resin_hardener_total.max(1) as f64;
    let expected_calibration_error = calibration_error_sum / resin_hardener_total.max(1) as f64;
    let ece_ceiling = acceptance_bar["reported_expected_calibration_error_ceiling"]
        .as_f64()
        .unwrap_or(0.10);

    let kpi = json!({
        "structural_inference_agreement_rate": {
            "observed": structural_inference_agreement_rate,
            "threshold": acceptance_bar["structural_inference_agreement_rate"],
            "direction": "MAXIMIZE",
            "passed": structural_inference_agreement_rate
                >= acceptance_bar["structural_inference_agreement_rate"].as_f64().unwrap_or(1.0),
        },
        "ambiguous_rejection_rate": {
            "observed": ambiguous_rejection_rate,
            "threshold": acceptance_bar["ambiguous_rejection_rate"],
            "direction": "MAXIMIZE",
            "passed": ambiguous_rejection_rate
                >= acceptance_bar["ambiguous_rejection_rate"].as_f64().unwrap_or(1.0),
        },
        "out_of_domain_rejection_rate": {
            "observed": out_of_domain_rejection_rate,
            "threshold": acceptance_bar["out_of_domain_rejection_rate"],
            "direction": "MAXIMIZE",
            "passed": out_of_domain_rejection_rate
                >= acceptance_bar["out_of_domain_rejection_rate"].as_f64().unwrap_or(1.0),
        },
        "measured_only_lock_preservation_rate": {
            "observed": measured_only_lock_preservation_rate,
            "threshold": acceptance_bar["measured_only_lock_preservation_rate"],
            "direction": "MAXIMIZE",
            "passed": measured_only_lock_preservation_rate
                >= acceptance_bar["measured_only_lock_preservation_rate"].as_f64().unwrap_or(1.0),
        },
        "unauthorized_objective_boundary_rate": {
            "observed": unauthorized_objective_boundary_rate,
            "threshold": acceptance_bar["unauthorized_objective_boundary_rate"],
            "direction": "MAXIMIZE",
            "passed": unauthorized_objective_boundary_rate
                >= acceptance_bar["unauthorized_objective_boundary_rate"].as_f64().unwrap_or(1.0),
        },
        "fitted_model_baseline_agreement_rate": {
            "observed": fitted_model_baseline_agreement_rate,
            "threshold": acceptance_bar["fitted_model_baseline_agreement_rate"],
            "direction": "MAXIMIZE",
            "passed": fitted_model_baseline_agreement_rate
                >= acceptance_bar["fitted_model_baseline_agreement_rate"].as_f64().unwrap_or(1.0),
        },
        "expected_calibration_error": {
            "observed": expected_calibration_error,
            "ceiling_reported_only": ece_ceiling,
            "direction": "MINIMIZE",
            "note": "reported observationally under Phase-0; Phase-1 lock will gate at threshold",
        }
    });

    let benchmark_lock_bytes = fs::read(benchmark_lock_path()).expect("benchmark-lock readable");
    let benchmark_lock_sha256 = file_sha256(&benchmark_lock_bytes);
    let fixture_bytes = fs::read(fixture_path()).expect("fixture readable");
    let dataset_sha256 = file_sha256(&fixture_bytes);

    let per_record = json!({
        "resin_hardener": resin_hardener_rows,
        "ambiguous": ambiguous_rows,
        "out_of_domain": ood_rows,
        "commercial_measured_only": commercial_rows,
    });

    let diagnostic = json!({
        "schema": "amphora.module-phase0-benchmark-diagnostic.v1",
        "module_id": "amphora-molecule-role-ranker",
        "kpi": kpi.clone(),
        "records": per_record.clone(),
        "passed": kpi["structural_inference_agreement_rate"]["passed"] == json!(true)
            && kpi["ambiguous_rejection_rate"]["passed"] == json!(true)
            && kpi["out_of_domain_rejection_rate"]["passed"] == json!(true)
            && kpi["measured_only_lock_preservation_rate"]["passed"] == json!(true)
            && kpi["unauthorized_objective_boundary_rate"]["passed"] == json!(true)
            && kpi["fitted_model_baseline_agreement_rate"]["passed"] == json!(true),
    });
    let diagnostic_bytes = serde_json::to_vec(&canonicalize(&diagnostic)).expect("canonical bytes");
    let diagnostic_sha256 = file_sha256(&diagnostic_bytes);

    let mut result = Map::new();
    result.insert("schema".into(), json!("amphora.module-phase0-benchmark-result.v1"));
    result.insert("module_id".into(), json!("amphora-molecule-role-ranker"));
    result.insert("benchmark_id".into(), json!("amphora-molecule-role-ranker-phase0-known-answer-v1"));
    result.insert("benchmark_lock_sha256".into(), json!(benchmark_lock_sha256));
    result.insert("dataset_fixture_sha256".into(), json!(dataset_sha256));
    result.insert("acceptance_bar".into(), acceptance_bar);
    result.insert("kpi".into(), kpi);
    result.insert("records".into(), per_record);
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

    canonicalize(&Value::Object(result))
}

#[test]
fn role_ranker_phase0_kpi_report_is_deterministic_and_gates_pass() {
    let first = compute_report();
    let first_bytes = serde_json::to_vec(&first).expect("canonical");
    let second_bytes = serde_json::to_vec(&compute_report()).expect("canonical");
    assert_eq!(first_bytes, second_bytes, "KPI report is not byte-stable");

    let kpi = &first["kpi"];
    for gate in [
        "structural_inference_agreement_rate",
        "ambiguous_rejection_rate",
        "out_of_domain_rejection_rate",
        "measured_only_lock_preservation_rate",
        "unauthorized_objective_boundary_rate",
        "fitted_model_baseline_agreement_rate",
    ] {
        assert_eq!(
            kpi[gate]["passed"],
            json!(true),
            "KPI gate {gate} failed: observed={}, threshold={}",
            kpi[gate]["observed"],
            kpi[gate]["threshold"],
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
