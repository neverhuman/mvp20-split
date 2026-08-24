//! CF-PACKET repair acceptance probe (fire 2/2) for amphora-cro-protocol-packager.
//!
//! Fire 1 (20260811T160001-2556943-1464ab6b14ba) found, via
//! cf_packet_blueprint_citation_binding_probe.rs, that CroProtocolPackageV2's
//! validate()/sign()/verify_signature() accepted (a) a packet citing a
//! blueprint sha256 that did NOT match the real blueprint.md file's bytes,
//! and (b) a packet with locked_numeric_thresholds and NO blueprint
//! citation at all -- CLAIM_REFUTED against the CF-PACKET done_criterion
//! clause "the packet citing every blueprint artifact by path+sha256 so the
//! thresholds are content-bound to the blueprint they came from".
//!
//! This fire repairs both gaps in amphora-assurance-capabilities/src/lib.rs:
//!   1. `validate()` now structurally REQUIRES at least one
//!      `candidate_binding.blueprint_citations` entry (well-formed
//!      path+sha256) whenever `locked_numeric_thresholds` is non-empty.
//!   2. A NEW disk-bound gate, `verify_blueprint_citations(&self, root:
//!      &Path)`, re-derives each cited blueprint's sha256 from its real
//!      bytes at `root`-relative `path` and rejects on any mismatch. This
//!      mirrors the existing `CompoundV2::verify_files(root)` /
//!      `MethodRegistry::verify_files(root)` convention in
//!      amphora-core::compound_v2 (validate() stays pure/disk-independent;
//!      a separate verify_*(root) does the content-binding I/O). Callers
//!      assembling a "final assembly" CF-PACKET packet MUST call both
//!      `validate()` and `verify_blueprint_citations(root)`.
//!
//! This probe re-runs the T-02/W-CRO1 attack shape (0 regressions expected)
//! and the exact NEW axis fire 1 found broken, now against the repaired
//! runtime, plus a positive control that plants the identical
//! mismatched-hash defect fire 1 used and confirms verify_blueprint_citations
//! detects it.

use std::collections::BTreeMap;
use std::fs;
use std::path::Path;

use amphora_assurance_capabilities::{CroProtocolPackageV2, CRO_PROTOCOL_PACKAGE_V2_SCHEMA};
use amphora_core::TrustStore;
use amphora_formulation_capabilities::{EquivalentBalanceV1, EQUIVALENT_BALANCE_SCHEMA};
use base64::engine::general_purpose::STANDARD as B64;
use base64::Engine;
use ed25519_dalek::SigningKey;
use serde_json::{json, Value};
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

const BLUEPRINT_REL_PATH: &str = "amphora-report-packager/reference/mvp20/out/blueprint.md";

fn workspace_root() -> &'static Path {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .expect("amphora-assurance-capabilities must be inside the workspace")
}

fn sha256_hex(bytes: &[u8]) -> String {
    let mut hasher = Sha256::new();
    hasher.update(bytes);
    format!("{:x}", hasher.finalize())
}

fn real_blueprint_sha256() -> String {
    let bytes = fs::read(workspace_root().join(BLUEPRINT_REL_PATH))
        .expect("blueprint.md must be readable from the workspace");
    sha256_hex(&bytes)
}

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

fn candidate_with_citation(blueprint_sha256: &str) -> Value {
    json!({
        "resin": "DGEBA",
        "hardener": "TETA",
        "blueprint_citations": [
            {
                "path": BLUEPRINT_REL_PATH,
                "sha256": blueprint_sha256,
            }
        ]
    })
}

fn baseline_packet_with_citation(blueprint_sha256: &str) -> CroProtocolPackageV2 {
    let candidate = candidate_with_citation(blueprint_sha256);
    let mut p = CroProtocolPackageV2::draft(
        "cf-packet-repair-probe-campaign",
        &candidate,
        balance(100.0, 25.0),
        "BLIND-CFPACKET-REPAIR-000".into(),
    )
    .expect("baseline draft");
    p.locked_numeric_thresholds
        .insert("recoat_window_min_hours".into(), 6.0);
    p.locked_numeric_thresholds
        .insert("pull_off_strength_min_mpa".into(), 5.0);
    p.protocol_lock_sha256 = Some(
        p.computed_protocol_lock_sha256()
            .expect("compute protocol lock hash"),
    );
    p.packet_id = p.computed_packet_id().expect("recompute packet_id");
    p
}

fn sign_fresh(mut p: CroProtocolPackageV2) -> (CroProtocolPackageV2, TrustStore, Result<(), String>) {
    let key = SigningKey::from_bytes(&[211; 32]);
    let mut trust = TrustStore::default();
    trust
        .insert("cf-packet-repair-signer", key.verifying_key().to_bytes())
        .unwrap();
    let sign_result = p.sign("cf-packet-repair-signer", &key).map_err(|e| e.to_string());
    (p, trust, sign_result)
}

#[test]
fn cf_packet_repair_content_binding_probe() {
    let root = workspace_root();
    let real_hash = real_blueprint_sha256();
    let wrong_hash = "f".repeat(64);
    assert_ne!(real_hash, wrong_hash);

    let mut probes: Vec<Value> = Vec::new();
    let mut n_slipped_through = 0_usize;

    // -----------------------------------------------------------------
    // Control: correctly-cited final-assembly packet round-trips clean
    // through validate()/sign()/verify_signature() AND the new
    // verify_blueprint_citations(root) gate.
    // -----------------------------------------------------------------
    let control_accepted;
    {
        let p = baseline_packet_with_citation(&real_hash);
        let validate_ok = p.validate().is_ok();
        let citation_ok = p.verify_blueprint_citations(root).is_ok();
        let (signed, trust, sign_res) = sign_fresh(p);
        let verify_ok = sign_res.is_ok() && signed.verify_signature(&trust).is_ok();
        control_accepted = validate_ok && citation_ok && sign_res.is_ok() && verify_ok;
        probes.push(json!({
            "group": "control_correct_citation",
            "probe": "correctly_cited_packet_round_trips_including_new_gate",
            "validate_ok": validate_ok,
            "verify_blueprint_citations_ok": citation_ok,
            "sign_ok": sign_res.is_ok(),
            "verify_signature_ok": verify_ok,
            "expected_accept": true,
            "accepted": control_accepted,
        }));
    }

    // -----------------------------------------------------------------
    // T-02/W-CRO1 attack shape re-run on the repaired runtime (0
    // regressions expected).
    // -----------------------------------------------------------------
    {
        let mut p = baseline_packet_with_citation(&real_hash);
        p.execution_authorized = true;
        let fail_closed = p.validate().is_err();
        if !fail_closed {
            n_slipped_through += 1;
        }
        probes.push(json!({"group": "t02_shape_execution_authorized", "fail_closed": fail_closed}));
    }
    for lock in REQUIRED_CRO_CLAIM_LOCKS {
        let mut p = baseline_packet_with_citation(&real_hash);
        p.claim_locks.remove(lock);
        let fail_closed = p.validate().is_err();
        if !fail_closed {
            n_slipped_through += 1;
        }
        probes.push(json!({"group": "t02_shape_claim_lock_strip", "lock": lock, "fail_closed": fail_closed}));
    }
    {
        let mut p = baseline_packet_with_citation(&real_hash);
        p.status = "APPROVED_FOR_EXECUTION".into();
        let fail_closed = p.validate().is_err();
        if !fail_closed {
            n_slipped_through += 1;
        }
        probes.push(json!({"group": "t02_shape_status_drift", "fail_closed": fail_closed}));
    }
    {
        let p = baseline_packet_with_citation(&real_hash);
        let (mut signed, trust, sign_res) = sign_fresh(p);
        assert!(sign_res.is_ok());
        let control_ok = signed.verify_signature(&trust).is_ok();
        let sig = signed.signature.clone().expect("signed");
        let mut payload_bytes = B64.decode(sig.payload.as_bytes()).expect("valid b64 payload");
        payload_bytes[0] ^= 0x01;
        let mut tampered = sig.clone();
        tampered.payload = B64.encode(payload_bytes);
        signed.signature = Some(tampered);
        let fail_closed = signed.verify_signature(&trust).is_err();
        if !fail_closed {
            n_slipped_through += 1;
        }
        probes.push(json!({
            "group": "t02_shape_one_byte_mutation",
            "control_unmutated_signature_verifies": control_ok,
            "fail_closed": fail_closed,
        }));
    }
    {
        let mut p = baseline_packet_with_citation(&real_hash);
        p.protocol_lock_sha256 = Some("a".repeat(64));
        p.packet_id = p.computed_packet_id().expect("recompute packet_id");
        let fail_closed = p.validate().is_err();
        if !fail_closed {
            n_slipped_through += 1;
        }
        probes.push(json!({"group": "w_cro1_shape_lock_hash_not_derived", "fail_closed": fail_closed}));
    }

    // -----------------------------------------------------------------
    // REPAIRED axis: the exact clauses fire 1 found unenforced.
    // -----------------------------------------------------------------
    let mut blueprint_axis: Vec<Value> = Vec::new();
    let mut gap_still_present = false;

    // (i) [PRE-COMMITTED CRITERION CLAUSE] cited blueprint sha256 does NOT
    //     match the real blueprint.md file -> must now fail closed via
    //     verify_blueprint_citations(root). validate()/sign()/
    //     verify_signature() alone cannot see this (no disk I/O by design,
    //     see doc comment) -- verify_blueprint_citations(root) is now the
    //     required additional gate for a "final assembly" packet.
    {
        let p = baseline_packet_with_citation(&wrong_hash);
        let validate_ok = p.validate().is_ok();
        let citation_check = p.verify_blueprint_citations(root);
        let citation_ok = citation_check.is_ok();
        let (signed, trust, sign_res) = sign_fresh(p);
        let verify_ok = sign_res.is_ok() && signed.verify_signature(&trust).is_ok();
        let fully_accepted_despite_wrong_hash = validate_ok && citation_ok && sign_res.is_ok() && verify_ok;
        if fully_accepted_despite_wrong_hash {
            gap_still_present = true;
        }
        blueprint_axis.push(json!({
            "probe": "wrong_blueprint_sha256_citation",
            "criterion_clause": "cited blueprint sha256 that does not match the blueprint file",
            "cited_sha256": wrong_hash,
            "real_blueprint_sha256": real_hash,
            "validate_ok": validate_ok,
            "verify_blueprint_citations_ok": citation_ok,
            "verify_blueprint_citations_err": citation_check.err().map(|e| e.to_string()),
            "sign_ok": sign_res.is_ok(),
            "verify_signature_ok": verify_ok,
            "fully_accepted_despite_mismatched_citation": fully_accepted_despite_wrong_hash,
            "rejected_by": if !citation_ok { "verify_blueprint_citations" } else { "none -- GAP" },
        }));
    }

    // (ii) no blueprint citation present at all, with thresholds locked ->
    //      validate() now structurally rejects (no disk I/O needed).
    {
        let candidate = json!({"resin": "DGEBA", "hardener": "TETA"});
        let mut p = CroProtocolPackageV2::draft(
            "cf-packet-repair-probe-campaign",
            &candidate,
            balance(100.0, 25.0),
            "BLIND-CFPACKET-REPAIR-001".into(),
        )
        .expect("draft without citation");
        p.locked_numeric_thresholds
            .insert("recoat_window_min_hours".into(), 6.0);
        p.protocol_lock_sha256 = Some(
            p.computed_protocol_lock_sha256()
                .expect("compute protocol lock hash"),
        );
        p.packet_id = p.computed_packet_id().expect("recompute packet_id");
        let validate_ok = p.validate().is_ok();
        let (signed, trust, sign_res) = sign_fresh(p);
        let verify_ok = sign_res.is_ok() && signed.verify_signature(&trust).is_ok();
        let accepted_with_no_citation = validate_ok && sign_res.is_ok() && verify_ok;
        if accepted_with_no_citation {
            gap_still_present = true;
        }
        blueprint_axis.push(json!({
            "probe": "no_blueprint_citation_present",
            "validate_ok": validate_ok,
            "sign_ok": sign_res.is_ok(),
            "verify_signature_ok": verify_ok,
            "accepted_with_no_citation": accepted_with_no_citation,
            "rejected_by": if !validate_ok { "validate" } else { "none -- GAP" },
        }));
    }

    // -----------------------------------------------------------------
    // POSITIVE CONTROL: plant the identical mismatched-hash defect fire 1
    // used, into a fresh copy of the (now-passing) real-citation packet,
    // and confirm verify_blueprint_citations(root) fires on it while the
    // unmutated packet does not.
    // -----------------------------------------------------------------
    let planted = {
        let mut p = baseline_packet_with_citation(&real_hash);
        // Mutate the candidate_binding's cited sha256 in place (path
        // untouched) -- same defect shape as axis (i), applied to a copy
        // of the packet the control already proved passes clean.
        p.candidate_binding["blueprint_citations"][0]["sha256"] = json!(wrong_hash);
        p.candidate_sha256 = amphora_core::stable_hash(&p.candidate_binding);
        p.packet_id = p.computed_packet_id().expect("recompute packet_id");
        p
    };
    let planted_detected = planted.verify_blueprint_citations(root).is_err();

    let result = json!({
        "harness": "cf_packet_repair_content_binding_probe",
        "schema_under_test": CRO_PROTOCOL_PACKAGE_V2_SCHEMA,
        "directive_probes": probes,
        "n_t02_shape_slipped_through": n_slipped_through,
        "control_correct_citation_accepted": control_accepted,
        "blueprint_axis": blueprint_axis,
        "blueprint_content_binding_gap_still_present": gap_still_present,
        "real_blueprint_path": BLUEPRINT_REL_PATH,
        "real_blueprint_sha256": real_hash,
        "positive_control": {
            "planted_defect": "candidate_binding.blueprint_citations[0].sha256 mutated to a value not matching the real blueprint.md bytes",
            "how_planted": format!("baseline_packet_with_citation(real_hash) cloned, then blueprint_citations[0].sha256 rewritten from {} to {}, candidate_sha256 and packet_id recomputed to keep the packet self-consistent", real_hash, wrong_hash),
            "detected": planted_detected,
            "evidence": "verify_blueprint_citations(root) returned Err(Binding) for the planted-defect packet",
        },
    });

    let out_path = std::env::var("CF_PACKET_REPAIR_PROBE_OUT")
        .unwrap_or_else(|_| {
            // Per-process, and under TMPDIR rather than a hardcoded /tmp. A fixed shared
            // path collides the moment a second account runs the suite: the file is owned
            // by whoever ran first and the write fails with EACCES, so the probe reports a
            // failure that has nothing to do with what it tests. Set CF_PACKET_REPAIR_PROBE_OUT
            // to pin the location when you want to read the output back.
            std::env::temp_dir()
                .join(format!("cf_packet_repair_probe_output.{}.json", std::process::id()))
                .to_string_lossy()
                .into_owned()
        });
    fs::write(&out_path, serde_json::to_vec_pretty(&result).unwrap())
        .expect("write probe output");

    assert!(control_accepted, "correctly-cited control packet must round-trip clean");
    assert_eq!(n_slipped_through, 0, "T-02/W-CRO1 attack shape regressed on repaired runtime");
    assert!(planted_detected, "positive control: planted mismatched-citation defect must be detected");
    assert!(!gap_still_present, "blueprint content-binding gap must be closed by the repair");
}
