use amphora_engine::EnginePool;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::path::PathBuf;

fn sha256_hex(bytes: &[u8]) -> String {
    let mut hasher = Sha256::new();
    hasher.update(bytes);
    format!("{:x}", hasher.finalize())
}

fn run_one(root: &PathBuf, label: &str, path: &str) -> Value {
    let bytes = std::fs::read(path).expect("read candidate file");
    let candidate: Value = serde_json::from_slice(&bytes).expect("parse candidate json");
    let pool = EnginePool::new(root, 1).expect("EnginePool::new (read-only registries)");
    let (result, _elapsed_ms) = pool
        .score(&candidate, 42, json!({"parent_ids": [], "generation": 0, "mutation_id": null}), "leak-probe-run")
        .expect("EnginePool::score (real compiled engine, no writes)");
    let normalized_formulation = result
        .pointer("/candidate/normalized_formulation")
        .cloned()
        .unwrap_or(Value::Null);
    let formula_hash_echo = normalized_formulation
        .get("formula_hash")
        .cloned()
        .unwrap_or(Value::Null);
    let candidate_id = result
        .pointer("/candidate/candidate_id")
        .and_then(Value::as_str)
        .unwrap_or("")
        .to_string();
    let result_hash = result
        .pointer("/provenance/result_hash")
        .and_then(Value::as_str)
        .unwrap_or("")
        .to_string();
    let result_bytes = serde_json::to_vec(&result).expect("serialize result");
    json!({
        "label": label,
        "candidate_file": path,
        "candidate_file_sha256": sha256_hex(&bytes),
        "candidate_id": candidate_id,
        "normalized_formulation_top_level_keys": normalized_formulation
            .as_object()
            .map(|o| o.keys().cloned().collect::<Vec<_>>())
            .unwrap_or_default(),
        "formula_hash_echoed_into_normalized_formulation": formula_hash_echo,
        "provenance_result_hash": result_hash,
        "full_result_sha256": sha256_hex(&result_bytes),
    })
}

fn main() {
    let root: PathBuf = std::env::args()
        .nth(1)
        .expect("usage: rust_harness_main <workspace_root> <clean.json> <poisoned.json>")
        .into();
    let clean_path = std::env::args().nth(2).expect("clean candidate path");
    let poison_path = std::env::args().nth(3).expect("poisoned candidate path");

    let clean = run_one(&root, "clean", &clean_path);
    let poison = run_one(&root, "poison", &poison_path);

    let causality_isolated = clean.get("candidate_id") == poison.get("candidate_id");
    let leak_confirmed = poison
        .get("formula_hash_echoed_into_normalized_formulation")
        .map(|v| v.is_string())
        .unwrap_or(false)
        && clean
            .get("formula_hash_echoed_into_normalized_formulation")
            .map(|v| v.is_null())
            .unwrap_or(false)
        && clean.get("provenance_result_hash") != poison.get("provenance_result_hash")
        && clean.get("full_result_sha256") != poison.get("full_result_sha256");

    let diagnostic = json!({
        "schema": "amphora.candidate-contract.normalized-formulation-engine-leak-diagnostic.v1",
        "harness": "amphora-candidate-contract/benchmarks/normalized-formulation-engine-leak-v1/rust_harness_main.rs",
        "engine_entry_point": "amphora_engine::EnginePool::score (the exact function amphora-cli::control::shadow_run calls for every candidate in its --candidate input array, with no candidate_type/lane restriction)",
        "clean": clean,
        "poison": poison,
        "causality_isolated_same_candidate_id": causality_isolated,
        "leak_confirmed": leak_confirmed,
    });
    println!("{}", serde_json::to_string_pretty(&diagnostic).unwrap());
}
