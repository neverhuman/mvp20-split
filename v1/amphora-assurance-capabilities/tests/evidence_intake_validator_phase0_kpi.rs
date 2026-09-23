//! Phase-0 KPI harness for `amphora-evidence-intake-validator`.
//!
//! Drives the deterministic `evaluate_evidence_intake` runtime (via
//! AssuranceCapability::new("amphora-evidence-intake-validator")) which
//! rejects every evidence package unless the FeatureSnapshot carries a
//! host-verified Ed25519 receipt with all 11 required fields matching the
//! candidate identity and package SHA-256 bit-exact. Verifies 3 positive
//! scenarios (SCORED) and 14 adversarial mutations (each targeting one
//! receipt field), plus 3 fail-closed probes on unsupported inputs.

use std::collections::BTreeMap;
use std::fs;
use std::path::PathBuf;

use amphora_assurance_capabilities::{
    AssuranceCapability, HOST_VERIFIED_RECEIPT_FEATURE, HOST_VERIFIED_RECEIPT_SCHEMA,
};
use amphora_core::{
    canonicalize, stable_hash, Capability, CandidateEnvelope, ExecutionContext, FeatureSnapshot,
};
use serde_json::{json, Map, Value};
use sha2::{Digest, Sha256};

const EVIDENCE_INTAKE: &str = "amphora-evidence-intake-validator";

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
        .join("amphora-evidence-intake-validator/evidence/phase0/benchmark/benchmark-lock.v1.json")
}

// SCHEMA-ERA FIX (B2). The shipped artifact
// `amphora-evidence-intake-validator/evidence/phase0/benchmark/result.v1.json` has exactly one
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
        .join("amphora-evidence-intake-validator-phase0-kpi-result.v1.json")
}

fn file_sha256(bytes: &[u8]) -> String {
    let mut digest = Sha256::new();
    digest.update(bytes);
    format!("{:x}", digest.finalize())
}

fn context() -> ExecutionContext {
    ExecutionContext {
        run_id: "phase0-kpi-evidence-intake-validator".into(),
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

fn evidence_candidate(id: &str, payload_extra: Value) -> CandidateEnvelope {
    let mut package = Map::new();
    package.insert("payload_kind".into(), Value::String("lab_measurement".into()));
    package.insert("payload_extra".into(), payload_extra);
    CandidateEnvelope::from_value(json!({
        "candidate_id": id,
        "candidate_type": "evidence_package",
        "evidence_refs": {"evidence_package": Value::Object(package)}
    }))
    .expect("valid evidence candidate")
}

fn build_valid_receipt(candidate: &CandidateEnvelope) -> Value {
    let package = &candidate.value()["evidence_refs"]["evidence_package"];
    let package_sha256 = stable_hash(package);
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
        "verifier_id": "host-trust-kernel-phase0"
    })
}

fn features_with(receipt: Option<Value>) -> FeatureSnapshot {
    let mut features = FeatureSnapshot::default();
    if let Some(r) = receipt {
        features
            .values
            .insert(HOST_VERIFIED_RECEIPT_FEATURE.into(), r);
    }
    features
}

fn evaluate(candidate: &CandidateEnvelope, features: &FeatureSnapshot) -> amphora_core::ModuleResult {
    AssuranceCapability::new(EVIDENCE_INTAKE)
        .expect("capability constructs")
        .evaluate(candidate, features, &context())
        .expect("evaluate ok")
}

fn mutate(receipt: &Value, key: &str, value: Value) -> Value {
    let mut obj = receipt.as_object().unwrap().clone();
    obj.insert(key.into(), value);
    Value::Object(obj)
}

fn remove_key(receipt: &Value, key: &str) -> Value {
    let mut obj = receipt.as_object().unwrap().clone();
    obj.remove(key);
    Value::Object(obj)
}

struct MutationProbe {
    probe_id: &'static str,
    mutated_receipt: Value,
    industrial_context: &'static str,
}

fn positive_scenarios() -> Vec<(String, CandidateEnvelope)> {
    vec![
        (
            "baseline-primer-lab-measurement".into(),
            evidence_candidate(
                "phase0-kpi-primer-lab",
                json!({"measurement": "gel_time_h", "value": 4.2}),
            ),
        ),
        (
            "topcoat-thickness-measurement".into(),
            evidence_candidate(
                "phase0-kpi-topcoat-dft",
                json!({"measurement": "dft_mil", "value": 3.1, "instrument": "elcometer"}),
            ),
        ),
        (
            "adhesive-pull-off-strength".into(),
            evidence_candidate(
                "phase0-kpi-adhesive-pull",
                json!({"measurement": "pull_off_mpa", "value": 8.5, "n_replicates": 5}),
            ),
        ),
    ]
}

fn compute_report() -> Value {
    let ctx = context();
    let mut per_scenario: Vec<Value> = Vec::new();

    // Positive scenarios.
    let scenarios = positive_scenarios();
    let n_positive = scenarios.len();

    let mut scored_pass = 0_usize;
    let mut score_1_pass = 0_usize;
    let mut host_gate_pass = 0_usize;
    let mut accepted_gate_pass = 0_usize;
    let mut signature_metric_pass = 0_usize;
    let mut package_sha_metric_pass = 0_usize;
    let mut envelope_pass_positive = 0_usize;
    let mut byte_replay_pass_positive = 0_usize;

    for (sid, candidate) in &scenarios {
        let receipt = build_valid_receipt(candidate);
        let features = features_with(Some(receipt.clone()));
        let out = evaluate(candidate, &features);

        let scored = out.status == "SCORED";
        if scored { scored_pass += 1; }
        let score_1 = out.score_0_1 == Some(1.0);
        if score_1 { score_1_pass += 1; }
        let host_gate = out.gates.get("host_verified_signature_receipt") == Some(&json!(true));
        if host_gate { host_gate_pass += 1; }
        let accepted = out.gates.get("evidence_package_accepted") == Some(&json!(true));
        if accepted { accepted_gate_pass += 1; }
        let signature = out.metrics.get("signature_verification").and_then(Value::as_str)
            == Some("HOST_VERIFIED_ED25519");
        if signature { signature_metric_pass += 1; }
        let expected_hash = stable_hash(&candidate.value()["evidence_refs"]["evidence_package"]);
        let package_sha = out.metrics.get("package_sha256").and_then(Value::as_str)
            == Some(expected_hash.as_str());
        if package_sha { package_sha_metric_pass += 1; }

        let out_json = serde_json::to_value(&out).unwrap();
        let envelope_ok = contains_banned_key(&out_json).is_none();
        if envelope_ok { envelope_pass_positive += 1; }

        let replay = AssuranceCapability::new(EVIDENCE_INTAKE)
            .unwrap()
            .evaluate(candidate, &features, &ctx)
            .unwrap();
        let byte_ok = serde_json::to_vec(&out).unwrap() == serde_json::to_vec(&replay).unwrap();
        if byte_ok { byte_replay_pass_positive += 1; }

        per_scenario.push(json!({
            "scenario_kind": "positive",
            "scenario_id": sid,
            "candidate_id": candidate.candidate_id(),
            "status": out.status,
            "score_0_1": out.score_0_1,
            "host_verified_signature_receipt_gate": out.gates.get("host_verified_signature_receipt"),
            "evidence_package_accepted_gate": out.gates.get("evidence_package_accepted"),
            "signature_verification": out.metrics.get("signature_verification"),
            "package_sha256": out.metrics.get("package_sha256"),
            "authority_envelope_preserved": envelope_ok,
            "byte_stable_two_replay": byte_ok,
        }));
    }

    // Adversarial mutations (14 probes).
    let anchor_candidate = evidence_candidate(
        "phase0-kpi-adversarial-anchor",
        json!({"measurement": "adhesion_mpa", "value": 8.0}),
    );
    let baseline_receipt = build_valid_receipt(&anchor_candidate);
    let other_candidate = evidence_candidate(
        "phase0-kpi-different-candidate",
        json!({"measurement": "different"}),
    );

    let mutations: Vec<MutationProbe> = vec![
        MutationProbe {
            probe_id: "no_host_receipt_feature",
            mutated_receipt: Value::Null,
            industrial_context: "candidate has evidence_package but FeatureSnapshot omits the host_verified_receipt key entirely",
        },
        MutationProbe {
            probe_id: "wrong_schema_string",
            mutated_receipt: mutate(&baseline_receipt, "schema", json!("amphora.wrong-schema.v99")),
            industrial_context: "receipt schema string does not match HOST_VERIFIED_RECEIPT_SCHEMA",
        },
        MutationProbe {
            probe_id: "accepted_false",
            mutated_receipt: mutate(&baseline_receipt, "accepted", json!(false)),
            industrial_context: "receipt.accepted=false - host explicitly did not accept",
        },
        MutationProbe {
            probe_id: "signature_verified_false",
            mutated_receipt: mutate(&baseline_receipt, "signature_verified", json!(false)),
            industrial_context: "receipt.signature_verified=false - signature check did not succeed",
        },
        MutationProbe {
            probe_id: "revocation_unchecked",
            mutated_receipt: mutate(&baseline_receipt, "revocation_checked", json!(false)),
            industrial_context: "receipt.revocation_checked=false - certificate revocation status unknown",
        },
        MutationProbe {
            probe_id: "receipt_stale",
            mutated_receipt: mutate(&baseline_receipt, "fresh", json!(false)),
            industrial_context: "receipt.fresh=false - receipt is stale beyond freshness window",
        },
        MutationProbe {
            probe_id: "wrong_signature_algorithm_es256",
            mutated_receipt: mutate(&baseline_receipt, "signature_algorithm", json!("ES256")),
            industrial_context: "receipt.signature_algorithm=ES256 - only Ed25519 accepted",
        },
        MutationProbe {
            probe_id: "trust_store_untrusted",
            mutated_receipt: mutate(&baseline_receipt, "trust_store_status", json!("UNTRUSTED")),
            industrial_context: "receipt.trust_store_status=UNTRUSTED - signing key not in trust store",
        },
        MutationProbe {
            probe_id: "wrong_candidate_id",
            mutated_receipt: mutate(
                &baseline_receipt,
                "candidate_id",
                json!(other_candidate.candidate_id()),
            ),
            industrial_context: "receipt.candidate_id references different candidate - misbound receipt",
        },
        MutationProbe {
            probe_id: "wrong_contract_hash",
            mutated_receipt: mutate(
                &baseline_receipt,
                "candidate_contract_hash_v1",
                json!("f".repeat(64)),
            ),
            industrial_context: "receipt.candidate_contract_hash_v1 does not match candidate contract hash",
        },
        MutationProbe {
            probe_id: "wrong_package_sha256",
            mutated_receipt: mutate(&baseline_receipt, "package_sha256", json!("0".repeat(64))),
            industrial_context: "receipt.package_sha256 does not match candidate evidence_package hash",
        },
        MutationProbe {
            probe_id: "empty_verifier_id",
            mutated_receipt: mutate(&baseline_receipt, "verifier_id", json!("")),
            industrial_context: "receipt.verifier_id is empty string - no verifier identity",
        },
        MutationProbe {
            probe_id: "receipt_has_twelfth_extra_field",
            mutated_receipt: mutate(
                &baseline_receipt,
                "adversary_extra_field",
                json!("payload smuggle"),
            ),
            industrial_context: "receipt has 12 fields instead of exact 11 - fails strict len check",
        },
        MutationProbe {
            probe_id: "receipt_missing_one_required_field",
            mutated_receipt: remove_key(&baseline_receipt, "revocation_checked"),
            industrial_context: "receipt has 10 fields (revocation_checked stripped) - fails strict len check",
        },
    ];

    let n_probes = mutations.len();
    let mut mutation_pass = 0_usize;
    let mut envelope_pass_probe = 0_usize;
    let mut byte_replay_pass_probe = 0_usize;

    for probe in &mutations {
        let features = if probe.mutated_receipt.is_null() {
            features_with(None)
        } else {
            features_with(Some(probe.mutated_receipt.clone()))
        };
        let out = evaluate(&anchor_candidate, &features);

        let mutated_ok = out.status == "FAILED_GATES"
            && out.score_0_1 == Some(0.0)
            && out.gates.get("host_verified_signature_receipt") == Some(&json!(false))
            && out.gates.get("evidence_package_accepted") == Some(&json!(false));
        if mutated_ok { mutation_pass += 1; }

        let out_json = serde_json::to_value(&out).unwrap();
        let envelope_ok = contains_banned_key(&out_json).is_none();
        if envelope_ok { envelope_pass_probe += 1; }

        let replay = AssuranceCapability::new(EVIDENCE_INTAKE)
            .unwrap()
            .evaluate(&anchor_candidate, &features, &ctx)
            .unwrap();
        let byte_ok = serde_json::to_vec(&out).unwrap() == serde_json::to_vec(&replay).unwrap();
        if byte_ok { byte_replay_pass_probe += 1; }

        per_scenario.push(json!({
            "scenario_kind": "adversarial",
            "probe_id": probe.probe_id,
            "industrial_context": probe.industrial_context,
            "status": out.status,
            "score_0_1": out.score_0_1,
            "host_verified_signature_receipt_gate": out.gates.get("host_verified_signature_receipt"),
            "evidence_package_accepted_gate": out.gates.get("evidence_package_accepted"),
            "mutation_fail_closed": mutated_ok,
            "authority_envelope_preserved": envelope_ok,
            "byte_stable_two_replay": byte_ok,
        }));
    }

    // Fail-closed probes on unsupported inputs.
    let mut ff_pass = 0_usize;
    let mut ff_probes: Vec<Value> = Vec::new();

    let wrong = CandidateEnvelope::from_value(json!({
        "candidate_id": "wrong-type",
        "candidate_type": "formulation",
        "formulation": {"part_A": {"resin": 1.0}, "part_B": {"hardener": 1.0}}
    }))
    .expect("candidate parses");
    let is_err = AssuranceCapability::new(EVIDENCE_INTAKE)
        .unwrap()
        .evaluate(&wrong, &FeatureSnapshot::default(), &ctx)
        .is_err();
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

    let n_pos = n_positive.max(1) as f64;
    let n_probe = n_probes.max(1) as f64;
    let n_all = (n_positive + n_probes).max(1) as f64;
    let all_envelope_pass = envelope_pass_positive + envelope_pass_probe;
    let all_byte_replay_pass = byte_replay_pass_positive + byte_replay_pass_probe;

    let kpi = json!({
        "positive_scenarios_scored_rate": {
            "observed": scored_pass as f64 / n_pos,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": n_positive,
            "passed": scored_pass as f64 / n_pos >= 1.0,
        },
        "positive_scenarios_score_one_rate": {
            "observed": score_1_pass as f64 / n_pos,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": n_positive,
            "passed": score_1_pass as f64 / n_pos >= 1.0,
        },
        "positive_host_verified_signature_receipt_gate_true_rate": {
            "observed": host_gate_pass as f64 / n_pos,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": n_positive,
            "passed": host_gate_pass as f64 / n_pos >= 1.0,
        },
        "positive_evidence_package_accepted_gate_true_rate": {
            "observed": accepted_gate_pass as f64 / n_pos,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": n_positive,
            "passed": accepted_gate_pass as f64 / n_pos >= 1.0,
        },
        "positive_signature_verification_metric_ed25519_rate": {
            "observed": signature_metric_pass as f64 / n_pos,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": n_positive,
            "passed": signature_metric_pass as f64 / n_pos >= 1.0,
        },
        "positive_package_sha256_metric_matches_stable_hash_rate": {
            "observed": package_sha_metric_pass as f64 / n_pos,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": n_positive,
            "passed": package_sha_metric_pass as f64 / n_pos >= 1.0,
        },
        "adversarial_receipt_mutation_fail_closed_rate": {
            "observed": mutation_pass as f64 / n_probe,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": n_probes,
            "passed": mutation_pass as f64 / n_probe >= 1.0,
        },
        "authority_envelope_preservation_rate": {
            "observed": all_envelope_pass as f64 / n_all,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": n_positive + n_probes,
            "passed": all_envelope_pass as f64 / n_all >= 1.0,
        },
        "unsupported_input_fail_closed_rate": {
            "observed": ff_rate,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "probe_sample_size": ff_total,
            "probes": ff_probes,
            "passed": ff_rate >= 1.0,
        },
        "byte_stable_two_replay_rate": {
            "observed": all_byte_replay_pass as f64 / n_all,
            "direction": "MAXIMIZE",
            "sample_size": n_positive + n_probes,
            "note": "observational; evaluate_evidence_intake invoked twice per scenario produces byte-identical ModuleResult",
        },
    });

    let benchmark_lock_bytes = fs::read(benchmark_lock_path()).expect("benchmark-lock readable");
    let benchmark_lock_sha256 = file_sha256(&benchmark_lock_bytes);

    let diagnostic = json!({
        "schema": "amphora.module-phase0-benchmark-diagnostic.v1",
        "module_id": "amphora-evidence-intake-validator",
        "kpi": kpi.clone(),
        "records": per_scenario.clone(),
        "passed": kpi["positive_scenarios_scored_rate"]["passed"] == json!(true)
            && kpi["positive_scenarios_score_one_rate"]["passed"] == json!(true)
            && kpi["positive_host_verified_signature_receipt_gate_true_rate"]["passed"] == json!(true)
            && kpi["positive_evidence_package_accepted_gate_true_rate"]["passed"] == json!(true)
            && kpi["positive_signature_verification_metric_ed25519_rate"]["passed"] == json!(true)
            && kpi["positive_package_sha256_metric_matches_stable_hash_rate"]["passed"] == json!(true)
            && kpi["adversarial_receipt_mutation_fail_closed_rate"]["passed"] == json!(true)
            && kpi["authority_envelope_preservation_rate"]["passed"] == json!(true)
            && kpi["unsupported_input_fail_closed_rate"]["passed"] == json!(true),
    });
    let diagnostic_bytes_canonical =
        serde_json::to_vec(&canonicalize(&diagnostic)).expect("canonical bytes");
    let diagnostic_sha256 = file_sha256(&diagnostic_bytes_canonical);

    let mut result = Map::new();
    result.insert("schema".into(), json!("amphora.module-phase0-benchmark-result.v1"));
    result.insert("module_id".into(), json!("amphora-evidence-intake-validator"));
    result.insert(
        "benchmark_id".into(),
        json!("amphora-evidence-intake-validator-phase0-host-receipt-integrity-v1"),
    );
    result.insert("benchmark_lock_sha256".into(), json!(benchmark_lock_sha256));
    result.insert("dataset_fixture_sha256".into(), json!(benchmark_lock_sha256));
    result.insert(
        "dataset_fixture_note".into(),
        json!("evidence-intake-validator Phase-0 harness constructs its 3 positive scenarios + 14 adversarial mutations + 3 fail-closed probes in-Rust and does not consume an external fixture. SHA-256 recorded is the on-disk benchmark-lock hash."),
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
fn evidence_intake_validator_phase0_kpi_report_is_deterministic_and_gates_pass() {
    let first = compute_report();
    let first_bytes = serde_json::to_vec(&first).expect("canonical");
    let second_bytes = serde_json::to_vec(&compute_report()).expect("canonical");
    assert_eq!(first_bytes, second_bytes, "KPI report is not byte-stable");

    let kpi = &first["kpi"];
    for gate in [
        "positive_scenarios_scored_rate",
        "positive_scenarios_score_one_rate",
        "positive_host_verified_signature_receipt_gate_true_rate",
        "positive_evidence_package_accepted_gate_true_rate",
        "positive_signature_verification_metric_ed25519_rate",
        "positive_package_sha256_metric_matches_stable_hash_rate",
        "adversarial_receipt_mutation_fail_closed_rate",
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
