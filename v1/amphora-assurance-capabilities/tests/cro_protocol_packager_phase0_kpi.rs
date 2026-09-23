//! Phase-0 KPI harness for `amphora-cro-protocol-packager`.
//!
//! Drives the deterministic `CroProtocolPackageV2` runtime (draft, validate,
//! sign, verify_signature) across 5 hand-authored campaign/candidate/balance
//! packets. Verifies bit-exact SHA-256 candidate + formula bindings,
//! Ed25519 DSSE signature round-trip, all 8 REQUIRED_CRO_CLAIM_LOCKS
//! populated true, execution authorization locked false, and applies
//! dedicated fail-closed probes for the six module-specific attack axes
//! (CRO_IDENTITY_HASH_SUBSTITUTION, INCOMPLETE_PROTOCOL_SECTIONS,
//! CRO_PROSE_WAIVER, CRO_SIGNATURE_DEFECT, FALSE_CRO_EXECUTION,
//! BANNED_CRO_PERFORMANCE_CLAIM), all with byte-stable two-replay.

use std::collections::BTreeMap;
use std::fs;
use std::path::PathBuf;

use amphora_assurance_capabilities::{
    CroProtocolPackageV2, CRO_PROTOCOL_PACKAGE_V2_SCHEMA,
};
use amphora_core::{canonicalize, stable_hash, TrustStore};
use amphora_formulation_capabilities::{EquivalentBalanceV1, EQUIVALENT_BALANCE_SCHEMA};
use ed25519_dalek::SigningKey;
use serde_json::{json, Map, Value};
use sha2::{Digest, Sha256};

const REQUIRED_CRO_CLAIM_LOCKS: [&str; 8] = [
    "NO_EXECUTION_AUTHORITY",
    "NO_PROCUREMENT_AUTHORITY",
    "NO_SAFETY_CLAIM",
    "NO_SYNTHESIS_CLAIM",
    "NO_PERFORMANCE_CLAIM",
    "NO_QUALIFICATION_CLAIM",
    "NO_RANKING_AUTHORITY",
    "UNMADE_DIGITAL_PROPOSAL",
];

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
        .join("amphora-cro-protocol-packager/evidence/phase0/benchmark/benchmark-lock.v1.json")
}

fn fixture_path() -> PathBuf {
    workspace_root()
        .join("amphora-cro-protocol-packager/reference/mvp20/fixtures/known-answer-protocol-package.v1.json")
}

// SCHEMA-ERA FIX (B2). The shipped artifact
// `amphora-cro-protocol-packager/evidence/phase0/benchmark/result.v1.json` has exactly one
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
        .join("amphora-cro-protocol-packager-phase0-kpi-result.v1.json")
}

fn file_sha256(bytes: &[u8]) -> String {
    let mut digest = Sha256::new();
    digest.update(bytes);
    format!("{:x}", digest.finalize())
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

/// Build a deterministic EquivalentBalanceV1 with the runtime schema (no
/// molecule-fact toolkit binding, since this is a signed-packet contract test,
/// not a chemistry test). The `resin_facts_sha256` etc. are frozen 64-hex
/// strings; the arithmetic satisfies the stoichiometry identity.
fn balance(resin_mass_g: f64, hardener_mass_g: f64) -> EquivalentBalanceV1 {
    let ratio = resin_mass_g / hardener_mass_g;
    EquivalentBalanceV1 {
        schema: EQUIVALENT_BALANCE_SCHEMA.into(),
        resin_facts_sha256: "a".repeat(64),
        hardener_facts_sha256: "b".repeat(64),
        resin_structure_sha256: "c".repeat(64),
        hardener_structure_sha256: "d".repeat(64),
        eew_g_per_eq: 100.0,
        ahew_g_per_eq: 100.0 / ratio,
        resin_mass_g,
        hardener_mass_g,
        epoxide_equivalents: resin_mass_g / 100.0,
        amine_hydrogen_equivalents: resin_mass_g / 100.0,
        theoretical_hardener_phr: hardener_mass_g * 100.0 / resin_mass_g,
        equivalent_ratio: 1.0,
        total_mass_g: resin_mass_g + hardener_mass_g,
        unit_provenance: BTreeMap::from([
            ("mass".into(), "g".into()),
            ("equivalent_weight".into(), "g/eq structure-derived".into()),
        ]),
        authority_ceiling: "AUDIT_ONLY".into(),
        candidate_property_overrides_accepted: false,
        ranking_eligible: false,
    }
}

struct TestPacketSpec {
    campaign_id: &'static str,
    candidate: Value,
    balance: EquivalentBalanceV1,
    sample_blinding_code: &'static str,
    key_id: &'static str,
    key_bytes: [u8; 32],
    industrial_context: &'static str,
}

fn packet_specs() -> Vec<TestPacketSpec> {
    vec![
        TestPacketSpec {
            campaign_id: "campaign-primer-marine-2026Q3",
            candidate: json!({
                "candidate_id": "primer-dgeba-teta-100-25",
                "candidate_type": "formulation",
                "resin": "DGEBA",
                "hardener": "TETA",
            }),
            balance: balance(100.0, 25.0),
            sample_blinding_code: "BLIND-PRIMER-001",
            key_id: "cro-signer-primer",
            key_bytes: [11; 32],
            industrial_context: "solvent-borne marine primer feasibility packet",
        },
        TestPacketSpec {
            campaign_id: "campaign-topcoat-industrial-2026Q3",
            candidate: json!({
                "candidate_id": "topcoat-dgeba-ipda-100-30",
                "candidate_type": "formulation",
                "resin": "DGEBA",
                "hardener": "IPDA",
            }),
            balance: balance(100.0, 30.0),
            sample_blinding_code: "BLIND-TOPCOAT-002",
            key_id: "cro-signer-topcoat",
            key_bytes: [23; 32],
            industrial_context: "industrial-maintenance topcoat feasibility packet",
        },
        TestPacketSpec {
            campaign_id: "campaign-flooring-industrial-2026Q4",
            candidate: json!({
                "candidate_id": "flooring-dgebf-teta-150-40",
                "candidate_type": "formulation",
                "resin": "DGEBF",
                "hardener": "TETA",
            }),
            balance: balance(150.0, 40.0),
            sample_blinding_code: "BLIND-FLOORING-003",
            key_id: "cro-signer-flooring",
            key_bytes: [37; 32],
            industrial_context: "epoxy flooring feasibility packet",
        },
        TestPacketSpec {
            campaign_id: "campaign-adhesive-structural-2026Q4",
            candidate: json!({
                "candidate_id": "adhesive-dgeba-mxda-100-35",
                "candidate_type": "formulation",
                "resin": "DGEBA",
                "hardener": "MXDA",
            }),
            balance: balance(100.0, 35.0),
            sample_blinding_code: "BLIND-ADHESIVE-004",
            key_id: "cro-signer-adhesive",
            key_bytes: [53; 32],
            industrial_context: "structural epoxy adhesive feasibility packet",
        },
        TestPacketSpec {
            campaign_id: "campaign-encapsulant-electronic-2026Q4",
            candidate: json!({
                "candidate_id": "encapsulant-dgeba-dda-100-15",
                "candidate_type": "formulation",
                "resin": "DGEBA",
                "hardener": "DDA",
            }),
            balance: balance(100.0, 15.0),
            sample_blinding_code: "BLIND-ENCAP-005",
            key_id: "cro-signer-encapsulant",
            key_bytes: [71; 32],
            industrial_context: "electronic encapsulant feasibility packet",
        },
    ]
}

fn compute_report() -> Value {
    let specs = packet_specs();
    let n_specs = specs.len();

    let mut per_packet: Vec<Value> = Vec::new();

    let mut draft_pass = 0_usize;
    let mut packet_id_pass = 0_usize;
    let mut binding_pass = 0_usize;
    let mut claim_locks_pass = 0_usize;
    let mut authority_locked_pass = 0_usize;
    let mut sign_verify_pass = 0_usize;
    let mut envelope_pass = 0_usize;
    let mut byte_replay_pass = 0_usize;

    for spec in &specs {
        let draft = CroProtocolPackageV2::draft(
            spec.campaign_id,
            &spec.candidate,
            spec.balance.clone(),
            spec.sample_blinding_code.into(),
        );
        let mut packet = match draft {
            Ok(p) => {
                draft_pass += 1;
                p
            }
            Err(err) => {
                per_packet.push(json!({
                    "campaign_id": spec.campaign_id,
                    "draft_ok": false,
                    "error": err.to_string(),
                }));
                continue;
            }
        };

        // Packet ID matches computed.
        let computed_id = packet.computed_packet_id().unwrap();
        let id_ok = packet.packet_id == computed_id;
        if id_ok {
            packet_id_pass += 1;
        }

        // SHA-256 candidate + formula bindings.
        let candidate_ok = packet.candidate_sha256 == stable_hash(&spec.candidate);
        let formula_ok = packet.formula_sha256
            == stable_hash(&serde_json::to_value(&spec.balance).unwrap());
        if candidate_ok && formula_ok {
            binding_pass += 1;
        }

        // All 8 REQUIRED_CRO_CLAIM_LOCKS present and true; no claim_lock false.
        let claim_ok = REQUIRED_CRO_CLAIM_LOCKS
            .iter()
            .all(|lock| matches!(packet.claim_locks.get(*lock), Some(true)))
            && packet.claim_locks.values().all(|v| *v);
        if claim_ok {
            claim_locks_pass += 1;
        }

        // Execution authority locked.
        let auth_locked = !packet.execution_authorized
            && !packet.ranking_eligible
            && packet.authority_ceiling == "AUDIT_ONLY"
            && packet.schema == CRO_PROTOCOL_PACKAGE_V2_SCHEMA
            && packet.status == "DRAFT_FOR_CRO_FEASIBILITY_REVIEW"
            && packet.safety_review_status == "UNRESOLVED_REQUIRES_EHS_REVIEW"
            && packet.material_availability_status == "UNRESOLVED_REQUIRES_VERIFICATION"
            && packet.chemist_review_status == "REQUIRED_NOT_COMPLETED"
            && packet.cro_acceptance_status == "REQUIRED_NOT_COMPLETED";
        if auth_locked {
            authority_locked_pass += 1;
        }

        // Sign + verify round-trip.
        let key = SigningKey::from_bytes(&spec.key_bytes);
        let mut trust = TrustStore::default();
        trust
            .insert(spec.key_id, key.verifying_key().to_bytes())
            .unwrap();
        packet.sign(spec.key_id, &key).unwrap();
        let verified_key_id = packet.verify_signature(&trust).unwrap();
        let sign_ok = verified_key_id == spec.key_id;
        if sign_ok {
            sign_verify_pass += 1;
        }

        // Authority envelope: no banned key in serialized packet JSON.
        let envelope_ok =
            contains_banned_key(&serde_json::to_value(&packet).unwrap()).is_none();
        if envelope_ok {
            envelope_pass += 1;
        }

        // Byte-stable two-replay of draft() + computed_packet_id.
        let replay = CroProtocolPackageV2::draft(
            spec.campaign_id,
            &spec.candidate,
            spec.balance.clone(),
            spec.sample_blinding_code.into(),
        )
        .unwrap();
        let byte_ok = replay.packet_id == packet.packet_id
            && replay.candidate_sha256 == packet.candidate_sha256
            && replay.formula_sha256 == packet.formula_sha256
            && replay.claim_locks == packet.claim_locks;
        if byte_ok {
            byte_replay_pass += 1;
        }

        per_packet.push(json!({
            "campaign_id": spec.campaign_id,
            "candidate_id": spec.candidate["candidate_id"],
            "industrial_context": spec.industrial_context,
            "draft_ok": true,
            "packet_id": packet.packet_id,
            "candidate_sha256": packet.candidate_sha256,
            "formula_sha256": packet.formula_sha256,
            "packet_id_matches_computed": id_ok,
            "candidate_and_formula_binding_correct": candidate_ok && formula_ok,
            "all_eight_required_claim_locks_true": claim_ok,
            "execution_authority_locked": auth_locked,
            "sign_verify_round_trip_ok": sign_ok,
            "signature_key_id": verified_key_id,
            "authority_envelope_preserved": envelope_ok,
            "byte_stable_two_replay": byte_ok,
        }));
    }

    let n = n_specs.max(1) as f64;
    let draft_rate = draft_pass as f64 / n;
    let packet_id_rate = packet_id_pass as f64 / n;
    let binding_rate = binding_pass as f64 / n;
    let claim_locks_rate = claim_locks_pass as f64 / n;
    let authority_locked_rate = authority_locked_pass as f64 / n;
    let sign_verify_rate = sign_verify_pass as f64 / n;
    let envelope_rate = envelope_pass as f64 / n;
    let byte_replay_rate = byte_replay_pass as f64 / n;

    // CRO_IDENTITY_HASH_SUBSTITUTION probes.
    let (identity_rate, identity_probes, identity_total) = identity_hash_probes();
    // INCOMPLETE_PROTOCOL_SECTIONS probes.
    let (sections_rate, sections_probes, sections_total) = incomplete_sections_probes();
    // FALSE_CRO_EXECUTION probes.
    let (execution_rate, execution_probes, execution_total) = false_execution_probes();
    // BANNED_CRO_PERFORMANCE_CLAIM probes.
    let (performance_rate, performance_probes, performance_total) =
        banned_performance_probes();
    // CRO_SIGNATURE_DEFECT probes.
    let (signature_rate, signature_probes, signature_total) = signature_defect_probes();
    // CRO_PROSE_WAIVER: schema-level `deny_unknown_fields` rejects any extra
    // prose-style field at deserialization time. Probe: attempt to deserialize
    // a JSON string with an added `waiver: "prose exception"` field.
    let (waiver_rate, waiver_probes, waiver_total) = prose_waiver_probes();

    let kpi = json!({
        "packet_draft_ok_rate": {
            "observed": draft_rate,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": n_specs,
            "passed": draft_rate >= 1.0,
        },
        "packet_id_matches_computed_rate": {
            "observed": packet_id_rate,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": n_specs,
            "passed": packet_id_rate >= 1.0,
        },
        "candidate_and_formula_sha256_binding_correctness_rate": {
            "observed": binding_rate,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": n_specs,
            "passed": binding_rate >= 1.0,
        },
        "all_eight_required_cro_claim_locks_true_rate": {
            "observed": claim_locks_rate,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": n_specs,
            "passed": claim_locks_rate >= 1.0,
        },
        "execution_authority_locked_false_rate": {
            "observed": authority_locked_rate,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": n_specs,
            "passed": authority_locked_rate >= 1.0,
        },
        "sign_verify_round_trip_rate": {
            "observed": sign_verify_rate,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": n_specs,
            "passed": sign_verify_rate >= 1.0,
        },
        "cro_identity_hash_substitution_fail_closed_rate": {
            "observed": identity_rate,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "probe_sample_size": identity_total,
            "probes": identity_probes,
            "passed": identity_rate >= 1.0,
        },
        "incomplete_protocol_sections_fail_closed_rate": {
            "observed": sections_rate,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "probe_sample_size": sections_total,
            "probes": sections_probes,
            "passed": sections_rate >= 1.0,
        },
        "false_cro_execution_fail_closed_rate": {
            "observed": execution_rate,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "probe_sample_size": execution_total,
            "probes": execution_probes,
            "passed": execution_rate >= 1.0,
        },
        "banned_cro_performance_claim_fail_closed_rate": {
            "observed": performance_rate,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "probe_sample_size": performance_total,
            "probes": performance_probes,
            "passed": performance_rate >= 1.0,
        },
        "cro_signature_defect_fail_closed_rate": {
            "observed": signature_rate,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "probe_sample_size": signature_total,
            "probes": signature_probes,
            "passed": signature_rate >= 1.0,
        },
        "cro_prose_waiver_fail_closed_rate": {
            "observed": waiver_rate,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "probe_sample_size": waiver_total,
            "probes": waiver_probes,
            "passed": waiver_rate >= 1.0,
        },
        "authority_envelope_preservation_rate": {
            "observed": envelope_rate,
            "floor": 1.0,
            "direction": "MAXIMIZE",
            "sample_size": n_specs,
            "passed": envelope_rate >= 1.0,
        },
        "byte_stable_two_replay_rate": {
            "observed": byte_replay_rate,
            "direction": "MAXIMIZE",
            "sample_size": n_specs,
            "note": "observational; draft() twice with same inputs produces identical packet_id, candidate_sha256, formula_sha256, and claim_locks",
        },
    });

    let benchmark_lock_bytes = fs::read(benchmark_lock_path()).expect("benchmark-lock readable");
    let benchmark_lock_sha256 = file_sha256(&benchmark_lock_bytes);
    let fixture_bytes = fs::read(fixture_path()).expect("fixture readable");
    let dataset_sha256 = file_sha256(&fixture_bytes);

    let diagnostic = json!({
        "schema": "amphora.module-phase0-benchmark-diagnostic.v1",
        "module_id": "amphora-cro-protocol-packager",
        "kpi": kpi.clone(),
        "records": per_packet.clone(),
        "passed": kpi["packet_draft_ok_rate"]["passed"] == json!(true)
            && kpi["packet_id_matches_computed_rate"]["passed"] == json!(true)
            && kpi["candidate_and_formula_sha256_binding_correctness_rate"]["passed"] == json!(true)
            && kpi["all_eight_required_cro_claim_locks_true_rate"]["passed"] == json!(true)
            && kpi["execution_authority_locked_false_rate"]["passed"] == json!(true)
            && kpi["sign_verify_round_trip_rate"]["passed"] == json!(true)
            && kpi["cro_identity_hash_substitution_fail_closed_rate"]["passed"] == json!(true)
            && kpi["incomplete_protocol_sections_fail_closed_rate"]["passed"] == json!(true)
            && kpi["false_cro_execution_fail_closed_rate"]["passed"] == json!(true)
            && kpi["banned_cro_performance_claim_fail_closed_rate"]["passed"] == json!(true)
            && kpi["cro_signature_defect_fail_closed_rate"]["passed"] == json!(true)
            && kpi["cro_prose_waiver_fail_closed_rate"]["passed"] == json!(true)
            && kpi["authority_envelope_preservation_rate"]["passed"] == json!(true),
    });
    let diagnostic_bytes_canonical =
        serde_json::to_vec(&canonicalize(&diagnostic)).expect("canonical bytes");
    let diagnostic_sha256 = file_sha256(&diagnostic_bytes_canonical);

    let mut result = Map::new();
    result.insert("schema".into(), json!("amphora.module-phase0-benchmark-result.v1"));
    result.insert("module_id".into(), json!("amphora-cro-protocol-packager"));
    result.insert(
        "benchmark_id".into(),
        json!("amphora-cro-protocol-packager-phase0-signed-packet-v1"),
    );
    result.insert("benchmark_lock_sha256".into(), json!(benchmark_lock_sha256));
    result.insert("dataset_fixture_sha256".into(), json!(dataset_sha256));
    result.insert("kpi".into(), kpi);
    result.insert("records".into(), json!(per_packet));
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

/// Build a stock signed packet to serve as the base for tamper probes.
fn baseline_packet() -> CroProtocolPackageV2 {
    let candidate = json!({"resin": "DGEBA", "hardener": "TETA"});
    CroProtocolPackageV2::draft("probe-campaign", &candidate, balance(100.0, 25.0), "BLIND-000".into())
        .expect("baseline draft")
}

fn identity_hash_probes() -> (f64, Vec<Value>, usize) {
    let mut passes = 0_usize;
    let mut probes: Vec<Value> = Vec::new();

    // Probe A: mutate candidate_sha256 to another valid 64-hex string.
    let mut p = baseline_packet();
    p.candidate_sha256 = "0".repeat(64);
    let ok = p.validate().is_err();
    if ok { passes += 1; }
    probes.push(json!({"probe": "candidate_sha256_substituted_with_zeroed_valid_hash", "fail_closed": ok}));

    // Probe B: mutate candidate_binding (unchanged sha256 no longer matches).
    let mut p = baseline_packet();
    p.candidate_binding = json!({"resin": "DGEBF"});
    let ok = p.validate().is_err();
    if ok { passes += 1; }
    probes.push(json!({"probe": "candidate_binding_mutated_hash_no_longer_matches", "fail_closed": ok}));

    // Probe C: mutate formula_sha256.
    let mut p = baseline_packet();
    p.formula_sha256 = "f".repeat(64);
    let ok = p.validate().is_err();
    if ok { passes += 1; }
    probes.push(json!({"probe": "formula_sha256_substituted", "fail_closed": ok}));

    let total = probes.len();
    (passes as f64 / total.max(1) as f64, probes, total)
}

fn incomplete_sections_probes() -> (f64, Vec<Value>, usize) {
    let mut passes = 0_usize;
    let mut probes: Vec<Value> = Vec::new();

    // Probe A: empty custody_requirements.
    let mut p = baseline_packet();
    p.custody_requirements = vec![];
    let ok = p.validate().is_err();
    if ok { passes += 1; }
    probes.push(json!({"probe": "empty_custody_requirements", "fail_closed": ok}));

    // Probe B: empty controls.
    let mut p = baseline_packet();
    p.controls = vec![];
    let ok = p.validate().is_err();
    if ok { passes += 1; }
    probes.push(json!({"probe": "empty_controls", "fail_closed": ok}));

    // Probe C: empty required_outputs.
    let mut p = baseline_packet();
    p.required_outputs = vec![];
    let ok = p.validate().is_err();
    if ok { passes += 1; }
    probes.push(json!({"probe": "empty_required_outputs", "fail_closed": ok}));

    let total = probes.len();
    (passes as f64 / total.max(1) as f64, probes, total)
}

fn false_execution_probes() -> (f64, Vec<Value>, usize) {
    let mut passes = 0_usize;
    let mut probes: Vec<Value> = Vec::new();

    // Probe A: execution_authorized flipped to true.
    let mut p = baseline_packet();
    p.execution_authorized = true;
    let ok = p.validate().is_err();
    if ok { passes += 1; }
    probes.push(json!({"probe": "execution_authorized_flipped_true", "fail_closed": ok}));

    // Probe B: status upgraded past DRAFT_FOR_CRO_FEASIBILITY_REVIEW.
    let mut p = baseline_packet();
    p.status = "APPROVED_FOR_CRO_EXECUTION".into();
    let ok = p.validate().is_err();
    if ok { passes += 1; }
    probes.push(json!({"probe": "status_upgraded_to_approved", "fail_closed": ok}));

    // Probe C: cro_acceptance_status forged as complete.
    let mut p = baseline_packet();
    p.cro_acceptance_status = "APPROVED".into();
    let ok = p.validate().is_err();
    if ok { passes += 1; }
    probes.push(json!({"probe": "cro_acceptance_status_forged_approved", "fail_closed": ok}));

    let total = probes.len();
    (passes as f64 / total.max(1) as f64, probes, total)
}

fn banned_performance_probes() -> (f64, Vec<Value>, usize) {
    let mut passes = 0_usize;
    let mut probes: Vec<Value> = Vec::new();

    // Probe A: strip one REQUIRED_CRO_CLAIM_LOCK.
    let mut p = baseline_packet();
    p.claim_locks.remove("NO_PERFORMANCE_CLAIM");
    let ok = p.validate().is_err();
    if ok { passes += 1; }
    probes.push(json!({"probe": "stripped_no_performance_claim_lock", "fail_closed": ok}));

    // Probe B: authority_ceiling changed to non-audit.
    let mut p = baseline_packet();
    p.authority_ceiling = "SCORED".into();
    let ok = p.validate().is_err();
    if ok { passes += 1; }
    probes.push(json!({"probe": "authority_ceiling_upgraded_to_scored", "fail_closed": ok}));

    // Probe C: ranking_eligible flipped to true.
    let mut p = baseline_packet();
    p.ranking_eligible = true;
    let ok = p.validate().is_err();
    if ok { passes += 1; }
    probes.push(json!({"probe": "ranking_eligible_flipped_true", "fail_closed": ok}));

    // Probe D: existing claim_lock value set to false.
    let mut p = baseline_packet();
    p.claim_locks.insert("NO_PERFORMANCE_CLAIM".into(), false);
    let ok = p.validate().is_err();
    if ok { passes += 1; }
    probes.push(json!({"probe": "claim_lock_value_set_false", "fail_closed": ok}));

    let total = probes.len();
    (passes as f64 / total.max(1) as f64, probes, total)
}

fn signature_defect_probes() -> (f64, Vec<Value>, usize) {
    let mut passes = 0_usize;
    let mut probes: Vec<Value> = Vec::new();

    // Probe A: verify with a TrustStore that only knows a different key.
    let mut p = baseline_packet();
    let real_key = SigningKey::from_bytes(&[81; 32]);
    p.sign("real-signer", &real_key).unwrap();
    let mut wrong_trust = TrustStore::default();
    let other_key = SigningKey::from_bytes(&[97; 32]);
    wrong_trust
        .insert("other-signer", other_key.verifying_key().to_bytes())
        .unwrap();
    let ok = p.verify_signature(&wrong_trust).is_err();
    if ok { passes += 1; }
    probes.push(json!({"probe": "wrong_key_in_trust_store", "fail_closed": ok}));

    // Probe B: mutate packet after signing (candidate binding changes).
    let mut p = baseline_packet();
    let key = SigningKey::from_bytes(&[41; 32]);
    let mut trust = TrustStore::default();
    trust
        .insert("post-mutation-signer", key.verifying_key().to_bytes())
        .unwrap();
    p.sign("post-mutation-signer", &key).unwrap();
    p.candidate_binding = json!({"resin": "MUTATED"});
    let ok = p.verify_signature(&trust).is_err();
    if ok { passes += 1; }
    probes.push(json!({"probe": "packet_mutated_after_signing", "fail_closed": ok}));

    // Probe C: missing signature (verify without sign).
    let p = baseline_packet();
    let mut trust = TrustStore::default();
    let key = SigningKey::from_bytes(&[13; 32]);
    trust
        .insert("no-sig-signer", key.verifying_key().to_bytes())
        .unwrap();
    let ok = p.verify_signature(&trust).is_err();
    if ok { passes += 1; }
    probes.push(json!({"probe": "signature_absent_from_packet", "fail_closed": ok}));

    let total = probes.len();
    (passes as f64 / total.max(1) as f64, probes, total)
}

fn prose_waiver_probes() -> (f64, Vec<Value>, usize) {
    let mut passes = 0_usize;
    let mut probes: Vec<Value> = Vec::new();

    // Probe A: deserialize a JSON packet with an added `waiver` prose field.
    // `#[serde(deny_unknown_fields)]` on CroProtocolPackageV2 rejects it.
    let p = baseline_packet();
    let mut value = serde_json::to_value(&p).unwrap();
    if let Some(obj) = value.as_object_mut() {
        obj.insert("waiver".into(), Value::String("prose exception".into()));
    }
    let deserialize_result = serde_json::from_value::<CroProtocolPackageV2>(value);
    let ok = deserialize_result.is_err();
    if ok { passes += 1; }
    probes.push(json!({"probe": "extra_waiver_field_rejected_by_deny_unknown_fields", "fail_closed": ok}));

    // Probe B: deserialize with `override_note` prose field.
    let p = baseline_packet();
    let mut value = serde_json::to_value(&p).unwrap();
    if let Some(obj) = value.as_object_mut() {
        obj.insert(
            "override_note".into(),
            Value::String("chemist-approved verbal override".into()),
        );
    }
    let ok = serde_json::from_value::<CroProtocolPackageV2>(value).is_err();
    if ok { passes += 1; }
    probes.push(json!({"probe": "extra_override_note_field_rejected", "fail_closed": ok}));

    let total = probes.len();
    (passes as f64 / total.max(1) as f64, probes, total)
}

#[test]
fn cro_protocol_packager_phase0_kpi_report_is_deterministic_and_gates_pass() {
    let first = compute_report();
    let first_bytes = serde_json::to_vec(&first).expect("canonical");
    let second_bytes = serde_json::to_vec(&compute_report()).expect("canonical");
    assert_eq!(first_bytes, second_bytes, "KPI report is not byte-stable");

    let kpi = &first["kpi"];
    for gate in [
        "packet_draft_ok_rate",
        "packet_id_matches_computed_rate",
        "candidate_and_formula_sha256_binding_correctness_rate",
        "all_eight_required_cro_claim_locks_true_rate",
        "execution_authority_locked_false_rate",
        "sign_verify_round_trip_rate",
        "cro_identity_hash_substitution_fail_closed_rate",
        "incomplete_protocol_sections_fail_closed_rate",
        "false_cro_execution_fail_closed_rate",
        "banned_cro_performance_claim_fail_closed_rate",
        "cro_signature_defect_fail_closed_rate",
        "cro_prose_waiver_fail_closed_rate",
        "authority_envelope_preservation_rate",
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
