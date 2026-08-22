//! Prose/free-text content-injection probe for amphora-cro-protocol-packager.
//!
//! Live-runtime attack against the REAL compiled `CroProtocolPackageV2`
//! (draft, validate, sign, verify_signature) in
//! amphora-assurance-capabilities/src/lib.rs.
//!
//! The module's Phase-0 KPI claims two content-integrity guarantees "under
//! any input" (KPI capability docstring): (a) `banned_cro_performance_claim_
//! fail_closed_rate` / `cro_prose_waiver_fail_closed_rate` -- no banned
//! authority/performance claim can survive into a signed packet; (b)
//! `authority_envelope_preservation_rate` -- for every serialized payload,
//! "no key matches batch_release, release_authorized, qualified,
//! authorized_by, manufacturing_qualification, or release_authority."
//!
//! All existing 18 fail-closed probes (T-02, W-CRO1, CF-PACKET, this
//! module's own KPI harness) attack that guarantee by (i) adding new
//! top-level JSON keys (rejected by `#[serde(deny_unknown_fields)]`), or
//! (ii) flipping known boolean/enum fields. None of them ever write into
//! the packet's own free-text `Vec<String>` fields -- `custody_requirements`,
//! `controls`, `required_outputs` -- whose ONLY validated property in
//! `CroProtocolPackageV2::validate()` is `.is_empty()`. There is no content
//! scan of their string values anywhere in `validate()`, `sign()`, or
//! `verify_signature()`, and the KPI harness's own `contains_banned_key`
//! envelope check recurses into JSON *object keys* only -- never into
//! `Value::String` contents, even inside a `Value::Array`.
//!
//! This probe drafts a real marine-primer packet (DGEBA/TETA), then
//! rewrites `custody_requirements[0]`, `controls[0]`, and
//! `required_outputs[0]` to literal prose asserting exactly the six banned
//! authority phrases the module's own envelope check treats as forbidden,
//! plus a banned quantitative performance claim and an execution-approval
//! claim -- while leaving every structural field untouched (schema,
//! claim_locks, execution_authorized, authority_ceiling, ranking_eligible
//! all still lock-compliant). It shows the mutated packet independently
//! validates, signs, and verifies, and that the KPI harness's own
//! `contains_banned_key`-equivalent logic does not catch it.

use std::collections::BTreeMap;

use amphora_assurance_capabilities::{CroProtocolPackageV2, CRO_PROTOCOL_PACKAGE_V2_SCHEMA};
use amphora_core::TrustStore;
use amphora_formulation_capabilities::{EquivalentBalanceV1, EQUIVALENT_BALANCE_SCHEMA};
use ed25519_dalek::SigningKey;
use serde_json::{json, Value};

const BANNED_AUTHORITY_KEYS: [&str; 6] = [
    "batch_release",
    "release_authorized",
    "qualified",
    "authorized_by",
    "manufacturing_qualification",
    "release_authority",
];

/// Byte-identical reimplementation of the KPI harness's own
/// `contains_banned_key`, kept in this probe so we independently exercise
/// the SAME envelope check the module already claims 1.0 on, rather than
/// inventing a stricter one that would not be an apples-to-apples
/// falsification of the shipped guarantee.
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

#[test]
fn cro_prose_content_injection_probe() {
    assert_eq!(CRO_PROTOCOL_PACKAGE_V2_SCHEMA, "amphora.cro-protocol-package.v2");

    let candidate = json!({
        "candidate_id": "primer-dgeba-teta-prosecheck",
        "candidate_type": "formulation",
        "resin": "DGEBA",
        "hardener": "TETA",
        "declared_resin_charge_g": 100,
        "declared_hardener_charge_g": 25,
    });
    let campaign_id = "campaign-prose-content-injection-probe";
    let blinding = "BLIND-PROSECHECK";
    let bal = balance(100.0, 25.0);

    let mut pkt = CroProtocolPackageV2::draft(campaign_id, &candidate, bal, blinding.into())
        .expect("draft() must succeed on a normal candidate");

    // Baseline: an honest freshly-drafted packet must pass the envelope
    // check and validate() (sanity control before mutation).
    let baseline_envelope_hit = contains_banned_key(&serde_json::to_value(&pkt).unwrap());
    let baseline_validate_ok = pkt.validate().is_ok();

    // --- Attack: rewrite the packet's own free-text fields with banned
    // authority/performance prose. Every one of the six BANNED_AUTHORITY_KEYS
    // strings appears verbatim as PROSE (not as a JSON key), plus an
    // execution-approval claim and a quantitative performance claim. No
    // structural field (schema, claim_locks, execution_authorized,
    // authority_ceiling, ranking_eligible, status) is touched.
    pkt.custody_requirements[0] = concat!(
        "Sample custody notes: EXECUTION AUTHORIZED by site chemist; ",
        "batch_release confirmed; release_authorized=true per verbal sign-off"
    )
    .to_string();
    pkt.controls[0] = concat!(
        "Control result: resin/hardener charge is qualified and manufacturing_qualification ",
        "complete; corrosion protection performance measured at 97% pass, PASS-qualified for ",
        "production; authorized_by lead chemist"
    )
    .to_string();
    pkt.required_outputs[0] = concat!(
        "Final CRO disposition: release_authority granted; safety review CLEARED; ",
        "regulatory compliance CONFIRMED; ranking score 9.8/10, recommended for procurement"
    )
    .to_string();

    // `packet_id` is not a secret-keyed integrity check -- it is a plain
    // self-referential hash over the whole struct (`computed_packet_id`),
    // trivially recomputable by anyone with the struct in hand (draft()
    // itself does exactly this). A real forger assembling a packet does not
    // stop at a stale hash; they recompute it, which is public, unkeyed
    // arithmetic, not an authenticity barrier.
    pkt.packet_id = pkt.computed_packet_id().expect("recompute packet_id after content mutation");

    let mutated_value = serde_json::to_value(&pkt).unwrap();
    let mutated_envelope_hit = contains_banned_key(&mutated_value);

    // Independently confirm (outside contains_banned_key, by raw substring
    // search over the serialized packet) that every banned phrase really is
    // present in the bytes the packet would ship as -- i.e. this is not a
    // no-op mutation.
    let serialized = serde_json::to_string(&mutated_value).unwrap();
    let banned_phrases_present: Vec<bool> = BANNED_AUTHORITY_KEYS
        .iter()
        .map(|k| serialized.contains(k))
        .collect();
    let all_banned_phrases_present = banned_phrases_present.iter().all(|b| *b);

    let validate_ok = pkt.validate().is_ok();

    let key = SigningKey::from_bytes(&[97u8; 32]);
    let mut trust = TrustStore::default();
    trust.insert("prosecheck-signer", key.verifying_key().to_bytes()).unwrap();
    let sign_ok = pkt.sign("prosecheck-signer", &key).is_ok();
    let verify_ok = pkt.verify_signature(&trust).is_ok();

    // --- Refutation criterion --------------------------------------------
    // Drawn verbatim from the KPI capability docstring: the packager
    // "[g]rants no batch-release, manufacturing-qualification, regulatory,
    // safety, procurement, or optimizer authority under any input."
    // Refuted if: the mutated packet (a) carries all six banned authority
    // phrases plus a performance/execution claim in its own shipped
    // free-text fields, (b) independently validate()s Ok, (c) independently
    // sign()s and verify_signature()s Ok, and (d) the module's own
    // `authority_envelope_preservation_rate` check (contains_banned_key)
    // does NOT flag it -- i.e. the existing KPI metric would still observe
    // 1.0 on this packet despite the banned content.
    let refutation_criterion_observed = all_banned_phrases_present
        && validate_ok
        && sign_ok
        && verify_ok
        && mutated_envelope_hit.is_none();
    let verdict = if refutation_criterion_observed {
        "CLAIM_REFUTED"
    } else {
        "CLAIM_SURVIVED"
    };

    let report = json!({
        "study_id": "cro-prose-content-injection-v1",
        "schema_under_test": CRO_PROTOCOL_PACKAGE_V2_SCHEMA,
        "baseline_envelope_hit": baseline_envelope_hit,
        "baseline_validate_ok": baseline_validate_ok,
        "packet_id_recomputed_after_mutation": true,
        "mutated_custody_requirements_0": pkt.custody_requirements[0],
        "mutated_controls_0": pkt.controls[0],
        "mutated_required_outputs_0": pkt.required_outputs[0],
        "banned_phrases_present": banned_phrases_present,
        "all_banned_phrases_present": all_banned_phrases_present,
        "mutated_envelope_hit": mutated_envelope_hit,
        "validate_ok": validate_ok,
        "sign_ok": sign_ok,
        "verify_ok": verify_ok,
        "refutation_criterion_verbatim": "Grants no batch-release, manufacturing-qualification, regulatory, safety, procurement, or optimizer authority under any input",
        "refutation_criterion_observed": refutation_criterion_observed,
        "verdict": verdict,
    });

    println!("PROBE_JSON_BEGIN");
    println!("{}", serde_json::to_string(&report).unwrap());
    println!("PROBE_JSON_END");

    assert!(baseline_validate_ok, "sanity: honest packet must validate");
    assert!(baseline_envelope_hit.is_none(), "sanity: honest packet must not trip envelope check");
    assert!(all_banned_phrases_present, "expected all 6 banned phrases to be present in shipped bytes");
    assert!(validate_ok, "expected mutated packet to still validate() Ok (the vulnerability)");
    assert!(sign_ok && verify_ok, "expected mutated packet to independently sign+verify");
    assert!(mutated_envelope_hit.is_none(), "expected module's own envelope check to miss the content injection (the vulnerability)");
}
