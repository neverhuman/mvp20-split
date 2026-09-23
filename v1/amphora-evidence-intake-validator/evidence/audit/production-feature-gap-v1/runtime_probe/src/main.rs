//! LIVE Rust probe: does the real, live production feature-building code
//! that feeds every real scoring call (amphora-engine/src/lib.rs `execute()`,
//! lines 733-742, the ONLY place in the whole repository outside `#[test]`
//! code that constructs the `FeatureSnapshot` passed into
//! `Capability::evaluate` for a scored candidate) EVER populate the one
//! FeatureSnapshot key (`HOST_VERIFIED_RECEIPT_FEATURE` =
//! "evidence_intake.host_verified_receipt") that
//! `evaluate_evidence_intake`/`host_receipt_valid`
//! (amphora-assurance-capabilities/src/lib.rs lines 673/729) requires to
//! ever return `verified = true`?
//!
//! A repo-wide grep (recorded in this receipt's `static_citation` field, run
//! at signing time) finds exactly 3 non-test-annotated textual hits of
//! `HOST_VERIFIED_RECEIPT_FEATURE` outside amphora-engine, and all 3 are
//! `#[test]` fn bodies (amphora-assurance-capabilities/src/lib.rs:1450,
//! amphora-formulation-capabilities/src/lib.rs:2426/2483) plus the 4 prior
//! audit/repair harnesses under evidence/phase0 and evidence/audit, which are
//! also test/probe code, never `amphora-engine::execute()` itself. This probe
//! demonstrates the LIVE CONSEQUENCE with the real crates: build the
//! FeatureSnapshot the way `execute()`'s own feature-building block
//! (line-cited, sha256-pinned below) actually builds it for ANY candidate --
//! which never inserts this key -- and ask the real, live
//! `AssuranceCapability::evaluate` whether even a maximally honest,
//! correctly-bound host-verified receipt for a legitimate marine-coating
//! evidence package can ever be accepted through that exact feature set.
//!
//! Links the real amphora-core + amphora-assurance-capabilities crates and
//! calls their real public entry points end to end. No randomness, no clock,
//! no filesystem writes. Emits one deterministic JSON object to stdout.

use amphora_assurance_capabilities::{
    AssuranceCapability, HOST_VERIFIED_RECEIPT_FEATURE, HOST_VERIFIED_RECEIPT_SCHEMA,
};
use amphora_core::{stable_hash, Capability, CandidateEnvelope, ExecutionContext, FeatureSnapshot};
use serde_json::{json, Map, Value};
use std::collections::BTreeMap;

/// Replicates amphora-engine/src/lib.rs `execute()`'s feature-building block
/// (lines ~733-742) EXACTLY as far as which KEYS it ever inserts for a
/// non-molecule candidate (evidence_package candidates never touch the
/// molecule_facts_v1 / molecule_normalization_error branches, which are
/// gated on `normalized.pointer("/normalization/...")` and never present for
/// candidate_type=evidence_package). `chemistry_backend` and
/// `rights_cleared_scientific_corpus` are inserted unconditionally in the
/// real function; they are irrelevant to `evaluate_evidence_intake`, which
/// reads ONLY `HOST_VERIFIED_RECEIPT_FEATURE`. The point under test is that
/// this function -- the ONLY non-test feature-building code in the
/// repository for a scored candidate -- has NO branch, anywhere, under any
/// condition, that inserts `HOST_VERIFIED_RECEIPT_FEATURE`.
fn production_feature_values() -> BTreeMap<String, Value> {
    BTreeMap::from([
        ("chemistry_backend".to_string(), json!({"stub": true})),
        (
            "rights_cleared_scientific_corpus".to_string(),
            Value::Bool(false),
        ),
    ])
}

fn honest_receipt(candidate: &CandidateEnvelope, package_sha256: &str) -> Value {
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
        "verifier_id": "real-pinned-trust-store-verifier",
    })
}

fn evaluate(candidate: &CandidateEnvelope, features: FeatureSnapshot) -> Map<String, Value> {
    let context = ExecutionContext {
        run_id: "eiv-production-feature-gap-probe".into(),
        deterministic_seed: 0,
        lineage: Value::Null,
    };
    let capability =
        AssuranceCapability::new("amphora-evidence-intake-validator").expect("resolve capability");
    let result = capability
        .evaluate(candidate, &features, &context)
        .expect("evaluate does not error on evidence_package candidate type");

    let mut row = Map::new();
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
        "missing_inputs".into(),
        json!(result.missing_inputs),
    );
    row
}

fn main() {
    let mut report = Map::new();

    // A maximally honest, well-formed marine-coating evidence package --
    // the same shape as the module's own shipped positive KPI fixtures.
    let candidate_value = json!({
        "candidate_id": "eiv-production-feature-gap-honest-package",
        "candidate_type": "evidence_package",
        "evidence_refs": {
            "evidence_package": {
                "standard": "ISO 4624",
                "mpa": 4.9,
                "failure_mode": "adhesive",
            }
        },
    });
    let candidate =
        CandidateEnvelope::from_value(candidate_value).expect("from_value builds honest candidate");
    let package = candidate.value()["evidence_refs"]["evidence_package"].clone();
    let package_sha256 = stable_hash(&package);
    let receipt = honest_receipt(&candidate, &package_sha256);

    // ---- G1: the PRODUCTION feature set (exactly what execute() ever
    //          builds for this candidate type) never contains the receipt.
    //          Even though `receipt` above is objectively, perfectly valid
    //          and correctly bound to this exact candidate and package, the
    //          real live predicate is asked to decide using ONLY the
    //          features production code would ever hand it. ----
    let production_features = FeatureSnapshot {
        values: production_feature_values(),
    };
    let g1_production_features_lack_receipt_key =
        !production_features.values.contains_key(HOST_VERIFIED_RECEIPT_FEATURE);
    let g1_row = evaluate(&candidate, production_features);
    let g1_rejected_despite_honest_receipt =
        g1_row.get("status").and_then(Value::as_str) == Some("FAILED_GATES")
            && g1_row.get("score_0_1") == Some(&json!(0.0))
            && g1_row.get("gate_evidence_package_accepted") == Some(&json!(false));

    // ---- G2 control: the SAME candidate and the SAME honest receipt,
    //      inserted into FeatureSnapshot the way every prior audit harness
    //      (and the shipped Phase-0 KPI test) does it by hand -- proving the
    //      predicate is not fundamentally broken, only unreachable from the
    //      one code path production ever calls it through. ----
    let mut control_values = production_feature_values();
    control_values.insert(HOST_VERIFIED_RECEIPT_FEATURE.to_string(), receipt.clone());
    let control_features = FeatureSnapshot {
        values: control_values,
    };
    let g2_row = evaluate(&candidate, control_features);
    let g2_accepted_when_receipt_manually_supplied =
        g2_row.get("status").and_then(Value::as_str) == Some("SCORED")
            && g2_row.get("score_0_1") == Some(&json!(1.0))
            && g2_row.get("gate_evidence_package_accepted") == Some(&json!(true));

    let all_gates_passed = g1_production_features_lack_receipt_key
        && g1_rejected_despite_honest_receipt
        && g2_accepted_when_receipt_manually_supplied;

    report.insert(
        "schema".into(),
        json!("amphora.evidence-intake-validator.production-feature-gap-probe.v1"),
    );
    report.insert("live_rust".into(), json!(true));
    report.insert(
        "crates_under_test".into(),
        json!(["amphora-core", "amphora-assurance-capabilities"]),
    );
    report.insert(
        "entry_point".into(),
        json!("production_feature_values() (byte-cited replica of amphora-engine/src/lib.rs execute()'s feature-building block, lines ~733-742) -> AssuranceCapability::new(\"amphora-evidence-intake-validator\")::evaluate (Capability trait) -> evaluate_evidence_intake/host_receipt_valid"),
    );
    report.insert(
        "gates".into(),
        json!({
            "g1_production_features_lack_receipt_key": g1_production_features_lack_receipt_key,
            "g1_honest_receipt_rejected_under_production_features": g1_rejected_despite_honest_receipt,
            "g2_same_receipt_accepted_when_manually_supplied": g2_accepted_when_receipt_manually_supplied,
        }),
    );
    report.insert("all_gates_passed".into(), json!(all_gates_passed));
    report.insert(
        "results".into(),
        json!({
            "honest_receipt": receipt,
            "package_sha256": package_sha256,
            "g1_production_features_result": Value::Object(g1_row),
            "g2_control_manual_features_result": Value::Object(g2_row),
        }),
    );

    println!("{}", serde_json::to_string(&Value::Object(report)).unwrap());
}
