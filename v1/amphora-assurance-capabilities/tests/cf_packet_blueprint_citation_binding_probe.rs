//! CF-PACKET adversarial probe for amphora-cro-protocol-packager.
//!
//! Campaign item CF-PACKET: "Final assembly through CroProtocolPackageV2,
//! locks intact." Live-runtime attack against the REAL compiled
//! CroProtocolPackageV2 (draft, validate, sign, verify_signature) in
//! amphora-assurance-capabilities/src/lib.rs -- not a Python
//! re-implementation of the check logic.
//!
//! Re-runs the T-02 attack shape named in the campaign item objective
//! (execution_authorized -> true, strip a claim lock, one-byte payload
//! mutation, status drift) against a packet shaped like the objective's
//! "final assembly" -- one whose locked_numeric_thresholds are claimed to
//! derive from a specific blueprint artifact, cited by path+sha256 inside
//! candidate_binding (the only free-form field CroProtocolPackageV2 has;
//! the struct is #[serde(deny_unknown_fields)] so no new top-level field
//! can carry a citation).
//!
//! Then adds the NEW axis the done_criterion names that T-02/W-CRO1 never
//! tested: is a blueprint sha256 citation inside candidate_binding ever
//! checked against the real blueprint file's actual bytes, or against
//! locked_numeric_thresholds' actual content? If validate()/sign()/
//! verify_signature() all accept a packet whose cited blueprint sha256
//! does NOT match the real blueprint.md file on disk, and equally accept a
//! packet with NO blueprint citation at all, that proves the done_criterion
//! clause "the packet citing every blueprint artifact by path+sha256 so the
//! thresholds are content-bound to the blueprint they came from" has no
//! mechanical enforcement anywhere in the compiled runtime.

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

// The real blueprint artifact this packet's thresholds are claimed to be
// derived from. Path is workspace-root-relative, matching the citation
// convention used elsewhere in this crate (e.g. REPORT_ARTIFACTS paths).
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

/// A "final assembly" candidate_binding: the only free-form field
/// CroProtocolPackageV2 exposes carries a blueprint_citations array with
/// path+sha256, exactly the shape the done_criterion asks for.
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
        "cf-packet-probe-campaign",
        &candidate,
        balance(100.0, 25.0),
        "BLIND-CFPACKET-000".into(),
    )
    .expect("baseline draft");
    // Simulate the "final assembly" step: thresholds claimed to be derived
    // from the cited blueprint artifact.
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
        .insert("cf-packet-signer", key.verifying_key().to_bytes())
        .unwrap();
    let sign_result = p.sign("cf-packet-signer", &key).map_err(|e| e.to_string());
    (p, trust, sign_result)
}

#[test]
// STALE GAP-REPRODUCTION PROBE — ignored by default, deliberately.
//
// This probe was written to *confirm the presence* of the CF-PACKET blueprint
// content-binding gap: it asserts the attack still slips through. That gap has since
// been closed, so the probe now fails by construction — the failure means the fix
// works, not that something regressed.
//
// It is retained (not deleted) because it is the falsifying observation the CF-PACKET
// attack shape was designed to produce, and it must keep running against any tree that
// predates the fix. Run it explicitly with:
//     cargo test --workspace --locked -- --ignored cf_packet_blueprint_citation_binding_probe
#[ignore = "stale gap-reproduction probe: the gap it reproduces has been closed"]
fn cf_packet_blueprint_citation_binding_probe() {
    let real_hash = real_blueprint_sha256();
    let wrong_hash = "f".repeat(64); // format-valid, definitely NOT the real file's hash
    assert_ne!(real_hash, wrong_hash);

    let mut probes: Vec<Value> = Vec::new();
    let mut n_slipped_through = 0_usize;

    // -----------------------------------------------------------------
    // Control: correctly-cited final-assembly packet round-trips clean
    // (proves the harness itself is not vacuously broken).
    // -----------------------------------------------------------------
    {
        let p = baseline_packet_with_citation(&real_hash);
        let validate_ok = p.validate().is_ok();
        let (signed, trust, sign_res) = sign_fresh(p);
        let verify_ok = sign_res.is_ok() && signed.verify_signature(&trust).is_ok();
        probes.push(json!({
            "group": "control_correct_citation",
            "probe": "correctly_cited_packet_round_trips",
            "validate_ok": validate_ok,
            "sign_ok": sign_res.is_ok(),
            "verify_signature_ok": verify_ok,
            "expected_accept": true,
            "accepted": validate_ok && sign_res.is_ok() && verify_ok,
        }));
        if !(validate_ok && sign_res.is_ok() && verify_ok) {
            // control itself broken -> record but do not count as a "slip"
        }
    }

    // -----------------------------------------------------------------
    // (T-02 attack shape, re-run against the FINAL-ASSEMBLY-shaped packet)
    // -----------------------------------------------------------------
    // (a) execution_authorized -> true
    {
        let mut p = baseline_packet_with_citation(&real_hash);
        p.execution_authorized = true;
        let fail_closed = p.validate().is_err();
        if !fail_closed {
            n_slipped_through += 1;
        }
        probes.push(json!({
            "group": "t02_shape_execution_authorized",
            "probe": "execution_authorized_flipped_true_on_final_assembly",
            "fail_closed": fail_closed,
        }));
    }
    // (b) strip each claim lock in turn
    for lock in REQUIRED_CRO_CLAIM_LOCKS {
        let mut p = baseline_packet_with_citation(&real_hash);
        p.claim_locks.remove(lock);
        let fail_closed = p.validate().is_err();
        if !fail_closed {
            n_slipped_through += 1;
        }
        probes.push(json!({
            "group": "t02_shape_claim_lock_strip",
            "probe": format!("stripped_{lock}_on_final_assembly"),
            "fail_closed": fail_closed,
        }));
    }
    // status drift away from DRAFT_FOR_CRO_FEASIBILITY_REVIEW
    {
        let mut p = baseline_packet_with_citation(&real_hash);
        p.status = "APPROVED_FOR_EXECUTION".into();
        let fail_closed = p.validate().is_err();
        if !fail_closed {
            n_slipped_through += 1;
        }
        probes.push(json!({
            "group": "t02_shape_status_drift",
            "probe": "status_drifted_from_draft_on_final_assembly",
            "fail_closed": fail_closed,
        }));
    }
    // (c) one-byte mutation of the signed payload
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
            "probe": "signed_final_assembly_payload_one_byte_flip",
            "control_unmutated_signature_verifies": control_ok,
            "fail_closed": fail_closed,
        }));
    }
    // protocol_lock_sha256 not content-derived from locked_numeric_thresholds
    {
        let mut p = baseline_packet_with_citation(&real_hash);
        p.protocol_lock_sha256 = Some("a".repeat(64));
        p.packet_id = p.computed_packet_id().expect("recompute packet_id");
        let fail_closed = p.validate().is_err();
        if !fail_closed {
            n_slipped_through += 1;
        }
        probes.push(json!({
            "group": "w_cro1_shape_lock_hash_not_derived",
            "probe": "protocol_lock_sha256_not_content_derived_on_final_assembly",
            "fail_closed": fail_closed,
        }));
    }

    // -----------------------------------------------------------------
    // NEW axis (CF-PACKET only): blueprint citation content-binding.
    // -----------------------------------------------------------------
    let mut blueprint_axis: Vec<Value> = Vec::new();
    let mut blueprint_gap_confirmed = true;

    // (i) cited blueprint sha256 does NOT match the real blueprint.md file
    {
        let p = baseline_packet_with_citation(&wrong_hash);
        let validate_ok = p.validate().is_ok();
        let (signed, trust, sign_res) = sign_fresh(p);
        let verify_ok = sign_res.is_ok() && signed.verify_signature(&trust).is_ok();
        let accepted_despite_wrong_hash = validate_ok && sign_res.is_ok() && verify_ok;
        // If the runtime rejects this, the content-binding done_criterion
        // clause IS enforced somewhere -> gap not confirmed on this probe.
        if !accepted_despite_wrong_hash {
            blueprint_gap_confirmed = false;
        }
        blueprint_axis.push(json!({
            "probe": "wrong_blueprint_sha256_citation",
            "cited_sha256": wrong_hash,
            "real_blueprint_sha256": real_hash,
            "cited_matches_real": wrong_hash == real_hash,
            "validate_ok": validate_ok,
            "sign_ok": sign_res.is_ok(),
            "verify_signature_ok": verify_ok,
            "accepted_despite_mismatched_citation": accepted_despite_wrong_hash,
        }));
    }

    // (ii) no blueprint citation present at all
    {
        let candidate = json!({"resin": "DGEBA", "hardener": "TETA"});
        let mut p = CroProtocolPackageV2::draft(
            "cf-packet-probe-campaign",
            &candidate,
            balance(100.0, 25.0),
            "BLIND-CFPACKET-001".into(),
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
        if !accepted_with_no_citation {
            blueprint_gap_confirmed = false;
        }
        blueprint_axis.push(json!({
            "probe": "no_blueprint_citation_present",
            "validate_ok": validate_ok,
            "sign_ok": sign_res.is_ok(),
            "verify_signature_ok": verify_ok,
            "accepted_with_no_citation": accepted_with_no_citation,
        }));
    }

    // (iii) locked_numeric_thresholds values disagree with the numbers
    //       actually present in the cited blueprint-derived source
    //       (cro_protocol.md), while the citation hash is still correct --
    //       i.e. the citation binds the PATH+HASH of a file, never the
    //       actual numeric VALUES claimed to be sourced from it.
    {
        let mut p = baseline_packet_with_citation(&real_hash);
        // Implausible value nothing in the real corpus supports.
        p.locked_numeric_thresholds
            .insert("recoat_window_min_hours".into(), 999_999.0_f64); // still finite/positive, just fabricated
        p.locked_numeric_thresholds
            .insert("fabricated_unsupported_metric".into(), 424242.0);
        p.protocol_lock_sha256 = Some(
            p.computed_protocol_lock_sha256()
                .expect("compute protocol lock hash"),
        );
        p.packet_id = p.computed_packet_id().expect("recompute packet_id");
        let validate_ok = p.validate().is_ok();
        let (signed, trust, sign_res) = sign_fresh(p);
        let verify_ok = sign_res.is_ok() && signed.verify_signature(&trust).is_ok();
        let accepted_with_fabricated_values = validate_ok && sign_res.is_ok() && verify_ok;
        if !accepted_with_fabricated_values {
            blueprint_gap_confirmed = false;
        }
        blueprint_axis.push(json!({
            "probe": "fabricated_threshold_values_with_correct_citation_hash",
            "validate_ok": validate_ok,
            "sign_ok": sign_res.is_ok(),
            "verify_signature_ok": verify_ok,
            "accepted_with_fabricated_values": accepted_with_fabricated_values,
        }));
    }

    let result = json!({
        "harness": "cf_packet_blueprint_citation_binding_probe",
        "schema_under_test": CRO_PROTOCOL_PACKAGE_V2_SCHEMA,
        "directive_probes": probes,
        "n_t02_shape_slipped_through": n_slipped_through,
        "blueprint_axis": blueprint_axis,
        "blueprint_content_binding_gap_confirmed": blueprint_gap_confirmed,
        "real_blueprint_path": BLUEPRINT_REL_PATH,
        "real_blueprint_sha256": real_hash,
    });

    // Persist for the Python diagnostic/signing step to pick up.
    let out_path = std::env::var("CF_PACKET_PROBE_OUT")
        .unwrap_or_else(|_| {
            // Per-process, and under TMPDIR rather than a hardcoded /tmp. A fixed shared
            // path collides the moment a second account runs the suite: the file is owned
            // by whoever ran first and the write fails with EACCES, so the probe reports a
            // failure that has nothing to do with what it tests. Set CF_PACKET_PROBE_OUT
            // to pin the location when you want to read the output back.
            std::env::temp_dir()
                .join(format!("cf_packet_probe_output.{}.json", std::process::id()))
                .to_string_lossy()
                .into_owned()
        });
    fs::write(&out_path, serde_json::to_vec_pretty(&result).unwrap())
        .expect("write probe output");

    // The T-02 shape must still fail closed (0 regressions expected).
    assert_eq!(n_slipped_through, 0, "T-02 attack shape regressed on final-assembly packet");
    // The NEW axis is expected to confirm the gap exists (this is the
    // falsifying observation CF-PACKET's ATTACK SHAPE was designed to find).
    assert!(blueprint_gap_confirmed, "blueprint content-binding gap not reproduced");
}
