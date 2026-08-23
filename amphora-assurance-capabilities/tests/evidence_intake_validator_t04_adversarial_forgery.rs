//! T-04 adversarial forgery probe for `amphora-evidence-intake-validator`.
//!
//! Reads real-crypto-constructed DSSE envelopes + host-verified-receipt
//! feature objects from `t04_cases.json` (built by
//! `benchmarks/adversarial-forgery-t04-v1/gen_cases.py` with real Ed25519
//! signing) and, for EVERY case, calls BOTH:
//!   (1) `amphora_core::verify_dsse` -- the REAL native DSSE/Ed25519
//!       verification function already present in this crate's dependency
//!       (used by the sibling CroProtocolPackage capability in this exact
//!       file, a few hundred lines above `evaluate_evidence_intake`).
//!   (2) `AssuranceCapability::new("amphora-evidence-intake-validator")
//!        .evaluate(...)` -- the actual shipped decision, fed the case's
//!        (possibly forged) 11-field host-verified-receipt object.
//!
//! Writes a JSON report of both results per case to CARGO_TARGET_TMPDIR.
//! Does not modify any shipped evidence, KPI, or manifest file.

use std::fs;
use std::path::PathBuf;

use amphora_assurance_capabilities::{AssuranceCapability, HOST_VERIFIED_RECEIPT_FEATURE};
use amphora_core::{
    verify_dsse, Capability, CandidateEnvelope, DsseEnvelope, DsseSignature, ExecutionContext,
    FeatureSnapshot, TrustStore,
};
use serde_json::Value;

const EVIDENCE_INTAKE: &str = "amphora-evidence-intake-validator";

fn workspace_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .expect("crate has a parent workspace")
        .to_path_buf()
}

fn cases_path() -> PathBuf {
    workspace_root().join(
        "amphora-evidence-intake-validator/evidence/phase0/repairs/T-04/work/t04_cases.json",
    )
}

fn report_path() -> PathBuf {
    PathBuf::from(env!("CARGO_TARGET_TMPDIR")).join("t04-adversarial-forgery-report.json")
}

fn context() -> ExecutionContext {
    ExecutionContext {
        run_id: "t04-adversarial-forgery-evidence-intake-validator".into(),
        deterministic_seed: 20260805,
        lineage: Value::Null,
    }
}

fn decode_hex(s: &str) -> Vec<u8> {
    assert_eq!(s.len() % 2, 0, "hex string must have even length");
    (0..s.len())
        .step_by(2)
        .map(|i| u8::from_str_radix(&s[i..i + 2], 16).expect("valid hex byte"))
        .collect()
}

fn build_trust_store(keys: &[Value]) -> TrustStore {
    let mut ts = TrustStore::default();
    for k in keys {
        let key_id = k["key_id"].as_str().unwrap().to_string();
        let hex = k["public_key_hex"].as_str().unwrap();
        let bytes = decode_hex(hex);
        let arr: [u8; 32] = bytes.try_into().expect("32-byte ed25519 pubkey");
        ts.insert(key_id.clone(), arr).expect("insert trust store key");
        if k["revoke"].as_bool().unwrap_or(false) {
            ts.revoke(key_id);
        }
    }
    ts
}

fn envelope_from_json(v: &Value) -> DsseEnvelope {
    DsseEnvelope {
        payload_type: v["payloadType"].as_str().unwrap().to_string(),
        payload: v["payload"].as_str().unwrap().to_string(),
        signatures: v["signatures"]
            .as_array()
            .unwrap()
            .iter()
            .map(|s| DsseSignature {
                keyid: s["keyid"].as_str().unwrap().to_string(),
                sig: s["sig"].as_str().unwrap().to_string(),
            })
            .collect(),
    }
}

#[test]
fn t04_adversarial_forgery_report() {
    // The 7 MB forgery corpus is deliberately omitted from the GitHub handoff
    // (see the explicit rule in .gitignore and the DATASETS.local.json entry).
    // Its generator IS checked in, so this is reproducible on demand.
    if !cases_path().exists() {
        eprintln!(
            "SKIP t04_adversarial_forgery_report: {} is absent. Regenerate it with:\n  \
             python3 amphora-evidence-intake-validator/evidence/phase0/repairs/T-04/work/gen_t04_cases.py",
            cases_path().display()
        );
        return;
    }
    let raw = fs::read_to_string(cases_path()).expect("t04_cases.json must be readable");
    let doc: Value = serde_json::from_str(&raw).expect("valid json");

    let trust_store = build_trust_store(doc["keys_to_register_in_test_trust_store"].as_array().unwrap());
    let ctx = context();

    let cases = doc["cases"].as_array().expect("cases array");
    assert!(cases.len() >= 12, "expected all 12 T-04 cases present");

    let mut records: Vec<Value> = Vec::new();
    let mut n_forgery_admitted = 0usize;
    let mut n_forgery_total = 0usize;
    let mut n_valid_unusual_accepted = 0usize;
    let mut n_valid_unusual_total = 0usize;
    let mut n_positive_control_rejected = 0usize;

    for case in cases {
        let case_id = case["case_id"].as_str().unwrap().to_string();
        let family = case["family"].as_str().unwrap().to_string();
        let directive_category = case["directive_category"].clone();

        // (1) REAL native DSSE/Ed25519 verification via amphora_core::verify_dsse.
        let envelope = envelope_from_json(&case["envelope"]);
        let dsse_result = verify_dsse(&envelope, &trust_store);
        let dsse_ok = dsse_result.is_ok();
        let dsse_error = dsse_result.as_ref().err().map(|e| e.to_string());

        // (2) REAL shipped predicate decision, fed the case's receipt object.
        let candidate = CandidateEnvelope::from_value(case["candidate"].clone())
            .expect("valid candidate envelope");
        let mut features = FeatureSnapshot::default();
        features
            .values
            .insert(HOST_VERIFIED_RECEIPT_FEATURE.into(), case["receipt"].clone());
        let out = AssuranceCapability::new(EVIDENCE_INTAKE)
            .expect("capability constructs")
            .evaluate(&candidate, &features, &ctx)
            .expect("evaluate ok");
        let predicate_accepted = out.gates.get("evidence_package_accepted") == Some(&Value::Bool(true));
        let predicate_status = out.status.clone();

        let expect_dsse_ok = case["expect_dsse_verify_dsse_ok"].as_bool().unwrap();
        assert_eq!(
            dsse_ok, expect_dsse_ok,
            "case {case_id}: real DSSE verify_dsse result did not match the ground truth this case was constructed to produce"
        );

        let divergence = predicate_accepted && !dsse_ok;

        if family == "forgery" {
            n_forgery_total += 1;
            if predicate_accepted {
                n_forgery_admitted += 1;
            }
        } else if family == "valid_unusual" {
            n_valid_unusual_total += 1;
            if predicate_accepted {
                n_valid_unusual_accepted += 1;
            }
        } else if family == "positive_control" {
            if !predicate_accepted {
                n_positive_control_rejected += 1;
            }
        }

        records.push(serde_json::json!({
            "case_id": case_id,
            "family": family,
            "directive_category": directive_category,
            "real_dsse_verify_dsse_ok": dsse_ok,
            "real_dsse_verify_dsse_error": dsse_error,
            "predicate_status": predicate_status,
            "predicate_evidence_package_accepted": predicate_accepted,
            "real_crypto_says_reject_but_predicate_accepted": divergence,
        }));
    }

    let report = serde_json::json!({
        "schema": "amphora.evidence-intake-validator.t04-adversarial-forgery-report.v1",
        "records": records,
        "counts": {
            "n_forgery_total": n_forgery_total,
            "n_forgery_admitted_by_predicate": n_forgery_admitted,
            "n_valid_unusual_total": n_valid_unusual_total,
            "n_valid_unusual_accepted_by_predicate": n_valid_unusual_accepted,
            "n_positive_control_correctly_rejected": n_positive_control_rejected,
        },
        "live_authority_under_test": {
            "predicate": "amphora-assurance-capabilities/src/lib.rs :: evaluate_evidence_intake, host_receipt_valid",
            "dsse_verifier": "amphora-core/src/crypto.rs :: verify_dsse (real Ed25519 + real revocation check)",
            "modified": false,
        },
    });
    fs::write(report_path(), serde_json::to_string_pretty(&report).unwrap())
        .expect("write report");
    eprintln!("wrote {}", report_path().display());
    eprintln!("{}", serde_json::to_string_pretty(&report).unwrap());
}
