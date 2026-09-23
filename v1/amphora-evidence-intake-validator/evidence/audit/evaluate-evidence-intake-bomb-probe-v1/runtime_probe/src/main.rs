//! LIVE Rust end-to-end probe: does the REAL evidence-intake acceptance
//! predicate (`AssuranceCapability("amphora-evidence-intake-validator")::evaluate`,
//! i.e. `evaluate_evidence_intake`/`host_receipt_valid` in
//! amphora-assurance-capabilities/src/lib.rs) ACCEPT a package that violates
//! the module's own strict-parser structural limits (MAX_JSON_DEPTH,
//! MAX_COLLECTION_ENTRIES), when that package is constructed the same way
//! the real scoring entrypoint `amphora-engine::execute()` constructs every
//! candidate it scores -- via `CandidateEnvelope::from_value`, never
//! `CandidateEnvelope::from_bytes`/`parse_json_strict`?
//!
//! Links the real amphora-core + amphora-assurance-capabilities crates and
//! calls their real public entry points end to end. No randomness, no clock,
//! no filesystem writes. Emits one deterministic JSON object to stdout.

use amphora_assurance_capabilities::{
    AssuranceCapability, HOST_VERIFIED_RECEIPT_FEATURE, HOST_VERIFIED_RECEIPT_SCHEMA,
};
use amphora_core::{stable_hash, Capability, CandidateEnvelope, ExecutionContext, FeatureSnapshot, MAX_JSON_DEPTH};
use serde_json::{json, Map, Value};

fn deep_array(depth: usize) -> String {
    format!("{}0{}", "[".repeat(depth), "]".repeat(depth))
}

fn build_receipt(candidate: &CandidateEnvelope, package_sha256: &str) -> Value {
    json!({
        "schema": HOST_VERIFIED_RECEIPT_SCHEMA,
        "accepted": true,
        "signature_verified": true,
        "revocation_checked": true,
        "fresh": true,
        "signature_algorithm": "Ed25519",
        "trust_store_status": "TRUSTED",
        "candidate_id": candidate.candidate_id(),
        "candidate_contract_hash_v1": candidate.contract_hash_v1(),
        "package_sha256": package_sha256,
        "verifier_id": "probe-host-trust-kernel",
    })
}

fn run_one(label: &str, evidence_package: Value) -> Map<String, Value> {
    let candidate_value = json!({
        "candidate_id": format!("eiv-bomb-probe-{label}"),
        "candidate_type": "evidence_package",
        "evidence_refs": { "evidence_package": evidence_package },
    });

    // This is EXACTLY the constructor amphora-engine::execute() calls (line
    // 732 of amphora-engine/src/lib.rs): CandidateEnvelope::from_value, never
    // from_bytes/parse_json_strict.
    let candidate = CandidateEnvelope::from_value(candidate_value).expect("from_value builds");

    let package = candidate.value()["evidence_refs"]["evidence_package"].clone();
    let package_sha256 = stable_hash(&package);
    let receipt = build_receipt(&candidate, &package_sha256);

    let mut values = std::collections::BTreeMap::new();
    values.insert(HOST_VERIFIED_RECEIPT_FEATURE.to_string(), receipt);
    let features = FeatureSnapshot { values };
    let context = ExecutionContext {
        run_id: format!("eiv-bomb-probe-{label}"),
        deterministic_seed: 0,
        lineage: Value::Null,
    };

    let capability =
        AssuranceCapability::new("amphora-evidence-intake-validator").expect("resolve capability");
    let result = capability
        .evaluate(&candidate, &features, &context)
        .expect("evaluate does not error on evidence_package candidate type");

    let mut row = Map::new();
    row.insert("label".into(), json!(label));
    row.insert("status".into(), json!(result.status));
    row.insert("score_0_1".into(), json!(result.score_0_1));
    row.insert(
        "gate_evidence_package_accepted".into(),
        result
            .gates
            .get("evidence_package_accepted")
            .cloned()
            .unwrap_or(Value::Null),
    );
    row.insert(
        "gate_host_verified_signature_receipt".into(),
        result
            .gates
            .get("host_verified_signature_receipt")
            .cloned()
            .unwrap_or(Value::Null),
    );
    row
}

fn main() {
    let mut report = Map::new();

    // Honest baseline: an ordinary, well-formed evidence package must be
    // ACCEPTED (sanity that the predicate isn't merely broken/inert).
    let honest = run_one(
        "honest-baseline",
        json!({"standard": "ISO 4624", "mpa": 4.9, "failure_mode": "adhesive"}),
    );

    // The structural-limit violator: nesting 40 levels past MAX_JSON_DEPTH.
    // parse_json_strict/CandidateEnvelope::from_bytes REJECTS this shape
    // (proven live in the sibling from-value-strict-parse-bypass-v1 probe,
    // g2_from_bytes_rejects_depth_bomb=true). This probe constructs the
    // identical shape via from_value (the constructor the real scoring path
    // actually uses) and asks the REAL, live evaluate_evidence_intake
    // predicate whether it accepts it end to end.
    let depth_bomb = deep_array(MAX_JSON_DEPTH + 40);
    let depth_bomb_row = run_one(
        "depth-bomb",
        json!({"payload": Value::from(serde_json::from_str::<Value>(&depth_bomb).unwrap())}),
    );

    // The entry-count-limit violator: 150,000 array entries, well past
    // MAX_COLLECTION_ENTRIES=100_000.
    let big_n = 150_000usize;
    let entry_bomb_row = run_one(
        "entry-bomb",
        json!({"rows": (0..big_n).map(Value::from).collect::<Vec<_>>()}),
    );

    let honest_accepted = honest.get("status").and_then(Value::as_str) == Some("SCORED");
    let depth_bomb_accepted =
        depth_bomb_row.get("status").and_then(Value::as_str) == Some("SCORED");
    let entry_bomb_accepted =
        entry_bomb_row.get("status").and_then(Value::as_str) == Some("SCORED");

    report.insert(
        "schema".into(),
        json!("amphora.evidence-intake-validator.evaluate-evidence-intake-bomb-probe.v1"),
    );
    report.insert("live_rust".into(), json!(true));
    report.insert(
        "crates_under_test".into(),
        json!(["amphora-core", "amphora-assurance-capabilities"]),
    );
    report.insert(
        "entry_point".into(),
        json!("AssuranceCapability::new(\"amphora-evidence-intake-validator\")::evaluate (Capability trait) -> evaluate_evidence_intake/host_receipt_valid"),
    );
    report.insert(
        "gates".into(),
        json!({
            "g_honest_baseline_accepted": honest_accepted,
            "g_depth_bomb_accepted_end_to_end": depth_bomb_accepted,
            "g_entry_bomb_accepted_end_to_end": entry_bomb_accepted,
        }),
    );
    report.insert(
        "all_gates_passed".into(),
        json!(honest_accepted && depth_bomb_accepted && entry_bomb_accepted),
    );
    report.insert(
        "results".into(),
        json!({
            "max_json_depth": MAX_JSON_DEPTH,
            "depth_bomb_depth_probed": MAX_JSON_DEPTH + 40,
            "entry_bomb_entries_probed": big_n,
            "honest_baseline": Value::Object(honest),
            "depth_bomb": Value::Object(depth_bomb_row),
            "entry_bomb": Value::Object(entry_bomb_row),
        }),
    );

    println!("{}", serde_json::to_string(&Value::Object(report)).unwrap());
}
